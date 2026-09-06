"""Actual SQLite admission consumer tests; synthetic workers, no AI execution."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from agent_factory.adapters import HEALTH_DIMENSIONS
from agent_factory.models import WorkItem
from agent_factory.storage import SQLiteStorage
from agent_factory.worker_admission import AdmissionRequest, WorkerAdmissionService
from agentfactory_cloud.worker_gateway import GatewayDenied, WorkerCredential, WorkerGateway


class GatewayFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.database = self.root / 'core.db'
        self.storage = SQLiteStorage(self.database)
        self.addCleanup(self.storage.close)
        self.authority = WorkerAdmissionService(self.storage)
        self.authority.configure_pool(pool_id='lab-pool', capacity=1,
            allowed_runtimes=('direct-cli',), valid_until=datetime.now(timezone.utc) + timedelta(hours=1),
            actor='trusted-test-host', reason='Synthetic one-slot lab')
        self.tokens = {}; self.credentials = []; self.jobs = []
        for worker, tenant in (('worker-a', 'tenant-a'), ('worker-b', 'tenant-b')):
            self.authority.bind_worker(worker_id=worker, tenant_id=tenant, pool_id='lab-pool',
                actor='trusted-test-host', reason='Synthetic registration')
            qualification = self.storage.record_worker_qualification(worker_id=worker,
                provider_id='synthetic', role='Implementation Worker', capabilities=['synthetic'],
                dimensions={name: {'status': 'pass', 'evidence': 'synthetic fixture'} for name in HEALTH_DIMENSIONS},
                evidence={'fixture': True}, status='qualified', ttl_seconds=3600)
            project = self.storage.create_project(worker, 'Synthetic gateway fixture')
            task = self.storage.create_task(WorkItem(title='Synthetic task', description='No provider call',
                project_id=project, permissions=['read_project']))
            run = self.storage.start_durable_run(project_id=project, task_id=task,
                workflow_id=worker, workflow_version='1', definition={'id': worker},
                stages=[{'id': 'implementation', 'depends_on': []}])
            self.storage.transition_durable_stage(run, 'implementation', 'running', {'reason': 'fixture'})
            self.authority.bind_project(project_id=project, tenant_id=tenant, authority_digest='a' * 64,
                actor='trusted-test-host', reason='Synthetic ownership')
            lifecycle = self.storage.db.execute('SELECT version FROM worker_lifecycle WHERE worker_id=?', (worker,)).fetchone()[0]
            self.jobs.append(AdmissionRequest(request_id='request-' + worker, tenant_id=tenant,
                project_id=project, task_id=task, run_id=run, stage_key='implementation', worker_id=worker,
                runtime='direct-cli', provider_id='synthetic', role='Implementation Worker',
                required_capabilities=('synthetic',), qualification_id=qualification,
                expected_pool_version=1, expected_worker_version=1, expected_project_version=1,
                expected_lifecycle_version=lifecycle, ttl_seconds=60))
            # Public fixture strings, never production credentials.
            token = 'synthetic-test-only-' + worker + '-credential'
            self.tokens[worker] = token
            instant = datetime.now(timezone.utc)
            self.credentials.append(WorkerCredential(worker, tenant, 1,
                hashlib.sha256(token.encode()).hexdigest(), instant - timedelta(seconds=1), instant + timedelta(hours=1)))
        self.gateway = self.make_gateway()
        self.token = self.tokens['worker-a']; self.job = self.jobs[0]

    def make_gateway(self, **changes):
        options = {'credentials': tuple(self.credentials), 'requests': tuple(self.jobs)}
        options.update(changes)
        return WorkerGateway(self.database, **options)

    def counts(self):
        return {table: self.storage.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                for table in ('assignments', 'leases', 'attempts', 'worker_admissions', 'events')}

    def stopped(self, receipt):
        return self.authority.reconcile_stopped(admission_id=receipt['admission_id'],
            fencing_token=receipt['fencing_token'], evidence_digest='b' * 64,
            actor='trusted-test-host', reason='Synthetic fixture has no launched process')


class WorkerGatewayTests(GatewayFixture):
    def test_claim_restart_replay_and_renew_use_same_core_receipt(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        before = self.counts()
        replay = self.make_gateway().claim(self.token, self.job.request_id)
        self.assertEqual(first, replay)
        self.assertEqual(before, self.counts())
        renewed = self.make_gateway().renew(self.token, self.job.request_id, first['fencing_token'])
        for name in ('admission_id', 'assignment_id', 'lease_id', 'attempt_id', 'run_id', 'stage_id', 'fencing_token'):
            self.assertEqual(first[name], renewed[name])
        self.assertGreaterEqual(renewed['expires_at'], first['expires_at'])
        self.assertTrue(renewed['active'])
        self.assertFalse(renewed['execution_eligible'])
        self.assertEqual(renewed['blocked_reason'], 'remote_launcher_unqualified')
        self.assertIsNone(renewed['worktree_id'])
        self.assertNotIn(self.token, str(renewed))
        self.assertNotIn(str(self.root), str(renewed))
        self.assertTrue(self.storage.integrity_check()['ok'])

    def test_invalid_or_expired_credentials_never_open_database(self):
        expired = self.make_gateway(clock=lambda: self.credentials[0].expires_at)
        with patch('agentfactory_cloud.worker_gateway.SQLiteStorage', side_effect=AssertionError('must not open')):
            for gateway, token in ((self.gateway, None), (self.gateway, 'x' * 40),
                                   (self.gateway, '\u2603' * 40), (expired, self.token)):
                with self.subTest(token=token), self.assertRaises(GatewayDenied) as denied:
                    gateway.claim(token, self.job.request_id)
                self.assertEqual(denied.exception.status, 401)

    def test_worker_tenant_and_request_scope_cannot_be_selected_by_worker(self):
        before = self.counts()
        variants = [self.jobs[1], replace(self.job, tenant_id='tenant-b'),
                    replace(self.job, expected_worker_version=2)]
        for job in variants:
            with self.subTest(job=job), self.assertRaises(GatewayDenied):
                self.make_gateway(requests=(job,)).claim(self.token, job.request_id)
        for request_id in ('unknown', [], '../request'):
            with self.subTest(request_id=request_id), self.assertRaises(GatewayDenied):
                self.gateway.claim(self.token, request_id)
        self.assertEqual(before, self.counts())

    def test_rebinding_invalidates_credential_and_cannot_revive_old_lease(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        self.authority.bind_worker(worker_id='worker-a', pool_id='lab-pool', tenant_id='tenant-a',
            expected_version=1, enabled=False, actor='trusted-test-host', reason='Revoke test credential')
        with self.assertRaises(GatewayDenied) as denied:
            self.gateway.renew(self.token, self.job.request_id, first['fencing_token'])
        self.assertEqual(denied.exception.status, 401)
        self.authority.bind_worker(worker_id='worker-a', pool_id='lab-pool', tenant_id='tenant-a',
            expected_version=2, enabled=True, actor='trusted-test-host', reason='New generation')
        with self.assertRaises(GatewayDenied):
            self.gateway.authenticate(self.token)
        self.assertEqual(self.storage.db.execute('SELECT occupancy_state FROM worker_admissions').fetchone()[0], 'occupied')

    def test_changed_trusted_request_cannot_reuse_id_after_restart(self):
        self.gateway.claim(self.token, self.job.request_id)
        before = self.counts()
        changed = self.make_gateway(requests=(replace(self.job, ttl_seconds=61),))
        with self.assertRaises(GatewayDenied):
            changed.claim(self.token, self.job.request_id)
        self.assertEqual(before, self.counts())

    def test_two_authenticated_tenants_compete_for_one_core_slot(self):
        barrier = threading.Barrier(2)
        def compete(job):
            barrier.wait(timeout=10)
            try:
                return self.make_gateway().claim(self.tokens[job.worker_id], job.request_id)
            except GatewayDenied as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(compete, self.jobs))
        self.assertEqual(sum(isinstance(r, dict) for r in results), 1)
        self.assertIn('worker_capacity_unavailable', results)
        self.assertEqual(self.counts()['attempts'], 1)

    def test_expired_lease_holds_capacity_until_exact_host_stop_reconciliation(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        # Actual persisted expiry simulates lost renewal without a minute-long sleep.
        self.storage.db.execute("UPDATE leases SET expires_at=? WHERE id=?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), first['lease_id']))
        self.storage.db.commit()
        for fence in (first['fencing_token'], first['fencing_token'] + 1):
            with self.assertRaises(GatewayDenied):
                self.gateway.renew(self.token, self.job.request_id, fence)
        self.assertFalse(self.gateway.claim(self.token, self.job.request_id)['active'])
        with self.assertRaises(GatewayDenied) as denied:
            self.gateway.claim(self.tokens['worker-b'], self.jobs[1].request_id)
        self.assertEqual(denied.exception.code, 'worker_capacity_unavailable')
        with self.assertRaises(PermissionError):
            self.authority.reconcile_stopped(admission_id=first['admission_id'], fencing_token=first['fencing_token'] + 1,
                evidence_digest='b' * 64, actor='trusted-test-host', reason='Wrong fence')
        self.stopped(first)
        second = self.gateway.claim(self.tokens['worker-b'], self.jobs[1].request_id)
        self.assertGreater(second['fencing_token'], first['fencing_token'])
        with self.assertRaises(GatewayDenied):
            self.gateway.renew(self.token, self.job.request_id, first['fencing_token'])
        self.assertEqual(self.gateway.claim(self.tokens['worker-b'], self.jobs[1].request_id), second)

    def test_drain_finishes_existing_work_but_quarantine_blocks_renewal(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        self.storage.set_worker_lifecycle('worker-a', 'draining', reason='Synthetic drain')
        self.assertTrue(self.gateway.renew(self.token, self.job.request_id, first['fencing_token'])['active'])
        with self.assertRaises(GatewayDenied):
            self.make_gateway(requests=(replace(self.job, request_id='new-work'),)).claim(self.token, 'new-work')
        self.storage.set_worker_lifecycle('worker-a', 'quarantined', reason='Synthetic quarantine')
        with self.assertRaises(GatewayDenied):
            self.gateway.renew(self.token, self.job.request_id, first['fencing_token'])
        self.assertFalse(self.gateway.claim(self.token, self.job.request_id)['active'])
        self.assertEqual(self.counts()['worker_admissions'], 1)

    def test_core_qualification_invalidation_blocks_claim_and_renewal(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        self.storage.record_worker_qualification(worker_id='worker-a', provider_id='synthetic',
            role='Implementation Worker', capabilities=['synthetic'],
            dimensions={name: {'status': 'fail', 'evidence': 'synthetic failure'} for name in HEALTH_DIMENSIONS},
            evidence={'fixture': 'failed canary'}, status='failed', ttl_seconds=60)
        with self.assertRaises(GatewayDenied):
            self.gateway.renew(self.token, self.job.request_id, first['fencing_token'])
        self.assertFalse(self.gateway.claim(self.token, self.job.request_id)['active'])

    def test_worktree_receipt_requires_exact_ready_core_attempt_binding(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        worktree = self.storage.create_managed_worktree(assignment_id=first['assignment_id'],
            fencing_token=first['fencing_token'], attempt_id=first['attempt_id'],
            repository='synthetic-repository', base_sha='c' * 40, branch='synthetic-branch',
            path=str(self.root / 'private-synthetic-worktree'))
        self.assertIsNone(self.gateway.claim(self.token, self.job.request_id)['worktree_id'])
        self.storage.transition_managed_worktree(worktree, 'ready')
        ready = self.gateway.claim(self.token, self.job.request_id)
        self.assertEqual(ready['worktree_id'], worktree)
        self.assertFalse(ready['execution_eligible'])
        self.assertNotIn(str(self.root), str(ready))
        self.storage.transition_managed_worktree(worktree, 'missing')
        self.assertIsNone(self.gateway.claim(self.token, self.job.request_id)['worktree_id'])

    def test_unknown_renewal_never_creates_admission(self):
        before = self.counts()
        with self.assertRaises(GatewayDenied):
            self.gateway.renew(self.token, self.job.request_id, 1)
        self.assertEqual(before, self.counts())

    def test_same_worker_replacement_never_accepts_previous_fence(self):
        first = self.gateway.claim(self.token, self.job.request_id)
        self.stopped(first)
        next_job = replace(self.job, request_id='replacement-same-worker')
        gateway = self.make_gateway(requests=(self.job, next_job))
        second = gateway.claim(self.token, next_job.request_id)
        self.assertGreater(second['fencing_token'], first['fencing_token'])
        self.assertNotEqual(second['attempt_id'], first['attempt_id'])
        before = self.counts()
        for request_id in (self.job.request_id, next_job.request_id):
            with self.subTest(request_id=request_id), self.assertRaises(GatewayDenied):
                gateway.renew(self.token, request_id, first['fencing_token'])
        self.assertEqual(before, self.counts())
        self.assertEqual(gateway.claim(self.token, next_job.request_id), second)

    def test_credential_lifetime_and_unique_configuration_are_bounded(self):
        credential = self.credentials[0]
        for changes in ({'worker_version': True}, {'token_digest': 'bad'},
                        {'issued_at': datetime.now()}, {'expires_at': credential.issued_at},
                        {'expires_at': credential.issued_at + timedelta(days=2)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(credential, **changes)
        with self.assertRaises(ValueError):
            self.make_gateway(credentials=(credential, credential))
        with self.assertRaises(ValueError):
            self.make_gateway(requests=(self.job, self.job))


if __name__ == '__main__':
    unittest.main()
