"""Verify the source supervisor sees a Python edit and reopens the local app."""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
log = Path(os.environ['LOCALAPPDATA']) / 'EcoVision/development.log'
source = root / 'desktop_diagnostics.py'


def latest_url():
    urls = re.findall(r'EcoVision [^:]+: (http://127\.0\.0\.1:\d+)', log.read_text(encoding='utf-8', errors='replace'))
    if not urls:
        raise RuntimeError('Open EcoVision Desarrollo first.')
    return urls[-1]


def wait_reopened(previous):
    until = time.monotonic() + 30
    while time.monotonic() < until:
        url = latest_url()
        if url != previous:
            try:
                with urllib.request.urlopen(url + '/api/session', timeout=1) as response:
                    state = json.load(response)
                if state['development'] and state['mode'] == 'menu' and state.get('native_ready'):
                    return url
            except OSError:
                pass
        time.sleep(.3)
    raise AssertionError('Development supervisor did not reopen the application.')


before = latest_url()
original = source.read_bytes()
try:
    source.write_bytes(original + b'\n# Development restart verification.\n')
    after = wait_reopened(before)
finally:
    source.write_bytes(original)
restored = wait_reopened(after)
result = dict(passed=['Python edit triggers a fresh native backend and returns to menu',
                      'Restoring the source triggers a second clean restart'],
              previous=before, changed=after, restored=restored)
(root/'verification/desktop-development-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
