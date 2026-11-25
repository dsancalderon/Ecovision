"""
EcoVision — Servidor y Aplicación Interactiva con Interfaz Web y PiP
====================================================================
Este script es una evolución interactiva de 'realtime_cam.py'.
Ejecuta la detección YOLO en tiempo real con la cámara web y transmite:
1. La interfaz web moderna con la máquina de 3 estados (Inicio -> Escaneando -> Resultado).
2. El feed de video Picture-in-Picture (PiP) ubicado en la esquina superior derecha.
3. Eventos en tiempo real mediante Server-Sent Events (SSE) y APIs JSON.

Uso:
    python realtime_ui_app.py
    python realtime_ui_app.py --port 5000
    python realtime_ui_app.py --desktop   (Abre en ventana de escritorio si pywebview está disponible)
"""

import os
import sys
import time
import json
import threading
import argparse
import webbrowser
from pathlib import Path

from flask import Flask, render_template, Response, jsonify, request, redirect
from desktop_runtime import ROOT, DATA, VERSION, DesktopSession, NativeLayout, model_path, revision, load_settings, save_settings

# ==========================================================================
# 1. Utilidades y Configuración de Modelo
# ==========================================================================

def search_best_model():
    return str(model_path())


# Mapeo de colores exclusivo por nombre de clase (BGR: Azul, Verde, Rojo)
CLASS_COLORS = {
    "botella_reciclable": (245, 175, 50),       # Celeste / Azul claro
    "botella_plastica_pet": (245, 175, 50),     # Celeste / Azul claro
    "botella": (245, 175, 50),
    "bottle": (245, 175, 50),                   # Modelo base YOLO
    "lata_aluminio": (219, 152, 52),            # Azul clásico
    "tetra_pak": (34, 126, 230),                # Naranja cálido
    "papel_carton": (182, 89, 155),             # Morado
}
DEFAULT_COLOR = (180, 180, 180)


def draw_styled_box(img, box, label, score, color=(245, 175, 50)):
    """Dibuja una caja delimitadora estilizada con esquinas modernas."""
    x1, y1, x2, y2 = map(int, box)
    
    # Rectángulo principal
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2, lineType=cv2.LINE_AA)
    
    # Esquinas decorativas
    corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
    if corner_len > 5:
        thick = 3
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), color, thick)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), color, thick)
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), color, thick)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), color, thick)
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), color, thick)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), color, thick)
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), color, thick)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), color, thick)

    # Texto de etiqueta
    tag = f"{label} ({score:.0%})"
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.55
    font_thick = 1
    (tw, th), _ = cv2.getTextSize(tag, font, font_scale, font_thick)
    
    label_y1 = max(0, y1 - th - 10)
    label_y2 = y1
    cv2.rectangle(img, (x1, label_y1), (x1 + tw + 12, label_y2), color, -1)
    
    text_color = (255, 255, 255)
    cv2.putText(img, tag, (x1 + 6, y1 - 6), font, font_scale, text_color, font_thick, lineType=cv2.LINE_AA)


# ==========================================================================
# 2. Gestor de Cámara y Detección de Alto Rendimiento (Multi-Hilo Desacoplado)
# ==========================================================================

