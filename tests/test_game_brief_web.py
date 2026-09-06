"""Real loopback API boundary and durable conflict behavior."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentfactory_cloud.brief_web import create_app
from agentfactory_cloud.game_briefs import FIELDS


class BriefAPITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.env = patch.dict('os.environ', {'AGENT_FACTORY_API_TOKEN': '', 'AGENT_FACTORY_API_ACTOR': 'Local Creator',
                 'AGENT_FACTORY_API_SCOPES': 'read,write', 'AGENT_FACTORY_API_TENANTS': '*'})
        self.env.start(); self.addCleanup(self.env.stop)
        self.app = create_app(Path(self.directory.name))
        self.client = TestClient(self.app, base_url='http://localhost'); self.addCleanup(self.client.close)

    def create(self):
        response = self.client.post('/api/briefs', json={'original_text': 'A moon garden', 'command_id': 'create-0001'})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_durable_create_read_edit_and_old_version(self):
        brief = self.create(); url = '/api/briefs/' + brief['id']
        response = self.client.post(url + '/edit', json={'expected_revision': 1, 'command_id': 'edit-0001',
                                   'fields': {key: 'Human text' for key in FIELDS}})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get(url).json()['revision'], 2)
        earlier = self.client.get(url + '?revision=1')
        self.assertEqual(earlier.status_code, 200, earlier.text)
        self.assertEqual(earlier.json()['fields']['genre'], '')

    def test_stale_edit_returns_conflict_without_overwrite(self):
        brief = self.create(); url = '/api/briefs/' + brief['id'] + '/edit'
        body = {'expected_revision': 1, 'command_id': 'edit-0001', 'fields': {key: 'First' for key in FIELDS}}
        self.assertEqual(self.client.post(url, json=body).status_code, 200)
        body.update(command_id='edit-0002', fields={key: 'Stale' for key in FIELDS})
        self.assertEqual(self.client.post(url, json=body).status_code, 409)

    def test_default_ai_disabled_and_caller_cannot_select_provider_or_authority(self):
        brief = self.create(); url = '/api/briefs/' + brief['id'] + '/suggest'
        body = {'expected_revision': 1, 'command_id': 'suggest-0001'}
        self.assertEqual(self.client.post(url, json=body).status_code, 400)
        body['provider'] = 'remote'
        self.assertEqual(self.client.post(url, json=body).status_code, 422)

    def test_cross_origin_nonloopback_and_oversized_body_denied(self):
        self.assertEqual(self.client.get('/api/briefs', headers={'Host': 'evil.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/briefs', headers={'Origin': 'http://evil.example'}, json={}).status_code, 403)
        self.assertEqual(self.client.post('/api/briefs', content='x' * 65537).status_code, 413)

    def test_authentication_write_scope_and_actor_isolation(self):
        brief = self.create()
        with patch.dict('os.environ', {'AGENT_FACTORY_API_TOKEN': 'test-only-local-key'}):
            self.assertEqual(self.client.get('/api/briefs').status_code, 401)
            response = self.client.post('/auth/login', json={'token': 'test-only-local-key'})
            self.assertEqual(response.status_code, 200)
            self.assertIn('HttpOnly', response.headers['set-cookie'])
            self.assertEqual(self.client.get('/api/briefs').status_code, 200)
            with patch.dict('os.environ', {'AGENT_FACTORY_API_SCOPES': 'read'}):
                self.assertEqual(self.client.post('/api/briefs', headers={'Authorization': 'Bearer test-only-local-key'}, json={}).status_code, 403)
            with patch.dict('os.environ', {'AGENT_FACTORY_API_ACTOR': 'Another Creator'}):
                response = self.client.get('/api/briefs/' + brief['id'], headers={'Authorization': 'Bearer test-only-local-key'})
                self.assertEqual(response.status_code, 404)


if __name__ == '__main__': unittest.main()
