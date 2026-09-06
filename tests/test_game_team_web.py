import unittest
from unittest.mock import patch
import test_game_brief_web as fixture
from agentfactory_cloud.scope_plans import ScopePlans

class GameTeamWebTests(unittest.TestCase):
    setUp=fixture.BriefAPITests.setUp
    create=fixture.BriefAPITests.create
    def setup_team(self):
        brief=self.create();p=ScopePlans(self.app.state.brief_store);plan=p.write(brief['id'],'Local Creator',1,'scope-0001')
        p.write(brief['id'],'Local Creator',1,'agree-0001',ident=plan['id'],expected_plan=1,agree=True)
        url='/api/briefs/'+brief['id']+'/team';return url,self.client.get(url).json()
    def test_explicit_bounded_assessment_and_no_live_endpoints(self):
        url,v=self.setup_team();self.assertIsNone(v['core_assessment'])
        body={'expected_digest':v['snapshot_digest'],'confirmed':True}
        response=self.client.post(url+'/assess',json=body)
        self.assertEqual(response.status_code,200,response.text);self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertFalse(response.json()['execution_ready'])
        for extra in ({'provider':'cloud'},{'candidates':[]},{'approved':True}):self.assertEqual(self.client.post(url+'/assess',json=body|extra).status_code,422)
        self.assertEqual(self.client.post(url+'/assess',json=body|{'confirmed':False}).status_code,400)
        for action in ('start','stop'):self.assertEqual(self.client.post(url+'/'+action,json={}).status_code,404)
    def test_access_origin_tenant_and_stale_rejection(self):
        url,v=self.setup_team();body={'expected_digest':v['snapshot_digest'],'confirmed':True}
        for env in ({'AGENT_FACTORY_API_TENANTS':'other'},{'AGENT_FACTORY_API_SCOPES':'read'}):
            with patch.dict('os.environ',env):self.assertEqual(self.client.post(url+'/assess',json=body).status_code,403)
        with patch.dict('os.environ',{'AGENT_FACTORY_API_ACTOR':'Other'}):self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.post(url+'/assess',json=body,headers={'Origin':'https://untrusted.example'}).status_code,403)
        self.assertEqual(self.client.post(url+'/assess',json=body|{'expected_digest':'0'*64}).status_code,409)
