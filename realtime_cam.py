"""
EcoVision — Prueba en Tiempo Real con Cámara Web y YOLO
======================================================
Este script permite probar la detección de objetos en tiempo real con la cámara de tu PC.
- Si ya descargaste tu modelo entrenado en Colab ('best.pt' o 'best.onnx'), lo usará automáticamente.
- Si aún no lo has entrenado, cargará 'yolov8n.pt' por defecto para que pruebes tu cámara de inmediato.

Controles:
- 'q' o 'ESC': Salir
- 's': Guardar captura de pantalla
- '+' / '-': Aumentar/disminuir umbral de confianza (conf threshold)
"""

import os
import sys
import time
from pathlib import Path
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] ultralytics no está instalado.")
    print("Ejecuta en tu terminal: pip install -r requirements.txt")
    sys.exit(1)


def search_best_model():
    """Busca el archivo de modelo en orden de prioridad."""
    possible_paths = [
        Path("model/best.pt"),
        Path("model/best.onnx"),
        Path("best.pt"),
        Path("best.onnx"),
        Path("yolov8n.pt")
    ]
    for p in possible_paths:
        if p.exists():
            return str(p)
    return "yolov8n.pt"  # Ultralytics lo descargará automáticamente si no existe


def draw_styled_box(img, box, label, score, color=(245, 175, 50)):
    """Dibuja una caja delimitadora con estilo moderno e información de clase/confianza."""
    x1, y1, x2, y2 = map(int, box)
    
    # Rectángulo principal
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2, lineType=cv2.LINE_AA)
    
    # Esquinas decorativas
    corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
    if corner_len > 5:
        thick = 4
        # Superior izquierda
        cv2.line(img, (x1, y1), (x1 + corner_len, y1), color, thick)
        cv2.line(img, (x1, y1), (x1, y1 + corner_len), color, thick)
        # Superior derecha
        cv2.line(img, (x2, y1), (x2 - corner_len, y1), color, thick)
        cv2.line(img, (x2, y1), (x2, y1 + corner_len), color, thick)
        # Inferior izquierda
        cv2.line(img, (x1, y2), (x1 + corner_len, y2), color, thick)
        cv2.line(img, (x1, y2), (x1, y2 - corner_len), color, thick)
        # Inferior derecha
        cv2.line(img, (x2, y2), (x2 - corner_len, y2), color, thick)
        cv2.line(img, (x2, y2), (x2, y2 - corner_len), color, thick)

    # Texto de etiqueta
    tag = f"{label} ({score:.0%})"
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.55
    font_thick = 1
    (tw, th), baseline = cv2.getTextSize(tag, font, font_scale, font_thick)
    
    # Fondo de la etiqueta
    label_y1 = max(0, y1 - th - 10)
    label_y2 = y1
    cv2.rectangle(img, (x1, label_y1), (x1 + tw + 12, label_y2), color, -1)
    
    # Texto en blanco para buen contraste
    text_color = (255, 255, 255)
    cv2.putText(img, tag, (x1 + 6, y1 - 6), font, font_scale, text_color, font_thick, lineType=cv2.LINE_AA)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="EcoVision — Detección en Tiempo Real")
    parser.add_argument("--cam", type=int, default=0, help="Índice de la cámara (0: Integrada, 1: USB Externa)")
    parser.add_argument("--model", type=str, default=None, help="Ruta al modelo YOLO")
    parser.add_argument("--conf", type=float, default=0.75, help="Umbral de confianza")
    args = parser.parse_args()

    model_path = args.model if args.model else search_best_model()
    print("=" * 60)
    print("♻️  EcoVision — Deteccion en tiempo real")
    print(f"📦 Cargando modelo: {model_path}")
    print(f"📷 Cámara seleccionada: Índice {args.cam}")
    if model_path == "yolov8n.pt" and not Path("model/best.pt").exists() and not Path("best.pt").exists():
        print("💡 [INFO]: Estás usando el modelo base 'yolov8n.pt'.")
        print("   Cuando entrenes tu modelo en Colab, guarda 'best.pt' en esta carpeta o en 'model/best.pt'.")
    print("=" * 60)

    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo '{model_path}': {e}")
        return

    # Iniciar captura de cámara
    camera_index = args.cam
    print(f"📷 [CÁMARA] Conectando a cámara en índice {camera_index}...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
    
    if not cap.isOpened():
        print(f"[AVISO] No se pudo abrir cámara con índice {camera_index}, probando índice por defecto...")
        cap = cv2.VideoCapture(0)
        camera_index = 0

    if not cap.isOpened():
        print("[ERROR] No se encontró ninguna cámara disponible.")
        return

    # Calentamiento del sensor CMOS USB
    for _ in range(5):
        cap.read()
        time.sleep(0.05)

    # Configurar resolución recomendada
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✅ Cámara {camera_index} iniciada con resolución: {actual_w}x{actual_h}")
    print("⌨️  Presiona 'q' para salir, 's' para guardar foto, '+' / '-' para cambiar umbral.")

    # Mapeo de colores exclusivo por nombre de clase (formato BGR: Azul, Verde, Rojo)
    class_colors = {
        "botella_reciclable": (245, 175, 50),       # Azul claro / Celeste (BGR: B=245, G=175, R=50)
        "botella_plastica_pet": (245, 175, 50),     # Azul claro / Celeste
        "botella": (245, 175, 50),                  # Azul claro
        "bottle": (245, 175, 50),                   # Azul claro (YOLO base)
        "lata_aluminio": (219, 152, 52),            # Azul clásico (BGR: B=219, G=152, R=52)
        "tetra_pak": (34, 126, 230),                # Naranja (BGR: B=34, G=126, R=230)
        "carton": (182, 89, 155),             # Morado (BGR: B=182, G=89, R=155)
    }
    default_color = (180, 180, 180)  # Color gris por defecto si la clase no está en el diccionario

    conf_threshold = args.conf
    prev_time = time.time()
    fps = 0.0

    window_name = "EcoVision - Deteccion en tiempo real (Presiona 'q' para salir)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1024, 576)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[AVISO] Error al capturar frame de la cámara.")
            break

        # Inferencia optimizada con YOLO (imgsz=320 para velocidad 4x en CPU)
        results = model.predict(source=frame, conf=conf_threshold, imgsz=320, verbose=False)
        result = results[0]


        # Dibujar detecciones
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy()
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                class_name = result.names.get(cls_id, f"Clase {cls_id}")
                
                # Asignación de color exclusivamente por nombre de clase
                color = class_colors.get(class_name.lower(), default_color)

                draw_styled_box(frame, coords, class_name, conf, color=color)

        # Cálculo de FPS
        curr_time = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, (curr_time - prev_time)))
        prev_time = curr_time

        # Barra superior con HUD (FPS, Confianza, Modelo)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], 45), (20, 24, 33), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        hud_text = f"EcoVision | Modelo: {Path(model_path).name} | FPS: {fps:.1f} | Conf: {conf_threshold:.2f}"
        cv2.putText(frame, hud_text, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow(window_name, frame)

        # Manejo de teclas
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' o ESC
            print("\n👋 Cerrando aplicación...")
            break
        elif key == ord('s'):
            os.makedirs("capturas", exist_ok=True)
            filename = f"capturas/captura_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Captura guardada en: {filename}")
        elif key == ord('+') or key == ord('='):
            conf_threshold = min(0.95, conf_threshold + 0.05)
            print(f"🔍 Umbral de confianza: {conf_threshold:.2f}")
        elif key == ord('-') or key == ord('_'):
            conf_threshold = max(0.10, conf_threshold - 0.05)
            print(f"🔍 Umbral de confianza: {conf_threshold:.2f}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
