"""Authenticated admission access; Core remains the sole lease authority.

No remote launcher, result publication or worker-supplied stop reconciliation is
enabled. The trusted host supplies credentials and approved Core requests.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from pathlib import Path
from types import MappingProxyType

from agent_factory.storage import SQLiteStorage
from agent_factory.worker_admission import (
    AdmissionRequest, CapacityUnavailableError, WorkerAdmissionService,
)


class GatewayDenied(PermissionError):
    def __init__(self, code='worker_access_denied', status=403):
        super().__init__(code)
        self.code, self.status = code, status


def _instant(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Aware worker credential time required')
    return value.astimezone(timezone.utc)


def _identifier(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 128 or not value.isascii()
            or any(not (c.isalnum() or c in '-_:.') for c in value)):
        raise ValueError('Invalid worker identifier')


@dataclass(frozen=True)
class WorkerCredential:
    worker_id: str
    tenant_id: str
    worker_version: int
    token_digest: str
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self):
        _identifier(self.worker_id); _identifier(self.tenant_id)
        if type(self.worker_version) is not int or self.worker_version < 1:
            raise ValueError('Invalid worker generation')
        if (not isinstance(self.token_digest, str) or len(self.token_digest) != 64
                or any(c not in '0123456789abcdef' for c in self.token_digest)):
            raise ValueError('Invalid worker credential digest')
        if not timedelta(0) < _instant(self.expires_at) - _instant(self.issued_at) <= timedelta(days=1):
            raise ValueError('Worker credentials require a bounded lifetime')


class WorkerGateway:
    def __init__(self, database: Path, *, credentials: tuple[WorkerCredential, ...],
                 requests: tuple[AdmissionRequest, ...], clock=None):
        # Configuration is provisioned by the host, never a worker HTTP body.
        if len(credentials) > 64 or len(requests) > 1024:
            raise ValueError('Worker gateway configuration limit')
        if len({c.token_digest for c in credentials}) != len(credentials):
            raise ValueError('Worker credential digests must be unique')
        jobs = {}
        for request in requests:
            _identifier(request.request_id)
            if request.request_id in jobs:
                raise ValueError('Core admission request IDs must be unique')
            jobs[request.request_id] = request
        self.database = Path(database)
        self.credentials = tuple(credentials)
        self.requests = MappingProxyType(jobs)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @contextmanager
    def _storage(self):
        storage = SQLiteStorage(self.database)
        try:
            yield storage
        finally:
            storage.close()

    def _credential(self, token):
        if not isinstance(token, str) or not 32 <= len(token) <= 256 or not token.isascii():
            raise GatewayDenied('worker_authentication_required', 401)
        digest = hashlib.sha256(token.encode('ascii')).hexdigest()
        credential = next((c for c in self.credentials if hmac.compare_digest(c.token_digest, digest)), None)
        current = _instant(self.clock())
        if credential is None or not _instant(credential.issued_at) <= current < _instant(credential.expires_at):
            raise GatewayDenied('worker_authentication_required', 401)
        return credential

    @staticmethod
    def _binding(storage, credential):
        row = storage.db.execute('SELECT * FROM worker_admission_workers WHERE worker_id=?',
                                 (credential.worker_id,)).fetchone()
        if (not row or not row['enabled'] or row['tenant_id'] != credential.tenant_id
                or row['version'] != credential.worker_version):
            raise GatewayDenied('worker_authentication_required', 401)

    def authenticate(self, token):
        credential = self._credential(token)  # Bad tokens never open Core storage.
        with self._storage() as storage:
            self._binding(storage, credential)
        return credential

    def _request(self, credential, request_id):
        try:
            _identifier(request_id)
        except ValueError:
            raise GatewayDenied('invalid_worker_request', 400) from None
        request = self.requests.get(request_id)
        if (request is None or request.worker_id != credential.worker_id
                or request.tenant_id != credential.tenant_id
                or request.expected_worker_version != credential.worker_version):
            raise GatewayDenied()
        return request

    @staticmethod
    def _view(storage, receipt):
        lease = receipt.lease
        worktree = storage.db.execute("""SELECT id FROM worktrees WHERE assignment_id=?
            AND lease_id=? AND fencing_token=? AND owner=? AND attempt_id=? AND task_id=?
            AND status='ready' ORDER BY id DESC LIMIT 1""",
            (lease.assignment_id, lease.lease_id, lease.fencing_token, lease.worker,
             receipt.attempt_id, lease.task_id)).fetchone()
        return {'request_id': receipt.request_id, 'admission_id': receipt.admission_id,
            'worker_id': lease.worker, 'tenant_id': receipt.tenant_id,
            'project_id': receipt.project_id, 'task_id': lease.task_id, 'run_id': receipt.run_id,
            'stage_id': receipt.stage_id, 'attempt_id': receipt.attempt_id,
            'assignment_id': lease.assignment_id, 'lease_id': lease.lease_id,
            'fencing_token': lease.fencing_token, 'expires_at': lease.expires_at,
            'active': receipt.active, 'occupancy': receipt.status,
            'worktree_id': int(worktree['id']) if worktree else None,
            'execution_eligible': False, 'blocked_reason': 'remote_launcher_unqualified'}

    def _operation(self, token, request_id, *, fence=None, renew=False):
        credential = self._credential(token)
        request = self._request(credential, request_id)
        if renew and (type(fence) is not int or fence < 1):
            raise GatewayDenied('invalid_worker_request', 400)
        try:
            with self._storage() as storage:
                self._binding(storage, credential)
                authority = WorkerAdmissionService(storage)
                if renew:
                    row = storage.db.execute('SELECT fencing_token FROM worker_admissions WHERE request_id=?',
                                             (request.request_id,)).fetchone()
                    if row is None or row['fencing_token'] != fence:
                        raise GatewayDenied('stale_worker_admission', 409)
                receipt = authority.admit(request)
                if renew:
                    storage.renew_task_lease(receipt.lease.assignment_id, fence,
                                             ttl_seconds=request.ttl_seconds)
                    receipt = authority.admit(request)
                return self._view(storage, receipt)
        except GatewayDenied:
            raise
        except CapacityUnavailableError:
            raise GatewayDenied('worker_capacity_unavailable', 409) from None
        except (PermissionError, ValueError, KeyError):
            raise GatewayDenied('worker_admission_denied', 409) from None

    def claim(self, token, request_id):
        return self._operation(token, request_id)

    def renew(self, token, request_id, fencing_token):
        return self._operation(token, request_id, fence=fencing_token, renew=True)
