import uuid
import unittest
import test_game_brief_browser as fixture
from agentfactory_cloud.scope_plans import ScopePlans

class GameTeamBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixture.GameBriefBrowserTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):fixture.GameBriefBrowserTests.tearDownClass.__func__(cls)
    setUp=fixture.GameBriefBrowserTests.setUp
    tearDown=fixture.GameBriefBrowserTests.tearDown
    def team(self):
        b=self.app.state.brief_store.create('A seed garden.','Browser Creator',str(uuid.uuid4()));p=ScopePlans(self.app.state.brief_store)
        scope=p.write(b['id'],'Browser Creator',1,str(uuid.uuid4()));p.write(b['id'],'Browser Creator',1,str(uuid.uuid4()),ident=scope['id'],expected_plan=1,agree=True)
        return b['id']
    def test_visible_roles_separate_confirmation_and_no_runtime(self):
        ident=self.team();posts=[];self.page.on('request',lambda r:posts.append(r.url) if r.method=='POST' else None)
        self.page.set_viewport_size({'width':390,'height':844});self.page.goto(self.url+'game-team#'+ident);self.page.wait_for_selector('#roles article')
        self.assertEqual(self.page.locator('#roles article').count(),5);self.assertEqual(posts,[])
        self.page.locator('#assess').click();self.assertIn('Confirm',self.page.locator('#status').inner_text());self.assertEqual(posts,[])
        self.page.locator('#confirmed').check();self.page.locator('#assess').click();self.page.wait_for_function("document.querySelector('#assessment').textContent.includes('Core recorded')")
        self.assertEqual(len(posts),1);self.assertIn('No AI team is running',self.page.locator('#status').inner_text())
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
        self.assertEqual(self.model.calls,0)
    def test_failure_clears_view_and_reload_recovers(self):
        ident=self.team();self.page.goto(self.url+'game-team#'+ident);self.page.wait_for_selector('#roles article')
        self.page.route('**/team',lambda route:route.fulfill(status=403,body='{}'));self.page.locator('#reload').click()
        self.page.wait_for_function("document.querySelector('#status').textContent.includes('unavailable')")
        self.assertEqual(self.page.locator('#roles article').count(),0);self.assertEqual(self.page.locator('#budget').inner_text(),'')
        self.page.unroute('**/team');self.page.locator('#reload').click();self.page.wait_for_selector('#roles article')
    def test_scope_page_links_exact_idea(self):
        ident=self.team();self.page.goto(self.url+'first-playable#'+ident)
        self.assertEqual(self.page.locator('#team-link').get_attribute('href'),'/game-team#'+ident)
