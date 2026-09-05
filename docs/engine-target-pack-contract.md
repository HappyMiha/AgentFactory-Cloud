# Engine, target and GamePack consumer contract proposal

AF-CLD-005 proposes version **1.0.0** for the Cloud consumer boundary. The
[contract](../contracts/v1/engine-target-pack.json) and
[fixtures](../contracts/v1/engine-target-pack-fixtures.json) are reference data.
They neither implement a game engine nor certify a target. The Godot-named example
is synthetic, as is the second dummy engine. No engine process is executed.

## Ownership and integration seam

Core owns shared EngineAdapter/TargetAdapter executable interfaces and optional
open-source game adapters, outside its neutral scheduler. Cloud selects a pinned
qualified version and applies tenant, rights, budget and product policy. Cloud
must not implement another scheduler or copy engine-specific execution branches.

At reviewed Core main `5f1487fca835615419c7977a40fa79f0301f6de7`,
`src/agent_factory/adapters.py` contains the provider health/execute adapter;
`src/agent_factory/packs.py` contains extension-pack lifecycle. Neither is claimed
to be the complete nine-operation game-engine interface proposed here. The
[upstream capability map](upstream-capability-map.md) remains authoritative about
missing integration evidence. Adoption requires a separately claimed Core change,
with the Core owner reviewing the interface before executable integration. This
Cloud proposal cannot close that implementation or its qualification task.

A future Core workflow supplies an operation and capability/profile identity to a
registered adapter. It does not compare engine names, language names or file
extensions to choose behavior. Engine-specific import/build/export logic belongs
inside the adapter/pack. The consumer fixture dispatcher demonstrates this rule
for two example engines and an arbitrary third identifier; it is **not proof of
an existing Core workflow's real-engine conformance**.

## Common request and typed results

Every request pins tenant/project/run/attempt, operation ID, operation, source
SHA-256, engine ID/version/digest, toolchain ID/version/digest, target ID/version
and GamePack ID/version/digest. Build ID and artifact SHA-256 are both absent
before a build exists and both required for run/crash collection. A run result
must name the exact requested artifact.
All fields in `request_binding` are required. Versions use exact three-part
numeric versions; floating aliases and ranges are not accepted. The engine digest
identifies the actual adapter distribution; the separate toolchain digest pins
its actual execution environment. Neither is a display name. A
GamePack digest covers its complete manifest and content, including language,
assets, task rules, dependency versions and rights references.

Requests carry explicit timeout seconds, maximum captured output bytes and budget
in minor units. Zero budget means no paid spend; time/output limits are positive.
The reference validates these fields structurally. Actual subprocess deadlines,
output retention and accounting must be enforced by Core's execution boundary.
A caller-supplied limit is not enforcement or authority.

| EngineAdapter operation | Successful payload | Meaning and limits |
| --- | --- | --- |
| `probe` | tools list, workspace-ready boolean | Actual selected tools/services and writable output area must be probed by the implementation. |
| `create` | source SHA-256 | Create a new source version from the selected pack in authorized workspace scope. |
| `import` | source SHA-256, provenance reference | Validate imported inputs and preserve origin; importing does not grant rights. |
| `validate` | report reference, zero errors | Static/engine checks only; this is not a playtest. |
| `test` | report reference, positive executed count, zero failures | Evidence records exact test kind and profile; zero tests is not success. |
| `build` | artifact SHA-256 and protected artifact reference | Build the exact requested source with the bound toolchain and target. |
| `run` | session reference, artifact SHA-256 | Start a bounded runtime session; spawning alone is not a passing playtest. |
| `collect_crash` | protected report reference, redacted boolean | Collect diagnostics with credential/private-data redaction before sharing. |
| `export_source` | archive SHA-256, protected archive and notices references | Export permitted source and provenance; this is separate from a playable package. |

The result envelope always repeats the exact request binding and contract version,
mode, status, typed payload, evidence reference, reason and next action. Status is
one of `succeeded`, `blocked`, `failed`, `cancelled`. Non-success has no successful
payload and requires a reason and a useful next action. Unsupported operations
return `blocked`, never a fabricated artifact or an empty successful result.
Simulation results remain simulation. `validate_result` checks structure and
meaning only; it does not verify a blob, execute an engine or authorize an action.

