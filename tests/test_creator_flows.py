"""Synthetic design checks; these are not a user study or production RBAC."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ROOT=Path(__file__).resolve().parents[1]/'prototypes/creator-operator'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


class CreatorContractTests(unittest.TestCase):
    def test_fixture_never_claims_product_or_minor_acceptance(self):
        data=json.loads((ROOT/'scenarios.json').read_text())
        self.assertEqual(data['product_acceptance'],'not-accepted')
        self.assertEqual(data['minor_pilot']['status'],'blocked')
        self.assertFalse(data['minor_pilot']['collects_child_data'])
        self.assertTrue(data['private_default'])
        self.assertNotIn('operator',data['roles']['creator'])
        self.assertEqual(set(data['scenarios']),{'first-use','failure','resume','cancellation'})


@unittest.skipIf(sync_playwright is None,'Install Playwright/Chromium for creator design checks')
class CreatorFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/'
        cls.runtime=sync_playwright().start()
        try:cls.browser=cls.runtime.chromium.launch()
        except Exception:
            cls.runtime.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join();raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.runtime.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1280,'height':900})
        self.page=self.context.new_page();self.requests=[]
        self.page.on('request',lambda request:self.requests.append((request.method,request.url)))
        self.page.goto(self.url)
        self.page.get_by_role('button',name='Create a game',exact=True).wait_for()

    def tearDown(self):self.context.close()

    def create(self):
        self.page.get_by_role('navigation').get_by_role('link',name='Create',exact=True).click()
        self.page.locator('#game-idea').wait_for()

    def settings(self):self.page.get_by_text('Preview settings',exact=True).click()

    def test_primary_navigation_and_no_creator_operator_details(self):
        self.assertEqual(self.page.locator('#navigation a:visible').all_text_contents(),['My Games','Create','Play','Change','Publish'])
        self.page.goto(self.url+'#operator')
        self.page.get_by_role('heading',name='Operator access required').wait_for()
        self.assertEqual(self.page.locator('.operator-grid').count(),0)
        self.settings();self.page.locator('#role').select_option('operator')
        self.assertEqual(self.page.locator('.operator-grid .panel').count(),5)
        self.page.locator('#role').select_option('creator')
        self.assertEqual(self.page.locator('.operator-grid').count(),0)

    def test_draft_survives_reload_and_background_updates_with_caret(self):
        self.create();idea=self.page.locator('#game-idea');idea.fill('A synthetic little moon garden')
        idea.evaluate('(node)=>{window.original=node;node.setSelectionRange(4,12)}')
        self.page.evaluate('refreshSample()')
        self.assertTrue(self.page.evaluate('document.activeElement===window.original && document.querySelector("#game-idea")===window.original'))
        self.assertEqual(idea.evaluate('(node)=>[node.selectionStart,node.selectionEnd]'),[4,12])
        self.page.reload();self.page.locator('#game-idea').wait_for()
        self.assertEqual(self.page.locator('#game-idea').input_value(),'A synthetic little moon garden')
        self.assertTrue(all(method=='GET' and url.startswith(self.url) for method,url in self.requests))

    def test_sample_plan_is_identified_and_does_not_start_work(self):
        self.create();self.page.locator('#game-idea').fill('Synthetic flying collector')
        self.page.get_by_role('button',name='Review the sample plan').click()
        self.assertIn('not an AI analysis',self.page.locator('#screen').inner_text())
        self.assertIn('Synthetic flying collector',self.page.locator('#screen').inner_text())
        self.page.get_by_role('button',name='Edit your idea').click()
        self.assertEqual(self.page.locator('#game-idea').input_value(),'Synthetic flying collector')
        self.assertTrue(all(method=='GET' for method,_ in self.requests))

    def test_cancellation_keeps_draft_and_escape_is_noop(self):
        self.create();self.page.locator('#game-idea').fill('Keep this synthetic idea')
        self.page.get_by_role('link',name='Change',exact=True).click()
        self.page.get_by_role('button',name='Cancel this sample attempt').click();self.page.keyboard.press('Escape')
        self.assertNotIn('Your work has stopped',self.page.locator('#screen').inner_text())
        self.page.get_by_role('button',name='Cancel this sample attempt').click();self.page.locator('#confirm-action').click()
        self.page.get_by_role('heading',name='Your work has stopped').wait_for()
        self.page.get_by_role('button',name='Revisit your saved idea').click()
        self.assertEqual(self.page.locator('#game-idea').input_value(),'Keep this synthetic idea')

    def test_deletion_is_confirmed_and_affects_only_own_draft(self):
        self.create();self.page.locator('#game-idea').fill('Delete this synthetic idea')
        self.page.evaluate("localStorage.setItem('unrelated-sample','keep')")
        self.page.locator('#delete').click();self.page.keyboard.press('Escape')
        self.assertEqual(self.page.locator('#game-idea').input_value(),'Delete this synthetic idea')
        self.page.locator('#delete').click();self.page.locator('#confirm-action').click()
        self.page.wait_for_function("localStorage.getItem('agentfactory-creator-design-v1')===null")
        self.assertEqual(self.page.evaluate("localStorage.getItem('unrelated-sample')"),'keep')
        self.assertEqual(self.page.locator('#game-idea').input_value(),'')

    def test_minor_paths_collect_no_input_or_self_authorization(self):
        self.settings()
        for value in ['teen','child']:
            self.page.locator('#age').select_option(value)
            self.page.locator('#game-idea').wait_for()
            self.assertTrue(self.page.locator('#game-idea').is_disabled())
            self.assertFalse(self.page.get_by_role('button',name='Review the sample plan').is_enabled())
            self.assertEqual(self.page.locator('input[type=email],input[type=date]').count(),0)
        self.assertEqual(self.page.evaluate('localStorage.length'),0)

    def test_play_and_publish_never_claim_missing_evidence(self):
        self.page.get_by_role('link',name='Play',exact=True).click()
        self.page.get_by_role('heading',name="A picture isn't a playtest").wait_for()
        self.assertIn('Not yet playable',self.page.locator('#screen').inner_text())
        self.assertEqual(self.page.locator('#screen button').all_text_contents(),['Review next step'])
        self.page.get_by_role('link',name='Publish',exact=True).click()
        self.page.get_by_role('heading',name='Sharing starts with a checked version').wait_for()
        self.assertIn('cannot publish, list or sell',self.page.locator('#screen').inner_text())
        self.assertEqual(self.page.locator('#screen button').all_text_contents(),['Review what is missing'])

    def test_storage_failure_is_visible_and_does_not_claim_saved(self):
        self.create()
        self.page.evaluate("() => { Storage.prototype.setItem=()=>{throw new Error('synthetic storage failure')}; }")
        self.page.locator('#game-idea').fill('Kept only in memory')
        self.assertIn('could not save',self.page.locator('#saved').inner_text())
        self.assertEqual(self.page.locator('#game-idea').input_value(),'Kept only in memory')

    def test_script_like_idea_is_text_and_small_screen_has_no_overflow(self):
        self.create();self.page.locator('#game-idea').fill('<img src=x onerror="window.bad=true">')
        self.page.get_by_role('button',name='Review the sample plan').click()
        self.assertFalse(self.page.evaluate('Boolean(window.bad)'))
        self.assertEqual(self.page.locator('#screen img').count(),0)
        self.page.set_viewport_size({'width':390,'height':844})
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
