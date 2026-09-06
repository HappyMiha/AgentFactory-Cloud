# Hosted storage boundary (AF-CLD-022)

Status: implemented component awaiting exact-commit peer review. The isolated PostgreSQL profile has actual runtime tests; hosted release acceptance is separate.

Cloud owns tenant/product records, product audit, request idempotency and a transactional delivery outbox. Core remains the single mission/execution authority. The accepted handoff is AutonomousMissionIntakeService with stable mission/source IDs. PostgreSQL must not copy Core mission tables, execute agent work, invent a second task register, or infer execution authority from a stored Cloud record.

## Proposed narrow interface

A trusted application composition resolves a current identity and tenant before using a tenant-bound repository. The storage adapter provides atomic record mutations with expected revisions, immutable source/build identities, append-only audit, request-key deduplication and an outbox event in the same transaction. Reads and writes require an explicit tenant context; database policy independently restricts rows. The runtime database role must not own tables or bypass row security. Migration/admin credentials are separate from runtime credentials.

The outbox is delivery bookkeeping for Cloud product events, not a scheduler or the team register. Delivery is at least once, with stable event IDs, bounded leases and acknowledgement by matching lease token. Consumers must deduplicate event IDs. A crash before commit publishes nothing; a crash after delivery before acknowledgement can redeliver the same event.

SourceVersion and Build records retain their accepted IDs, digests and references during migration and replay. Existing local briefs reference authoritative Core source/mission IDs; those references remain external and unchanged. No hosted brief API is mounted by this task. Existing SQLite local intake/identity behavior remains the local profile until an explicit consumer integration is reviewed.

## Migration and recovery evidence required

Use versioned, checksum-verified migrations under an exclusive migration lock. An incompatible schema blocks runtime access. Migrate representative synthetic Cloud-owned records from SQLite with explicit tenant bindings and unchanged source/build identity; reject conflicting identities instead of remapping them. Replaying a migration must be idempotent. Never migrate live sessions or credentials through generic JSON exports.

Qualification must use an actual isolated PostgreSQL cluster, a restricted runtime role, at least two synthetic tenants, immutable audit checks, revision races, retry/conflicting idempotency keys, rollback on transaction interruption and outbox lease recovery. Backup/restore must recover a fresh isolated database and compare canonical identities, audit and pending event invariants. An encrypted backup artifact and key-handling boundary must be verified before claiming the encrypted-backup profile.

Production deployment, database provisioning outside the isolated test environment, hosted authentication wiring and minor launch remain separate gates. A passing mocked adapter does not satisfy PostgreSQL migration or restore acceptance.

## Open prerequisite assessment

No replacement Core storage port is currently assumed: the adapter stores Cloud-owned product records and external Core references only. If implementing the accepted handoff requires mutating Core mission state through PostgreSQL, stop that expansion and propose an exact Core prerequisite for coordinated review. Cloud008 brief/scope source paths remain owned by its task.

## Implemented API and limits

Install `requirements-postgres.txt` into the host environment. PostgreSQL is optional; the existing SQLite app needs no new dependency. SQL migrations are packaged as Python data in `storage_migrations`, so wheels include their exact checksum. `migrate(admin_connection)` atomically applies version 1 under an advisory lock or rejects a mismatched version/checksum. `grant_runtime(admin_connection, role)` grants only the required table privileges. Provision an unprivileged non-owner LOGIN role independently; do not pass administrator credentials to `HostedStore`.

`HostedStore(connection_info)` opens bounded, transaction-local tenant contexts. `TenantContext(tenant_id, actor)` is created by trusted composition only after current identity and action permission checks. It is not a capability token or authentication API. A caller able to execute arbitrary SQL or set tenant context is trusted at the application boundary; row policies prevent omitted or mismatched SQL filters, not a compromised service account. The adapter rejects superuser, bypass, administrative and table-owner runtime roles. Database administrators retain maintenance authority.

`put(context, id, kind, identity, body, expected_revision=..., command_id=...)` requires a nonempty immutable identity map and a domain-validated JSON body. This is a storage envelope, not a second domain-transition evaluator. The caller supplies the authoritative immutable source/build references in `identity`; the storage layer never parses or approves a Core mission. Domain validation, ownership of linked records and action permissions remain required at the consumer seam before calling this API. No public HTTP API is exposed here.

