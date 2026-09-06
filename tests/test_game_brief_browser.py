"""Real browser + HTTP + SQLite journeys; model output is a labelled test fixture."""
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import uvicorn
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentfactory_cloud.brief_web import create_app
from test_game_briefs import FakeModel


class GameBriefBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = patch.dict(os.environ, {'AGENT_FACTORY_API_TOKEN': '', 'AGENT_FACTORY_API_ACTOR': 'Browser Creator',
                                        'AGENT_FACTORY_API_SCOPES': 'read,write', 'AGENT_FACTORY_API_TENANTS': '*'})
        cls.env.start()
        cls.directory = tempfile.TemporaryDirectory()
        cls.model = FakeModel()
        cls.app = create_app(Path(cls.directory.name), model=cls.model)
        cls.sock = socket.socket(); cls.sock.bind(('127.0.0.1', 0)); cls.sock.listen(32)
        cls.url = f'http://127.0.0.1:{cls.sock.getsockname()[1]}/'
        cls.server = uvicorn.Server(uvicorn.Config(cls.app, log_level='error', lifespan='off'))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={'sockets': [cls.sock]}, daemon=True)
        cls.thread.start()
        deadline = time.monotonic() + 10
        while not cls.server.started and time.monotonic() < deadline:
            time.sleep(.02)
        if not cls.server.started:
            cls.server.should_exit = True; cls.thread.join(5); cls.sock.close(); cls.directory.cleanup(); cls.env.stop()
            raise RuntimeError('Local test server did not start')
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch()
        except Exception:
            cls.playwright.stop(); cls.server.should_exit = True; cls.thread.join(5)
            cls.sock.close(); cls.directory.cleanup(); cls.env.stop(); raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop(); cls.server.should_exit = True; cls.thread.join(10)
        cls.sock.close(); cls.directory.cleanup(); cls.env.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 1000})
        self.page = self.context.new_page(); self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.url); self.page.locator('#workspace').wait_for(state='visible')

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def create(self, original='  Хочу маленьку гру про сад.\nГравець збирає насіння.  '):
        self.page.locator('#original').fill(original)
        self.page.locator('#create').click()
        self.page.locator('#editor').wait_for(state='visible')
        self.page.wait_for_function("document.querySelector('#version').textContent==='Version 1'")
        return original

    def test_exact_original_and_human_edits_survive_reload_and_history(self):
        original = self.create()
        self.page.locator('#field-core_loop').fill('Зібрати три насінини')
        self.page.locator('#save').click()
        self.page.wait_for_function("document.querySelector('#version').textContent==='Version 2'")
        self.page.reload(); self.page.locator('#editor').wait_for(state='visible')
        self.assertEqual(self.page.locator('#field-core_loop').input_value(), 'Зібрати три насінини')
        self.assertEqual(self.page.locator('#source').text_content(), original)
        self.page.get_by_text('Earlier versions and answers', exact=True).click()
        self.page.locator('#history').select_option('1'); self.page.locator('#view-version').click()
        self.page.wait_for_function("document.querySelector('#version').textContent==='Version 1'")
        self.assertEqual(self.page.locator('#field-core_loop').input_value(), '')

    def test_ai_confirmation_escape_then_explicit_suggestion_and_answer(self):
        self.create(); before = self.model.calls
        self.page.locator('#suggest').click(); self.page.keyboard.press('Escape')
        self.assertEqual(self.model.calls, before)
        self.page.locator('#suggest').click(); self.page.locator('#confirm-action').click()
        self.page.wait_for_function("document.querySelector('#version').textContent==='Version 2'")
        self.assertEqual(self.model.calls, before + 1)
        self.assertIn('AI suggestion', self.page.locator('#kind').inner_text())
        self.assertEqual(self.page.locator('.question').count(), 1)
        self.page.get_by_role('button', name='Touch', exact=True).click(); self.page.locator('#save').click()
        self.page.wait_for_function("document.querySelector('#version').textContent==='Version 3'")
        self.assertEqual(self.page.locator('#field-controls').input_value(), 'Touch')
        self.page.get_by_text('Earlier versions and answers', exact=True).click()
        self.assertIn('Which controls? — Touch', self.page.locator('#answers').inner_text())

    def test_stale_second_tab_cannot_erase_new_version_or_its_unsaved_edit(self):
        self.create(); other = self.context.new_page(); other.goto(self.page.url)
        other.locator('#editor').wait_for(state='visible')
        self.page.locator('#field-genre').fill('First saved choice'); self.page.locator('#save').click()
        self.page.wait_for_function("document.querySelector('#version').textContent==='Version 2'")
        other.locator('#field-genre').fill('My unsaved conflicting choice'); other.locator('#save').click()
        other.wait_for_function("document.querySelector('#status').textContent.includes('newer version')")
        self.assertEqual(other.locator('#field-genre').input_value(), 'My unsaved conflicting choice')
        self.page.reload(); self.page.locator('#editor').wait_for(state='visible')
        self.assertEqual(self.page.locator('#field-genre').input_value(), 'First saved choice')

    def test_unsaved_navigation_needs_confirmation_and_escape_keeps_text(self):
        self.create(); self.page.locator('#field-genre').fill('Keep my draft')
        self.page.locator('#new').click(); self.page.keyboard.press('Escape')
        self.assertEqual(self.page.locator('#field-genre').input_value(), 'Keep my draft')
        self.assertTrue(self.page.locator('#editor').is_visible())

    def test_script_like_text_is_plain_and_layout_fits_desktop_and_mobile(self):
        self.create('<img src=x onerror="window.bad=true"> A garden game')
        self.assertFalse(self.page.evaluate('Boolean(window.bad)'))
        self.assertEqual(self.page.locator('#source img').count(), 0)
        screenshot_dir = os.getenv('BRIEF_SCREENSHOT_DIR')
        for width, height, name in ((1280, 1000, 'desktop'), (390, 844, 'mobile')):
            self.page.set_viewport_size({'width': width, 'height': height})
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            if screenshot_dir:
                folder = Path(screenshot_dir); folder.mkdir(parents=True, exist_ok=True)
                self.page.screenshot(path=str(folder / f'brief-{name}.png'), full_page=True)


if __name__ == '__main__': unittest.main()