class VisionCameraManager:
    """
    Administra la visión artificial con arquitectura desacoplada en 2 hilos:
    - Hilo 1 (Captura & Render): Lee la cámara a 30 FPS continuos sin bloqueos.
    - Hilo 2 (Inferencia Asíncrona): Ejecuta YOLO en segundo plano con imgsz optimizado (320px).
    """
    
    def __init__(self, model_path, camera_index=0, conf_threshold=0.75):
        global cv2, np
        import cv2
        import numpy as np
        self.model_path = model_path
        self.camera_index = camera_index
        self.conf_threshold = conf_threshold
        
        self.model = None
        self.cap = None
        self.is_running = False
        
        # Hilos
        self.capture_thread = None
        self.infer_thread = None
        self.lock = threading.Lock()
        
        # Buffers de frames
        self.raw_frame = None
        self.latest_jpeg = self._create_initial_placeholder()
        
        # Telemetría y estado
        self.cam_fps = 0.0
        self.ai_fps = 0.0
        self.cached_boxes = []  # Lista de detecciones activas
        self.active_detection = None
        self.detection_count = 0  # Objetos sobre el umbral en el último fotograma analizado

        # Contadores para la evaluación con la interfaz abierta (RNF-03) y la latencia automática (RNF-04)
        self.frame_seq = 0              # identificador del fotograma capturado más reciente
        self.capture_total = 0          # fotogramas leídos de la cámara
        self.inference_total = 0        # inferencias completadas
        self.new_frame_total = 0        # inferencias sobre un fotograma no analizado antes
        self.infer_ms = []              # duración de cada inferencia (ms)
        self.object_first_seen = None   # instante (monotonic) de la primera detección del objeto actual
        self._last_nonzero = 0.0
        self.last_infer_time = 0
        self.last_capture_time = 0
        
        self._load_model()

    def _create_initial_placeholder(self):
        """Crea un frame inicial en JPEG para evitar conexiones HTTP colgadas."""
        placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
        placeholder[:] = (20, 35, 25) # Verde oscuro de fondo
        cv2.putText(placeholder, "EcoVision - Inicializando Camara...", (100, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (34, 197, 94), 2, cv2.LINE_AA)
        ret, buf = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buf.tobytes() if ret else None

    def _load_model(self):
        try:
            from ultralytics import YOLO
            print(f"📦 [AI] Cargando modelo: {self.model_path}")
            # Limitar hilos de CPU para evitar sobrecarga
            import torch
            torch.set_num_threads(min(4, os.cpu_count() or 4))
            self.model = YOLO(self.model_path)
            print("✅ [AI] Modelo YOLO cargado exitosamente con aceleración CPU.")
        except Exception as e:
            print(f"❌ [AI ERROR] No se pudo cargar el modelo '{self.model_path}': {e}")
            self.model = None

    def start(self):
        """Inicia los hilos de captura e inferencia asíncrona."""
        if self.is_running:
            return
        
        self.is_running = True
        self._open_camera()
        
        # Iniciar hilo de captura continua
        self.capture_thread = threading.Thread(target=self._capture_and_stream_loop, daemon=True)
        self.capture_thread.start()

        # Iniciar hilo de inferencia IA en segundo plano
        self.infer_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.infer_thread.start()
        
        print("🎥 [CÁMARA] Pipeline de captura a 30 FPS + Inferencia IA asíncrona activos.")

    def _open_camera(self):
        try:
            target_idx = self.camera_index
            print(f"📷 [CÁMARA] Conectando a cámara en índice {target_idx}...")
            if sys.platform == "win32":
                self.cap = cv2.VideoCapture(target_idx, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(target_idx)

            if not self.cap.isOpened():
                print(f"⚠️ [CÁMARA] No se pudo abrir índice {target_idx}.")
                self.cap.release()
                self.cap = None

            if self.cap is not None:
                # Intentar configurar resolución
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)

                # Calentamiento y estabilización del sensor CMOS (evita pantalla negra inicial en Windows)
                warmed_frame = None
                for _ in range(15):
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        warmed_frame = frame
                    time.sleep(0.035)

                if warmed_frame is not None:
                    with self.lock:
                        self.raw_frame = warmed_frame
                        self.last_capture_time = time.monotonic()

                w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"✅ [CÁMARA] Cámara USB/Externa {target_idx} activa ({w}x{h} @ 30 FPS - Sensor Calibrado)")
            else:
                print("⚠️ [CÁMARA] No se detectó cámara física. Requiere reintentar desde el menú.")
        except Exception as e:
            print(f"⚠️ [CÁMARA] Error al iniciar cámara: {e}")
            self.cap = None

    def _inference_loop(self):
        """Hilo dedicado exclusivamente a inferencia YOLO (corre en paralelo sin congelar el video)."""
        prev_infer_time = time.time()
        
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.1)
                continue
            frame_to_infer = None
            with self.lock:
                if self.raw_frame is not None:
                    frame_to_infer = self.raw_frame.copy()
                    frame_id = self.frame_seq

            if frame_to_infer is None or self.model is None:
                time.sleep(0.02)
                continue

            try:
                t_infer0 = time.perf_counter()
                # Inferencia optimizada con imgsz=320 para velocidad 5x en CPU
                results = self.model.predict(
                    source=frame_to_infer,
                    conf=self.conf_threshold,
                    imgsz=320,
                    verbose=False
                )
                result = results[0]
                new_boxes = []
                best_det = None

                if result.boxes is not None and len(result.boxes) > 0:
                    best_box = max(result.boxes, key=lambda b: float(b.conf[0].item()))
                    best_conf = float(best_box.conf[0].item())
                    best_cls_id = int(best_box.cls[0].item())
                    best_class_name = result.names.get(best_cls_id, f"Clase {best_cls_id}").lower()

                    best_det = {
                        "class_name": best_class_name,
                        "confidence": best_conf,
                        "box": [float(c) for c in best_box.xyxy[0].cpu().numpy()]
                    }

                    for box in result.boxes:
                        coords = box.xyxy[0].cpu().numpy()
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        class_name = result.names.get(cls_id, f"Clase {cls_id}")
                        new_boxes.append((coords, class_name, conf))

                now = time.time()
                dt = now - prev_infer_time
                if dt > 0:
                    self.ai_fps = 0.8 * self.ai_fps + 0.2 * (1.0 / dt)
                prev_infer_time = now

                mono = time.monotonic()
                with self.lock:
                    self.cached_boxes = new_boxes
                    self.active_detection = best_det
                    # predict() ya filtra por conf_threshold, así que cada caja es un objeto válido
                    self.detection_count = len(new_boxes)
                    self.last_infer_time = now
                    # contadores de desempeño
                    self.inference_total += 1
                    if frame_id != getattr(self, "_last_frame_id", -1):
                        self.new_frame_total += 1
                        self._last_frame_id = frame_id
                    self.infer_ms.append((time.perf_counter() - t_infer0) * 1000.0)
                    if len(self.infer_ms) > 50000:
                        del self.infer_ms[:10000]
                    # latencia automática: primer instante en que el objeto actual superó el umbral
                    if new_boxes:
                        self._last_nonzero = mono
                        if self.object_first_seen is None:
                            self.object_first_seen = mono
                    elif self.object_first_seen is not None and mono - self._last_nonzero > 0.6:
                        self.object_first_seen = None  # el objeto salió del encuadre: siguiente intento

            except Exception as e:
                pass

            # Pequeña pausa para no saturar el 100% de la CPU
            time.sleep(0.01)

    def _capture_and_stream_loop(self):
        """Hilo de captura continua y renderizado de video fluido a 30 FPS."""
        prev_time = time.time()
        
        while self.is_running:
            frame = None
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    with self.lock:
                        self.raw_frame = None
                        self.active_detection = None
                        self.cached_boxes = []
                    time.sleep(0.05)
                    continue
                else:
                    self.last_capture_time = time.monotonic()
                    # Si el frame llega en negro por reajuste del sensor CMOS, conservar el frame anterior iluminado
                    if frame.mean() < 1.5:
                        with self.lock:
                            if self.raw_frame is not None and self.raw_frame.mean() > 5.0:
                                frame = self.raw_frame.copy()
            else:
                # Frame sintético en standby
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                frame[:] = (20, 35, 25)
                cv2.putText(frame, "EcoVision - Camara en espera", (400, 360),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 245, 160), 2)
                time.sleep(0.033)

            # Actualizar raw_frame para el hilo de inferencia
            with self.lock:
                self.raw_frame = frame
                if self.cap is not None and self.cap.isOpened():
                    self.frame_seq += 1
                    self.capture_total += 1
                boxes_to_draw = list(self.cached_boxes)
                current_detection = self.active_detection
                last_infer = self.last_infer_time

            # Limpiar cajas si hace más de 0.5s no hay inferencia reciente
            if time.time() - last_infer > 0.5:
                boxes_to_draw = []

            # Dibujar bounding boxes cacheadas sobre el frame actual en tiempo real
            display_frame = frame.copy()
            for coords, class_name, conf in boxes_to_draw:
                color = CLASS_COLORS.get(class_name.lower(), DEFAULT_COLOR)
                draw_styled_box(display_frame, coords, class_name, conf, color=color)

            # Cálculo de FPS de video
            curr_time = time.time()
            dt = curr_time - prev_time
            if dt > 0:
                self.cam_fps = 0.9 * self.cam_fps + 0.1 * (1.0 / dt)
            prev_time = curr_time

            # Barra superior HUD en el visor
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, 0), (display_frame.shape[1], 38), (10, 16, 30), -1)
            cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)

            model_name = Path(self.model_path).name
            hud_text = f"EcoVision | {model_name} | CAM: {self.cam_fps:.0f} FPS | AI: {self.ai_fps:.0f} FPS"
            cv2.putText(display_frame, hud_text, (12, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

            # Optimización de streaming: Redimensionar a 640x360 para compresión ultrarrápida
            stream_frame = cv2.resize(display_frame, (640, 360), interpolation=cv2.INTER_LINEAR)
            ret, buffer = cv2.imencode('.jpg', stream_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            if ret:
                with self.lock:
                    self.latest_jpeg = buffer.tobytes()

            # Ajuste dinámico de tasa de refresco (~30 FPS)
            time.sleep(0.005)

    def get_jpeg(self):
        with self.lock:
            return self.latest_jpeg

    def get_status(self):
        with self.lock:
            fresh = time.time() - self.last_infer_time < 1 and time.monotonic() - self.last_capture_time < 2
            return {
                "fps": float(f"{self.cam_fps:.1f}"),
                "ai_fps": float(f"{self.ai_fps:.1f}"),
                "active_detection": self.active_detection if fresh else None,
                "detection_count": self.detection_count if fresh else 0,
                "multiple_objects": fresh and self.detection_count > 1,
                "conf_threshold": self.conf_threshold,
                "model_name": Path(self.model_path).name,
                "camera_connected": self.cap is not None and self.cap.isOpened() and time.monotonic() - self.last_capture_time < 2
            }

    def get_perf(self):
        """Contadores acumulados desde el inicio de la sesión (para medir con la interfaz abierta)."""
        with self.lock:
            ms = sorted(self.infer_ms)
            n = len(ms)
            def pct(q):
                return round(ms[min(n - 1, int(round(q * (n - 1))))], 1) if n else None
            return {
                "t": time.monotonic(),
                "capture_total": self.capture_total,
                "inference_total": self.inference_total,
                "new_frame_total": self.new_frame_total,
                "infer_ms": {"n": n, "media": round(sum(ms) / n, 1) if n else None,
                             "mediana": pct(0.5), "p95": pct(0.95)},
                "camera_connected": self.cap is not None and self.cap.isOpened() and time.monotonic() - self.last_capture_time < 2,
            }

    def mark_result(self, class_name, confidence):
        """Latencia desde la primera detección del objeto hasta que la interfaz muestra el resultado."""
        with self.lock:
            first = self.object_first_seen
            self.object_first_seen = None  # el siguiente intento arranca un cronómetro nuevo
        if first is None:
            return None
        return round(time.monotonic() - first, 3)

    def stop(self):
        self.is_running = False
        for thread in (self.capture_thread, self.infer_thread):
            if thread and thread is not threading.current_thread():
                thread.join(timeout=10)
        if self.cap:
            self.cap.release()
        self.cap = None
        self.active_detection = None
        if any(t and t.is_alive() for t in (self.capture_thread, self.infer_thread)):
            raise RuntimeError("El motor anterior aún está terminando. Cierra EcoVision antes de cambiar de modo.")
        print("🛑 [CÁMARA] Cámara liberada.")



# ==========================================================================
# 3. Aplicación Flask y Rutas
# ==========================================================================

app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
session = DesktopSession(VisionCameraManager)
vision_manager = None


@app.before_request
def local_requests_only():
    if request.host.split(":")[0] not in {"127.0.0.1", "localhost"}:
        return jsonify(error="Solo conexiones locales."), 403
    if request.method == "POST" and (request.headers.get("Sec-Fetch-Site") == "cross-site" or
            (request.headers.get("Origin") and request.headers["Origin"] != request.host_url.rstrip("/"))):
        return jsonify(error="Origen no permitido."), 403


@app.after_request
def local_resources(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; media-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.context_processor
def desktop_context():
    media = {}
    for key in ("botella_plastica_pet", "lata_aluminio", "tetra_pak", "papel_carton", "vidrio", "no_reciclable"):
        if (ROOT / "static/videos" / f"{key}.mp4").is_file():
            media[key] = {"src": f"/static/videos/{key}.mp4"}
            if (ROOT / "static/videos" / f"{key}-poster.jpg").is_file():
                media[key]["poster"] = f"/static/videos/{key}-poster.jpg"
    return dict(app_version=VERSION, development=app.config.get("DEVELOPMENT", False), session_state=session.snapshot(), material_media=media,
                ui_revision=revision([ROOT / "static", ROOT / "templates"]) if app.config.get("DEVELOPMENT") else VERSION)


@app.route("/")
def index():
    return render_template("desktop.html")


@app.route("/workspace")
def workspace():
    state = session.snapshot()
    if state["phase"] != "ready" or state["mode"] not in {"simulation", "real"}:
        return redirect("/")
    return render_template("index.html", interface_only=state["mode"] == "simulation")


@app.route("/api/session")
def session_status():
    return jsonify(**session.snapshot(), version=VERSION, development=app.config.get("DEVELOPMENT", False),
                   ui_revision=revision([ROOT / "static", ROOT / "templates"]) if app.config.get("DEVELOPMENT") else VERSION,
                   camera_index=load_settings().get("camera_index", 0), model_provisional=True,
                   native_ready=app.config.get("NATIVE_READY", False), native_layout=app.config.get("NATIVE_LAYOUT", {}))


@app.route("/api/mode", methods=["POST"])
def select_mode():
    data = request.get_json(silent=True) or {}
    try:
        camera = data.get("camera_index", load_settings().get("camera_index", 0))
        if not session.select(data.get("mode"), camera):
            return jsonify(error="Espera a que termine la preparación actual."), 409
        save_settings({"camera_index": camera})
        return jsonify(status="accepted"), 202
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.route("/api/cameras")
def cameras():
    from camera_catalog import available_cameras
    try:
        return jsonify(cameras=available_cameras())
    except Exception:
        return jsonify(cameras=[], error="No se pudieron consultar las cámaras.")


@app.route("/favicon.ico")
def favicon():
    """Servir favicon de la aplicación."""
    from flask import send_from_directory
    ico_path = os.path.join(app.static_folder, "images")
    return send_from_directory(ico_path, "icon_ecovision.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/images/<path:filename>")
def serve_images(filename):
    """Redirecciona o sirve imágenes desde static/images."""
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.static_folder, "images"), filename)


def generate_video_stream():
    """Generador de frames MJPEG para el elemento <img> del frontend."""
    manager = session.manager
    while session.snapshot()["mode"] == "real" and manager and session.manager is manager and manager.is_running:
        if manager:
            jpeg = manager.get_jpeg()
            if jpeg:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
        time.sleep(0.03)


@app.route("/video_feed")
def video_feed():
    """Ruta del stream de video en vivo."""
    if session.snapshot()["mode"] != "real" or session.snapshot()["phase"] != "ready":
        return Response(status=409)
    return Response(generate_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def current_status():
    """Estado compartido por la API y los eventos, incluso sin cámara."""
    if session.snapshot()["mode"] != "real":
        return {"fps": 0, "ai_fps": 0, "active_detection": None,
                "camera_connected": False, "interface_only": True}
    if session.manager:
        return session.manager.get_status()
    return {"status": "error", "message": "Manager no inicializado"}


@app.route("/api/status")
def api_status():
    """Devuelve el estado actual de la detección, FPS y configuración."""
    return jsonify(current_status())


@app.route("/api/stream")
def api_stream():
    """Server-Sent Events (SSE) para enviar actualizaciones en tiempo real."""
    def event_stream():
        manager = session.manager
        while session.snapshot()["mode"] == "real" and manager and session.manager is manager:
            if manager:
                status = current_status()
                payload = json.dumps(status)
                yield f"data: {payload}\n\n"
            time.sleep(0.15)

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/api/perf")
def api_perf():
    """Contadores de captura e inferencia acumulados; los lee verification/medir_app.py (RNF-03 con interfaz)."""
    if session.snapshot()["mode"] != "real" or not session.manager:
        return jsonify(error="Solo disponible en modo real."), 409
    return jsonify(session.manager.get_perf())


@app.route("/api/latency_mark", methods=["POST"])
def api_latency_mark():
    """La interfaz avisa que mostró un resultado; se registra la latencia automática en outputs/latencias.csv (RNF-04)."""
    if session.snapshot()["mode"] != "real" or not session.manager:
        return jsonify(error="Solo disponible en modo real."), 409
    data = request.get_json(silent=True) or {}
    class_name = str(data.get("class_name", ""))[:40]
    confidence = float(data.get("confidence", 0) or 0)
    latency = session.manager.mark_result(class_name, confidence)
    status = session.manager.get_status()
    out_dir = ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "latencias.csv"
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        if new_file:
            f.write("fecha_hora,clase,confianza,latencia_s,fps_captura,inferencias_por_s\n")
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{class_name},{confidence:.3f},"
                f"{'' if latency is None else latency},{status['fps']},{status['ai_fps']}\n")
    return jsonify(latency_s=latency, archivo=str(path))


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    """Permite disparar una clasificación simulada desde el frontend o scripts externos."""
    if session.snapshot()["mode"] != "simulation" or session.snapshot()["phase"] != "ready":
        return jsonify(error="La simulación solo está disponible en modo Simulación."), 409
    data = request.get_json() or {}
    class_name = data.get("class_name", "botella_plastica_pet")
    confidence = float(data.get("confidence", 0.95))
    return jsonify({
        "status": "success",
        "simulated_class": class_name,
        "confidence": confidence
    })


# ==========================================================================
# 4. Función de Inicio Principal (Aplicación de Escritorio Nativa)
# ==========================================================================

def main():
    from werkzeug.serving import make_server
    import logging
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "yolo").mkdir(parents=True, exist_ok=True)
    log_file = DATA / "ecovision.log"
    if sys.stdout is None:
        sys.stdout = open(log_file, "a", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = sys.stdout
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="EcoVision Desktop")
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--serve", action="store_true", help="Backend local para verificación")
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--model")
    parser.add_argument("--diagnostics", metavar="JSON", help="Verificar el motor offline sin abrir cámara")
    parser.add_argument("--conf", type=float, default=.75)
    cameras = parser.add_mutually_exclusive_group()
    cameras.add_argument("--cam", type=int, dest="camera_index")
    cameras.add_argument("--cam1", action="store_const", const=0, dest="camera_index")
    cameras.add_argument("--cam2", action="store_const", const=1, dest="camera_index")
    cameras.add_argument("--sin-camara", "--no-cam", action="store_true")
    args = parser.parse_args()
    if args.diagnostics:
        from desktop_diagnostics import run
        return run(args.diagnostics)
    if args.camera_index is not None and not 0 <= args.camera_index <= 20:
        parser.error("Selecciona un índice entre 0 y 20.")
    if not 0.1 <= args.conf <= .95:
        parser.error("La confianza debe estar entre 0.1 y 0.95.")
    app.config["DEVELOPMENT"] = args.dev and not getattr(sys, "frozen", False)
    app.config["TEMPLATES_AUTO_RELOAD"] = app.config["DEVELOPMENT"]
    session.options.update(model_path=args.model, conf_threshold=args.conf)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    server = make_server("127.0.0.1", args.port, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"EcoVision {VERSION}: {url}", flush=True)
    try:  # los scripts de medición leen aquí la dirección del servidor local
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "server_url.txt").write_text(url, encoding="utf-8")
    except OSError:
        pass
    if args.sin_camara:
        session.select("simulation")
    elif args.camera_index is not None:
        session.select("real", args.camera_index)
    restart = threading.Event()
    finished = threading.Event()
    try:
        if args.serve or args.browser:
            if args.browser:
                webbrowser.open_new(url)
            while not finished.wait(.5):
                pass
        else:
            import webview

            class DesktopBridge:
                def ready(self):
                    app.config["NATIVE_READY"] = True

                def layout(self, view, content_height, viewport_width, viewport_height):
                    state = native_layout.apply(view, content_height, viewport_width, viewport_height)
                    app.config["NATIVE_LAYOUT"] = state
                    return state

                def restart(self):
                    if app.config["DEVELOPMENT"]:
                        restart.set()
                        window.destroy()

            window = webview.create_window(
                "EcoVision" + (" · Desarrollo" if args.dev else ""), url,
                width=616, height=500, min_size=(480, 360),
                fullscreen=False, resizable=False, background_color="#ffffff",
                js_api=DesktopBridge())
            native_layout = NativeLayout(window)
            if app.config["DEVELOPMENT"]:
                baseline = revision(list(ROOT.glob("*.py")))

                def watch_python():
                    while not finished.wait(1):
                        if revision(list(ROOT.glob("*.py"))) != baseline:
                            restart.set()
                            window.destroy()
                            return

                threading.Thread(target=watch_python, daemon=True).start()
            webview.start(gui="edgechromium", icon=str(ROOT / "static/images/icon_ecovision.ico"),
                          storage_path=str(DATA / "webview" / str(os.getpid())))
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback
        log_file.write_text(traceback.format_exc(), encoding="utf-8")
        if not args.serve:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"No se pudo abrir EcoVision. Revisa WebView2. Detalles: {log_file}", "EcoVision", 16)
        raise
    finally:
        finished.set()
        try:
            session.close()
        finally:
            server.shutdown()
            server.server_close()
    return 75 if restart.is_set() else 0


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())
