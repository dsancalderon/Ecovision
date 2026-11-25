"""Local paths, release identity and serialized desktop mode transitions."""
import hashlib
import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA = Path(os.environ.get("ECOVISION_DATA_DIR", str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EcoVision")))
VERSION = "0.2.0"
os.environ["YOLO_OFFLINE"] = "true"
os.environ["YOLO_AUTOINSTALL"] = "false"
os.environ["YOLO_CONFIG_DIR"] = str(DATA / "yolo")


def revision(paths):
    digest = hashlib.sha256()
    for folder in paths:
        for path in sorted(folder.rglob("*")) if folder.is_dir() else [folder]:
            if path.is_file() and path.suffix in {".py", ".js", ".css", ".html", ".json"}:
                digest.update(str(path.relative_to(ROOT)).encode())
                digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def model_path():
    # Explicitly local: never substitute a model name that triggers a download.
    for path in (DATA / "models" / "best.pt", ROOT / "model" / "best.pt", ROOT / "model" / "best.onnx"):
        if path.is_file():
            return path
    raise FileNotFoundError("No hay un modelo local. Instala best.pt en la carpeta model.")


class DesktopSession:
    def __init__(self, factory):
        self.factory = factory
        self.manager = None
        self.lock = threading.RLock()
        self.worker = None
        self.closing = False
        self.options = {"camera_index": 0, "conf_threshold": .75, "model_path": None}
        self.state = dict(mode="menu", phase="ready", progress=100, message="Elige cómo quieres probar EcoVision.", error=None, model_classes=[])

    def snapshot(self):
        with self.lock:
            return dict(self.state)

    def update(self, **values):
        with self.lock:
            self.state.update(values)

    def select(self, mode, camera=0):
        if mode not in {"menu", "simulation", "real"}:
            raise ValueError("Modo no válido.")
        if type(camera) is not int or not 0 <= camera <= 20:
            raise ValueError("Selecciona una cámara entre 0 y 20.")
        with self.lock:
            if self.closing or (self.worker and self.worker.is_alive()):
                return False
            self.update(mode=mode, phase="loading", progress=10, message="Preparando el modo…", error=None, model_classes=[])
            self.worker = threading.Thread(target=self._switch, args=(mode, camera), daemon=True)
            self.worker.start()
            return True

    def _switch(self, mode, camera):
        try:
            if self.manager:
                self.update(message="Liberando la cámara…", progress=20)
                self.manager.stop()
                self.manager = None
            if mode == "real":
                path = Path(self.options["model_path"]) if self.options["model_path"] else model_path()
                if not path.is_file():
                    raise FileNotFoundError("El modelo seleccionado no existe en este equipo.")
                self.update(message="Cargando el modelo provisional…", progress=35)
                manager = self.factory(str(path), camera_index=camera, conf_threshold=self.options["conf_threshold"])
                self.manager = manager
                if manager.model is None:
                    raise RuntimeError("No se pudo cargar el modelo local. Puedes volver al menú y usar simulación.")
                names = manager.model.names
                classes = list(names.values()) if isinstance(names, dict) else list(names)
                self.update(message="Conectando la cámara…", progress=70, model_classes=classes, model_name=path.name)
                manager.start()
                if manager.cap is None or not manager.cap.isOpened() or manager.raw_frame is None:
                    raise RuntimeError("No se recibieron imágenes de esa cámara. Reintenta o elige otro índice.")
            if self.closing:
                if self.manager:
                    self.manager.stop()
                    self.manager = None
                return
            self.update(phase="ready", progress=100, message="Listo para comenzar.")
        except Exception as exc:
            if self.manager:
                try:
                    self.manager.stop()
                    self.manager = None
                except Exception as stop_error:
                    exc = RuntimeError(f"{exc} {stop_error}")
            self.update(phase="error", error=str(exc), message=str(exc))

    def close(self):
        self.closing = True
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=30)
        if self.manager:
            self.manager.stop()
            self.manager = None


def save_settings(values):
    DATA.mkdir(parents=True, exist_ok=True)
    temporary = DATA / "settings.tmp"
    temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(DATA / "settings.json")


def load_settings():
    try:
        return json.loads((DATA / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def center_native_window(window):
    """Use one native coordinate space so Windows DPI scaling is applied only once."""
    if sys.platform == 'win32' and window.native is not None:
        from System import Action
        from System.Drawing import Point
        from System.Windows.Forms import Screen
        placement = {}

        def center():
            form = window.native
            bounds = Screen.FromControl(form).Bounds
            left = bounds.X + (bounds.Width - form.Width) // 2
            top = bounds.Y + (bounds.Height - form.Height) // 2
            form.Location = Point(left, top)
            placement.update(left=int(form.Left), top=int(form.Top),
                width=int(form.Width), height=int(form.Height),
                screen_left=int(bounds.X), screen_top=int(bounds.Y),
                screen_width=int(bounds.Width), screen_height=int(bounds.Height))

        window.native.Invoke(Action(center))
        return placement
    import webview
    screen = webview.screens[0]
    window.move(screen.x + round((screen.width-window.width)/2), screen.y + round((screen.height-window.height)/2))
    return {}


class NativeLayout:
    """Centered fixed-size start form, fullscreen classification, compact return."""
    def __init__(self, window, fullscreen=False):
        self.window = window
        self.fullscreen = False
        self.frame = (6, 29)
        self.last_view = None
        self.state = {}

    def apply(self, view, content_height=400, viewport_width=600, viewport_height=400):
        window = self.window
        if view == 'workspace':
            if not self.fullscreen:
                window.toggle_fullscreen()
                self.fullscreen = True
            self.last_view = view
            self.state = dict(view=view, width=window.width, height=window.height, fullscreen=True)
            return self.state
        if view != 'home':
            raise ValueError('Vista no válida.')
        was_fullscreen = self.fullscreen
        if was_fullscreen:
            window.toggle_fullscreen()
            self.fullscreen = False
        old_width, old_height = window.width, window.height
        if not was_fullscreen:
            frame_width = max(0, min(40, old_width - int(viewport_width)))
            frame_height = max(0, min(100, old_height - int(viewport_height)))
            self.frame = (frame_width, frame_height)
        width = 600 + self.frame[0]
        height = max(320, min(700, int(content_height))) + self.frame[1]
        if abs(width - old_width) > 1 or abs(height - old_height) > 1:
            window.resize(width, height)
            # Windows may cap the requested size to the available screen area.
            width, height = window.width, window.height
        placement = center_native_window(window)
        self.last_view = view
        self.state = dict(view=view, width=width, height=height, fullscreen=False, centered=True, placement=placement)
        return self.state