Creation expects revision zero; updates require the exact current revision. The immutable identity map and record kind cannot change. Deletion is represented by a domain tombstone in `body`, not physical row removal. Stable request keys are scoped to tenant and actor; replay returns the original result even if the record has advanced. Keys and audit history currently have no expiry or purge operation. Retention/deletion policy integration must be reviewed before real user data is stored. JSON request data is bounded to 64 KiB and opaque identifiers to 128 ASCII characters. Current same-tenant writes serialize; performance qualification for large tenants is not claimed.

`lease(context, seconds=30)` reserves one undelivered product event for 1–300 seconds. `acknowledge(context, event_id, lease_token)` requires the current unexpired lease. An expired or wrong token returns a conflict. Event payloads contain stable record identity, revision and content digest, not a mutable copy of the record or any execution instruction. Consumers need an idempotent operation keyed by event ID and must retrieve the correct authorized record version if required; this adapter does not dispatch workers. A delivered event is retained with its acknowledgement time.

## SQLite snapshot handoff

`import_sqlite_snapshot(store, context, path)` reads a **Cloud-owned export** table `cloud_product_export(document TEXT)` from SQLite in read-only mode. Every document contains exactly `tenant_id`, `id`, `kind`, `revision`, `identity` and `body`. All rows must belong to the trusted context, with unique record IDs and positive revisions. The snapshot is bounded to 1,000 records and 64 KiB canonical aggregate data in this first profile. Larger imports must be explicitly partitioned into reviewed snapshots; atomicity is per snapshot.

The import preserves record IDs, revisions, original identity maps and bodies. Identical replay is a no-op; an existing conflicting record aborts the entire import. Each new record receives an audit and delivery event in the same transaction. This is not an importer for arbitrary Core SQLite schemas, identity credentials, sessions or local briefs without tenant mapping. A separate trusted export/mapping step must supply the agreed Cloud envelope; no heuristic remapping of mission/source IDs is allowed.

## Run actual qualification

Set `CLOUD_POSTGRES_ADMIN_JSON` to a private JSON file containing `host`, `port`, `user`, `password`; set `CLOUD_POSTGRES_BIN` to PostgreSQL's binary directory. The test harness permits only `127.0.0.1` on a nondefault port. The operator must supply an isolated disposable cluster, never a production database. `CLOUD_POSTGRES_TEST_WORK` optionally selects a test artifact directory. No credentials belong in the repository, test output, Bus or command-line arguments.

Run `python -m unittest discover -s tests -p test_hosted_store.py -v`. Each test creates unique `cloud022_test_...` databases and an unprivileged role, and cleans up only those recorded names. Without explicit configuration the suite skips actual PostgreSQL tests; a skip is not qualification. The verified profile is PostgreSQL 17.11 on Windows with psycopg 3.3.5. Tests use synthetic source/build references only.

Actual cases include cross-tenant raw SQL denial and unset context, privileged runtime rejection, immutable audit/identity guards, concurrent revision conflict, stable idempotent replay, server-side transaction failure, terminated client connection rollback, bounded outbox leases, stale/foreign acknowledgement denial, SQLite identity/revision preservation, whole-snapshot conflict rollback and migration checksum rejection.

The recovery test runs real `pg_dump` custom format with all tenant rows under the isolated administrator, encrypts the dump with Fernet authenticated encryption, verifies a wrong key rejects it, decrypts to `pg_restore` stdin for a fresh database and compares all record/request/audit/outbox/schema values. Runtime grants are applied separately and tenant isolation is checked again. The synthetic encryption key exists only for the test lifetime. This proves the tested backup/restore path, not production key custody, scheduling or retention; those require separately protected durable keys, access controls and a reviewed operational runbook.

For rollback, stop writes, retain the failed database for diagnosis, restore the last verified encrypted backup into a new database and verify identities/pending deliveries before switching the application configuration. Do not edit migration checksums, drop immutable history or auto-downgrade an incompatible schema. Outbox consumers must tolerate replay after recovery. No automatic production switch or destructive downgrade is implemented.

PostgreSQL policy behavior and backup assumptions follow the official [row security documentation](https://www.postgresql.org/docs/17/ddl-rowsecurity.html) and [pg_dump documentation](https://www.postgresql.org/docs/17/app-pgdump.html).
