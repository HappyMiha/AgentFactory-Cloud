import unittest
import test_game_brief_browser as fixture

class GuidanceBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixture.GameBriefBrowserTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):fixture.GameBriefBrowserTests.tearDownClass.__func__(cls)
    setUp=fixture.GameBriefBrowserTests.setUp
    tearDown=fixture.GameBriefBrowserTests.tearDown
    def open(self):
        self.page.goto(self.url+'connections');self.page.wait_for_selector('#details:not([hidden])')
    def test_mobile_choices_have_no_secret_input_or_network_mutation(self):
        posts=[];self.page.on('request',lambda r:posts.append(r.url) if r.method=='POST' else None)
        self.page.set_viewport_size({'width':390,'height':844});self.open()
        self.assertEqual(self.page.locator('#checks li').count(),6)
        for choice in ('chatgpt','openai-api','claude-chat','anthropic-api','codex-cli','claude-code','other'):
            self.page.locator('#product').select_option(choice)
            self.assertTrue(self.page.locator('#details').is_visible())
        self.assertEqual(self.page.locator('input,textarea').count(),0)
        self.assertEqual(posts,[]);self.assertEqual(self.model.calls,0)
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
    def test_refresh_failure_clears_and_recovers(self):
        self.open();self.page.route('**/api/connection-guidance',lambda r:r.fulfill(status=403,body='{}'))
        self.page.locator('#refresh').click();self.page.wait_for_function("document.querySelector('#status').textContent.includes('недоступні')")
        self.assertEqual(self.page.locator('#sources a').count(),0);self.assertTrue(self.page.locator('#product').is_disabled())
        self.page.unroute('**/api/connection-guidance');self.page.locator('#refresh').click();self.page.wait_for_selector('#details:not([hidden])')
    def test_expiry_on_selection_removes_old_sources(self):
        self.open();self.page.evaluate("Date.now=()=>Date.parse('2026-10-06T00:00:00Z')")
        self.page.locator('#product').select_option('openai-api')
        self.assertTrue(self.page.locator('#details').is_hidden());self.assertEqual(self.page.locator('#sources a').count(),0)
    def test_old_response_cannot_restore_guidance_after_newer_failure(self):
        self.open();payload=self.context.request.get(self.url+'api/connection-guidance').json();pending=[]
        self.page.route('**/api/connection-guidance',lambda route:pending.append(route))
        self.page.locator('#refresh').click();self.page.locator('#refresh').click()
        self.assertEqual(len(pending),2)
        pending[1].fulfill(status=403,body='{}');self.page.wait_for_function("document.querySelector('#status').textContent.includes('недоступні')")
        pending[0].fulfill(json=payload)
        self.page.wait_for_load_state('networkidle')
        self.assertTrue(self.page.locator('#product').is_disabled());self.assertEqual(self.page.locator('#sources a').count(),0)

    def test_team_link_preserves_current_page_in_separate_tab(self):
        import uuid
        brief=self.app.state.brief_store.create('A garden.','Browser Creator',str(uuid.uuid4()))
        self.page.goto(self.url+'game-team#'+brief['id']);self.page.wait_for_selector('#roles article')
        self.page.locator('#confirmed').check()
        with self.page.expect_popup() as opened:
            self.page.locator('a[href="/connections"]').click()
        popup=opened.value
        try:
            popup.wait_for_selector('#details:not([hidden])')
            self.assertIn('/game-team#'+brief['id'],self.page.url)
            self.assertTrue(self.page.locator('#confirmed').is_checked())
        finally:popup.close()
