"""Mediciones de EcoVision con la aplicación completa en ejecución (interfaz abierta).

1) Tasa de inferencia con la interfaz abierta (RNF-03):
       .venv\\Scripts\\python.exe verification\\medir_app.py --seg 60
   Requiere la app abierta en MODO REAL (ventana de PyWebView visible). Lee los contadores de
   /api/perf al inicio y al final de la ventana de medición y calcula las tasas reales.

2) Resumen de la latencia automática (RNF-04):
       .venv\\Scripts\\python.exe verification\\medir_app.py --latencias
   Lee outputs/latencias.csv, que la app escribe sola cada vez que muestra un resultado en modo
   real (latencia = desde la primera detección sobre el umbral hasta la tarjeta de resultado).

La dirección del servidor se toma de %LOCALAPPDATA%\\EcoVision\\server_url.txt (la escribe la app
al arrancar) o de --url.
"""
import argparse, csv, json, os, statistics as st, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("ECOVISION_DATA_DIR", str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EcoVision")))


def leer(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def pct(valores, q):
    v = sorted(valores)
    return v[min(len(v) - 1, int(round(q * (len(v) - 1))))]


def medir_tasa(base, seg):
    print(f"Midiendo {seg} s con la interfaz abierta en {base} ...")
    a = leer(base + "/api/perf")
    if not a.get("camera_connected"):
        print("AVISO: la cámara no está conectada; la medición no es válida.")
    t0 = time.monotonic()
    time.sleep(seg)
    b = leer(base + "/api/perf")
    dt = time.monotonic() - t0
    inf = b["inference_total"] - a["inference_total"]
    nuevos = b["new_frame_total"] - a["new_frame_total"]
    cap = b["capture_total"] - a["capture_total"]
    res = {
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "condicion": "aplicacion completa en ejecucion (PyWebView + Flask + MJPEG + SSE)",
        "duracion_s": round(dt, 1),
        "fps_captura": round(cap / dt, 1),
        "inferencias": inf,
        "inferencias_por_s": round(inf / dt, 1),
        "fotogramas_nuevos_analizados_por_s": round(nuevos / dt, 1),
        "ms_inferencia_sesion": b["infer_ms"],
    }
    out = ROOT / "verification" / "medir_app_resultado.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    print("Guardado en", out)


def resumir_latencias():
    path = ROOT / "outputs" / "latencias.csv"
    if not path.exists():
        print("No existe", path, "- aún no se ha registrado ningún resultado en modo real.")
        return
    filas = [f for f in csv.DictReader(path.open(encoding="utf-8")) if f.get("latencia_s")]
    por_clase = {}
    for f in filas:
        por_clase.setdefault(f["clase"], []).append(float(f["latencia_s"]))
    def resumen(v):
        return {"n": len(v), "min_s": round(min(v), 2), "mediana_s": round(pct(v, 0.5), 2),
                "p95_s": round(pct(v, 0.95), 2), "max_s": round(max(v), 2), "media_s": round(st.mean(v), 2)}
    res = {c: resumen(v) for c, v in sorted(por_clase.items())}
    todos = [x for v in por_clase.values() for x in v]
    if todos:
        res["TOTAL"] = resumen(todos)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    out = ROOT / "verification" / "latencias_resumen.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Guardado en", out, "| registros:", len(filas))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=None, help="http://127.0.0.1:PUERTO (por defecto se lee server_url.txt)")
    ap.add_argument("--seg", type=int, default=60)
    ap.add_argument("--latencias", action="store_true", help="solo resumir outputs/latencias.csv")
    a = ap.parse_args()
    if a.latencias:
        resumir_latencias(); return
    base = a.url or (DATA / "server_url.txt").read_text(encoding="utf-8").strip()
    medir_tasa(base.rstrip("/"), a.seg)


if __name__ == "__main__":
    main()
