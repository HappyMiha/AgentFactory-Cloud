# Core and Cloud responsibility contract

Task: **AF-CLD-001**. Status: **Proposed for integration and owner review**.

This document refines the existing product direction into one responsibility map.
It is a design contract, not evidence of implemented Cloud software, deployed
services, accepted games, or approved license terms. AF-CLD-002 owns concrete data
schemas and APIs; AF-CLD-003 owns the versioned upstream capability assessment.

## Vocabulary and repository boundary

| Term | Meaning | Repository / decision owner |
| --- | --- | --- |
| Core | Provider-neutral orchestration, execution, evidence and artifact contracts | AgentFactory |
| Pack | Optional roles, workflows, engine adapters or build targets using Core contracts | AgentFactory, outside the neutral scheduler |
| Cloud | Hosted creator product and its product access policies | AgentFactory-Cloud |
| Games | Brief, game settings, play feedback and release experience | Cloud logical module |
| Community | Public discovery, sharing, moderation and social presentation | Cloud logical module |
| Marketplace | Listings, purchases, buyer entitlements and seller payouts | Cloud logical module |
| Project | Product workspace linking a creator's source versions and outputs | Cloud product identity; mapped to Core execution references |
| Source version | Immutable input snapshot and its provenance | Core snapshot contract; Cloud project access policy |
| Run | Execution of a versioned plan against explicit inputs | Core |
| Artifact | Identified output with content digest, provenance and evidence | Core generic contract; Cloud access/publication policy |
| Build | Artifact produced for an engine and target profile | Core optional target pack; Cloud release selection |
| Release | Product-approved selection of source/build/evidence versions | Cloud Games |
| Listing | A versioned offer or public presentation, distinct from a build | Cloud Community or Marketplace as specified below |
| Remix | New Cloud project derived from a permitted source version | Cloud permission decision using Core fork/checkpoint primitives |

There are exactly two repositories: AgentFactory and AgentFactory-Cloud. Games,
Community and Marketplace are modules, not additional repositories. Core retains
its existing Apache-2.0 license. This contract does not select a Cloud license or
assign rights in third-party or generated content.

Core must work without a Cloud account, billing service or game engine. A non-game
consumer can use providers, scheduling, evidence and artifacts without loading a
game pack. Engine-specific logic belongs in optional packs, not scheduler branches.
Cloud consumes those packs; it must not introduce a second engine adapter.

## One owner for each decision

The owner column identifies the sole implementation owner of the stated decision.
A consumer supplies inputs and policy constraints without duplicating that owner.

| Decision or capability | Sole owner | Consumer / handoff |
| --- | --- | --- |
| Task dependency execution, retries, pause and stop primitives | Core neutral runtime | Cloud submits bounded work and presents resulting evidence |
| Provider invocation, requested/effective model evidence | Core provider contract | Cloud supplies an authorized connection reference and product limits |
| Engine detection, build invocation and target validation | Core optional engine/target packs | Games selects a qualified pack and target version |
| Generic snapshots, content identity, provenance and fork execution | Core artifact/checkpoint contract | Cloud maps versions to tenant/project access |
| Generic evidence and verification result representation | Core evidence contract | Games evaluates product release gates |
| Brief editing, scope approval and feedback interpretation UX | Cloud Games | Approved inputs are passed to Core |
| Hosted identity, tenant access, session and secret provisioning | Cloud platform | Core receives scoped execution capabilities, not product passwords |
| Hosted worker provisioning, isolation and service quotas | Cloud platform | Core dispatches through generic worker contracts |
| Creator budget authorization and quota entitlement | Cloud platform | Core enforces supplied run limits and reports usage |
| Game release approval and selection of playable/downloadable builds | Cloud Games | Uses pinned Core artifacts and evidence |
| Public sharing and content moderation decisions | Cloud Community | Games supplies a candidate release; Marketplace consumes moderation status |
| Sale terms, listing price, buyer entitlement and payout | Cloud Marketplace | References a permitted release and required moderation result |
| Rights assertions, publication permission and Remix eligibility | Cloud rights policy | Games, Community and Marketplace request the same decision |
| Actual fork of authorized inputs | Core checkpoint/fork contract | Cloud first authorizes exact source version and requested use |
| Portable export assembly for a creator | Cloud Games | Uses Core source/build/provenance artifacts and rights policy result |

