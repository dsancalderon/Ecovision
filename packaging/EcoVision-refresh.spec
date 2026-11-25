# Repackage current application sources using the dependency inventory from a full build.
# Only for unchanged dependencies. Normal releases use ../EcoVision.spec.
from pathlib import Path
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.misc import load_py_data_struct
from PyInstaller.archive.readers import ZlibArchiveReader
from PyInstaller.config import CONF

root = Path(SPECPATH).parent
snapshot = root / 'build/EcoVision/Analysis-00.toc'
if not snapshot.is_file():
    raise RuntimeError('Run a full EcoVision.spec build first.')
cached = dict(zip((item[0] for item in Analysis._GUTS), load_py_data_struct(snapshot)))
pure = list(cached['pure'])
for name in ('desktop_diagnostics', 'camera_catalog'):
    pure = [entry for entry in pure if entry[0] != name]
    pure.append((name, str(root/f'{name}.py'), 'PYMODULE'))
datas = [entry for entry in cached['datas'] if entry[0].replace('\\','/').split('/')[0] not in {'templates','static','model'}]
for folder in ('templates','static','model'):
    for path in sorted((root/folder).rglob('*')):
        if path.is_file():
            datas.append((str(path.relative_to(root)), str(path), 'DATA'))
previous_pyz = root/'build/EcoVision-refresh/PYZ-00.pyz'
if previous_pyz.is_file():
    previous = ZlibArchiveReader(str(previous_pyz))
    # External dependencies are unchanged; application modules always compile fresh.
    CONF['code_cache'][id(pure)] = {name: previous.extract(name) for name, path, _ in pure
                                  if Path(path).parent != root and name in previous.toc}
pyz = PYZ(pure)
exe = EXE(pyz, cached['scripts'], [], exclude_binaries=True, name='EcoVision',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, append_pkg=False, icon=str(root/'static/images/icon_ecovision.ico'))
coll = COLLECT(exe, cached['binaries'], datas, strip=False, upx=False, name='EcoVision')
