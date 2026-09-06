"""Cloud product persistence, not a mission scheduler or authentication service."""
from contextlib import contextmanager, closing
from dataclasses import dataclass, field
import hashlib
import json
import re
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .storage_migrations import VERSION, SQL, TABLES


class StoreConflict(ValueError):
    pass


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', value):
        raise ValueError('Invalid storage identity')
    return value


def canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ValueError('Invalid JSON document') from None
    if len(raw) > 65536:
        raise ValueError('Document exceeds 64 KiB')
    return raw


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


SCHEMA_DIGEST = hashlib.sha256(SQL.encode()).hexdigest()


def migrate(connection):
    """Trusted migration connection only; all schema changes commit together."""
    with connection.transaction():
        connection.execute('SELECT pg_advisory_xact_lock(22022001)')
        connection.execute('CREATE TABLE IF NOT EXISTS cloud_schema (version integer PRIMARY KEY, digest text NOT NULL)')
        rows = connection.execute('SELECT version,digest FROM cloud_schema ORDER BY version').fetchall()
        if rows:
            if rows != [(VERSION, SCHEMA_DIGEST)]:
                raise StoreConflict('Unknown or modified Cloud schema migration')
            return
        connection.execute(SQL)
        connection.execute('INSERT INTO cloud_schema VALUES (%s,%s)', (VERSION, SCHEMA_DIGEST))


def grant_runtime(connection, role):
    """Grant only required table operations to a separately provisioned runtime role."""
    identifier(role)
    with connection.transaction():
        row = connection.execute('SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=%s', (role,)).fetchone()
        if not row or any(row):
            raise ValueError('Runtime role must be unprivileged')
        connection.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(role)))
        connection.execute(sql.SQL('GRANT SELECT ON cloud_schema TO {}').format(sql.Identifier(role)))
        for table in TABLES:
            connection.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(sql.Identifier(table), sql.Identifier(role)))
        for table in ('cloud_records', 'cloud_outbox'):
            connection.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(sql.Identifier(table), sql.Identifier(role)))


@dataclass(frozen=True)
class TenantContext:
    # A trusted host resolves current membership and action permission first.
    # Constructing this object is not an authentication/authorization decision.
    tenant_id: str
    actor: str

    def __post_init__(self):
        identifier(self.tenant_id)
        identifier(self.actor)


@dataclass
class HostedStore:
    connection_info: dict = field(repr=False)

    @contextmanager
    def transaction(self, context):
        if not isinstance(context, TenantContext):
            raise ValueError('Trusted tenant context required')
        with psycopg.connect(**self.connection_info, connect_timeout=5, row_factory=dict_row) as db:
            role = db.execute('SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=current_user').fetchone()
            owned = db.execute("SELECT 1 FROM pg_class WHERE relname=ANY(%s) AND pg_has_role(current_user,relowner,'USAGE')", (list(TABLES),)).fetchone()
            if any(role.values()) or owned:
                raise PermissionError('Use a non-owner, non-bypass runtime role')
            version = db.execute('SELECT version,digest FROM cloud_schema').fetchall()
            if version != [{'version': VERSION, 'digest': SCHEMA_DIGEST}]:
                raise StoreConflict('Storage schema not qualified for this adapter')
            db.execute("SELECT set_config('cloud.tenant_id',%s,true)", (context.tenant_id,))
            db.execute("SELECT set_config('statement_timeout','5000',true)")
            db.execute("SELECT set_config('lock_timeout','5000',true)")
            yield db

    @staticmethod
    def record(row):
        return {key: row[key] for key in ('tenant_id', 'id', 'kind', 'revision', 'identity', 'body')}

    def get(self, context, ident):
        identifier(ident)
        with self.transaction(context) as db:
            row = db.execute('SELECT * FROM cloud_records WHERE tenant_id=%s AND id=%s', (context.tenant_id, ident)).fetchone()
            if not row:
                raise KeyError('Record unavailable')
            return self.record(row)

    def put(self, context, ident, kind, identity, body, *, expected_revision, command_id):
        """Persist an already domain-validated document and immutable external identity."""
        for value in (ident, kind, command_id):
            identifier(value)
        if type(expected_revision) is not int or expected_revision < 0 or not isinstance(body, dict) or not isinstance(identity, dict) or not identity:
            raise ValueError('Explicit immutable identity, body and expected revision required')
        request = digest([ident, kind, identity, body, expected_revision])
        with self.transaction(context) as db:
            # Serialize same-tenant command replay and record revision changes.
            lock = int.from_bytes(hashlib.sha256(context.tenant_id.encode()).digest()[:8], 'big', signed=True)
            db.execute('SELECT pg_advisory_xact_lock(%s)', (lock,))
            old = db.execute('SELECT * FROM cloud_requests WHERE tenant_id=%s AND actor=%s AND command_id=%s', (context.tenant_id, context.actor, command_id)).fetchone()
            if old:
                if old['request_digest'] != request:
                    raise StoreConflict('Idempotency key belongs to a different command')
                return old['result']
            row = db.execute('SELECT * FROM cloud_records WHERE tenant_id=%s AND id=%s FOR UPDATE', (context.tenant_id, ident)).fetchone()
            if (row['revision'] if row else 0) != expected_revision:
                raise StoreConflict('Record revision changed')
            if row and (row['identity'] != identity or row['kind'] != kind):
                raise StoreConflict('Immutable source/build identity changed; use a new record')
            result = {'tenant_id': context.tenant_id, 'id': ident, 'kind': kind,
                      'revision': expected_revision+1, 'identity': identity, 'body': body}
            if row:
                db.execute('UPDATE cloud_records SET revision=%s,body=%s WHERE tenant_id=%s AND id=%s', (result['revision'], Jsonb(body), context.tenant_id, ident))
            else:
                db.execute('INSERT INTO cloud_records VALUES(%s,%s,%s,%s,%s,%s)', (context.tenant_id, ident, kind, 1, Jsonb(identity), Jsonb(body)))
            event = uuid.uuid4()
            db.execute('INSERT INTO cloud_audit(tenant_id,event_id,actor,record_id,revision,content_digest) VALUES(%s,%s,%s,%s,%s,%s)', (context.tenant_id, event, context.actor, ident, result['revision'], digest(result)))
            payload = {'event_id': str(event), 'record_id': ident, 'revision': result['revision'], 'content_digest': digest(result)}
            db.execute('INSERT INTO cloud_outbox(tenant_id,event_id,payload) VALUES(%s,%s,%s)', (context.tenant_id, event, Jsonb(payload)))
            db.execute('INSERT INTO cloud_requests VALUES(%s,%s,%s,%s,%s)', (context.tenant_id, context.actor, command_id, request, Jsonb(result)))
            return result

    def lease(self, context, *, seconds=30):
        if type(seconds) is not int or not 1 <= seconds <= 300:
            raise ValueError('Lease must be between 1 and 300 seconds')
        with self.transaction(context) as db:
            row = db.execute('SELECT event_id FROM cloud_outbox WHERE tenant_id=%s AND delivered_at IS NULL AND (lease_until IS NULL OR lease_until<clock_timestamp()) ORDER BY created_at,event_id FOR UPDATE SKIP LOCKED LIMIT 1', (context.tenant_id,)).fetchone()
            if not row:
                return None
            token = uuid.uuid4()
            result = db.execute("UPDATE cloud_outbox SET lease_token=%s,lease_until=clock_timestamp()+(%s * interval '1 second'),attempts=attempts+1 WHERE tenant_id=%s AND event_id=%s RETURNING payload,lease_token,attempts", (token, seconds, context.tenant_id, row['event_id'])).fetchone()
            return {'event': result['payload'], 'lease_token': str(result['lease_token']), 'attempts': result['attempts']}

    def acknowledge(self, context, event_id, lease_token):
        try:
            event, token = uuid.UUID(event_id), uuid.UUID(lease_token)
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Invalid outbox acknowledgement') from None
        with self.transaction(context) as db:
            row = db.execute('UPDATE cloud_outbox SET delivered_at=clock_timestamp() WHERE tenant_id=%s AND event_id=%s AND lease_token=%s AND lease_until>clock_timestamp() AND delivered_at IS NULL RETURNING event_id', (context.tenant_id, event, token)).fetchone()
            if not row:
                raise StoreConflict('Expired, foreign or superseded delivery lease')