Rights policy is one Cloud platform capability, not a separate implementation per
module. A public paid listing therefore needs three distinct decisions: Games
selects a release, Community permits public presentation, Marketplace permits the
offer under the shared rights result. None substitutes for another's approval.

Core may enforce generic access or human gates for its own local users. Cloud must
also authorize hosted actions at its boundary; Core acceptance does not imply a
Cloud user is entitled to publish, spend, Remix or sell.

## Unreal and gameplay AI responsibilities

The [Unreal use-case plan](unreal-gameplay-plan.md) keeps three responsibilities separate:

| Part | Owner | Boundary |
| --- | --- | --- |
| AI development team | Core | Task ownership, model routing, budget enforcement, recovery and evidence |
| Unreal editor adapter | Optional Core engine pack | Reuse a qualified MCP backend; one owner mutates an editor session; produce source and build receipts |
| Gameplay AI contract | Optional Core runtime contract, used by a game pack | Typed observations/actions, identity, session/save epochs, memory and bounded asynchronous inference |
| Game-specific NPCs and world rules | Game pack | Validate every proposed action against game state; preserve save/load and deterministic fallback |
| Creator acceptance and hosted gameplay service, if offered | Cloud | Qualified setup, player access, service budgets and the full build/play/change evidence |

Development permissions do not grant a player session access to coding tools or provider master keys. Closing AgentFactory must not break the declared game profile. Temporal may recover development and hosted jobs; it does not own per-frame NPC behavior or become a required server inside the first Windows package.

## Required rights and provenance records

These are required logical fields for the AF-CLD-002 schema design, not a claim of
an existing API. Each source, generated asset, build, listing and remix carries
its own versioned record; a project-level checkbox cannot replace these records.

| Field | Required meaning |
| --- | --- |
| `subject` | Kind, stable ID, immutable version and content digest where applicable |
| `owner` | Asserted rights holder(s), scope of the assertion, claimant and supporting evidence references; explicit `unknown` when unverified |
| `origin` | Imported/created/generated/derived classification, upstream subject versions, source references, contributor and relevant run/tool/provider/model references |
| `license` | Terms reference and version (SPDX identifier when applicable), allowed uses/restrictions, component obligations, evidence and verification status; `unknown` is a valid non-authorizing state |
| `attribution` | Required notices, credited parties, source links and how those notices must accompany each output |
| `rights_status` | Pending, verified-for-specified-use, disputed or denied, with the use, evidence, reviewer and decision timestamp |

`owner` records an assertion, not automatic title. The creator's account is a
custodian/access principal and is not automatically the owner of every component.
Provider-generated content records the relevant terms/evidence; generation alone
does not establish exclusivity, transferable ownership or permission to resell.
No token, credential, private prompt or personal identifier is required in an
exported provenance record. Protected evidence stays behind access control.

| Subject | Origin and ownership rule | License and attribution rule |
| --- | --- | --- |
| Source | Identify the source version, its authors/claims, imports and derivations | Preserve component terms and notices; project terms cannot override dependencies |
| Generated asset | Link generation run/tool/model and all input references; record claimant and rights uncertainty | Preserve applicable input/output terms; unresolved rights block affected publishing/sale/Remix uses |
| Build | Link exact source version, target pack/toolchain and included asset digests | Carry the combined obligations of included components; compiling does not erase attribution |
| Listing | Link exact release/build/source offering and the party authorized to offer it | State precisely what access/license the buyer or player gets; do not broaden underlying rights |
| Remix | Link immutable parent source version, permission evidence and new contributions | Carry parent obligations and credits; new contribution rights do not replace inherited terms |

An unknown record can be retained privately for review where permitted by policy.
Unknown or disputed rights never count as permission for the affected export,
publication, sale or remix. Evaluate each requested use separately. Revocation or
a dispute invalidates later eligibility decisions; it does not rewrite historical
provenance or claim that an already delivered license was legally undone.

