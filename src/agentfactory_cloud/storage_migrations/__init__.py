"""Checksum-pinned Cloud product schema. No Core mission tables."""
VERSION = 1
SQL = r"""
CREATE TABLE cloud_records (
 tenant_id text NOT NULL, id text NOT NULL, kind text NOT NULL,
 revision bigint NOT NULL CHECK(revision>0), identity jsonb NOT NULL,
 body jsonb NOT NULL, PRIMARY KEY(tenant_id,id),
 CHECK(jsonb_typeof(identity)='object' AND jsonb_typeof(body)='object')
);
CREATE TABLE cloud_requests (
 tenant_id text NOT NULL, actor text NOT NULL, command_id text NOT NULL,
 request_digest text NOT NULL, result jsonb NOT NULL,
 PRIMARY KEY(tenant_id,actor,command_id)
);
CREATE TABLE cloud_audit (
 tenant_id text NOT NULL, event_id uuid NOT NULL, actor text NOT NULL,
 record_id text NOT NULL, revision bigint NOT NULL, content_digest text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(), PRIMARY KEY(tenant_id,event_id)
);
CREATE TABLE cloud_outbox (
 tenant_id text NOT NULL, event_id uuid NOT NULL, payload jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 delivered_at timestamptz, lease_token uuid, lease_until timestamptz,
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
 PRIMARY KEY(tenant_id,event_id),
 FOREIGN KEY(tenant_id,event_id) REFERENCES cloud_audit(tenant_id,event_id)
);
CREATE FUNCTION cloud_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Immutable Cloud history'; END $$;
CREATE TRIGGER cloud_audit_immutable BEFORE UPDATE OR DELETE ON cloud_audit
 FOR EACH ROW EXECUTE FUNCTION cloud_immutable();
CREATE TRIGGER cloud_request_immutable BEFORE UPDATE OR DELETE ON cloud_requests
 FOR EACH ROW EXECUTE FUNCTION cloud_immutable();
CREATE FUNCTION cloud_record_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.tenant_id,NEW.id,NEW.kind,NEW.identity) IS DISTINCT FROM
    (OLD.tenant_id,OLD.id,OLD.kind,OLD.identity) OR NEW.revision<>OLD.revision+1 THEN
  RAISE EXCEPTION 'Immutable identity or invalid revision';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER cloud_record_identity BEFORE UPDATE ON cloud_records
 FOR EACH ROW EXECUTE FUNCTION cloud_record_identity();
CREATE TRIGGER cloud_record_durable BEFORE DELETE ON cloud_records
 FOR EACH ROW EXECUTE FUNCTION cloud_immutable();
CREATE FUNCTION cloud_outbox_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.tenant_id,NEW.event_id,NEW.payload,NEW.created_at) IS DISTINCT FROM
    (OLD.tenant_id,OLD.event_id,OLD.payload,OLD.created_at) THEN
  RAISE EXCEPTION 'Immutable event identity';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER cloud_outbox_identity BEFORE UPDATE ON cloud_outbox
 FOR EACH ROW EXECUTE FUNCTION cloud_outbox_identity();
CREATE TRIGGER cloud_outbox_durable BEFORE DELETE ON cloud_outbox
 FOR EACH ROW EXECUTE FUNCTION cloud_immutable();
"""
TABLES = ('cloud_records', 'cloud_requests', 'cloud_audit', 'cloud_outbox')
for table in TABLES:
    SQL += f"""
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_boundary ON {table}
 USING (tenant_id=current_setting('cloud.tenant_id',true))
 WITH CHECK (tenant_id=current_setting('cloud.tenant_id',true));
"""
