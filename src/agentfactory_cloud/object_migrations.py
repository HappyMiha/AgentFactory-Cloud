"""Additive hosted-object schema; preserves the accepted Cloud product schema."""
import hashlib

from psycopg import sql

from .hosted_store import StoreConflict, identifier


VERSION = 1
TABLES = ('cloud_objects', 'cloud_object_refs', 'cloud_object_events', 'cloud_object_quotas')
SQL = """
CREATE TABLE cloud_object_quotas (
 tenant_id text PRIMARY KEY, bytes_limit bigint NOT NULL CHECK(bytes_limit>=0)
);
CREATE TABLE cloud_objects (
 tenant_id text NOT NULL, id uuid NOT NULL, actor text NOT NULL,
 command_id text NOT NULL, request_digest text NOT NULL, manifest jsonb NOT NULL,
 object_key text NOT NULL UNIQUE, size bigint NOT NULL CHECK(size>=0),
 state text NOT NULL CHECK(state IN ('pending','ready','deleting','deleted')),
 retain_until timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,actor,command_id)
);
CREATE TABLE cloud_object_refs (
 tenant_id text NOT NULL, object_id uuid NOT NULL, reference text NOT NULL,
 PRIMARY KEY(tenant_id,object_id,reference),
 FOREIGN KEY(tenant_id,object_id) REFERENCES cloud_objects(tenant_id,id)
);
CREATE TABLE cloud_object_events (
 tenant_id text NOT NULL, event_id uuid NOT NULL, actor text NOT NULL,
 object_id uuid, action text NOT NULL, evidence jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(), PRIMARY KEY(tenant_id,event_id)
);
CREATE TRIGGER cloud_object_events_immutable BEFORE UPDATE OR DELETE ON cloud_object_events
 FOR EACH ROW EXECUTE FUNCTION cloud_immutable();
CREATE FUNCTION cloud_object_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.tenant_id,NEW.id,NEW.actor,NEW.command_id,NEW.request_digest,NEW.manifest,
     NEW.object_key,NEW.size,NEW.retain_until,NEW.created_at) IS DISTINCT FROM
    (OLD.tenant_id,OLD.id,OLD.actor,OLD.command_id,OLD.request_digest,OLD.manifest,
     OLD.object_key,OLD.size,OLD.retain_until,OLD.created_at) THEN
  RAISE EXCEPTION 'Immutable object identity';
 END IF;
 IF NOT (NEW.state=OLD.state OR
     (OLD.state='pending' AND NEW.state IN ('ready','deleting')) OR
     (OLD.state='ready' AND NEW.state='deleting') OR
     (OLD.state='deleting' AND NEW.state='deleted')) THEN
  RAISE EXCEPTION 'Invalid object transition';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER cloud_object_identity BEFORE UPDATE ON cloud_objects
 FOR EACH ROW EXECUTE FUNCTION cloud_object_identity();
CREATE TRIGGER cloud_object_durable BEFORE DELETE ON cloud_objects
 FOR EACH ROW EXECUTE FUNCTION cloud_immutable();
"""
for table in TABLES:
    SQL += f"""
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_boundary ON {table}
 USING (tenant_id=current_setting('cloud.tenant_id',true))
 WITH CHECK (tenant_id=current_setting('cloud.tenant_id',true));
"""
DIGEST = hashlib.sha256(SQL.encode()).hexdigest()


def migrate(connection):
    """Call after hosted_store.migrate, using the separate migration identity."""
    with connection.transaction():
        connection.execute('SELECT pg_advisory_xact_lock(23023001)')
        connection.execute('CREATE TABLE IF NOT EXISTS cloud_object_schema (version integer PRIMARY KEY, digest text NOT NULL)')
        rows = connection.execute('SELECT version,digest FROM cloud_object_schema ORDER BY version').fetchall()
        if rows:
            if rows != [(VERSION, DIGEST)]:
                raise StoreConflict('Unknown or modified object schema')
            return
        connection.execute(SQL)
        connection.execute('INSERT INTO cloud_object_schema VALUES (%s,%s)', (VERSION, DIGEST))


def grant_runtime(connection, role):
    identifier(role)
    with connection.transaction():
        row = connection.execute('SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=%s', (role,)).fetchone()
        if not row or any(row):
            raise ValueError('Object runtime role must be unprivileged')
        connection.execute(sql.SQL('GRANT SELECT ON cloud_object_schema TO {}').format(sql.Identifier(role)))
        for table in TABLES:
            connection.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(sql.Identifier(table), sql.Identifier(role)))
        for table in ('cloud_objects', 'cloud_object_quotas'):
            connection.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(sql.Identifier(table), sql.Identifier(role)))
        connection.execute(sql.SQL('GRANT DELETE ON cloud_object_refs TO {}').format(sql.Identifier(role)))
