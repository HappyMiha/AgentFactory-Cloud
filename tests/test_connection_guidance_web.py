import unittest
from unittest.mock import patch
from fastapi import FastAPI
import test_game_brief_web as fixture
from agentfactory_cloud.connection_guidance_web import install_routes

class GuidanceWebTests(unittest.TestCase):
    setUp=fixture.BriefAPITests.setUp
    def test_readonly_no_store_and_no_account_input(self):
        r=self.client.get('/api/connection-guidance');self.assertEqual(r.status_code,200)
        self.assertEqual(r.headers['cache-control'],'no-store');self.assertFalse(r.json()['can_connect'])
        self.assertEqual(self.client.get('/api/connection-guidance?approved=true').status_code,400)
        for path in ('/api/connection-guidance','/api/connection-guidance/connect','/api/connection-guidance/canary'):
            self.assertIn(self.client.post(path,json={'approved':True,'secret':'synthetic'}).status_code,(404,405))
    def test_auth_tenant_and_catalogue_failure(self):
        with patch.dict('os.environ',{'AGENT_FACTORY_API_TENANTS':'other'}):self.assertEqual(self.client.get('/api/connection-guidance').status_code,403)
        with patch.dict('os.environ',{'AGENT_FACTORY_API_TOKEN':'synthetic-token'}):self.assertEqual(self.client.get('/api/connection-guidance').status_code,401)
        with patch('agentfactory_cloud.connection_guidance_web.guidance',side_effect=OSError('private path')):
            r=self.client.get('/api/connection-guidance');self.assertEqual(r.status_code,503);self.assertNotIn('private path',r.text)
    def test_mount_requires_boundary(self):
        with self.assertRaises(ValueError):install_routes(FastAPI(),'.')
