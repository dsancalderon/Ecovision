"""Offline diagnostic for a packaged inference runtime, without physical camera."""
import json
import socket
import sys
from pathlib import Path


def run(output):
    result = {"errors": [], "passed": [], "frozen": bool(getattr(sys, 'frozen', False))}
    original_connect = socket.socket.connect
    def block_network(*args, **kwargs):
        raise OSError("Network disabled by offline diagnostic")
    socket.socket.connect = block_network
    try:
        from desktop_runtime import ROOT, VERSION, model_path
        import cv2
        import numpy as np
        from ultralytics import YOLO
        model = YOLO(str(model_path()))
        result.update(version=VERSION, model_classes=list(model.names.values()), model_provisional=True)
        result['passed'].append('Local provisional model loaded with network disabled')
        prediction = model.predict(np.zeros((360, 640, 3), dtype=np.uint8), imgsz=320, verbose=False)
        assert prediction and prediction[0].names
        result['passed'].append('CPU inference completes on synthetic frame; physical accuracy not tested')
        assert cv2.imencode('.jpg', np.zeros((32, 32, 3), dtype=np.uint8))[0]
        for path in ['templates/desktop.html', 'static/vendor/fonts.css', 'static/vendor/icons.css', 'static/videos/botella_plastica_pet.mp4']:
            assert (ROOT / path).is_file(), path
        result['passed'].append('OpenCV encoding and packaged local resources available')
    except Exception as exc:
        import traceback
        result['errors'].append(traceback.format_exc())
    finally:
        socket.socket.connect = original_connect
        Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 1 if result['errors'] else 0
