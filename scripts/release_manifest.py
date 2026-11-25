import hashlib
import importlib.metadata
import json
import sys
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from desktop_runtime import VERSION, revision
from ultralytics import YOLO

target = root / 'dist/EcoVision'
verified = []
for folder in ['templates', 'static', 'model']:
    for path in (root/folder).rglob('*'):
        if path.is_file():
            bundled = target/'_internal'/path.relative_to(root)
            if not bundled.is_file() or hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(bundled.read_bytes()).digest():
                raise RuntimeError(f'El paquete no contiene el recurso final: {path.relative_to(root)}')
            verified.append(str(path.relative_to(root)))
manifest = dict(version=VERSION, revision=revision([root/'realtime_ui_app.py', root/'desktop_runtime.py', root/'static', root/'templates']),
                model_provisional=True, model_classes=list(YOLO(str(root/'model/best.pt')).names.values()),
                source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['realtime_ui_app.py','desktop_runtime.py','desktop_diagnostics.py','camera_catalog.py']},
                model_sha256=hashlib.sha256((root/'model/best.pt').read_bytes()).hexdigest(),
                resources_verified=len(verified),
                executable_sha256=hashlib.sha256((target/'EcoVision.exe').read_bytes()).hexdigest(),
                dependencies={p: importlib.metadata.version(p) for p in ['pyinstaller', 'pywebview', 'flask', 'ultralytics', 'torch', 'opencv-python']})
(target/'release.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
if (target/'EcoVision.pkg').is_file():
    manifest['package_sha256'] = hashlib.sha256((target/'EcoVision.pkg').read_bytes()).hexdigest()
    (target/'release.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(target/'Instalar EcoVision.vbs').write_text((root/'packaging/Instalar EcoVision.vbs').read_text(encoding='utf-8').replace('@@APP_VERSION@@', VERSION), encoding='ascii')
shutil.copy2(root/'DESKTOP.md', target/'LEEME.md')
if (root/'packaging/dependencies').is_dir():
    shutil.copytree(root/'packaging/dependencies', target/'dependencies', dirs_exist_ok=True)
print(json.dumps(manifest, indent=2))