## TargetAdapter and compatibility matrix

TargetAdapter reports its exact profile version, supported operations, required
host/toolchain features and policy gates. It prepares/validates packaging through
the same typed operation envelope; it cannot silently replace the engine or pack.
Targets are distinct capabilities, not a generic 'export succeeded' flag.

| Target | Required additional capability/decision | Qualification in this proposal |
| --- | --- | --- |
| Web | Selected browser/runtime profile and actual hosting/export evidence | Synthetic fixture only |
| Windows | Exact OS/architecture/runtime profile and executable validation | Synthetic fixture only |
| Android | Android toolchain; device/runtime checks in actual qualification | Blocked for both example engines |
| iOS | Apple toolchain and signing authority; actual supported host required | Blocked for both examples |
| Store packaging | Store account and signing authority, separate store policy approval | Blocked for both examples |
| Partner console | Partner approval, licensed toolchain and signing authority | Blocked; never advertised as supported |

The two manifests expose Web and Windows only as **synthetic compatibility**.
Tests may fabricate other capabilities to exercise gate denial, but cannot make a
real target qualified. The reference `plan` blocks **every live request**, even
when a fixture claims `qualification=qualified` or caller-provided gates are set.
Production must replace this rehearsal with authenticated Core evidence and Cloud
action-time decisions, not remove the block and trust JSON fields.

GamePack manifests pin contract/pack/engine/target versions and content digest,
language, supported operations and protected rights reference. Language and game
rules stay in the pack. A pack for one engine version cannot silently run under a
different engine. No shell command, credentials or executable source is loaded
from these fixtures. A missing/unknown target or operation needs a clear blocked
state and a next action, not a fallback to another engine or commercial target.

## Permission, recovery and acceptance rules

The proposal maps source-reading operations to `workspace_read` and source/runtime
mutations to `workspace_write`. These are logical requirements, not new grants.
Core must enforce workspace isolation and separately authorize process/network
capabilities, artifact output locations and any runtime session. `test` and `run`
may execute untrusted game code: read access alone does not authorize execution.
Cloud verifies tenant ownership, rights for the specific use and spending before
submitting a request. Signing credentials remain in protected services. Neither
an adapter nor an export can grant publication, sale or owner acceptance.

Cancellation prevents dispatch; a cancelled request cannot report success. At
runtime, Core must terminate bounded work, collect permitted diagnostics and
persist the actual outcome. Retry increments attempt and uses a new operation ID;
a replay with the same ID is deduplicated against the immutable request digest.
A changed binding with a reused ID is a conflict. Persist results/outbox records
atomically and do not issue a public URL or bill twice after an uncertain timeout.
These are mandatory implementation handoff requirements, not behaviors already
implemented by the stateless fixture validator.

Evidence is tied to source, engine, target, pack and actual artifact. New source,
pack, toolchain or policy versions require affected checks again. Revocation,
expiry and changed rights are re-evaluated before each action. A green contract
test is not Ready, Playable, Exportable, Publishable or Sellable. Publication and
sale retain their separate domain and evidence-policy reviews and human gates.

Exact version matching is the initial compatibility rule. An incompatible shape,
operation meaning, authority requirement or qualification interpretation needs a
new reviewed contract version and new conformance evidence. Migrations preserve
old immutable records and do not reinterpret them as newly qualified results.

## Reproducible conformance and remaining work

Run `python scripts/validate_engine_target_pack.py` and
`python -m unittest discover -s tests -p test_engine_target_pack.py -v`.
The fixtures exercise nine typed operations against two engines (18 results).
Counterexamples cover unsupported operations/targets, partner gates, mismatched
identities, versions, permissions, cancellation, invalid result types, unsuccessful
checks, retry binding, explicit limits and simulation promotion. Adjacent domain
and upstream-map tests must also pass before this proposal is pushed.

Independent review accepts this proposal's engineering evidence only. Remaining
product gates include Core executable interface adoption, real installed-engine
and target qualification, sandbox/resource enforcement, authenticated evidence,
rights/spend services and an owner-accepted Cloud journey. Neither this document
nor a merged PR records those gates as complete.
