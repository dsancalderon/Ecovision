"""Ensure repackaging contains the final source bytecode, including local modules."""
import marshal
import sys
import types
from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader

root = Path(__file__).resolve().parents[1]
package = root/'dist/EcoVision/EcoVision.pkg'
archive = CArchiveReader(str(package if package.is_file() else root/'dist/EcoVision/EcoVision.exe'))
pyz = archive.open_embedded_archive('PYZ.pyz')


def normalized(code):
    return code.replace(co_filename='source', co_consts=tuple(normalized(value) if isinstance(value, types.CodeType) else value for value in code.co_consts))


for name in ['realtime_ui_app', 'desktop_runtime', 'desktop_diagnostics', 'camera_catalog']:
    expected = compile((root/f'{name}.py').read_bytes(), 'source', 'exec', dont_inherit=True)
    actual = marshal.loads(archive.extract(name)) if name == 'realtime_ui_app' else pyz.extract(name)
    if normalized(expected) != normalized(actual):
        raise AssertionError(f'Packaged code differs from current source: {name}')
    print(f'Verified final bytecode: {name}')
