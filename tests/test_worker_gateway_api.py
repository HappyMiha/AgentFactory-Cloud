"""Loopback HTTP lab: actual sockets plus adversarial ASGI boundary cases."""
import asyncio
import http.client
import json
import socket
import threading
import time
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import uvicorn

from agentfactory_cloud.worker_gateway_api import worker_gateway_router
from test_worker_gateway import GatewayFixture


class WorkerGatewayAPITests(GatewayFixture):
    def setUp(self):
        super().setUp()
        self.app = FastAPI()
        self.app.include_router(worker_gateway_router(self.gateway))
        self.client = TestClient(self.app, base_url='http://127.0.0.1', client=('127.0.0.1', 12345))
        self.addCleanup(self.client.close)
        self.headers = {'Authorization': 'Bearer ' + self.token}
        self.body = {'request_id': self.job.request_id}

    def test_authenticated_claim_and_fenced_renew(self):
        response = self.client.post('/worker/admissions', headers=self.headers, json=self.body)
        self.assertEqual(response.status_code, 200, response.text)
        receipt = response.json()
        self.assertFalse(receipt['execution_eligible'])
        self.assertEqual(response.headers['cache-control'], 'no-store')
        response = self.client.post('/worker/admissions/renew', headers=self.headers,
            json=self.body | {'fencing_token': receipt['fencing_token']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['admission_id'], receipt['admission_id'])

    def test_transport_and_duplicate_authorization_rejected_before_admission(self):
        before = self.counts()
        for extra in ({'Host': 'remote.example'}, {'Origin': 'http://127.0.0.1'},
                      {'Forwarded': 'for=127.0.0.1'}, {'X-Forwarded-For': '127.0.0.1'},
                      {'X-Forwarded-Proto': 'https'}):
            with self.subTest(extra=extra):
                response = self.client.post('/worker/admissions', headers=self.headers | extra, json=self.body)
                self.assertEqual(response.status_code, 403)
        with TestClient(self.app, base_url='http://localhost', client=('192.0.2.1', 12345)) as remote:
            self.assertEqual(remote.post('/worker/admissions', headers=self.headers, json=self.body).status_code, 403)
        duplicated = [('Authorization', 'Bearer ' + self.token)] * 2
        self.assertEqual(self.client.post('/worker/admissions', headers=duplicated, json=self.body).status_code, 401)
        self.assertEqual(before, self.counts())

    def test_missing_or_invalid_auth_is_checked_before_receiving_body(self):
        received = []
        sent = []
        async def receive():
            received.append(True)
            raise AssertionError('Unauthorized request body must not be read')
        async def send(message):
            sent.append(message)
        scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                 'method': 'POST', 'scheme': 'http', 'path': '/worker/admissions',
                 'raw_path': b'/worker/admissions', 'query_string': b'',
                 'headers': [(b'host', b'localhost')], 'client': ('127.0.0.1', 12345),
                 'server': ('127.0.0.1', 80), 'root_path': ''}
        asyncio.run(self.app(scope, receive, send))
        self.assertEqual(received, [])
        self.assertEqual(sent[0]['status'], 401)

    def test_strict_document_denies_worker_authority_and_private_data_echo(self):
        before = self.counts()
        bodies = [json.dumps(self.body | {field: 'private-untrusted-value'}) for field in
            ('tenant_id', 'worker_id', 'project_id', 'task_id', 'run_id', 'provider_id', 'qualification_id',
             'runtime', 'worktree', 'capabilities', 'ttl_seconds', 'stop_evidence', 'result')]
        bodies += ['[]', '{}', '{', 'x' * 1025,
            '{"request_id":"one","request_id":"two"}', '{"request_id":true}',
            '{"request_id":"../elsewhere"}', '{"request_id":'+ '[]' + '}']
        for body in bodies:
            with self.subTest(body=body[:80]):
                response = self.client.post('/worker/admissions', headers=self.headers, content=body)
                self.assertEqual(response.status_code, 400, response.text)
                self.assertNotIn('private-untrusted-value', response.text)
                self.assertNotIn(self.token, response.text)
                self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(before, self.counts())

    def test_unknown_and_other_worker_requests_have_same_denial(self):
        other = self.client.post('/worker/admissions', headers=self.headers,
            json={'request_id': self.jobs[1].request_id})
        unknown = self.client.post('/worker/admissions', headers=self.headers,
            json={'request_id': 'unknown'})
        self.assertEqual(other.status_code, 403)
        self.assertEqual(other.json(), unknown.json())
        self.assertEqual(self.counts()['attempts'], 0)

    def test_errors_are_redacted_and_cannot_release_or_publish(self):
        with patch.object(self.gateway, 'claim', side_effect=RuntimeError('private-host-path-token')):
            response = self.client.post('/worker/admissions', headers=self.headers, json=self.body)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private-host', response.text)
        for route in ('stop', 'release', 'reconcile', 'results', 'launch', 'register'):
            self.assertEqual(self.client.post('/worker/' + route, headers=self.headers, json=self.body).status_code, 404)
        for fence in (True, 0, '1', 1.5):
            self.assertEqual(self.client.post('/worker/admissions/renew', headers=self.headers,
                json=self.body | {'fencing_token': fence}).status_code, 400)

    def test_revocation_between_authentication_and_claim_is_rechecked(self):
        original = self.gateway.claim
        def revoked(*args):
            # Simulate rotation while an authenticated request body is arriving.
            with self.gateway._storage() as storage:
                from agent_factory.worker_admission import WorkerAdmissionService
                WorkerAdmissionService(storage).bind_worker(worker_id='worker-a', pool_id='lab-pool',
                    tenant_id='tenant-a', expected_version=1, enabled=False,
                    actor='trusted-test-host', reason='Revoke during body arrival')
            return original(*args)
        with patch.object(self.gateway, 'claim', side_effect=revoked):
            response = self.client.post('/worker/admissions', headers=self.headers, json=self.body)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.counts()['attempts'], 0)

    def test_real_http_server_restart_lost_response_replay_and_stale_renewal(self):
        def start_server(gateway):
            app = FastAPI(); app.include_router(worker_gateway_router(gateway))
            listener = socket.socket()
            listener.bind(('127.0.0.1', 0))
            listener.listen(8)
            server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False,
                proxy_headers=False, lifespan='off', limit_concurrency=8))
            thread = threading.Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
            thread.start()
            def stop():
                server.should_exit = True
                thread.join(timeout=8)
                listener.close()
                self.assertFalse(thread.is_alive(), 'Loopback server did not stop')
            self.addCleanup(stop)
            deadline = time.monotonic() + 8
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(server.started)
            return listener.getsockname()[1], stop
        def post(port, body, token, path='/worker/admissions'):
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=8)
            try:
                connection.request('POST', path, json.dumps(body),
                    {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
                response = connection.getresponse()
                return response.status, json.loads(response.read())
            finally:
                connection.close()
        port, stop = start_server(self.gateway)
        status, first = post(port, self.body, self.token)
        self.assertEqual(status, 200, first)
        # Client treats the first reply as lost; restart the actual transport.
        stop()
        port, _ = start_server(self.make_gateway())
        status, replay = post(port, self.body, self.token)
        self.assertEqual(status, 200, replay)
        self.assertEqual(first, replay)
        self.assertEqual(self.counts()['attempts'], 1)
        status, _ = post(port, {'request_id': self.jobs[1].request_id}, self.tokens['worker-b'])
        self.assertEqual(status, 409)
        self.stopped(first)
        status, _ = post(port, self.body | {'fencing_token': first['fencing_token']},
                         self.token, '/worker/admissions/renew')
        self.assertEqual(status, 409)
        status, replacement = post(port, {'request_id': self.jobs[1].request_id}, self.tokens['worker-b'])
        self.assertEqual(status, 200, replacement)
        self.assertGreater(replacement['fencing_token'], first['fencing_token'])
        self.assertFalse(replacement['execution_eligible'])


if __name__ == '__main__':
    unittest.main()
