"""
EcoVision — Procesador y Optimizador de Videos de Materiales
Toma un video descargado de Gemini (Veo), lo valida, optimiza (H.264, sin audio,
resolución adecuada, duración de giro) y genera automáticamente el póster JPG
en static/videos/ listo para la interfaz.

Uso:
    python scripts/process_material_video.py --input "C:\\Users\\Santi\\Downloads\\mi_video.mp4" --material papel_carton
    # O para buscar automáticamente el último video descargado:
    python scripts/process_material_video.py --auto --material papel_carton
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_VIDEOS_DIR = BASE_DIR / "static" / "videos"
DOWNLOADS_DIR = Path(os.path.expanduser("~")) / "Downloads"

MATERIALS = [
    "botella_plastica_pet",
    "lata_aluminio",
    "tetra_pak",
    "papel_carton",
    "vidrio",
    "no_reciclable"
]

def find_latest_download():
    if not DOWNLOADS_DIR.exists():
        return None
    mp4s = list(DOWNLOADS_DIR.glob("*.mp4"))
    if not mp4s:
        return None
    mp4s.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return mp4s[0]

def probe_video(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
        "-of", "json",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Error analizando video con ffprobe: {res.stderr}")
    return json.loads(res.stdout)

def process_video(input_path, material_key, duration_limit=None):
    if material_key not in MATERIALS:
        raise ValueError(f"Material desconocido '{material_key}'. Opciones válidas: {MATERIALS}")

    STATIC_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    dest_video = STATIC_VIDEOS_DIR / f"{material_key}.mp4"
    dest_poster = STATIC_VIDEOS_DIR / f"{material_key}-poster.jpg"

    print(f"\n🔍 Analizando video de origen: {input_path}")
    probe = probe_video(input_path)
    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_name") != "aac"), streams[0] if streams else {})
    width = int(video_stream.get("width", 720))
    height = int(video_stream.get("height", 1280))
    orig_duration = float(probe.get("format", {}).get("duration", 0))

    print(f"   - Resolución original: {width}x{height}")
    print(f"   - Duración original: {orig_duration:.2f} s")
    print(f"   - Códec: {video_stream.get('codec_name')}")

    # Optimización de video con ffmpeg:
    # 1. Sin audio (-an)
    # 2. H.264 compatible web (-c:v libx264 -pix_fmt yuv420p)
    # 3. Faststart para streaming instantáneo (-movflags +faststart)
    # 4. Duración si se especifica
    print(f"\n⚙️ Procesando video para EcoVision...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path)
    ]
    if duration_limit and duration_limit > 0:
        ffmpeg_cmd.extend(["-t", str(duration_limit)])

    ffmpeg_cmd.extend([
        "-an",
        "-c:v", "libx264",
        "-crf", "22",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(dest_video)
    ])

    res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Error al codificar video: {res.stderr}")

    print(f"✅ Video optimizado guardado en: {dest_video}")

    # Generación de póster JPG (primer fotograma a resolución adaptada)
    poster_w = 288 if width == 720 and height == 1280 else min(512, width)
    print(f"📸 Extrayendo fotograma clave para el póster ({dest_poster.name})...")
    poster_cmd = [
        "ffmpeg", "-y",
        "-i", str(dest_video),
        "-ss", "00:00:00.000",
        "-vframes", "1",
        "-vf", f"scale={poster_w}:-1",
        "-q:v", "3",
        str(dest_poster)
    ]
    res_p = subprocess.run(poster_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res_p.returncode != 0:
        print(f"⚠️ Advertencia extrayendo póster: {res_p.stderr}")
    else:
        print(f"✅ Póster guardado en: {dest_poster}")

    # Diagnóstico final
    final_probe = probe_video(dest_video)
    final_size_kb = int(final_probe.get("format", {}).get("size", 0)) / 1024
    final_dur = float(final_probe.get("format", {}).get("duration", 0))
    print("\n📦 Resumen del Entregable:")
    print(f"   - Archivo Video: {dest_video.name} ({final_size_kb:.1f} KB, {final_dur:.2f} s)")
    print(f"   - Archivo Póster: {dest_poster.name} ({dest_poster.stat().st_size / 1024:.1f} KB)")
    print(f"   - Estado en UI: Listo para reproducirse en la tarjeta de resultado.")
    print("---------------------------------------------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesar e integrar videos de Gemini para EcoVision.")
    parser.add_argument("--input", "-i", type=str, help="Ruta al video MP4 de origen.")
    parser.add_argument("--auto", "-a", action="store_true", help="Buscar automáticamente el video más reciente en Descargas.")
    parser.add_argument("--material", "-m", type=str, default="papel_carton", choices=MATERIALS, help="Clase del material.")
    parser.add_argument("--duration", "-d", type=float, default=None, help="Recortar a esta duración en segundos (opcional).")

    args = parser.parse_args()

    input_file = None
    if args.input:
        input_file = Path(args.input)
    elif args.auto:
        input_file = find_latest_download()
        if not input_file:
            print("❌ No se encontró ningún archivo .mp4 reciente en la carpeta Descargas.")
            sys.exit(1)
        print(f"📁 Video más reciente encontrado: {input_file.name}")
    else:
        print("❌ Debe especificar --input <ruta> o --auto para procesar.")
        sys.exit(1)

    if not input_file.exists():
        print(f"❌ El archivo '{input_file}' no existe.")
        sys.exit(1)

    process_video(input_file, args.material, args.duration)
