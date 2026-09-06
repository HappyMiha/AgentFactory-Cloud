# Server and worker qualification (AF-CLD-024)

Work in progress. This task is not complete. The first component collects a
read-only inventory of an explicitly selected development node. The next component
provides an optional authenticated loopback admission API using the merged Core
worker authority. Neither component qualifies remote execution.

The separately reported server has no verified target, access or inventory in
the current evidence. Do not infer that it is any development PC, scan possible
addresses or deploy to it. Its inventory, access roles, backup/recovery,
network/service boundaries and capacity decision remain unresolved acceptance
gates. HappyDucky02 coordinates the three owners' development-node lab tests.

Run `python scripts/qualify_workers.py inventory --workspace <local-workspace>
--output <new-private-file>` in a qualified Python environment. This performs
Core's fixed bounded OS/GPU observations plus local interface counting and Linux
virtualization signals. It does not contact remote nodes or invoke discovered
toolchains. The output uses exclusive creation and mode 0600 on POSIX. Keep it
outside Git and the bus, under the owner's local access controls. On Windows,
the parent folder must already have private ACLs. The destination is selected by
the trusted operator and is not accepted from remote input.

Both the CLI and direct `inventory(workspace)` entry point validate the workspace
before Core collection or any target-directory lookup. UNC/device and ambiguous
paths are rejected lexically. On Windows a known local drive type is required,
then each parent is checked without following reparse points; mapped remote
drives, junctions, symlinks and cloud placeholders are rejected. This uses the
documented [drive classification](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getdrivetypew)
and [reparse-point attributes](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-point-operations).
On Linux the bounded kernel mount table must classify every covering mount as a
supported local filesystem before any workspace lookup. CIFS/NFS, autofs, FUSE,
overlay and unknown types are rejected; each parent must then be a non-symlink
directory. Other operating systems and unavailable classification fail closed.
The operator must choose another supported local volume if classification fails.
This is a local operator check, not isolation against an administrator changing
mounts or path components concurrently during observation.

CPU/RAM/OS, the selected workspace volume, each separate GPU/VRAM observation and
detected software come from Core. Cloud adds a timestamped digest and explicit
gaps. Interface names, IP addresses, hostname, listening ports and raw kernel
contents are omitted. Unknown observations remain unknown, and measured zero
remains zero. No aggregate GPU pool or concurrency promise is derived from this
inventory. Linux virtualization flags, KVM presence and cgroup presence are
observations only; other platforms currently report those fields as unknown.

All inventory reports have `execution_eligible=false`, an empty list of qualified
capabilities, and a blocked capacity decision. Installed toolchains still need
actual version/capability tests. Network isolation, sandbox behavior, workload
capacity, worker admission and fault recovery require separate evidence. A report
digest binds bytes; it does not authenticate the machine or prove freshness.

The worker composition retains Core as the sole scheduler and
lease authority: `SQLiteStorage.record_worker_qualification`, worker lifecycle,
`claim_runnable_task`, fenced attempts/renew/release, and `RuntimeBinding` already
exist. Cloud owns authenticated access and the host-profile envelope. It must not
add a second job table or copy Core fencing logic into PostgreSQL. Core's accepted
AF-GC-043 now supplies atomic admission; the consumer is described below. Remote
dispatch remains disabled and no worker endpoint is installed by default.

Inspection on Core `60e7895` confirmed that its low-level trusted claim method
can assign an unqualified quarantined synthetic worker. Identical worker-slot
conflict domains in two projects do not reserve a global slot: Core normalizes
those domains under each project. These are current primitive semantics, not a
remote admission contract. A local isolated SQLite fixture reproduced both
conditions without invoking any runtime. This historical finding led to the
accepted Core AF-GC-043 boundary; it is not a claim about that newer implementation.

Cloud's dependency is advanced from `29f67dc` to merged Core `60e7895` so the
inventory collector is available. This dependency change requires explicit
integration review and Cloud regression tests; merely importing the module is
not the regression evidence. The Cloud024 task and broader acceptance remain
open after this component is pushed or merged.

The dependency upgrade was additionally checked with an actual database fixture:
under old Core `29f67dc`, create two synthetic English/Ukrainian briefs, edit each
twice and answer a clarification. Snapshot every Core and Cloud table and each
original source/current brief/historical version. Reopen the same files under
`60e7895` using `SQLiteStorage` and `BriefStore`. All six brief versions, two
clarification histories, original source identities/content and pre-existing
table rows were preserved. The only changed old table was the migration ledger,
which retained its old rows and added migrations 73 and 74. Four new Core tables
were created. No model/provider was invoked and no new storage authority added.

## Authenticated admission lab component