def import_sqlite_snapshot(store, context, path):
    """Import a reviewed Cloud product snapshot, never a Core mission database.

    Input table: cloud_product_export(document TEXT). Only one trusted tenant,
    at most 1000 canonical record envelopes. Identities/revisions are preserved.
    """
    import sqlite3
    from pathlib import Path
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as source:
        raw = source.execute('SELECT document FROM cloud_product_export LIMIT 1001').fetchall()
    if len(raw) > 1000:
        raise ValueError('Snapshot exceeds 1000 records')
    records = []
    seen = set()
    for (document,) in raw:
        if not isinstance(document, str) or len(document) > 65536:
            raise ValueError('Invalid snapshot record')
        record = json.loads(document)
        if not isinstance(record, dict) or set(record) != {'tenant_id','id','kind','revision','identity','body'}:
            raise ValueError('Invalid snapshot envelope')
        if record['tenant_id'] != context.tenant_id or record['id'] in seen:
            raise ValueError('Foreign tenant or duplicate snapshot identity')
        for key in ('tenant_id','id','kind'):
            identifier(record[key])
        if type(record['revision']) is not int or record['revision'] < 1 or not isinstance(record['identity'],dict) or not record['identity'] or not isinstance(record['body'],dict):
            raise ValueError('Invalid snapshot version or identity')
        canonical(record)
        seen.add(record['id']);records.append(record)
    snapshot_digest = digest(sorted(records, key=lambda item: item['id']))
    with store.transaction(context) as db:
        db.execute('SELECT pg_advisory_xact_lock(%s)', (int.from_bytes(hashlib.sha256(context.tenant_id.encode()).digest()[:8],'big',signed=True),))
        for record in records:
            old = db.execute('SELECT * FROM cloud_records WHERE tenant_id=%s AND id=%s', (context.tenant_id,record['id'])).fetchone()
            if old:
                if store.record(old) != record:
                    raise StoreConflict('Snapshot conflicts with an existing identity/version')
                continue
            db.execute('INSERT INTO cloud_records VALUES(%s,%s,%s,%s,%s,%s)', (record['tenant_id'],record['id'],record['kind'],record['revision'],Jsonb(record['identity']),Jsonb(record['body'])))
            event = uuid.uuid4()
            db.execute('INSERT INTO cloud_audit(tenant_id,event_id,actor,record_id,revision,content_digest) VALUES(%s,%s,%s,%s,%s,%s)', (context.tenant_id,event,context.actor,record['id'],record['revision'],digest(record)))
            db.execute('INSERT INTO cloud_outbox(tenant_id,event_id,payload) VALUES(%s,%s,%s)', (context.tenant_id,event,Jsonb({'event_id':str(event),'record_id':record['id'],'revision':record['revision'],'content_digest':digest(record),'migration_snapshot_digest':snapshot_digest})))
    return {'records':len(records),'snapshot_digest':snapshot_digest}
