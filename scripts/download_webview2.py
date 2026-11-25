"""Build-time download of Microsoft's complete x64 WebView2 installer."""
import urllib.request
from pathlib import Path

target = Path(__file__).resolve().parents[1] / 'packaging/dependencies/MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
target.parent.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen('https://go.microsoft.com/fwlink/p/?LinkId=2124701', timeout=120) as response:
    with target.open('wb') as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
if target.stat().st_size < 10_000_000:
    raise RuntimeError('Downloaded file is too small for the standalone runtime installer.')
print(f'{target.name}: {target.stat().st_size} bytes')
