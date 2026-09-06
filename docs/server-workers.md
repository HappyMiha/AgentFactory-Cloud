# Server and worker qualification (AF-CLD-024)

Work in progress. This task is not complete. The first implementation collects a
read-only inventory of an explicitly selected development node. It reuses the
merged Core hardware collector; it does not register a qualified worker yet.

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

The subsequent worker composition must retain Core as the sole scheduler and
lease authority: `SQLiteStorage.record_worker_qualification`, worker lifecycle,
`claim_runnable_task`, fenced attempts/renew/release, and `RuntimeBinding` already
exist. Cloud owns tenant admission and the host-profile envelope. It must not add
a second job table or copy Core fencing logic into PostgreSQL. Atomic qualification
and lifecycle checks at dispatch, capacity across tenants and exact trusted
tenant/run/task/worktree/attempt binding still need integration review before
remote dispatch is enabled. No public worker endpoint is installed by this step.

Inspection on Core `60e7895` confirmed that its low-level trusted claim method
can assign an unqualified quarantined synthetic worker. Identical worker-slot
conflict domains in two projects do not reserve a global slot: Core normalizes
those domains under each project. These are current primitive semantics, not a
remote admission contract. A local isolated SQLite fixture reproduced both
conditions without invoking any runtime. Do not implement a racy Cloud
select-then-claim check or a second lease authority to hide this missing seam.
The coordinator must review an upstream atomic admission boundary first.

Cloud's dependency is advanced from `29f67dc` to merged Core `60e7895` so the
inventory collector is available. This dependency change requires explicit
integration review and Cloud regression tests; merely importing the module is
not the regression evidence. The Cloud024 task and broader acceptance remain
open after this component is pushed or merged.
