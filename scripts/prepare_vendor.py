"""Download pinned UI assets for offline distribution (build-time only)."""
import re
import urllib.request
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "static" / "vendor"
TARGET.mkdir(parents=True, exist_ok=True)


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


fonts = download("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap").decode()
for i, url in enumerate(dict.fromkeys(re.findall(r"url\((https://[^)]+)\)", fonts))):
    filename = f"font-{i}{Path(url).suffix}"
    (TARGET / filename).write_bytes(download(url))
    fonts = fonts.replace(url, filename)
(TARGET / "fonts.css").write_text(fonts, encoding="utf-8")
styles = []
for weight in ("regular", "bold", "fill", "duotone"):
    base = f"https://unpkg.com/@phosphor-icons/web@2.1.2/src/{weight}/"
    css = download(base + "style.css").decode()
    css = re.sub(r'src:.*?;', lambda match: 'src: ' + re.search(r'url\([^)]*\.woff2[^)]*\)\s*format\([^)]*\)', match[0])[0] + ';', css, flags=re.S)
    for url in dict.fromkeys(re.findall(r'url\([\"\']?([^\)\"\']+)', css)):
        name = Path(url.split("?")[0]).name
        (TARGET / name).write_bytes(download(base + url.lstrip("./")))
        css = css.replace(url, name)
    styles.append(css)
(TARGET / "icons.css").write_text("\n".join(styles), encoding="utf-8")
licenses = {
    "PHOSPHOR-LICENSE.txt": "https://unpkg.com/@phosphor-icons/web@2.1.2/LICENSE",
    "OUTFIT-OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/outfit/OFL.txt",
    "JAKARTA-OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/plusjakartasans/OFL.txt",
    "JETBRAINS-OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/OFL.txt",
}
for name, url in licenses.items():
    (TARGET / name).write_bytes(download(url))
print("Offline fonts, icons and licenses saved.")
