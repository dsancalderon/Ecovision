# Windows one-folder distribution: no extraction of the AI runtime on every launch.
from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH)
os.environ['YOLO_OFFLINE'] = 'true'
os.environ['YOLO_AUTOINSTALL'] = 'false'
datas = [(str(root / name), name) for name in ('templates', 'static', 'model')]
datas += collect_data_files('ultralytics')
a = Analysis(
    [str(root / 'realtime_ui_app.py')], pathex=[str(root)],
    binaries=[], datas=datas,
    hiddenimports=['webview', 'webview.platforms.edgechromium', 'webview.platforms.winforms', 'torch', 'torchvision', 'ultralytics'] + collect_submodules('ultralytics.models.yolo'),
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'IPython', 'notebook', 'pytest', 'tensorboard'],
    noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='EcoVision',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, append_pkg=False, icon=str(root / 'static/images/icon_ecovision.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='EcoVision')
