"""Mide la tasa de inferencia y los FPS de captura de EcoVision (Tabla 12 del documento).

Uso (desde la carpeta EcoVision, con la app cerrada y la cámara conectada):
    .venv\\Scripts\\python.exe verification\\medir_fps.py [--cam 0] [--seg 60]

Sesión A: inferencia aislada sobre imágenes fijas (techo del modelo en el equipo).
Sesión B: captura e inferencia en hilos separados, como en la aplicación.
Misma configuración que la app: imgsz=320, conf=0.75. No guarda imágenes.
"""
import argparse, glob, json, platform, statistics as st, threading, time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent


def pct(a, q):
    a = sorted(a)
    return a[min(len(a) - 1, int(round(q / 100 * (len(a) - 1))))]


def resumen(tiempos_ms, segundos):
    return dict(inferencias=len(tiempos_ms), inf_por_s=round(len(tiempos_ms) / segundos, 1),
                ms_media=round(st.mean(tiempos_ms), 1), ms_mediana=round(pct(tiempos_ms, 50), 1),
                ms_p95=round(pct(tiempos_ms, 95), 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--seg", type=int, default=60)
    ap.add_argument("--modelo", default=str(ROOT / "model" / "best.pt"))
    a = ap.parse_args()

    m = YOLO(a.modelo)
    print("Clases del modelo:", m.names)
    imgs = [cv2.resize(cv2.imread(p), (1280, 720)) for p in sorted(glob.glob(str(ROOT / "verification" / "*_frame_*.png")))]
    if not imgs:
        imgs = [np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)]
    for _ in range(5):
        m.predict(imgs[0], imgsz=320, conf=0.75, verbose=False)

    print(f"Sesión A: inferencia aislada ({a.seg} s)...")
    t, t0, i = [], time.time(), 0
    while time.time() - t0 < a.seg:
        s = time.perf_counter()
        m.predict(imgs[i % len(imgs)], imgsz=320, conf=0.75, verbose=False)
        t.append((time.perf_counter() - s) * 1000)
        i += 1
    A = resumen(t, time.time() - t0)
    print("  ", A)

    print(f"Sesión B: cámara {a.cam} + inferencia ({a.seg} s)...")
    cap = cv2.VideoCapture(a.cam, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    ok, f = cap.read()
    B = {"camara_ok": bool(ok), "resolucion": [int(cap.get(3)), int(cap.get(4))]}
    if ok:
        ultimo, n_cap, parar = [f], [0], [False]

        def capturar():
            while not parar[0]:
                ok2, fr = cap.read()
                if ok2:
                    ultimo[0] = fr
                    n_cap[0] += 1

        th = threading.Thread(target=capturar, daemon=True)
        th.start()
        time.sleep(1)
        n_cap[0], ti, t0 = 0, [], time.time()
        while time.time() - t0 < a.seg:
            s = time.perf_counter()
            m.predict(ultimo[0].copy(), imgsz=320, conf=0.75, verbose=False)
            ti.append((time.perf_counter() - s) * 1000)
        el = time.time() - t0
        parar[0] = True
        th.join(2)
        B.update(fps_captura=round(n_cap[0] / el, 1), **resumen(ti, el))
    cap.release()
    print("  ", B)

    salida = dict(fecha=time.strftime("%Y-%m-%d %H:%M"), equipo=platform.processor(), modelo=a.modelo,
                  clases=list(m.names.values()), A_inferencia_aislada=A, B_captura_mas_inferencia=B)
    out = ROOT / "verification" / "medir_fps_resultado.json"
    out.write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Guardado en", out)


if __name__ == "__main__":
    main()
