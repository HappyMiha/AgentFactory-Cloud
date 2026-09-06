# Protected object delivery (AF-CLD-023)

Cloud stores source, build and asset bytes in a private S3-compatible bucket and
keeps tenant manifests, references, reservations and access evidence in PostgreSQL.
Core source/build IDs and content digests remain external immutable inputs. A
Cloud object ID identifies a storage envelope; it does not replace Core artifact
identity, validate provenance rights, approve a build or authorize execution.

This is an optional hosted component on top of AF-CLD-022. No public HTTP route or
existing local brief workflow is switched to hosted storage. Trusted application
composition must resolve current identity, tenant membership and the specific
write/read/export/delete permission before constructing `TenantContext`. It must
also validate ownership and rights of the supplied external origin and reference.
The context is not an authentication token. PostgreSQL RLS independently rejects
missing or foreign tenant filters; the application service and database
administrator remain trusted. Bucket credentials never go to creators, manifests,
download URLs, logs or the task register.

## Qualified component profile

Install `requirements-objects.txt` into the host environment. The existing SQLite
application has no new required dependency. Run `hosted_store.migrate` and grants
first, then `object_migrations.migrate` and its grants with a separate administrator.
The additive object schema has its own version/checksum and migration lock; it
does not rewrite the accepted version-1 product migration. Runtime identities may
not own these tables or bypass RLS. Unknown checksums block access.

Construct `S3Objects.connect` using a configured private bucket and protected
service credentials. HTTPS is required except for the isolated `127.0.0.1` test
profile. Construction rejects versioned buckets, non-owner ACL grants, any bucket
policy or external lifecycle configuration. The initial profile requires sole
adapter write/delete ownership of a nonversioned bucket. Administrators must not
change those settings or delete bytes independently while it is in use. MinIO's
owner-only compatibility ACL omits its canonical IDs; the actual profile also
tests anonymous access denial against the server.

`ProtectedObjects(HostedStore(...), blobs, ClamdScanner(port))` uses a separate
loopback ClamAV daemon. An absent/unreachable scanner, malformed reply, non-clear
verdict, mismatched digest or signature set older than seven days blocks upload.
The isolated daemon uses UTC; the receipt records engine and signature versions,
signature time and content digest. A clear malware result is one inspection
result, never a guarantee that executing generated code is safe. Code execution
still needs the separately owned sandbox capability.

The initial object limit is 1 byte through 8 MiB, read into bounded memory before
reservation. A future HTTP consumer must enforce the same ingress limit before
buffering; this component is not an unbounded network upload parser. Allowed media
labels are text/plain, application/json, application/zip, application/octet-stream,
image/png, image/jpeg, audio/ogg and audio/wav. Labels are metadata rather than
content-type certification; delivery must use attachment disposition and must not
serve active content under a trusted application origin.

ZIP inspection runs without extraction: at most 256 entries, 8 MiB per entry,
32 MiB total expansion, expansion ratio at most 100 and a five-second inspection
deadline. Paths reject traversal, absolute/drive paths, controls, portable reserved
names and ambiguous separators. Symlinks/devices, encrypted entries, duplicate
case-folded names, nested archives and unsupported compression are blocked. Other
archive formats and self-extracting ZIPs are unsupported. ClamAV then scans the
exact outer bytes. Larger game builds, multipart uploads, remote scanners, public
buckets, object versions and lifecycle-managed retention need a separately tested
profile; they are not silently accepted by this one.

## Durable operations

`configure_quota` belongs only to trusted entitlement/administrative composition.
Quota defaults to unavailable, includes pending/ready/deleting bytes, and is checked
under a same-tenant PostgreSQL advisory lock. Lowering a quota blocks additional
uploads without deleting existing objects. This profile serializes same-tenant
operations, including bounded S3 I/O; it makes no high-throughput claim.

`upload` requires a stable command ID, exact SHA-256, external origin kind/ID and
provenance reference, path/media label and a timezone-aware retention timestamp.
An immutable manifest and quota reservation commit before S3 I/O. Object keys
combine a tenant hash with a random storage-envelope ID, never an uploaded path.
Conditional create prevents overwriting an existing key. A complete read checks
size and SHA-256 before the row becomes ready. S3 requests have explicit connect
and read timeouts and no automatic SDK retry.

