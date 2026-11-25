"""Launch source in a project environment; restart only after an intentional exit 75."""
import subprocess
import sys
import os
from pathlib import Path

root = Path(__file__).resolve().parent
log_dir = Path(os.environ.get('LOCALAPPDATA', str(root))) / 'EcoVision'
log_dir.mkdir(parents=True, exist_ok=True)
while True:
    with (log_dir / 'development.log').open('a', encoding='utf-8') as log:
        result = subprocess.run([sys.executable, '-X', 'utf8', str(root / "realtime_ui_app.py"), "--dev"], cwd=root, stdout=log, stderr=log)
    if result.returncode != 75:
        if result.returncode:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"EcoVision no pudo iniciar. Revisa {log_dir / 'development.log'}", 'EcoVision Desarrollo', 16)
        break
