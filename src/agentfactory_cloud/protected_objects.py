"""Tenant delivery of bytes bound to external Core identities; no execution authority."""
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import re
import uuid
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from psycopg.types.json import Jsonb

from .hosted_store import HostedStore, StoreConflict, canonical, digest, identifier
from .object_migrations import DIGEST, TABLES, VERSION
from .upload_inspection import MAX_BYTES, inspect_upload


class ObjectUnavailable(KeyError):
    pass


@dataclass
class S3Objects:
    client: object = field(repr=False)
    bucket: str

    def __post_init__(self):
        # Physical erasure is qualified only without hidden versions or external lifecycle rules.
        if self.client.get_bucket_versioning(Bucket=self.bucket).get('Status'):
            raise StoreConflict('Versioned buckets are outside the qualified deletion profile')
        acl = self.client.get_bucket_acl(Bucket=self.bucket)
        # MinIO's owner-only compatibility ACL omits both canonical IDs.
        if len(acl['Grants']) != 1 or any(g['Grantee'].get('Type') != 'CanonicalUser'
               or g['Grantee'].get('ID', '') != acl['Owner'].get('ID', '')
               or g.get('Permission') != 'FULL_CONTROL' for g in acl['Grants']):
            raise StoreConflict('Bucket must be private')
        for operation, missing in [('get_bucket_policy', 'NoSuchBucketPolicy'),
                                   ('get_bucket_lifecycle_configuration', 'NoSuchLifecycleConfiguration')]:
            try:
                getattr(self.client, operation)(Bucket=self.bucket)
            except ClientError as exc:
                if exc.response['Error']['Code'] != missing:
                    raise
            else:
                raise StoreConflict('Bucket policy/lifecycle must be absent in this isolated profile')

    @classmethod
    def connect(cls, *, endpoint, bucket, access_key, secret_key):
        target = urlsplit(endpoint)
        if (target.username or target.password or target.query or target.fragment
                or target.path not in ('', '/') or not target.hostname
                or (target.scheme != 'https' and not
                    (target.scheme == 'http' and target.hostname == '127.0.0.1'))):
            raise ValueError('S3 requires HTTPS or the isolated loopback test profile')
        client = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key, region_name='us-east-1',
                              config=Config(connect_timeout=3, read_timeout=5,
                                            retries={'total_max_attempts': 1},
                                            s3={'addressing_style': 'path'}))
        return cls(client, bucket)

    def read(self, key, size, sha256):
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        stream = response['Body']
        try:
            data = stream.read(size + 1)
        finally:
            stream.close()
        if len(data) != size or hashlib.sha256(data).hexdigest() != sha256:
            raise StoreConflict('Object integrity mismatch')
        return data

    def put(self, key, data, manifest):
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data,
                                   ContentType=manifest['media_type'], IfNoneMatch='*',
                                   Metadata={'sha256': manifest['sha256']})
        except ClientError as exc:
            if exc.response['ResponseMetadata']['HTTPStatusCode'] != 412:
                raise
        # Also verifies recovery after a successful PUT whose response was lost.
        self.read(key, len(data), manifest['sha256'])

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                return
            raise
        raise StoreConflict('Object deletion not yet confirmed')


