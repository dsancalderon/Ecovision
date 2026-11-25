"""Mode isolation and recovery without opening a physical camera."""
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import realtime_ui_app as eco
from desktop_runtime import DesktopSession


class FakeManager:
    connected = True

    def __init__(self, path, **options):
        self.options = options
        self.model = SimpleNamespace(names={0: 'botella_reciclable', 1: 'carton'})
        self.cap = SimpleNamespace(isOpened=lambda: self.connected)
        self.raw_frame = object()
        self.stopped = False

    def start(self):
        pass

    def stop(self):
        self.stopped = True


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.session = DesktopSession(FakeManager)
        self.old_session = eco.session
        eco.session = self.session
        self.client = eco.app.test_client()
        self.settings = patch.object(eco, 'save_settings')
        self.settings.start()

    def tearDown(self):
        self.session.close()
        eco.session = self.old_session
        self.settings.stop()

    def choose(self, mode, camera=0):
        response = self.client.post('/api/mode', json={'mode': mode, 'camera_index': camera})
        self.assertEqual(response.status_code, 202)
        self.session.worker.join(3)
        self.assertFalse(self.session.worker.is_alive())

    def test_menu_and_simulation_never_construct_engine(self):
        with patch.object(self.session, 'factory', side_effect=AssertionError('Camera opened')):
            self.assertIn('choose-simulation', self.client.get('/').text)
            self.assertEqual(self.client.get('/workspace').status_code, 302)
            self.choose('simulation')
            page = self.client.get('/workspace').text
            self.assertIn('data-interface-only="true"', page)
            self.assertNotIn('src="/video_feed"', page)
            self.assertIn('id="sim-toolbar" >', page)
            self.assertEqual(self.client.get('/video_feed').status_code, 409)
            self.assertEqual(self.client.post('/api/simulate', json={}).status_code, 200)
            self.assertFalse(self.client.get('/api/status').json['camera_connected'])

    def test_real_mode_blocks_simulation_and_releases_on_return(self):
        self.choose('real', 1)
        manager = self.session.manager
        self.assertEqual(manager.options['camera_index'], 1)
        self.assertEqual(self.session.snapshot()['model_classes'], ['botella_reciclable', 'carton'])
        page = self.client.get('/workspace').text
        self.assertIn('id="sim-toolbar" hidden', page)
        self.assertIn('Modelo provisional', page)
        self.assertEqual(self.client.post('/api/simulate', json={}).status_code, 409)
        self.choose('simulation')
        self.assertTrue(manager.stopped)
        self.assertIsNone(self.session.manager)
        self.choose('menu')
        self.assertEqual(self.client.get('/workspace').status_code, 302)

    def test_camera_failure_has_explicit_error_and_can_recover(self):
        with patch.object(FakeManager, 'connected', False):
            self.choose('real')
        self.assertEqual(self.session.snapshot()['phase'], 'error')
        self.assertIsNone(self.session.manager)
        self.assertEqual(self.session.snapshot()['mode'], 'real')
        self.choose('simulation')
        self.assertEqual(self.session.snapshot()['phase'], 'ready')

    def test_missing_model_does_not_download_or_open_camera(self):
        with patch('desktop_runtime.model_path', side_effect=FileNotFoundError('Falta best.pt')), \
                patch.object(self.session, 'factory') as factory:
            self.choose('real')
            factory.assert_not_called()
        self.assertEqual(self.session.snapshot()['phase'], 'error')
        self.assertEqual(self.session.snapshot()['error'], 'Falta best.pt')

    def test_concurrent_switches_are_rejected(self):
        entered, release = threading.Event(), threading.Event()
        def slow_factory(*args, **kwargs):
            entered.set()
            release.wait(3)
            return FakeManager(*args, **kwargs)
        self.session.factory = slow_factory
        self.assertTrue(self.session.select('real'))
        self.assertTrue(entered.wait(2))
        try:
            self.assertFalse(self.session.select('simulation'))
        finally:
            release.set()
            self.session.worker.join(3)

    def test_invalid_input_and_cross_site_requests_do_not_change_mode(self):
        for payload in ({'mode': 'other'}, {'mode': 'real', 'camera_index': -1}, {'mode': 'real', 'camera_index': True}):
            self.assertEqual(self.client.post('/api/mode', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/api/mode', json={'mode': 'real'}, headers={'Origin': 'https://external.example'}).status_code, 403)
        self.assertEqual(self.session.snapshot()['mode'], 'menu')
        self.assertIn("connect-src 'self'", self.client.get('/').headers['Content-Security-Policy'])

    def test_return_to_menu_preserves_camera_selection(self):
        with patch.object(eco, 'load_settings', return_value={'camera_index': 1}):
            response = self.client.post('/api/mode', json={'mode': 'menu'})
            self.assertEqual(response.status_code, 202)
            self.session.worker.join(3)
            eco.save_settings.assert_called_with({'camera_index': 1})

    def test_ui_has_no_remote_runtime_resources(self):
        for filename in ['templates/index.html', 'templates/desktop.html', 'static/vendor/fonts.css', 'static/vendor/icons.css']:
            source = (Path(eco.ROOT) / filename).read_text(encoding='utf-8')
            self.assertNotIn('https://', source)
        for filename in ['fonts.css', 'icons.css']:
            import re
            source = (eco.ROOT / 'static/vendor' / filename).read_text(encoding='utf-8')
            for url in re.findall(r'url\([\"\']?([^\)\"\']+)', source):
                self.assertTrue((eco.ROOT / 'static/vendor' / url).is_file(), url)


if __name__ == '__main__':
    unittest.main()
