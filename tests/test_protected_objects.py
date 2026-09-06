"""Actual opt-in S3, PostgreSQL and ClamAV tests; no fake object-store acceptance."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import sys
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
import uuid
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


@unittest.skipUnless(os.environ.get('CLOUD_OBJECTS_TEST_JSON'), 'Actual isolated S3/PostgreSQL/ClamAV configuration required')
class ProtectedObjectTests(unittest.TestCase):
    def setUp(self):
        import boto3
        import psycopg
        from psycopg import sql
        from botocore.config import Config
        from agentfactory_cloud.hosted_store import HostedStore, TenantContext, migrate, grant_runtime
        from agentfactory_cloud.object_migrations import migrate as migrate_objects, grant_runtime as grant_objects
        from agentfactory_cloud.protected_objects import ProtectedObjects, S3Objects
        from agentfactory_cloud.upload_inspection import ClamdScanner
        self.pg, self.sql = psycopg, sql
        self.config = json.loads(Path(os.environ['CLOUD_OBJECTS_TEST_JSON']).read_text())
        pg = self.config['postgres']
        if pg['host'] != '127.0.0.1' or pg['port'] == 5432 or not self.config['s3']['endpoint'].startswith('http://127.0.0.1:'):
            raise ValueError('Only explicit disposable loopback services are allowed')
        self.admin = psycopg.connect(**pg, dbname='postgres', autocommit=True)
        self.addCleanup(self.admin.close)
        self.name = 'cloud023_test_' + uuid.uuid4().hex[:16]
        self.role = self.name + '_role'
        password = secrets.token_urlsafe(32)
        self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(self.role), sql.Literal(password)))
        self.admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(self.name)))
        self.addCleanup(self.cleanup_database)
        with psycopg.connect(**pg, dbname=self.name) as db:
            migrate(db); grant_runtime(db, self.role)
            migrate_objects(db); grant_objects(db, self.role)
        self.store = HostedStore({**pg, 'user': self.role, 'password': password, 'dbname': self.name})
        self.a = TenantContext('tenant-a', 'creator-a'); self.b = TenantContext('tenant-b', 'creator-b')
        s3 = self.config['s3']
        self.client = boto3.client('s3', endpoint_url=s3['endpoint'], aws_access_key_id=s3['access_key'],
                                   aws_secret_access_key=s3['secret_key'], region_name='us-east-1',
                                   config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}, retries={'total_max_attempts': 1}))
        self.bucket = self.name.replace('_', '-')
        self.client.create_bucket(Bucket=self.bucket)
        self.addCleanup(self.cleanup_bucket)
        self.blobs = S3Objects.connect(bucket=self.bucket, **s3)
        self.scanner = ClamdScanner(self.config['clamd_port'])
        self.objects = ProtectedObjects(self.store, self.blobs, self.scanner)
        self.objects.configure_quota(self.a, 16*1024*1024)
        self.objects.configure_quota(self.b, 16*1024*1024)
        self.expiry = datetime.now(timezone.utc) - timedelta(seconds=1)

    def cleanup_database(self):
        self.admin.execute(self.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(self.sql.Identifier(self.name)))
        self.admin.execute(self.sql.SQL('DROP ROLE {}').format(self.sql.Identifier(self.role)))

    def cleanup_bucket(self):
        # A unique recorded test bucket only. Never enumerate or purge other buckets.
        for page in self.client.get_paginator('list_objects_v2').paginate(Bucket=self.bucket):
            for obj in page.get('Contents', []):
                self.client.delete_object(Bucket=self.bucket, Key=obj['Key'])
        self.client.delete_bucket(Bucket=self.bucket)

    def upload(self, context=None, data=b'print("safe synthetic game")', **changes):
        values = dict(path='src/game.gd', media_type='text/plain', sha256=hashlib.sha256(data).hexdigest(),
                      origin={'kind': 'SourceVersion', 'id': 'external-core-source', 'provenance_ref': 'rights-fixture'},
                      retain_until=self.expiry, command_id='upload-1')
        values.update(changes)
        return self.objects.upload(context or self.a, data, **values)

    def row(self, ident):
        with self.objects.transaction(self.a) as db:
            return self.objects.row(db, self.a, ident)

    def assert_erased(self, ident):
        key = self.row(ident)['object_key']
        value = self.client.get_object(Bucket=self.bucket, Key=key)
        try:
            self.assertEqual(value['Body'].read(), b'')
            self.assertEqual(value['Metadata'], {'agentfactory-deleted': 'v1'})
        finally:
            value['Body'].close()

    def test_real_roundtrip_manifest_export_and_tenant_denial(self):
        from agentfactory_cloud.protected_objects import ObjectUnavailable
        item = self.upload(); ident = item['id']
        self.assertEqual(item['state'], 'ready')
        self.assertEqual(item['manifest']['origin']['id'], 'external-core-source')
        self.assertNotIn('object_key', item)
        self.assertEqual(self.objects.download(self.a, ident, export=True), b'print("safe synthetic game")')
        for operation in (self.objects.download, self.objects.manifest, self.objects.delete):
            with self.assertRaises(ObjectUnavailable): operation(self.b, ident)
        with self.objects.transaction(self.b) as db:
            self.assertEqual(db.execute('SELECT * FROM cloud_objects').fetchall(), [])
        key = self.row(ident)['object_key']
        with self.assertRaises(HTTPError) as denied:
            urlopen(self.config['s3']['endpoint']+'/'+self.bucket+'/'+key, timeout=3)
        self.assertEqual(denied.exception.code, 403)
        audit_path = Path(self.config['audit_log'])
        deadline = time.monotonic()+5
        while True:
            audit = [json.loads(line) for line in audit_path.read_text().splitlines()] if audit_path.exists() else []
            own = [entry for entry in audit if entry.get('bucket') == self.bucket]
            if any(e['api'] == 'GetObject' and e['status_code'] == 403 for e in own):
                break
            if time.monotonic() > deadline:
                self.fail('Actual S3 denied access missing from server audit log')
            time.sleep(0.05)
        self.assertTrue(any(e['api'] == 'PutObject' and e['status_code'] == 200 for e in own))
        self.assertTrue(all(set(e) == {'time','request_id','api','bucket','status_code'} for e in own))
        events = self.objects.evidence(self.a)
        self.assertEqual([e['action'] for e in events], ['quota', 'upload_reserved', 'upload_ready', 'export'])
        self.assertEqual(events[2]['evidence']['inspection']['scan']['verdict'], 'clear')

    def test_quota_race_and_idempotency_preserve_one_object(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        self.objects.configure_quota(self.a, 4)
        def put(n):
            try: return self.upload(data=b'data', command_id=str(n))['state']
            except StoreConflict: return 'quota'
        with ThreadPoolExecutor(max_workers=2) as workers:
            self.assertCountEqual(list(workers.map(put, (1, 2))), ['ready', 'quota'])
        self.assertEqual(len(self.client.list_objects_v2(Bucket=self.bucket).get('Contents', [])), 1)

    def test_replay_conflict_and_deleted_upload_never_resurrects(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        first = self.upload()
        self.assertEqual(self.upload(), first)
        with self.assertRaises(StoreConflict): self.upload(data=b'changed')
        self.objects.delete(self.a, first['id'])
        self.assertEqual(self.upload()['state'], 'deleted')
        self.assert_erased(first['id'])

    def test_concurrent_same_command_returns_one_stable_identity(self):
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: self.upload(), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(self.client.list_objects_v2(Bucket=self.bucket)['KeyCount'], 1)

    def test_database_connection_terminated_after_actual_put_recovers(self):
        from agentfactory_cloud.protected_objects import ProtectedObjects
        original_transaction = self.objects.transaction
        active_pid = []
        @contextmanager
        def tracked(context):
            with original_transaction(context) as db:
                active_pid[:] = [db.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']]
                yield db
        self.objects.transaction = tracked
        original_put = self.blobs.put
        def terminate(*args):
            original_put(*args)
            self.admin.execute('SELECT pg_terminate_backend(%s)', (active_pid[0],))
        self.blobs.put = terminate
        with self.assertRaises(self.pg.Error): self.upload()
        self.blobs.put = original_put
        self.objects = ProtectedObjects(self.store, self.blobs, self.scanner)
        self.assertEqual(self.upload()['state'], 'ready')
        self.assertEqual(self.client.list_objects_v2(Bucket=self.bucket)['KeyCount'], 1)

    def test_public_policy_and_versioning_profiles_block(self):
        from agentfactory_cloud.protected_objects import S3Objects
        from agentfactory_cloud.hosted_store import StoreConflict
        policy = {'Version': '2012-10-17', 'Statement': [{'Effect': 'Allow', 'Principal': '*',
                  'Action': ['s3:GetObject'], 'Resource': ['arn:aws:s3:::'+self.bucket+'/*']}]}
        self.client.put_bucket_policy(Bucket=self.bucket, Policy=json.dumps(policy))
        try:
            with self.assertRaises(StoreConflict): S3Objects(self.client, self.bucket)
        finally:
            self.client.delete_bucket_policy(Bucket=self.bucket)
        self.client.put_bucket_versioning(Bucket=self.bucket, VersioningConfiguration={'Status': 'Enabled'})
        with self.assertRaises(StoreConflict): S3Objects(self.client, self.bucket)

    def test_interrupted_upload_recovers_same_key_after_response_loss(self):
        original = self.blobs.put
        def lost(*args):
            original(*args)
            raise OSError('injected response loss after actual S3 PUT')
        self.blobs.put = lost
        with self.assertRaises(OSError): self.upload()
        self.blobs.put = original
        with self.objects.transaction(self.a) as db:
            rows = db.execute('SELECT * FROM cloud_objects').fetchall()
            self.assertEqual(len(rows), 1); self.assertEqual(rows[0]['state'], 'pending')
            ident, key = str(rows[0]['id']), rows[0]['object_key']
        result = self.upload()
        self.assertEqual(result['id'], ident); self.assertEqual(result['state'], 'ready')
        self.assertEqual(self.row(ident)['object_key'], key)
        self.assertEqual(self.client.list_objects_v2(Bucket=self.bucket)['KeyCount'], 1)

    def test_abandoned_reservation_cleans_up_without_remote_bytes(self):
        original = self.blobs.put
        def unavailable(*args):
            raise OSError('injected outage before PUT')
        self.blobs.put = unavailable
        with self.assertRaises(OSError): self.upload()
        self.blobs.put = original
        with self.objects.transaction(self.a) as db:
            row = db.execute('SELECT * FROM cloud_objects').fetchone()
            self.assertEqual(row['state'], 'pending')
        self.assertEqual(self.objects.cleanup(self.a)[0]['state'], 'deleted')
        self.assertEqual(self.upload()['state'], 'deleted')
        self.assert_erased(str(row['id']))

    def test_late_put_after_backend_loss_and_cleanup_cannot_recreate_payload(self):
        entered, release = threading.Event(), threading.Event()
        errors, active_pid = [], []
        original_transaction, original_put = self.objects.transaction, self.blobs.put
        @contextmanager
        def tracked(context):
            with original_transaction(context) as db:
                active_pid[:] = [db.execute('SELECT pg_backend_pid() AS pid').fetchone()['pid']]
                yield db
        self.objects.transaction = tracked
        def delayed(*args):
            entered.set()
            if not release.wait(10):
                raise TimeoutError('Test PUT release deadline')
            original_put(*args)
        self.blobs.put = delayed
        def upload():
            try:
                self.upload()
            except Exception as exc:
                errors.append(type(exc).__name__)
        thread = threading.Thread(target=upload); thread.start()
        try:
            self.assertTrue(entered.wait(5))
            self.admin.execute('SELECT pg_terminate_backend(%s)', (active_pid[0],))
            deleted = self.objects.cleanup(self.a)
            self.assertEqual(deleted[0]['state'], 'deleted')
            release.set(); thread.join(10)
            self.assertFalse(thread.is_alive()); self.assertTrue(errors)
            self.assert_erased(deleted[0]['id'])
            self.assertEqual(self.objects.manifest(self.a, deleted[0]['id'])['state'], 'deleted')
            self.assertEqual(sum(o['Size'] for o in self.client.list_objects_v2(Bucket=self.bucket)['Contents']), 0)
            self.blobs.put = original_put
            self.objects.configure_quota(self.a, 1)
            self.assertEqual(self.upload(data=b'x', command_id='after-erasure')['state'], 'ready')
        finally:
            release.set(); thread.join(10)
            self.blobs.put = original_put
            self.objects.transaction = original_transaction

    def test_conditional_erase_rechecks_when_pending_upload_wins_create_race(self):
        from unittest.mock import patch
        with patch.object(self.blobs, 'put', side_effect=OSError('Before actual PUT')):
            with self.assertRaises(OSError): self.upload()
        with self.objects.transaction(self.a) as db:
            row = db.execute('SELECT * FROM cloud_objects').fetchone()
        item, key = self.objects.public(row), row['object_key']
        # The late upload wins immediately after the eraser observes absence.
        # Its first create must conflict, then CAS erases the now-existing bytes.
        original = self.blobs.client.put_object
        raced = []
        def put(**kwargs):
            if kwargs['Body'] == b'' and kwargs.get('IfNoneMatch') == '*' and not raced:
                raced.append(True)
                self.client.put_object(Bucket=self.bucket, Key=key, Body=b'print("safe synthetic game")', IfNoneMatch='*')
            return original(**kwargs)
        self.blobs.client.put_object = put
        try:
            self.assertEqual(self.objects.delete(self.a, item['id'])['state'], 'deleted')
            self.assertTrue(raced)
            self.assert_erased(item['id'])
        finally:
            self.blobs.client.put_object = original

    def test_retained_manifest_cap_includes_deleted_storage_fences(self):
        from unittest.mock import patch
        from agentfactory_cloud.hosted_store import StoreConflict
        with patch('agentfactory_cloud.protected_objects.MAX_MANIFESTS', 1):
            item = self.upload()
            self.objects.delete(self.a, item['id'])
            with self.assertRaises(StoreConflict): self.upload(command_id='second')
            self.assertEqual(self.upload()['state'], 'deleted')
            self.assert_erased(item['id'])

    def test_interrupted_delete_retains_quota_and_blocks_new_reference(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        item = self.upload()
        original = self.blobs.delete
        def lost(key):
            original(key)
            raise OSError('injected loss after actual S3 deletion')
        self.blobs.delete = lost
        with self.assertRaises(OSError): self.objects.delete(self.a, item['id'])
        self.assertEqual(self.objects.manifest(self.a, item['id'])['state'], 'deleting')
        with self.assertRaises(StoreConflict): self.objects.reference(self.a, item['id'], 'project-a')
        self.objects.configure_quota(self.a, len(b'print("safe synthetic game")'))
        with self.assertRaises(StoreConflict): self.upload(command_id='another')
        self.blobs.delete = original
        self.assertEqual(self.objects.delete(self.a, item['id'])['state'], 'deleted')
        self.assertEqual(self.upload(command_id='another')['state'], 'ready')

    def test_cleanup_retention_references_and_unknown_keys(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        referenced = self.upload()
        self.objects.reference(self.a, referenced['id'], 'release-original')
        retained = self.upload(command_id='retained', retain_until=datetime.now(timezone.utc)+timedelta(days=1))
        expired = self.upload(command_id='expired')
        self.client.put_object(Bucket=self.bucket, Key='unmanaged', Body=b'leave alone')
        result = self.objects.cleanup(self.a)
        self.assertEqual([x['id'] for x in result], [expired['id']])
        for item in (referenced, retained):
            with self.assertRaises(StoreConflict): self.objects.delete(self.a, item['id'])
            self.assertTrue(self.objects.download(self.a, item['id']))
        self.assertEqual(self.client.get_object(Bucket=self.bucket, Key='unmanaged')['Body'].read(), b'leave alone')
        self.objects.reference(self.a, referenced['id'], 'release-original', attach=False)
        self.assertEqual(self.objects.cleanup(self.a)[0]['id'], referenced['id'])

    def test_cleanup_rechecks_reference_attached_after_enumeration(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        item = self.upload()
        original = self.objects.delete
        def raced(context, ident):
            self.objects.reference(context, ident, 'new-reference')
            return original(context, ident)
        self.objects.delete = raced
        self.assertEqual(self.objects.cleanup(self.a), [])
        self.assertTrue(self.objects.download(self.a, item['id']))

    def test_actual_antivirus_and_archive_threats_reject_before_reservation(self):
        from agentfactory_cloud.upload_inspection import InspectionBlocked
        # Standard harmless antivirus test string, never executable content.
        eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        target = io.BytesIO()
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('bomb', b'x'*1024*1024)
        for data, changes in [(eicar, {}), (b'safe', {'path': '../escape'}),
                              (target.getvalue(), {'path': 'data.zip', 'media_type': 'application/zip'})]:
            with self.subTest(changes=changes), self.assertRaises(InspectionBlocked):
                self.upload(data=data, **changes)
        with self.objects.transaction(self.a) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM cloud_objects').fetchone()['n'], 0)
        self.assertEqual(self.client.list_objects_v2(Bucket=self.bucket).get('KeyCount', 0), 0)

    def test_actual_source_build_asset_and_zip_profiles(self):
        target = io.BytesIO()
        with zipfile.ZipFile(target, 'w') as z: z.writestr('src/main.gd', 'print("hello")')
        for kind, data, media, name in [('SourceVersion', b'source', 'text/plain', 'source.gd'),
                                      ('Build', target.getvalue(), 'application/zip', 'build.zip'),
                                      ('Asset', b'synthetic asset', 'application/octet-stream', 'asset.bin')]:
            item = self.upload(data=data, path=name, media_type=media, command_id=kind,
                               origin={'kind': kind, 'id': 'external-'+kind, 'provenance_ref': 'rights-fixture'})
            self.assertEqual(self.objects.download(self.a, item['id']), data)

    def test_integrity_tampering_blocks_export_without_false_success_evidence(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        item = self.upload(); key = self.row(item['id'])['object_key']
        self.client.put_object(Bucket=self.bucket, Key=key, Body=b'tampered')
        with self.assertRaises(StoreConflict): self.objects.download(self.a, item['id'], export=True)
        self.assertNotIn('export', [e['action'] for e in self.objects.evidence(self.a)])

    def test_history_identity_and_tenant_rls_cannot_be_changed_by_runtime_sql(self):
        self.upload()
        for statement in ["UPDATE cloud_objects SET manifest='{}'", 'DELETE FROM cloud_objects',
                          "UPDATE cloud_object_events SET action='fake'", 'DELETE FROM cloud_object_events',
                          "INSERT INTO cloud_object_quotas VALUES('tenant-other',1)"]:
            with self.subTest(statement=statement), self.assertRaises(self.pg.Error), self.objects.transaction(self.a) as db:
                db.execute(statement)
        with self.pg.connect(**self.store.connection_info) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM cloud_objects').fetchone()[0], 0)

    def test_schema_replay_and_unknown_checksum_block(self):
        from agentfactory_cloud.hosted_store import StoreConflict
        from agentfactory_cloud.object_migrations import migrate
        with self.pg.connect(**self.config['postgres'], dbname=self.name) as db:
            migrate(db)
            db.execute("UPDATE cloud_object_schema SET digest='changed'")
        with self.assertRaises(StoreConflict): self.objects.cleanup(self.a)

    def test_evidence_pagination_remains_tenant_bound(self):
        self.upload()
        first = self.objects.evidence(self.a, limit=2)
        second = self.objects.evidence(self.a, after=(first[-1]['created_at'], first[-1]['event_id']), limit=2)
        self.assertEqual(len(first+second), 3)
        self.assertEqual(len({e['event_id'] for e in first+second}), 3)
        self.assertEqual([e['action'] for e in self.objects.evidence(self.b)], ['quota'])