The current dependency is accepted Core
`765bea67f0164a71b24a8e5d042cd4d90c3e7101` (AF-GC-043). `WorkerGateway` delegates to
`WorkerAdmissionService.admit` and `SQLiteStorage.renew_task_lease` in the same Core
database used by the trusted host. Core owns qualification, worker/project/pool
versions, lifecycle, global capacity, durable attempts, leases and fencing. Cloud
has no new scheduler, lease table, qualification issuer or result store.

Provisioning is a trusted host operation, not a remote registration API:

1. The operator supplies the existing Core database and independently established
   tenant ownership, worker registration, bounded pool capacity and qualification
   evidence. Inventory alone does not supply any of those permissions.
2. Construct immutable Core `AdmissionRequest` objects for explicitly approved
   work. Preserve each request ID and every field across a host restart. A changed
   scope needs a new request ID; the same ID with changed fields conflicts in Core.
   Keep the allowlist bounded (at most 1024 requests) and private on the host.
3. Generate each worker's random secret with `secrets.token_urlsafe(32)`. Deliver
   it through the operator's authenticated private channel. Store only its SHA-256
   digest in a `WorkerCredential` together with the exact Core worker ID, tenant
   ID, worker-binding version and aware UTC issue/expiry times (at most one day).
   The gateway accepts at most 64 credentials; raw secrets never enter Git, the
   bus, URLs, receipts or the Core request/event record. Protect the host config
   and database with OS access controls. The fixture tokens in tests are public
   synthetic values and must never be reused.
4. Construct `WorkerGateway(database, credentials=(...), requests=(...))`. To run
   the explicit local lab, include `worker_gateway_router(gateway)` in a dedicated
   FastAPI application, bind Uvicorn to `127.0.0.1`, disable proxy-header handling
   and access logging, and apply bounded connection/time limits. This router is
   absent from the default creator application and has no automatic startup CLI.

The only HTTP operations are:

| Operation | JSON body | Result |
| --- | --- | --- |
| `POST /worker/admissions` | `request_id` | New or replayed Core admission receipt |
| `POST /worker/admissions/renew` | `request_id`, positive integer `fencing_token` | Renew the existing exact Core lease |

Both require one `Authorization: Bearer ...` header. Worker-supplied tenant, task,
provider, runtime, capability, TTL, worktree, result or stop fields are rejected.
Bodies are limited to 1024 bytes with no extra or duplicate fields. Authentication
precedes body reception and is checked again when applying the operation. Unknown
and other-worker request IDs receive the same denial. Only loopback peers and
loopback Host values are accepted; browser Origin and forwarding headers are
rejected. Failures use fixed redacted codes and `no-store` responses.

Credential revocation/rotation updates the Core worker binding using its expected
version, then provisions a new secret bound to the new version. Disabling and
re-enabling a binding does not revive an older credential or its admission.
Credential expiry stops gateway access but does not prove a process stopped or
release a Core slot. Plan rotation and stop reconciliation together; do not delete
an occupancy record to restore access.

A receipt includes tenant, worker, project, task, run, stage, attempt, assignment,
lease, fence and expiry identifiers. A ready Core worktree ID is included only
when its task, attempt, assignment, lease, fence and owner match; private paths are
omitted. Its presence is still not launcher qualification. Every response has
`execution_eligible=false` and `blocked_reason=remote_launcher_unqualified`.
`active` describes Core lease authority at observation time, not remote execution
permission. Expired/revoked replay can return an inactive historical receipt.

Core allows an existing admission to renew during its first draining transition,
while denying new admissions. Quarantine, stale qualification or authority
versions deny renewal. Expired leases and disconnected workers retain occupied
capacity. Only a trusted host's exact-fence `reconcile_stopped` call may free it
after independently proving the launcher/process stopped. There is deliberately
no worker HTTP stop, release, launch or result endpoint; a worker acknowledgement
is not that proof. A stale renewal cannot revive the reconciled admission.

The component tests use actual disposable SQLite databases and a real loopback
HTTP server, including transport restart, replay, cross-tenant slot competition,
revocation, drain/quarantine, lease loss and host reconciliation. Test worktree
rows and qualification records are synthetic; no remote host, engine, provider
or model is invoked. AF-CLD-024 still needs independently verified server access,
an authenticated encrypted remote transport, sandbox/toolchain qualification,
an exact-bound launcher/result path and actual process-loss/replacement drills.

The `60e7895` → `765bea6` dependency upgrade also reopened an actual old Core/Cloud
fixture with two briefs, six historical versions and two clarification histories.
Every existing row, original source and current/historical brief was preserved;
only the Core migration ledger gained migration 75 and four admission tables
were added. This supplements the earlier `29f67dc` → `60e7895` preservation check.