A portable package includes source, supported builds, a provenance/component
manifest and required license/attribution files. Exported games must run with their
normal engine/target requirements without an AgentFactory runtime, login or store.
Cloud credentials, tenant identifiers and hosted-only services are not runtime
dependencies. An optional hosted integration must be disclosed separately and
cannot be represented as an independently portable game.

## Design walkthrough: coin-collecting Godot game

This is a synthetic responsibility review, not a claim that a game was built.

| Step | Input → output | Sole decision owner | Boundary check |
| --- | --- | --- | --- |
| 1 | Creator describes a cat collecting coins with three lives → approved brief v1 | Games | No runtime-specific parsing added to the scheduler |
| 2 | Brief + chosen Godot pack → bounded plan/run request | Games | Core pack supplies reusable engine behavior |
| 3 | Authorized source snapshot + plan → run, source v1 and evidence | Core | Cloud account policy stays outside provider adapters |
| 4 | Source v1 + qualified Web/Windows profiles → build artifacts and verification evidence | Core optional packs | No parallel Cloud Godot exporter |
| 5 | Build/evidence + playtest → approved release v1 or rejected candidate | Games | A passing build is not product acceptance |
| 6 | Release + rights records → allowed public sharing or denial | Community using shared rights policy | Neither a run nor a build grants publication permission |
| 7 | Release + export-use decision → source/builds/manifest/notices package | Games | Open in Godot or run supported build outside Cloud |
| 8 | Feedback → approved change plan → source/build v2 | Games for plan; Core for execution | Distinct decisions retain the same owners as steps 2–5 |
| 9 | Existing release references → selected v1 rollback | Games | Core artifacts remain immutable |
| 10 | Parent v1 + Remix permission → new project and source fork | Cloud rights policy for permission; Core for fork | Parent origin and notices survive; new work has separate claims |
| 11 | Permitted release + sale eligibility → priced listing | Marketplace | Sale cannot override Community or rights denials |

Concrete provenance trace: `source-v1` names the creator's source claim and any
imported coin asset; `build-web-v1` references that source and asset; `listing-v1`
references the release; `remix-source-v1` references the parent source plus the
permission evidence. Each of the five subject kinds has its own owner, origin,
license and attribution record. Missing coin-asset permission blocks the uses
requiring that permission even if the game builds successfully.

## Design walkthrough: non-game document workflow

A local user asks for a report from permitted input documents. The local consumer
supplies scope, source references, provider configuration and limits. Core runs
its generic plan, records effective model and review evidence, and returns a
report artifact with provenance. No game pack, Godot installation, Cloud account,
Marketplace listing or Cloud billing is needed. The consumer decides whether the
report satisfies its requirements and whether it may be distributed under the
input/output terms. Core provides execution evidence, not a publishing license.

If Cloud later hosts this workflow, Cloud owns account access, quotas and delivery;
Core owns the same execution contracts. AF-CLD-066 remains the separate optional
Cloud non-game product gate. This example does not claim that gate is complete.

## Overlap resolution and acceptance record

The walkthrough resolves adapter duplication to Core packs, fork mechanics to
Core, Remix permission to Cloud, artifact identity to Core, publication/commerce
to Cloud, and rights policy to one shared Cloud capability. No unresolved duplicate
implementation owner remains in this proposed map. A new overlap requires an
explicit change to this map and a versioned contract handoff before implementation.

AF-CLD-002 must translate the logical rights fields and references into concrete
schemas, validation and API errors. AF-CLD-003 must map each capability to a pinned
Core commit and its evidence; this map alone establishes no implementation status.
Provider, engine and third-party terms still require review for the selected use.
Owner approval of Cloud license terms remains separate from this design.

Author walkthrough: HappyHahahaker reviewed the game and non-game examples against
all three AF-CLD-001 criteria. Independent integration review and owner acceptance
remain pending in the task PR. Neither this document nor its tests mark the task
or product accepted; the shared register records completion only after review and
merge under the team workflow.
