"""Self-test using EcoVision's own WebView API, without OS input injection."""
import json
import sys
import time
import threading
from pathlib import Path
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import realtime_ui_app as eco
import webview
from desktop_runtime import NativeLayout

server = make_server('127.0.0.1', 0, eco.app, threaded=True)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'
class Bridge:
    def ready(self):
        pass

    def layout(self, view, content_height, viewport_width, viewport_height):
        return layout.apply(view, content_height, viewport_width, viewport_height)

window = webview.create_window('EcoVision · verificación nativa', url, width=616, height=500, min_size=(480,360), resizable=False, js_api=Bridge())
layout = NativeLayout(window)
result = {'passed': [], 'errors': []}


def wait(expression, timeout=25):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        try:
            if window.evaluate_js(expression):
                return
        except Exception:
            pass
        time.sleep(.2)
    raise AssertionError(expression)


def run():
    try:
        wait("document.querySelector('#menu-panel')?.hidden === false")
        wait("document.body.classList.contains('native-desktop') && Math.abs(innerHeight-document.querySelector('.home-shell').getBoundingClientRect().height)<3")
        assert window.width < 700 and window.height < 650
        result['home_window'] = dict(width=window.width, height=window.height)
        def assert_centered():
            p = layout.state['placement']
            assert abs(p['left'] + p['width']/2 - (p['screen_left']+p['screen_width']/2)) <= 1
            assert abs(p['top'] + p['height']/2 - (p['screen_top']+p['screen_height']/2)) <= 1
            assert window.native.Left == p['left'] and window.native.Top == p['top']
        assert_centered()
        result['native_placement'] = layout.state['placement']
        assert not window.native.MaximizeBox
        assert window.evaluate_js("window.scrollTo(0,100); scrollY===0 && document.body.scrollTop===0")
        assert window.evaluate_js("!document.dispatchEvent(new KeyboardEvent('keydown',{key:'F11',cancelable:true,bubbles:true}))")
        result['passed'].append('Start window centered, no scroll, maximize disabled and F11 blocked')
        assert window.evaluate_js("document.querySelector('.home-brand').complete && document.querySelector('.home-brand').naturalWidth>0")
        assert window.evaluate_js("document.querySelector('#camera-choice').closest('[role=group]').contains(document.querySelector('#choose-real'))")
        result['passed'].append('Native start window fits form; centered logo and grouped real camera selector')
        result['passed'].append('Native WebView2 menu loaded')
        window.evaluate_js("document.querySelector('#choose-simulation').click()")
        wait("location.pathname === '/workspace' && typeof App !== 'undefined'")
        wait("innerWidth>1000 && innerHeight>=650")
        assert window.native.is_fullscreen
        result['passed'].append('Classification runs in native fullscreen')
        assert window.evaluate_js("getComputedStyle(document.querySelector('#scanner-box')).visibility === 'visible' && document.querySelector('#cam-standby > span').textContent === 'Cámara desactivada'")
        assert window.evaluate_js("document.body.dataset.interfaceOnly === 'true' && !document.querySelector('#main-video-feed').hasAttribute('src')")
        window.evaluate_js("sounds.enabled=false; document.querySelector('[data-class=\"botella_plastica_pet\"]').click()")
        wait("App.currentState === 3 && !document.querySelector('video').paused && document.querySelector('video').currentTime > .15")
        before = window.evaluate_js("document.querySelector('video').currentTime")
        wait(f"document.querySelector('video').currentTime > {before + .1}", timeout=5)
        result['passed'].append('PET video decodes and advances in native WebView2 result card')
        window.evaluate_js("App.transitionToState(1); document.querySelector('[data-class=\"papel_carton\"]').click()")
        wait("App.currentState === 3 && !document.querySelector('video').paused && document.querySelector('video').currentTime > .15")
        result['passed'].append('Cardboard video plays in native WebView2 result card')
        external = window.evaluate_js("performance.getEntriesByType('resource').filter(r=>!r.name.startsWith(location.origin)).map(r=>r.name)")
        assert not external, external
        window.evaluate_js("document.querySelector('#return-menu').click()")
        wait("location.pathname === '/' && document.querySelector('#menu-panel')?.hidden === false")
        wait("document.body.classList.contains('native-desktop') && Math.abs(innerHeight-document.querySelector('.home-shell').getBoundingClientRect().height)<3")
        assert window.width < 700
        assert not window.native.is_fullscreen and not window.native.MaximizeBox
        assert_centered()
        assert eco.session.manager is None
        result['passed'].append('Return to native menu without camera or model; zero external UI resources')
    except Exception as exc:
        import traceback
        result['errors'].append(traceback.format_exc())
        result['layout_debug'] = dict(width=window.width, height=window.height, layout=layout.state,
            page=window.evaluate_js("({path:location.pathname,innerWidth,innerHeight,api:Object.keys(window.pywebview?.api||{}),fitting:Desktop.fitting})"))
        result['layout_debug'].update(x=window.x,y=window.y,maximize=bool(window.native.MaximizeBox),screens=[str(s) for s in webview.screens])
    finally:
        window.destroy()


try:
    webview.start(func=run, gui='edgechromium')
finally:
    eco.session.close()
    server.shutdown()
    server.server_close()
    output = Path(__file__).with_name('desktop-native-results.json')
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
if result['errors'] or not result['passed']:
    raise SystemExit(1)
