"""
EcoVision — Extractor de Fotogramas / Capturas de Video
======================================================
Este script te permite seleccionar un archivo de video y guardar capturas
de alta calidad cada vez que presiones la barra espaciadora.

Controles:
- [ESPACIO]: 📸 Guardar captura del fotograma actual
- [P] o [ENTER]: ⏯ Pausar / Reanudar reproducción
- [D] / [→]: Avanzar 1 fotograma (o 30 fotogramas con Shift)
- [A] / [←]: Retroceder 1 fotograma
- [+] / [-]: Aumentar / Disminuir velocidad de reproducción
- [R]: Reiniciar video al inicio
- [Q] o [ESC]: Salir
- Barra deslizadora (Trackbar): Navegar a cualquier parte del video
"""

import os
import sys
import time
from pathlib import Path
import cv2

# Intentar importar tkinter para la ventana de selección de archivos
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False


def select_video_file() -> str:
    """Abre un cuadro de diálogo para seleccionar un archivo de video."""
    # Si se pasó la ruta por argumento en consola
    if len(sys.argv) > 1:
        input_path = sys.argv[1].strip('\"\'')
        if os.path.isfile(input_path):
            return input_path
        else:
            print(f"[AVISO] La ruta proporcionada no existe: {input_path}")

    if HAS_TKINTER:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()

        print("📂 Abriendo ventana para seleccionar video...")
        filetypes = [
            ("Archivos de video", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv *.m4v *.ts"),
            ("Todos los archivos", "*.*")
        ]
        video_path = filedialog.askopenfilename(
            title="EcoVision - Selecciona un archivo de video",
            filetypes=filetypes
        )
        root.destroy()

        if video_path:
            return video_path

    # Fallback por terminal
    print("\nIngresa la ruta del archivo de video:")
    path_input = input("Ruta del video > ").strip('\"\'')
    return path_input if os.path.isfile(path_input) else ""


def format_time(seconds: float) -> str:
    """Convierte segundos a formato MM:SS o HH:MM:SS."""
    seconds = int(max(0, seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def main():
    print("=" * 65)
    print("🎬  EcoVision — Extractor de Fotogramas de Video")
    print("=" * 65)

    video_path = select_video_file()
    if not video_path or not os.path.exists(video_path):
        print("❌ No se seleccionó ningún archivo de video válido. Saliendo...")
        return

    video_name = Path(video_path).stem
    output_dir = Path("capturas_video")
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error al abrir el video: {video_path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0 or video_fps != video_fps:  # Verificación <= 0 o NaN
        video_fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_duration = total_frames / video_fps if total_frames > 0 else 0

    print(f"\n📁 Video: {Path(video_path).name}")
    print(f"📐 Resolución: {width}x{height} | FPS: {video_fps:.2f}")
    print(f"⏱  Duración: {format_time(total_duration)} ({total_frames} frames)")
    print(f"💾 Las capturas se guardarán en: {output_dir.resolve()}\n")
    print("Controles disponibles:")
    print("  • [ESPACIO]    -> 📸 Guardar captura del frame actual")
    print("  • [P / ENTER]  -> ⏯ Pausar / Reanudar")
    print("  • [D / →]      -> ⏩ Avanzar 1 frame (o 30 con Shift)")
    print("  • [A / ←]      -> ⏪ Retroceder 1 frame (o 30 con Shift)")
    print("  • [+ / -]      -> ⚡ Velocidad (0.25x a 4x)")
    print("  • [R]          -> 🔄 Reiniciar video")
    print("  • [Q / ESC]    -> 🚪 Salir\n")

    window_name = f"EcoVision Frame Extractor - {Path(video_path).name}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1100, 650)

    # Trackbar para navegación
    trackbar_updating = False

    def on_trackbar_change(pos):
        nonlocal trackbar_updating
        if not trackbar_updating and total_frames > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)

    if total_frames > 0:
        cv2.createTrackbar("Progreso", window_name, 0, max(1, total_frames - 1), on_trackbar_change)

    is_paused = False
    speeds = [0.25, 0.5, 1.0, 1.5, 2.0, 4.0]
    speed_idx = 2  # 1.0x por defecto
    saved_count = 0
    feedback_text = ""
    feedback_time = 0.0

    current_frame = None

    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                # Si llega al final del video, pausar en el último frame
                is_paused = True
                print("🏁 Fin del video alcanzado. (Presiona 'R' para reiniciar o 'Q' para salir)")
            else:
                current_frame = frame
        else:
            # En pausa, si no hay frame, leer el actual
            if current_frame is None:
                ret, frame = cap.read()
                if ret:
                    current_frame = frame

        if current_frame is None:
            # Si aún no hay frame válido
            break

        current_frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        current_time_sec = current_frame_idx / video_fps if video_fps > 0 else 0

        # Actualizar posición del trackbar sin disparar bucle
        if total_frames > 0 and not is_paused:
            trackbar_updating = True
            cv2.setTrackbarPos("Progreso", window_name, min(current_frame_idx, total_frames - 1))
            trackbar_updating = False

        # Preparar frame para visualización con interfaz gráfica HUD
        display_frame = current_frame.copy()
        h, w = display_frame.shape[:2]

        # Barra superior semi-transparente
        hud_height = 45
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, hud_height), (18, 22, 28), -1)
        cv2.addWeighted(overlay, 0.75, display_frame, 0.25, 0, display_frame)

        # Información de estado
        status_str = "⏸ PAUSADO" if is_paused else "▶ REPRODUCIENDO"
        status_color = (0, 165, 255) if is_paused else (46, 204, 113)  # Naranja / Verde
        speed_str = f"{speeds[speed_idx]}x"
        time_str = f"{format_time(current_time_sec)} / {format_time(total_duration)}"
        frame_str = f"Frame: {current_frame_idx}/{total_frames}"

        info_text = f"{frame_str}  |  {time_str}  |  Vel: {speed_str}  |  Capturas: {saved_count}"
        
        # Dibujar estado
        cv2.putText(display_frame, status_str, (15, 28),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, status_color, 1, cv2.LINE_AA)
        
        # Dibujar detalles
        cv2.putText(display_frame, info_text, (170, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (235, 235, 235), 1, cv2.LINE_AA)

        # Barra inferior con ayuda de teclas
        bottom_bar_y = h - 30
        overlay_bottom = display_frame.copy()
        cv2.rectangle(overlay_bottom, (0, bottom_bar_y), (w, h), (18, 22, 28), -1)
        cv2.addWeighted(overlay_bottom, 0.70, display_frame, 0.30, 0, display_frame)

        help_text = "[ESPACIO] Capturar  |  [P] Pausar  |  [A/D] -/+ 1 Frame  |  [+/-] Vel  |  [R] Reiniciar  |  [Q] Salir"
        cv2.putText(display_frame, help_text, (15, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 190, 200), 1, cv2.LINE_AA)

        # Feedback visual al tomar captura (banner verde)
        if time.time() - feedback_time < 1.8 and feedback_text:
            banner_w = 480
            banner_h = 42
            bx1 = (w - banner_w) // 2
            by1 = hud_height + 15
            bx2 = bx1 + banner_w
            by2 = by1 + banner_h

            banner_overlay = display_frame.copy()
            cv2.rectangle(banner_overlay, (bx1, by1), (bx2, by2), (39, 174, 96), -1)
            cv2.addWeighted(banner_overlay, 0.85, display_frame, 0.15, 0, display_frame)
            cv2.rectangle(display_frame, (bx1, by1), (bx2, by2), (46, 204, 113), 2, cv2.LINE_AA)

            cv2.putText(display_frame, feedback_text, (bx1 + 15, by1 + 27),
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(window_name, display_frame)

        # Calcular tiempo de espera según FPS y velocidad actual
        if is_paused:
            wait_delay = 30
        else:
            base_delay = 1000.0 / (video_fps * speeds[speed_idx])
            wait_delay = max(1, int(base_delay))

        key = cv2.waitKeyEx(wait_delay)
        if key == -1:
            continue

        raw_key = key & 0xFF

        # Salir (Q o ESC)
        if raw_key == ord('q') or raw_key == 27:
            print("\n👋 Cerrando extractor...")
            break

        # Capturar fotograma (ESPACIO)
        elif raw_key == 32:  # Barra espaciadora
            if current_frame is not None:
                saved_count += 1
                timestamp_str = time.strftime("%Y%m%d_%H%M%S")
                filename = output_dir / f"{video_name}_frame_{current_frame_idx:06d}_{timestamp_str}.jpg"
                
                # Guardar el frame limpio en alta calidad (JPEG 95%)
                cv2.imwrite(str(filename), current_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                feedback_text = f"📸 Captura guardada #{saved_count}: frame {current_frame_idx}"
                feedback_time = time.time()
                print(f"📸 [{saved_count}] Fotograma {current_frame_idx} guardado en: {filename}")

        # Pausar / Reanudar (P o ENTER)
        elif raw_key == ord('p') or raw_key == 13:
            is_paused = not is_paused
            state_msg = "Pausado" if is_paused else "Reproduciendo"
            print(f"⏯  {state_msg}")

        # Avanzar 1 fotograma (D o Flecha Derecha)
        elif raw_key == ord('d') or key == 2555904 or key == 2424832 or raw_key == 83:
            is_paused = True
            next_frame_idx = min(total_frames - 1, current_frame_idx + 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame_idx)
            ret, frame = cap.read()
            if ret:
                current_frame = frame
                trackbar_updating = True
                cv2.setTrackbarPos("Progreso", window_name, next_frame_idx)
                trackbar_updating = False

        # Retroceder 1 fotograma (A o Flecha Izquierda)
        elif raw_key == ord('a') or key == 2424832 or key == 2490368 or raw_key == 81:
            is_paused = True
            prev_frame_idx = max(0, current_frame_idx - 2)
            cap.set(cv2.CAP_PROP_POS_FRAMES, prev_frame_idx)
            ret, frame = cap.read()
            if ret:
                current_frame = frame
                trackbar_updating = True
                cv2.setTrackbarPos("Progreso", window_name, prev_frame_idx)
                trackbar_updating = False

        # Avanzar 30 frames rápido (W)
        elif raw_key == ord('w'):
            is_paused = True
            jump_idx = min(total_frames - 1, current_frame_idx + 30)
            cap.set(cv2.CAP_PROP_POS_FRAMES, jump_idx)
            ret, frame = cap.read()
            if ret:
                current_frame = frame
                trackbar_updating = True
                cv2.setTrackbarPos("Progreso", window_name, jump_idx)
                trackbar_updating = False

        # Retroceder 30 frames rápido (S)
        elif raw_key == ord('s'):
            is_paused = True
            jump_idx = max(0, current_frame_idx - 30)
            cap.set(cv2.CAP_PROP_POS_FRAMES, jump_idx)
            ret, frame = cap.read()
            if ret:
                current_frame = frame
                trackbar_updating = True
                cv2.setTrackbarPos("Progreso", window_name, jump_idx)
                trackbar_updating = False

        # Aumentar velocidad (+)
        elif raw_key in (ord('+'), ord('=')):
            if speed_idx < len(speeds) - 1:
                speed_idx += 1
                print(f"⚡ Velocidad: {speeds[speed_idx]}x")

        # Disminuir velocidad (-)
        elif raw_key in (ord('-'), ord('_')):
            if speed_idx > 0:
                speed_idx -= 1
                print(f"⚡ Velocidad: {speeds[speed_idx]}x")

        # Reiniciar video (R)
        elif raw_key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            is_paused = False
            ret, frame = cap.read()
            if ret:
                current_frame = frame
            print("🔄 Video reiniciado al inicio.")

    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 65)
    print(f"✅ Proceso finalizado. Total de capturas guardadas: {saved_count}")
    if saved_count > 0:
        print(f"📂 Carpeta de destino: {output_dir.resolve()}")
    print("=" * 65)


if __name__ == "__main__":
    main()