If the process or database connection fails after PUT, the manifest stays pending
and quota stays reserved. Retry with the same actor/command and identical inputs:
the existing key is checked and promoted once. Conflicting inputs are rejected.
Replaying a completed deletion returns its tombstone, never resurrects an object.
Unknown remote outcomes must be reconciled by retrying this command, not by
creating a new upload ID. `manifest` exposes status and metadata without a key or
download capability.

`download(..., export=True)` verifies current tenant availability and the actual
size/digest, then commits an export event before returning bytes. Normal downloads
also produce evidence. An integrity mismatch or failed evidence transaction
returns no successful delivery. Authentication revocation must be checked by the
host on each call; the component issues no long-lived presigned URLs.

Before a project/source/release becomes externally referenced, its trusted
consumer must call `reference(..., attach=True)` with an authorized stable
reference. Removing it requires the corresponding authorized domain operation.
All consumers must use this reference index; cleanup cannot infer links hidden
in arbitrary external JSON. References may attach only to ready objects.

`delete` first checks retained-until time and current references under the same
tenant lock, then commits a deleting tombstone. New references are blocked. It
deletes the S3 object and confirms absence before committing deleted state and
releasing quota. A lost delete response leaves deleting state; retry safely
confirms absence. Repeated deletion is idempotent. Cancellation of an abandoned
pending upload uses this same method; an unexpired retention period still blocks
physical erasure rather than bypassing policy.

`cleanup` processes at most 100 expired unreferenced managed manifests and rechecks
references at deletion time. It handles pending uploads and interrupted deletions.
It never lists and deletes arbitrary bucket keys: unknown/unmanaged objects need
operator reconciliation, and referenced objects remain available. No automatic
background cleanup process is launched by this component.

Append-only events retain actor, operation, object ID and digest evidence. The
`evidence` API is tenant-bound and paged with a timestamp/UUID cursor. Manifests and
events remain after byte deletion. Their metadata retention and privacy policy,
backup protection, key custody and production release need a separate reviewed
operational configuration before real user data is stored.

## Reproduce actual qualification

The Linux Docker helper starts only disposable labeled services, using synthetic
credentials in private files. S3, PostgreSQL and ClamAV publish on random loopback
ports with memory/CPU limits. Data uses disposable storage; no source directory,
Docker socket or production volume is mounted. The private audit collector binds
only the Linux Docker bridge gateway and requires a random webhook token. It
persists an allowlist of server time, request ID, API, synthetic bucket and status;
authorization headers, object keys and raw audit messages are discarded.

```bash
python scripts/qualify_objects.py start --work /absolute/private/test-directory
export CLOUD_OBJECTS_TEST_JSON=/absolute/private/test-directory/services.json
python -m unittest discover -s tests -p test_protected_objects.py -v
python -m unittest discover -s tests -p test_upload_inspection.py -v
python scripts/qualify_objects.py stop --work /absolute/private/test-directory
```

Wait for actual service readiness before testing. Keep failed startup state for
inspection and use the recorded stop command; do not start a duplicate. The helper
requires Linux Docker and `/proc` for safe audit-process cleanup. Windows reviewers
can supply the same private configuration format for explicitly isolated services;
the helper itself is not claimed as a Windows deployment tool. Test setup permits
only a nondefault loopback PostgreSQL port and loopback S3 endpoint.

Actual qualification uses MinIO RELEASE.2025-09-07T16-13-09Z (pinned container digest),
PostgreSQL 17.11, boto3 1.43.82, psycopg 3.3.5 and ClamAV 1.4.6. The observed
signature set was 28108, dated 2026-08-30 UTC. The pinned MinIO image is an isolated
compatibility fixture, not a recommendation or approval for production deployment.

Tests use separate synthetic tenants and real services for round trips, source/
build/asset envelopes, anonymous/cross-tenant denial, actual redacted S3 access
logs, quota/replay races, malicious archives and the harmless EICAR antivirus test
string. Fault cases include lost PUT/DELETE responses, actual PostgreSQL backend
termination after PUT, retained quota, idempotent recovery, corrupted stored bytes,
reference races and immutable SQL history. Source/build samples are synthetic
storage payloads; these tests do not certify a generated game or deployed Cloud.
Absent opt-in infrastructure causes explicit skips, not runtime qualification.
Exact-commit results and independent review belong in the task PR.

The adapter follows the official [S3 conditional PUT contract](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html),
[ClamD streaming protocol](https://docs.clamav.net/manual/Usage/ClamdProtocol.html)
and [MinIO audit webhook format](https://github.com/minio/minio/blob/master/docs/logging/README.md).