@dataclass
class ProtectedObjects:
    store: HostedStore
    blobs: S3Objects
    scanner: object = field(default=None, repr=False)

    @contextmanager
    def transaction(self, context):
        with self.store.transaction(context) as db:
            version = db.execute('SELECT version,digest FROM cloud_object_schema').fetchall()
            owned = db.execute('SELECT 1 FROM pg_class WHERE relname=ANY(%s) AND pg_has_role(current_user,relowner,\'USAGE\')', (list(TABLES),)).fetchone()
            if owned or version != [{'version': VERSION, 'digest': DIGEST}]:
                raise StoreConflict('Unqualified object schema or runtime owner')
            lock = int.from_bytes(hashlib.sha256(('objects:' + context.tenant_id).encode()).digest()[:8], 'big', signed=True)
            db.execute('SELECT pg_advisory_xact_lock(%s)', (lock,))
            yield db

    @staticmethod
    def event(db, context, ident, action, evidence):
        canonical(evidence)
        db.execute('INSERT INTO cloud_object_events(tenant_id,event_id,actor,object_id,action,evidence) VALUES(%s,%s,%s,%s,%s,%s)',
                   (context.tenant_id, uuid.uuid4(), context.actor, ident, action, Jsonb(evidence)))

    @staticmethod
    def row(db, context, ident):
        try:
            ident = uuid.UUID(str(ident))
        except ValueError:
            raise ObjectUnavailable('Object unavailable') from None
        row = db.execute('SELECT * FROM cloud_objects WHERE tenant_id=%s AND id=%s', (context.tenant_id, ident)).fetchone()
        if not row:
            raise ObjectUnavailable('Object unavailable')
        return row

    @staticmethod
    def public(row):
        # Internal bucket/key and credentials are never part of a delivery capability.
        return {'id': str(row['id']), 'tenant_id': row['tenant_id'],
                'state': row['state'], 'manifest': row['manifest']}

    def configure_quota(self, context, bytes_limit):
        """Trusted entitlement/administrative composition only, never a creator API."""
        if type(bytes_limit) is not int or not 0 <= bytes_limit <= 1024**4:
            raise ValueError('Quota must be 0 bytes to 1 TiB')
        with self.transaction(context) as db:
            db.execute('INSERT INTO cloud_object_quotas VALUES(%s,%s) ON CONFLICT(tenant_id) DO UPDATE SET bytes_limit=excluded.bytes_limit',
                       (context.tenant_id, bytes_limit))
            self.event(db, context, None, 'quota', {'bytes_limit': bytes_limit})

    def upload(self, context, data, *, path, media_type, sha256, origin,
               retain_until, command_id):
        """Upload one bounded object. The caller has authenticated current write rights."""
        identifier(command_id)
        if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_BYTES:
            raise ValueError('Object size outside supported profile')
        if not isinstance(sha256, str) or not re.fullmatch('[0-9a-f]{64}', sha256) or hashlib.sha256(data).hexdigest() != sha256:
            raise ValueError('Content does not match its external digest')
        if not isinstance(origin, dict) or set(origin) != {'kind', 'id', 'provenance_ref'}:
            raise ValueError('Explicit external identity and provenance reference required')
        if origin['kind'] not in ('SourceVersion', 'Build', 'Asset'):
            raise ValueError('Unsupported external object kind')
        identifier(origin['id']); identifier(origin['provenance_ref'])
        if not isinstance(retain_until, datetime) or retain_until.tzinfo is None:
            raise ValueError('Timezone-aware retention timestamp required')
        retain_until = retain_until.astimezone(timezone.utc)
        manifest = {'path': path, 'media_type': media_type, 'sha256': sha256, 'size': len(data),
                    'origin': dict(origin), 'retain_until': retain_until.isoformat()}
        request = digest(manifest)
        # Every retry is inspected before sending bytes; a stale scanner blocks promotion.
        inspection = inspect_upload(data, path, media_type, self.scanner)
        with self.transaction(context) as db:
            old = db.execute('SELECT * FROM cloud_objects WHERE tenant_id=%s AND actor=%s AND command_id=%s',
                             (context.tenant_id, context.actor, command_id)).fetchone()
            if old:
                if old['request_digest'] != request:
                    raise StoreConflict('Upload command belongs to different content')
                if old['state'] != 'pending':
                    return self.public(old)
                ident = old['id']
            else:
                quota = db.execute('SELECT bytes_limit FROM cloud_object_quotas WHERE tenant_id=%s', (context.tenant_id,)).fetchone()
                used = db.execute("SELECT COALESCE(SUM(size),0) AS used FROM cloud_objects WHERE tenant_id=%s AND state<>'deleted'", (context.tenant_id,)).fetchone()['used']
                if not quota or used + len(data) > quota['bytes_limit']:
                    raise StoreConflict('Object quota unavailable or exhausted')
                ident = uuid.uuid4()
                key = 'objects/' + hashlib.sha256(context.tenant_id.encode()).hexdigest() + '/' + ident.hex
                db.execute("INSERT INTO cloud_objects(tenant_id,id,actor,command_id,request_digest,manifest,object_key,size,state,retain_until) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s)",
                           (context.tenant_id, ident, context.actor, command_id, request, Jsonb(manifest), key, len(data), retain_until))
                self.event(db, context, ident, 'upload_reserved', {'manifest': manifest, 'inspection': inspection})
        # Durable reservation survives process/database failure during remote I/O.
        with self.transaction(context) as db:
            row = self.row(db, context, ident)
            if row['state'] == 'pending':
                self.blobs.put(row['object_key'], data, manifest)
                db.execute("UPDATE cloud_objects SET state='ready' WHERE tenant_id=%s AND id=%s", (context.tenant_id, ident))
                self.event(db, context, ident, 'upload_ready', {'sha256': sha256, 'inspection': inspection})
            return self.public(self.row(db, context, ident))

    def manifest(self, context, ident):
        with self.transaction(context) as db:
            return self.public(self.row(db, context, ident))

    def download(self, context, ident, *, export=False):
        """Check current read/export permission before entering this trusted component."""
        if type(export) is not bool:
            raise ValueError('Literal export flag required')
        with self.transaction(context) as db:
            row = self.row(db, context, ident)
            if row['state'] != 'ready':
                raise ObjectUnavailable('Object unavailable')
            data = self.blobs.read(row['object_key'], row['size'], row['manifest']['sha256'])
            self.event(db, context, row['id'], 'export' if export else 'download', {'sha256': row['manifest']['sha256'], 'size': len(data)})
            return data  # Evidence commits before bytes reach the caller.

    def reference(self, context, ident, reference, *, attach=True):
        """Caller validates referenced project/artifact ownership and domain linkage."""
        identifier(reference)
        if type(attach) is not bool:
            raise ValueError('Literal reference operation required')
        with self.transaction(context) as db:
            row = self.row(db, context, ident)
            if row['state'] != 'ready':
                raise StoreConflict('Only available objects can be referenced')
            if attach:
                db.execute('INSERT INTO cloud_object_refs VALUES(%s,%s,%s) ON CONFLICT DO NOTHING', (context.tenant_id, row['id'], reference))
            else:
                db.execute('DELETE FROM cloud_object_refs WHERE tenant_id=%s AND object_id=%s AND reference=%s', (context.tenant_id, row['id'], reference))
            self.event(db, context, row['id'], 'reference_attached' if attach else 'reference_detached', {'reference': reference})

    def delete(self, context, ident):
        """Retriable deletion; retention and references are checked before the tombstone."""
        with self.transaction(context) as db:
            row = self.row(db, context, ident)
            if row['state'] == 'deleted':
                return self.public(row)
            if row['state'] != 'deleting':
                refs = db.execute('SELECT 1 FROM cloud_object_refs WHERE tenant_id=%s AND object_id=%s LIMIT 1', (context.tenant_id, row['id'])).fetchone()
                current = db.execute('SELECT clock_timestamp() AS now').fetchone()['now']
                if refs or row['retain_until'] > current:
                    raise StoreConflict('Object is referenced or retained')
                db.execute("UPDATE cloud_objects SET state='deleting' WHERE tenant_id=%s AND id=%s", (context.tenant_id, row['id']))
                self.event(db, context, row['id'], 'deletion_requested', {'sha256': row['manifest']['sha256']})
        # New references cannot attach to a committed deleting row.
        with self.transaction(context) as db:
            row = self.row(db, context, ident)
            if row['state'] == 'deleting':
                self.blobs.delete(row['object_key'])
                db.execute("UPDATE cloud_objects SET state='deleted' WHERE tenant_id=%s AND id=%s", (context.tenant_id, row['id']))
                self.event(db, context, row['id'], 'deletion_confirmed', {'sha256': row['manifest']['sha256']})
            return self.public(self.row(db, context, ident))

    def cleanup(self, context, *, limit=50):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('Cleanup batch must be 1 to 100')
        with self.transaction(context) as db:
            rows = db.execute("""SELECT id FROM cloud_objects o WHERE tenant_id=%s
                AND state<>'deleted' AND retain_until<=clock_timestamp()
                AND NOT EXISTS(SELECT 1 FROM cloud_object_refs r WHERE r.tenant_id=o.tenant_id AND r.object_id=o.id)
                ORDER BY created_at,id LIMIT %s""", (context.tenant_id, limit)).fetchall()
        results = []
        for row in rows:
            try:
                results.append(self.delete(context, row['id']))
            except StoreConflict:
                continue  # A reference attached after enumeration; deletion rechecks.
        return results

    def evidence(self, context, *, after=None, limit=100):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('Evidence batch must be 1 to 100')
        # Timestamp/UUID tuple cursor gives deterministic bounded access to retained history.
        cursor = (datetime.min.replace(tzinfo=timezone.utc), uuid.UUID(int=0))
        if after is not None:
            cursor = (datetime.fromisoformat(after[0]), uuid.UUID(after[1]))
        with self.transaction(context) as db:
            rows = db.execute('SELECT event_id,object_id,actor,action,evidence,created_at FROM cloud_object_events WHERE tenant_id=%s AND (created_at,event_id)>(%s,%s) ORDER BY created_at,event_id LIMIT %s',
                              (context.tenant_id, *cursor, limit)).fetchall()
            return [{**row, 'event_id': str(row['event_id']), 'object_id': str(row['object_id']) if row['object_id'] else None,
                     'created_at': row['created_at'].isoformat()} for row in rows]
