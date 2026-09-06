# Product backlog

Planning revision: **2026-09-06**. The **67 stable tasks and 7 epics** retain their product requirements. Proposed labels below describe the planning baseline; use the [live shared task register](https://github.com/HappyMiha/AgentFactory/blob/team-state/team-state.json) for current ownership and engineering completion. Release and deployment acceptance remain separate.

The [JSON backlog](../examples/agentfactory-cloud-backlog.json) is the source of truth for IDs, dependencies, roles, sizes, and acceptance criteria. This document is its readable view. The [product description](product-description.md) explains the goal; the [roadmap](roadmap.md) explains the order; [planning notes](planning-notes.md) record changes from the supplied package.

Core owns shared orchestration contracts and optional open-source game packs. Cloud owns the consumer product and accepts the integration. An AF-CLD task does not authorize a duplicate Core implementation. The existing [42 AF-GC requirements](https://github.com/HappyMiha/AgentFactory/blob/main/docs/core-cloud-backlog.md) stay upstream.

## How to use this backlog

Start with M0, then prove the Godot journey in M1. Compare stage readiness before priority: P0 blocks its stage; P1 is important; P2 is later work. All required release tasks must pass, whatever their priority. S is up to 2, M up to 5, and L up to 10 engineer-days as rough estimates. Split L work before implementation. These sizes are not delivery dates.

Every task needs evidence for its exact version, independent review, and owner acceptance. Missing or skipped evidence cannot count as success. Real gameplay needs an actual playtest. Relevant rights, account, secret, budget, stop, and recovery checks are part of completion. Documents and schema validation do not make planned software complete.

Internal dependencies below are AF-CLD IDs in this repository. The current loader does not enforce cross-repository or conditional release rules. Before starting a task or releasing a feature, a reviewer must check its pinned upstream capability evidence and applicable gates. Core component acceptance must not depend on Cloud product acceptance.

**First review batch:** 001 → 002 → 003 → 005 → 006 → 004. This is a practical review order; use the explicit dependencies to decide what can run in parallel.

## Release gates

| Stage | Required gate | Scope note |
| --- | --- | --- |
| M0 | AF-CLD-001, AF-CLD-002, AF-CLD-003, AF-CLD-004, AF-CLD-005, AF-CLD-006 | All six contract tasks. |
| M1 | AF-CLD-020 | Godot first-playable proof. |
| M2 | AF-CLD-034 | Private hosted alpha. |
| M3 | AF-CLD-044 | Public creator beta and Remix. |
| M4 | AF-CLD-051 | Marketplace. |
| M5 | AF-CLD-060 | Console 059 is optional; a narrower M5 scope needs a recorded revision. |
| M6 | AF-CLD-067 | Factory commerce 062 and non-game 066 are optional; enabled features add gates below. |

Any minor pilot also needs 004 and 021. Public Remix needs 040, 042, 043, and 044. A paid marketplace needs 051; expanded engine/store support needs 060; factory commerce needs 051 and 062; non-game support needs 066. Console support requires actual partner and target qualification under 059. An unavailable target stays unsupported.

M2 release follows M1; M3 follows M2; M4 follows M3. M5 and M6 can reuse earlier stable contracts without waiting for every optional product expansion. Earlier design work can proceed when its own dependencies allow.

## Task index

| ID | Task | Stage | Priority | Size | Role | Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| [AF-CLD-001](#af-cld-001) | Agree on the Core and Cloud product boundaries | M0 | P0 | S | product-architect | None |
| [AF-CLD-002](#af-cld-002) | Define the shared data model and API contracts | M0 | P0 | M | solution-architect | 001 |
| [AF-CLD-003](#af-cld-003) | Map Cloud work to the existing Core backlog | M0 | P0 | S | product-owner | 001 |
| [AF-CLD-004](#af-cld-004) | Design separate Creator and Operator views | M0 | P0 | M | frontend-engineer | 002, 003 |
| [AF-CLD-005](#af-cld-005) | Define engine, build target, and game pack interfaces | M0 | P0 | M | platform-engineer | 002 |
| [AF-CLD-006](#af-cld-006) | Define evidence levels and release gates | M0 | P0 | S | qa-architect | 002 |
| [AF-CLD-007](#af-cld-007) | Turn a plain-language idea into a Game Brief | M1 | P0 | M | product-engineer | 002, 004 |
| [AF-CLD-008](#af-cld-008) | Keep the first playable version small | M1 | P0 | M | game-producer | 007 |
| [AF-CLD-009](#af-cld-009) | Assemble a visible AI game team | M1 | P0 | M | agent-systems-engineer | 005, 008 |
| [AF-CLD-010](#af-cld-010) | Prepare a small Godot 2D starter pack | M1 | P0 | M | godot-engineer | 005, 008 |
| [AF-CLD-011](#af-cld-011) | Connect a real Godot engine adapter | M1 | P0 | L | godot-engineer | 005, 010 |
| [AF-CLD-012](#af-cld-012) | Keep source versions and working game checkpoints | M1 | P0 | M | backend-engineer | 002, 006 |
| [AF-CLD-013](#af-cld-013) | Connect live coding workers to game tasks | M1 | P0 | L | agent-runtime-engineer | 009, 011, 012 |
| [AF-CLD-014](#af-cld-014) | Check the rules of the generated game | M1 | P0 | M | qa-engineer | 010, 011 |
| [AF-CLD-015](#af-cld-015) | Build a Web version and add Play | M1 | P0 | M | fullstack-engineer | 011, 012, 014 |
| [AF-CLD-016](#af-cld-016) | Export a Windows game and the full source | M1 | P0 | M | release-engineer | 011, 012, 014 |
| [AF-CLD-017](#af-cld-017) | Turn play feedback into a change plan | M1 | P0 | M | product-engineer | 007, 015 |
| [AF-CLD-018](#af-cld-018) | Create version 2, restore version 1, and try a private remix | M1 | P0 | L | workflow-engineer | 013, 014, 017 |
| [AF-CLD-019](#af-cld-019) | Show progress and enforce budget and stop controls | M1 | P0 | M | platform-engineer | 009, 013 |
| [AF-CLD-020](#af-cld-020) | Accept three real reference games | M1 | P0 | L | qa-lead | 015, 016, 018, 019 |
| [AF-CLD-021](#af-cld-021) | Add account boundaries, roles, and the 12+ access gate | M2 | P0 | L | security-engineer | 002, 006 |
| [AF-CLD-022](#af-cld-022) | Use PostgreSQL for hosted state | M2 | P0 | L | database-engineer | 002, 021 |
| [AF-CLD-023](#af-cld-023) | Store source, builds, and assets as protected objects | M2 | P0 | M | backend-engineer | 021, 022 |
| [AF-CLD-024](#af-cld-024) | Qualify server resources and register remote workers | M2 | P0 | L | distributed-systems-engineer | 021, 022 |
| [AF-CLD-025](#af-cld-025) | Make hosted workflows survive restarts | M2 | P0 | L | workflow-engineer | 022, 024 |
| [AF-CLD-026](#af-cld-026) | Isolate agent and build jobs | M2 | P0 | L | security-platform-engineer | 024, 025 |
| [AF-CLD-027](#af-cld-027) | Guide creators through AI connections | M2 | P0 | M | integration-engineer | 004, 021 |
| [AF-CLD-028](#af-cld-028) | Keep Cloud credentials outside game work | M2 | P0 | L | security-engineer | 021, 027 |
| [AF-CLD-029](#af-cld-029) | Enforce Cloud quotas and track usage | M2 | P0 | M | billing-platform-engineer | 022, 025, 027 |
| [AF-CLD-030](#af-cld-030) | Provide the hosted Creator Portal | M2 | P0 | L | fullstack-engineer | 004, 021, 025, 029 |
| [AF-CLD-031](#af-cld-031) | Serve protected playable builds | M2 | P0 | M | cloud-engineer | 023, 026, 030 |
| [AF-CLD-032](#af-cld-032) | Export a portable ownership package | M2 | P0 | M | release-engineer | 023, 030 |
| [AF-CLD-033](#af-cld-033) | Add operations visibility and recovery drills | M2 | P0 | L | site-reliability-engineer | 022, 023, 025, 026 |
| [AF-CLD-034](#af-cld-034) | Accept the private Cloud alpha | M2 | P0 | L | release-manager | 020, 021, 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, 032, 033 |
| [AF-CLD-035](#af-cld-035) | Add releases and visibility controls | M3 | P1 | M | backend-engineer | 034 |
| [AF-CLD-036](#af-cld-036) | Add creator profiles and libraries | M3 | P1 | M | fullstack-engineer | 021, 035 |
| [AF-CLD-037](#af-cld-037) | Add game pages with browser Play | M3 | P1 | M | frontend-engineer | 031, 035 |
| [AF-CLD-038](#af-cld-038) | Add Discover, search and tags | M3 | P1 | M | search-engineer | 035, 037 |
| [AF-CLD-039](#af-cld-039) | Add share links and embed controls | M3 | P1 | S | fullstack-engineer | 035, 037 |
| [AF-CLD-040](#af-cld-040) | Add Remix and Fork with source history | M3 | P1 | L | backend-engineer | 032, 035, 036 |
| [AF-CLD-041](#af-cld-041) | Add likes, bookmarks and basic play statistics | M3 | P2 | M | analytics-engineer | 037, 038 |
| [AF-CLD-042](#af-cld-042) | Add age-aware moderation and reporting | M3 | P0 | L | trust-safety-engineer | 026, 035, 037 |
| [AF-CLD-043](#af-cld-043) | Check asset origin and licences before release | M3 | P0 | L | ip-compliance-engineer | 023, 035, 040 |
| [AF-CLD-044](#af-cld-044) | Approve a limited public creator beta | M3 | P1 | L | release-manager | 035, 036, 037, 038, 039, 040, 042, 043, 041 |
| [AF-CLD-045](#af-cld-045) | Add seller setup and adult or guardian approval | M4 | P0 | L | compliance-product-engineer | 036, 044 |
| [AF-CLD-046](#af-cld-046) | Add sale listings, prices and licence choices | M4 | P1 | M | commerce-engineer | 035, 043, 045 |
| [AF-CLD-047](#af-cld-047) | Add checkout through a payment provider | M4 | P0 | L | payments-engineer | 021, 046 |
| [AF-CLD-048](#af-cld-048) | Add purchase access and the buyer library | M4 | P0 | M | backend-engineer | 046, 047 |
| [AF-CLD-049](#af-cld-049) | Add the revenue ledger, fees and payouts | M4 | P0 | L | financial-systems-engineer | 045, 047, 048 |
| [AF-CLD-050](#af-cld-050) | Add refunds, disputes and fraud review | M4 | P0 | L | risk-engineer | 047, 048, 049 |
| [AF-CLD-051](#af-cld-051) | Approve the marketplace release | M4 | P1 | L | release-manager | 045, 046, 047, 048, 049, 050 |
| [AF-CLD-052](#af-cld-052) | Publish an EngineAdapter SDK and compatibility tests | M5 | P1 | L | sdk-engineer | 005, 034 |
| [AF-CLD-053](#af-cld-053) | Qualify the Unity adapter | M5 | P1 | L | unity-engineer | 052 |
| [AF-CLD-054](#af-cld-054) | Prove Unreal feasibility and qualify its adapter | M5 | P1 | L | unreal-engineer | 052 |
| [AF-CLD-055](#af-cld-055) | Add Android builds and Google Play preparation | M5 | P1 | L | mobile-release-engineer | 052, 043 |
| [AF-CLD-056](#af-cld-056) | Add Apple builds and App Store preparation | M5 | P1 | L | apple-platform-engineer | 052, 028, 043 |
| [AF-CLD-057](#af-cld-057) | Add Steam release preparation | M5 | P1 | L | store-integration-engineer | 032, 043, 046 |
| [AF-CLD-058](#af-cld-058) | Add a shared PC store packaging contract | M5 | P2 | M | store-integration-engineer | 052, 032 |
| [AF-CLD-059](#af-cld-059) | Plan optional console support behind partner approval (optional) | M5 | P2 | L | platform-partnership-engineer | 052, 028 |
| [AF-CLD-060](#af-cld-060) | Approve the multi-engine and multi-target release | M5 | P1 | L | release-manager | 052, 053, 054, 055, 056, 057, 058 |
| [AF-CLD-061](#af-cld-061) | Package reusable Agent Teams and Factory templates | M6 | P2 | L | agent-platform-engineer | 009, 052 |
| [AF-CLD-062](#af-cld-062) | Add an optional marketplace for Factories and packs (optional) | M6 | P2 | L | marketplace-engineer | 051, 061 |
| [AF-CLD-063](#af-cld-063) | Let creators choose qualified models and team budgets | M6 | P2 | M | agent-systems-engineer | 029, 061 |
| [AF-CLD-064](#af-cld-064) | Publish an API, SDK and signed webhooks | M6 | P2 | L | api-platform-engineer | 021, 025, 029, 061 |
| [AF-CLD-065](#af-cld-065) | Qualify self-hosted and hybrid deployment | M6 | P2 | L | deployment-engineer | 024, 025, 026, 033 |
| [AF-CLD-066](#af-cld-066) | Explore a later non-game executable pack (optional) | M6 | P2 | L | product-platform-engineer | 052, 061, 064 |
| [AF-CLD-067](#af-cld-067) | Approve the defined general-availability scope | M6 | P2 | L | release-manager | 034, 044, 061, 063, 064, 065 |

## M0: Agree the product contract and Core bridge

**Epic:** AF-CLD-E0. Define two-repository ownership, shared contracts, creator needs, and release evidence.

### AF-CLD-001

**Agree on the Core and Cloud product boundaries**

Define one shared product vocabulary, clear ownership, and the boundary between the reusable orchestration engine and the game creation service.

Priority: **P0** · Size: **S** · Role: **product-architect** · Status: **Proposed**

Depends on: None.

**Acceptance criteria**

- The design uses two repositories: AgentFactory for open-source Core, and AgentFactory-Cloud for the commercial product. Games, Community, and Marketplace are logical modules, not extra repositories.
- Core remains useful outside games. AgentFactory coordinates existing engines; exported games do not require an AgentFactory runtime or store.
- Source, generated assets, builds, listings, and remixes have explicit owner, origin, license, and attribution fields. Ownership claims stay within the rights actually available.

**How to check:** Review an end-to-end game example and a non-game example against the responsibility map; resolve every overlapping owner.

**Components:** Product glossary; responsibility map; source and asset rights model

**Test environment:** Planning documents only; no deployment required

**Expected output:** Reviewed boundary decision and ownership table

### AF-CLD-002

**Define the shared data model and API contracts**

Describe the records and state changes needed to take a game idea through creation, play, release, and later sales.

Priority: **P0** · Size: **M** · Role: **solution-architect** · Status: **Proposed**

Depends on: AF-CLD-001.

**Acceptance criteria**

- The model covers Tenant/User, Project, GameBrief, FactoryBlueprint, AgentTeam, Run, SourceVersion, Build, PlaySession, Feedback, Release, Listing, Purchase, and Entitlement.
- Missing or failed checks block positive readiness and release promotions. Failure, blocked, cancellation, and recovery transitions remain explicit. Playable builds require evidence for the exact source and artifact.
- API contracts are versioned and scoped to an account or team. Mutations define idempotency keys and ETag conflict handling.

**How to check:** Walk through success, stale update, retry, deletion, and cross-tenant examples; check that each has an unambiguous result.

**Components:** Entity diagram; state transition table; versioned request and response examples

**Test environment:** Contract fixtures without real accounts or credentials

**Expected output:** Domain model, API examples, error catalogue, and compatibility rules

### AF-CLD-003

**Map Cloud work to the existing Core backlog**

Reuse the AF-GC plan and Core foundations. Record what Cloud reuses, extends, migrates, or must build instead of creating a second implementation of the same capability.

Priority: **P0** · Size: **S** · Role: **product-owner** · Status: **Proposed**

Depends on: AF-CLD-001.

**Acceptance criteria**

- The map links AF-GC-026 to the Godot journey, AF-GC-031 to local/hybrid qualification, AF-GC-034 to Unity, and AF-GC-037 to export/share qualification.
- Each Cloud capability has one implementation owner, upstream version, reuse decision, and integration acceptance test. References are checked at the relevant milestone; Godot does not wait for Unity or every future AF-GC task.
- A proposed AF-GC task is never recorded as implemented without accepted evidence. The mapping document alone does not satisfy the upstream or Cloud release gate.

**How to check:** Review all 67 Cloud tasks against the 42 upstream AF-GC tasks; find duplicate ownership, missing evidence, and circular release prerequisites.

**Components:** Versioned capability map; upstream evidence references

**Test environment:** Read-only access to both repositories and their acceptance records

**Expected output:** Core-to-Cloud traceability table and unresolved integration list

### AF-CLD-004

**Design separate Creator and Operator views**

Make the creator journey easy to understand while keeping technical controls available to the people who operate the service.

Priority: **P0** · Size: **M** · Role: **frontend-engineer** · Status: **Proposed**

Depends on: AF-CLD-002, AF-CLD-003.

**Acceptance criteria**

- Creator navigation uses My Games, Create, Play, Change, and Publish. The main path does not require task IDs, JSON, worker leases, or provider internals.
- Operator views keep approvals, evidence, workers, audit, and diagnostics behind role-based access.
- Every creator state shows a plain-language status, one next action, and optional technical details. Draft input survives refresh and background updates.
- The design defines the 12+ age path, guardian involvement where required, private defaults, data minimization, deletion, and who may authorize spending. Provider age and account rules are checked before a minor pilot.

**How to check:** Review clickable or paper flows for first use, failure, resume, and cancellation with adult testers; plan supervised 12+ usability testing only after the account and consent gate.

**Components:** Creator and Operator navigation; error copy; age and guardian policy decision

**Test environment:** Design prototype with synthetic data; no child data collection

**Expected output:** Reviewed screen flows, accessibility checklist, and minor-pilot entry requirements

### AF-CLD-005

**Define engine, build target, and game pack interfaces**

Keep engine choice, game rules, language, and export targets outside the universal orchestration logic.

Priority: **P0** · Size: **M** · Role: **platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-002.

**Acceptance criteria**

- EngineAdapter defines probe, create, import, validate, test, build, run, collect_crash, and export_source operations with typed results.
- TargetAdapter separates Web, Windows, Android, iOS, store packaging, and partner-gated console targets.
- Conformance fixtures prove the Core workflow does not branch on Godot, Unity, or Unreal. Shared interfaces and optional open-source game adapters live in Core outside the neutral scheduler; Cloud integrates their qualified versions.

**How to check:** Review one Godot example and a second dummy engine against the same contract; verify unsupported operations return an explicit blocked result.

**Components:** EngineAdapter; TargetAdapter; GamePack manifest; capability matrix

**Test environment:** Contract fixtures; actual engine qualification is a later task

**Expected output:** Versioned interface proposal, sample manifests, and compatibility rules

### AF-CLD-006

**Define evidence levels and release gates**

Separate a simulation, a passing code check, a successful engine build, a real playtest, and human acceptance.

Priority: **P0** · Size: **S** · Role: **qa-architect** · Status: **Proposed**

Depends on: AF-CLD-002.

**Acceptance criteria**

- Every build records its source digest, engine and toolchain identity, validator results, and runtime evidence.
- Ready, Playable, Exportable, Publishable, and Sellable have separate, testable requirements tied to an exact version.
- The UI never calls a game ready after only simulation or API checks. Missing, skipped, stale, or unrelated evidence cannot satisfy a gate.

**How to check:** Evaluate sample records for a good build, a failed build, a stale source digest, and a skipped playtest; confirm only the correct states are allowed.

**Components:** Evidence schema; gate rules; reviewer and owner acceptance records

**Test environment:** Synthetic evidence fixtures

**Expected output:** Gate matrix, evidence examples, and release review template


## M1: Prove the Godot game loop

**Epic:** AF-CLD-E1. Build, play, export, change, restore, and privately remix small Godot games with real evidence.

### AF-CLD-007

**Turn a plain-language idea into a Game Brief**

Keep the creator's original idea and help them turn it into a short, editable game plan.

Priority: **P0** · Size: **M** · Role: **product-engineer** · Status: **Proposed**

Depends on: AF-CLD-002, AF-CLD-004.

**Acceptance criteria**

- The brief covers genre, core loop, controls, win/lose rules, visual style, target platform, first playable version, and deferred scope.
- The original Ukrainian or English input is kept unchanged as the source requirement. Generated assumptions are clearly separate.
- Unclear requests produce at most a few focused questions, with simple suggested answers, instead of a technical form.

**How to check:** Use Ukrainian and English plain paragraphs, vague requests, and conflicting edits; compare the stored original and resulting brief.

**Components:** Mission intake bridge; GameBrief editor; clarification flow

**Test environment:** Synthetic idea set; one qualified model route for live evaluation

**Expected output:** Versioned brief, assumptions, clarification history, and intake evaluation report

### AF-CLD-008

**Keep the first playable version small**

Turn an ambitious idea into a small, testable game without losing the creator's longer-term plans.

Priority: **P0** · Size: **M** · Role: **game-producer** · Status: **Proposed**

Depends on: AF-CLD-007.

**Acceptance criteria**

- Multiplayer, open-world, or AAA requests receive a small vertical slice and a separate future roadmap; the system does not promise any complexity in one run.
- The creator can edit assumptions, exclusions, and scope, and sees an estimated AI budget before agreeing to the plan.
- The plan contains actionable leaf tasks and game-specific acceptance criteria. Unsupported engines or features produce a clear limitation and an alternative.

**How to check:** Evaluate small, oversized, and impossible sample requests; confirm each first milestone has a playable goal, budget estimate, and explicit exclusions.

**Components:** Scope planner; capability catalogue; cost estimate

**Test environment:** Reference briefs and estimated usage fixtures

**Expected output:** First-playable plan, deferred roadmap, and scope evaluation results

### AF-CLD-009

**Assemble a visible AI game team**

Give each game a Game Director, Designer, Developer, QA/Playtester, and Build Engineer with clear responsibilities.

Priority: **P0** · Size: **M** · Role: **agent-systems-engineer** · Status: **Proposed**

Depends on: AF-CLD-005, AF-CLD-008.

**Acceptance criteria**

- Role contracts are provider-neutral, versioned, and compatible with existing routing and approval rules.
- The producing model cannot accept its own work. The reviewer has a verified independent effective identity, even after fallback or retry.
- The creator can see the roles, current work, and budget allocation, and can stop the team. Available providers are selected by tested capability, not a brand name alone.

**How to check:** Exercise missing reviewer, shared model aliases, fallback, and budget exhaustion; verify no route silently bypasses review separation.

**Components:** Game Studio role pack; Workforce Composer bridge; route qualification

**Test environment:** At least one qualified coding route and one independent review route

**Expected output:** Versioned team plan, effective identity report, and role-level budget view

### AF-CLD-010

**Prepare a small Godot 2D starter pack**

Provide a repeatable starting point for small 2D games using Godot and GDScript.

Priority: **P0** · Size: **M** · Role: **godot-engineer** · Status: **Proposed**

Depends on: AF-CLD-005, AF-CLD-008.

**Acceptance criteria**

- The pack includes a project skeleton, input map, scene rules, tests, export presets, and coding guidance.
- Workers can change the reference templates. Replaying an unchanged template does not count as generating the requested game.
- The engine version, export templates, dependency versions, licenses, and attribution are recorded. Only assets with suitable rights are included.

**How to check:** Import the pack on a clean environment, run its checks, export it, and verify one requested behavior change in a generated version.

**Components:** Godot 2D GamePack; GDScript conventions; export presets

**Test environment:** Pinned Godot and matching export templates in an isolated workspace

**Expected output:** Versioned starter pack, license inventory, and reproducible setup record

### AF-CLD-011

**Connect a real Godot engine adapter**

Run actual engine checks, imports, tests, Web and Windows builds, and the game process lifecycle.

Priority: **P0** · Size: **L** · Role: **godot-engineer** · Status: **Proposed**

Depends on: AF-CLD-005, AF-CLD-010.

**Acceptance criteria**

- The adapter distinguishes a missing engine, incompatible project, parse error, test failure, export failure, and runtime crash.
- Commands use allowlisted executable and argument vectors instead of arbitrary shell text. Logs have size limits and identify the run and build.
- Healthy and deliberately broken fixtures pass the qualification matrix. Setup probes verify the installed engine and templates before reporting readiness.

**How to check:** Run good and broken projects through every operation, then cancel a long build and verify that child processes stop and evidence remains.

**Components:** Godot EngineAdapter; process runner; engine probe; error mapping

**Test environment:** Pinned Godot toolchain; disposable workspaces; qualified OS sandbox

**Expected output:** Adapter qualification report, bounded logs, build manifests, and failure fixtures

### AF-CLD-012

**Keep source versions and working game checkpoints**

Make each change in an isolated worktree and preserve the last working game when a later attempt fails.

Priority: **P0** · Size: **M** · Role: **backend-engineer** · Status: **Proposed**

Depends on: AF-CLD-002, AF-CLD-006.

**Acceptance criteria**

- SourceVersion, accepted commit, and Build have immutable identities and a recorded relationship.
- Updating the latest-working pointer is atomic and safe to repeat. A failed build cannot move it.
- Restore creates a new version and audit record without rewriting history or overwriting active work.

**How to check:** Interrupt commits and promotions, submit a stale worker result, and restore an older build; confirm exact source/build identity and unchanged history.

**Components:** Core worktree authority; source/build records; promotion and restore service

**Test environment:** Isolated Git repository and artifact store with fault fixtures

**Expected output:** Version history, digest-linked checkpoints, and restart/restore evidence

### AF-CLD-013

**Connect live coding workers to game tasks**

Use a qualified Codex, Claude, Hermes, or other worker to make real changes inside the leased game worktree and return structured evidence.

Priority: **P0** · Size: **L** · Role: **agent-runtime-engineer** · Status: **Proposed**

Depends on: AF-CLD-009, AF-CLD-011, AF-CLD-012.

**Acceptance criteria**

- The worker receives an immutable task context with only the needed game data, not the full tenant data set.
- Changed files, diffs, commands, usage, effective model, and terminal reason are recorded without secrets. The accepted result is a real integrated commit.
- Retry and restart reconcile the previous attempt before repeating an accepted mutation or paid invocation. Unknown provider outcomes stop for reconciliation.

**How to check:** Request a real gameplay change, attempt an out-of-worktree write, interrupt delivery, and verify the final commit, reviewer identity, and usage ledger.

**Components:** Core coding-worker boundary; immutable context; typed handoff; commit integration

**Test environment:** Qualified sandbox and coding/review routes; bounded test budget

**Expected output:** Candidate diff, accepted commit, independent review, and restart evidence

### AF-CLD-014

**Check the rules of the generated game**

Validate the key behaviors of the first playable game as well as whether the code compiles.

Priority: **P0** · Size: **M** · Role: **qa-engineer** · Status: **Proposed**

Depends on: AF-CLD-010, AF-CLD-011.

**Acceptance criteria**

- Validators check import, script parsing, required scenes, input actions, win/lose states, and export.
- Each acceptance criterion links to primary evidence. Skipped or unknown results do not count as success.
- A failed validator starts only a bounded repair attempt or blocks the run with a clear explanation. Graphical play remains a separate required check.

**How to check:** Inject a missing input, broken scene, unreachable win condition, and export error; verify each failure is caught and tied to the correct criterion.

**Components:** Game validators; evidence mapper; bounded repair policy

**Test environment:** Healthy and broken Godot reference fixtures

**Expected output:** Criterion-to-evidence report, validator results, and repair-limit evidence

### AF-CLD-015

**Build a Web version and add Play**

Let the creator play a specific checked browser build without entering technical commands.

Priority: **P0** · Size: **M** · Role: **fullstack-engineer** · Status: **Proposed**

Depends on: AF-CLD-011, AF-CLD-012, AF-CLD-014.

**Acceptance criteria**

- Play opens the exact build digest and shows controls, version notes, and Stop/Exit.
- Crashes produce evidence without damaging the Control Plane. Game code runs on a separate preview origin with no platform session cookies or provider secrets.
- The previous playable version stays available while agents work on the next one. Web export and browser support are qualified for the pinned Godot version.

**How to check:** Play the exact artifact in the supported browsers, trigger a crash and an attempted platform access, and verify version identity and isolation.

**Components:** Web TargetAdapter; isolated preview; Play controls; crash capture

**Test environment:** Godot Web export templates; isolated origin; browser test matrix

**Expected output:** Web artifact, checksum, graphical play evidence, and preview security results

### AF-CLD-016

**Export a Windows game and the full source**

Give the creator a portable or installable Windows build and a project they can open outside AgentFactory.

Priority: **P0** · Size: **M** · Role: **release-engineer** · Status: **Proposed**

Depends on: AF-CLD-011, AF-CLD-012, AF-CLD-014.

**Acceptance criteria**

- The Windows package runs on a clean supported machine and includes a checksum, README, and version manifest.
- The source archive excludes credentials, machine-specific paths, caches, and other tenants' artifacts. An asset with unclear export rights blocks release.
- The creator can open the project in the qualified Godot version and continue editing it manually.

**How to check:** Download, scan, unpack, and play on a clean Windows machine; reopen the source without AgentFactory and verify the manifest and licenses.

**Components:** Windows TargetAdapter; source exporter; secret and rights checks

**Test environment:** Pinned export templates; clean supported Windows test machine

**Expected output:** Windows build, source archive, checksums, licenses, and clean-machine evidence

### AF-CLD-017

**Turn play feedback into a change plan**

Let the creator describe a change after playing and review a short plan linked to the version they actually tested.

Priority: **P0** · Size: **M** · Role: **product-engineer** · Status: **Proposed**

Depends on: AF-CLD-007, AF-CLD-015.

**Acceptance criteria**

- Feedback records the played build/version, text, an optional permitted screenshot, and steps needed to reproduce the issue.
- The change proposal shows affected requirements, risks, scope, and extra budget before work begins.
- Stale or conflicting feedback is highlighted and resolved instead of silently changing a newer version.

**How to check:** Submit feedback from current and old builds, attach an allowed screenshot, and create a conflicting edit; verify the proposed changes and budget need an explicit decision.

**Components:** PlaySession and Feedback records; change proposal editor

**Test environment:** Two versioned playable fixtures and redacted sample feedback

**Expected output:** Version-linked feedback, reviewed change proposal, and conflict-handling evidence

### AF-CLD-018

**Create version 2, restore version 1, and try a private remix**

Prove the loop from a working game to feedback, an accepted change, a new version, and a one-action restore. Also test a private remix before public community features.

Priority: **P0** · Size: **L** · Role: **workflow-engineer** · Status: **Proposed**

Depends on: AF-CLD-013, AF-CLD-014, AF-CLD-017.

**Acceptance criteria**

- A new run creates a separate SourceVersion and Build and checks the requested behavior, not only general build success.
- A failed version 2 leaves version 1 playable. Restore works in one action and keeps both versions in history.
- The simple version history shows origin, cost, and evidence.
- The creator can privately fork their own game or an explicitly remixable sample, request a visible change, and play the result. The original stays unchanged; source/build lineage and attribution are retained. Public discovery and remix remain AF-CLD-040.

**How to check:** Run v1 to feedback to v2 to restore; then remix a permitted sample and deny a no-remix sample. Compare source digests, behavior, and unchanged originals.

**Components:** Versioned change workflow; restore action; private fork and rights check

**Test environment:** Working game fixtures, own project, licensed remix sample, and denied sample

**Expected output:** v1/v2 play evidence, restore log, private remix lineage, and rights checks

### AF-CLD-019

**Show progress and enforce budget and stop controls**

Give the creator clear progress, predictable spending limits, and control over long agent and build runs.

Priority: **P0** · Size: **M** · Role: **platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-009, AF-CLD-013.

**Acceptance criteria**

- The UI shows the current step, last activity, spent and reserved budget, blockers, and the next action without inventing a completion time.
- A hard cap blocks new paid calls. Raising the cap needs an explicit authorized decision; unknown usage is reserved or reconciled before new work.
- Pause, Resume, and Stop cover scheduling, provider work, and build processes. Accepted results survive; already incurred charges and providers that cannot cancel are explained.

**How to check:** Hit the budget limit during a run, lose a provider response, and pause or stop each stage; verify charges, child processes, accepted work, and resumed state.

**Components:** Core budget ledger; progress feed; cancellation and reconciliation controls

**Test environment:** Usage fixtures and bounded live calls in a qualified sandbox

**Expected output:** Budget and cancellation test results, usage history, and recovery evidence

### AF-CLD-020

**Accept three real reference games**

Qualify the first playable journey across three small genres on clean supported environments.

Priority: **P0** · Size: **L** · Role: **qa-lead** · Status: **Proposed**

Depends on: AF-CLD-015, AF-CLD-016, AF-CLD-018, AF-CLD-019.

**Acceptance criteria**

- A platformer, top-down collector, and puzzle each pass idea to build to play to feedback to version 2.
- The evidence includes real Web play, a clean Windows run, source reopening, failure recovery, restore, and the private remix test from AF-CLD-018.
- Owner acceptance follows actual gameplay and independent review, not simulation or API tests alone. Relevant upstream Godot evidence is linked through AF-CLD-003.
- Internal qualification uses adults or synthetic data. Any 12+ participant pilot waits for the age, consent, provider-account, and data controls in AF-CLD-021.

**How to check:** Run the complete acceptance script for all three games from clean environments and retain criterion-linked evidence for each source/build pair.

**Components:** Reference game suite; acceptance script; independent reviewer; owner sign-off

**Test environment:** Clean Windows environment, supported browsers, qualified model routes, and fixed evaluation budget

**Expected output:** Three source/build bundles, play records, restore/remix evidence, and M1 gate decision


## M2: Qualify the private Cloud alpha

**Epic:** AF-CLD-E2. Offer the proven journey through protected accounts, isolated workers, durable state, and controlled costs.

### AF-CLD-021

**Add account boundaries, roles, and the 12+ access gate**

Prepare a safe multi-user service with clear permissions and an approved age and guardian policy before any minor pilot.

Priority: **P0** · Size: **L** · Role: **security-engineer** · Status: **Proposed**

Depends on: AF-CLD-002, AF-CLD-006.

**Acceptance criteria**

- Creator, Player, Moderator, Support, and Admin have only the permissions they need; every resource checks the account or team boundary.
- Automated negative tests reject cross-tenant reads and writes, including artifacts, worker results, previews, and support tools.
- Sessions, recovery, and account deletion have audit records and rate limits.
- The supported age/jurisdiction matrix, guardian consent where needed, provider account eligibility, private defaults, retention/deletion, and spending authority are approved and tested before 12+ participants join. Unsupported age/provider paths are blocked with a clear alternative.

**How to check:** Test every role and tenant boundary, account recovery/deletion, and synthetic age/guardian cases; require a reviewed minor-pilot decision before recruitment.

**Components:** Identity service; tenant authorization; role policy; age and guardian controls

**Test environment:** Separate synthetic tenants and test identity accounts; no real minor data during qualification

**Expected output:** Access matrix, privacy and provider-policy decisions, negative-test report, and minor-pilot gate record

### AF-CLD-022

**Use PostgreSQL for hosted state**

Keep SQLite for the local profile and provide a migration-managed PostgreSQL profile for Cloud.

Priority: **P0** · Size: **L** · Role: **database-engineer** · Status: **Proposed**

Depends on: AF-CLD-002, AF-CLD-021.

**Acceptance criteria**

- The schema supports tenant isolation, immutable audit records, idempotency, and a transactional outbox.
- Migration and replay keep accepted source and build identities intact.
- Restoring a backup into a fresh database recovers authoritative state and passes integrity checks. Core interfaces stay independent of the Cloud deployment.

**How to check:** Migrate representative local state, retry outbox delivery, interrupt a transaction, and restore to a fresh database; compare identities and invariants.

**Components:** Core storage interface; Cloud PostgreSQL adapter; migrations; outbox

**Test environment:** Isolated PostgreSQL test database and encrypted backup target

**Expected output:** Migration and rollback plan, adapter qualification, and restore evidence

### AF-CLD-023

**Store source, builds, and assets as protected objects**

Move large files into S3-compatible storage with content digests and clear account ownership.

Priority: **P0** · Size: **M** · Role: **backend-engineer** · Status: **Proposed**

Depends on: AF-CLD-021, AF-CLD-022.

**Acceptance criteria**

- Objects record digest, media type, size, origin, retention, and tenant ownership.
- Uploads enforce quota and reject unsafe paths, archive bombs, and files blocked by the malware policy.
- Deletion and export leave evidence. Cleanup does not delete referenced artifacts, and guessed object keys do not grant access.

**How to check:** Try cross-tenant downloads and malicious archives; interrupt upload and deletion, run orphan cleanup, and verify referenced artifacts remain available.

**Components:** Object store adapter; upload inspection; retention and cleanup service

**Test environment:** Isolated S3-compatible bucket with separate test tenants and access logs

**Expected output:** Object manifests, upload threat-test results, and retention/export evidence

### AF-CLD-024

**Qualify server resources and register remote workers**

Inspect the available server, then let qualified Linux, Windows, or GPU nodes safely claim agent and build jobs.

Priority: **P0** · Size: **L** · Role: **distributed-systems-engineer** · Status: **Proposed**

Depends on: AF-CLD-021, AF-CLD-022.

**Acceptance criteria**

- A read-only inventory records CPU, RAM, GPU/VRAM, disk, OS, network, virtualization, and installed toolchains. User-reported server availability is not treated as proof of a running game pipeline.
- Workers advertise tested capabilities, toolchain versions, capacity, and health. An unsupported or underpowered node has a clear blocked state.
- Each lease binds tenant, run, task, worktree, and attempt. A stale worker cannot finish a newer attempt.
- Fault tests cover drain, quarantine, replacement, and recovery of abandoned jobs. Inventory, worker registration, sandbox qualification, and production readiness have separate evidence.

**How to check:** Review inventory before scheduling; run lease expiry, stale completion, capacity exhaustion, worker loss, and replacement drills on isolated nodes.

**Components:** Read-only hardware probe; worker registry; fenced leases; capability scheduler

**Test environment:** Authorized test nodes only; access and capacity of the reported server remain to be confirmed

**Expected output:** Redacted server inventory, capacity decision, worker qualification report, and fault evidence

### AF-CLD-025

**Make hosted workflows survive restarts**

Use the existing Temporal integration as a foundation for Cloud workflows that recover after deployments, restarts, and worker loss.

Priority: **P0** · Size: **L** · Role: **workflow-engineer** · Status: **Proposed**

Depends on: AF-CLD-022, AF-CLD-024.

**Acceptance criteria**

- Workflow IDs are stable, activities are idempotent, and versioning and rollback are documented.
- Continue-as-new, retry, and cancellation do not duplicate accepted commits, build promotions, or settled usage entries. Use provider-side idempotency where supported; an unknown chargeable outcome blocks a new invocation until reconciliation.
- Local state, the Cloud ledger, and workflow history have a documented source of truth and reconciliation process.

**How to check:** Restart workers at paid-call, commit, promotion, and workflow rollover boundaries; replay histories and verify one accepted result and reconciled usage.

**Components:** Temporal workflows and activities; versioning; reconciliation; authoritative Cloud ledger

**Test environment:** Isolated Temporal and PostgreSQL environment with failure injection

**Expected output:** Replay records, restart and rollout results, and operator recovery runbook

### AF-CLD-026

**Isolate agent and build jobs**

Treat generated code as untrusted and run it in disposable environments with enforced resource and network limits.

Priority: **P0** · Size: **L** · Role: **security-platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-024, AF-CLD-025.

**Acceptance criteria**

- Qualification proves workspace write scope, CPU/RAM/disk/time/process limits, and network egress rules are enforced.
- Build jobs cannot access Control Plane credentials or another tenant. Credentialed agent execution is a separate boundary from untrusted builds.
- Teardown, sanitized crash reports, and deliberately malicious fixtures leave audit evidence. A process or container alone is not assumed to provide sufficient isolation.

**How to check:** Run hostile read/write, network, fork, disk-fill, and timeout fixtures; verify containment, cancellation, cleanup, and absence of test secrets.

**Components:** Qualified OS or virtual-machine sandbox; resource limits; egress policy; cleanup

**Test environment:** Disposable test runners isolated from real users and production secrets

**Expected output:** Sandbox threat model, isolation report, malicious-fixture evidence, and teardown runbook

### AF-CLD-027

**Guide creators through AI connections**

Explain chat subscriptions, APIs, coding tools, and local models, then verify the connection the creator is actually allowed to use.

Priority: **P0** · Size: **M** · Role: **integration-engineer** · Status: **Proposed**

Depends on: AF-CLD-004, AF-CLD-021.

**Acceptance criteria**

- At least one coding route and one independent review route pass a bounded capability canary with the actual selected model.
- The wizard distinguishes authentication, quota, model access, capability, and network errors, and shows the next repair step.
- An unsupported provider or model never appears Ready. A chat subscription does not automatically mean API credits or permission for unattended use.
- Sign-in uses the provider's supported flow. API keys go only into a protected connection form, never chat. Local models require an explicit reachable endpoint and qualified capacity; installation guidance and host consent follow the AF-GC bridge.

**How to check:** Test expired credentials, missing model access, no quota, unavailable local host, and a wrong effective model; verify recovery instructions without exposing secrets.

**Components:** Connection wizard; provider capability and entitlement checks; canary runner

**Test environment:** Supported test accounts with small explicit usage limits; local endpoint fixtures only for an offered local route, plus unavailable/unsupported local cases without making hybrid a Cloud alpha prerequisite.

**Expected output:** Connection evidence, supported route matrix, and guided error/recovery copy

### AF-CLD-028

**Keep Cloud credentials outside game work**

Extend the credential broker for Cloud without exposing provider or store keys to prompts, logs, game code, or general browser API responses.

Priority: **P0** · Size: **L** · Role: **security-engineer** · Status: **Proposed**

Depends on: AF-CLD-021, AF-CLD-027.

**Acceptance criteria**

- Secrets are encrypted at rest, scoped by tenant/provider/purpose, and can be rotated or revoked without redeployment.
- A synthetic secret canary is absent from logs, traces, artifacts, support bundles, and model context.
- Only the trusted provider execution boundary receives the smallest required short-lived credential. Untrusted build and game processes receive none.

**How to check:** Inject a synthetic canary, run provider and build jobs, revoke during a lease, and inspect all output channels for leakage and expired access.

**Components:** Encrypted secret store; scoped credential broker; lease revocation; redaction

**Test environment:** Test key management and isolated trusted agent runner; synthetic keys only for leak tests

**Expected output:** Credential-flow diagram, rotation/revocation evidence, and secret-canary report

### AF-CLD-029

**Enforce Cloud quotas and track usage**

Control model usage, build minutes, storage, and concurrency for each account, project, and run.

Priority: **P0** · Size: **M** · Role: **billing-platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-022, AF-CLD-025, AF-CLD-027.

**Acceptance criteria**

- An idempotent ledger links requested and effective model, token usage and cost, build minutes, and storage.
- Soft and hard limits have predictable actions. Insufficient available balance cannot start new paid work; reservations prevent concurrent overspend.
- The creator sees an estimate before a run and actual or clearly pending costs after each iteration. Credits are internal usage units at this stage; paid checkout is deferred.

**How to check:** Run concurrent jobs at a shared cap, duplicate a usage event, delay provider billing, and exhaust storage; reconcile totals and verify no new work exceeds the cap.

**Components:** Usage ledger; reservations; quota policy; cost display

**Test environment:** Provider usage fixtures and isolated build/storage metering

**Expected output:** Usage reconciliation report, quota tests, and cost-per-playable baseline

### AF-CLD-030

**Provide the hosted Creator Portal**

Offer Create, AI Team, Build, Play, Change, and Export in the browser without requiring a local command line.

Priority: **P0** · Size: **L** · Role: **fullstack-engineer** · Status: **Proposed**

Depends on: AF-CLD-004, AF-CLD-021, AF-CLD-025, AF-CLD-029.

**Acceptance criteria**

- Onboarding, project resume, and recovery continue correctly after refresh or reconnect from another device. Draft edits are not overwritten by status polling.
- The main flow supports Ukrainian and English, keyboard navigation, and laptop/mobile widths.
- Operator diagnostics appear only for an authorized role. A creator sees one next action, clear progress, current budget, and the last working version.
- The 12+ pilot runs only after AF-CLD-021 is accepted and measures completion without operator help, understanding of budget/stop controls, and time to first playable.

**How to check:** Run browser journeys for first use, keyboard-only use, refresh, reconnect, failure, and stop; conduct the approved supervised usability pilot and record observed difficulties.

**Components:** Creator Portal; project history; localization; accessible controls; role-filtered status

**Test environment:** Private staging, supported browsers/devices, and approved pilot accounts

**Expected output:** Browser journey evidence, usability findings, and accessibility report

### AF-CLD-031

**Serve protected playable builds**

Deliver private and unlisted Web builds through controlled links and a CDN without exposing storage or the Control Plane.

Priority: **P0** · Size: **M** · Role: **cloud-engineer** · Status: **Proposed**

Depends on: AF-CLD-023, AF-CLD-026, AF-CLD-030.

**Acceptance criteria**

- A URL is scoped, expiring, and tied to a release/build. Guessing an object key grants no access; unlisted means link-accessible, not private.
- Browser headers, CSP, and a separate game origin enforce the preview boundary. Generated code receives no platform session or provider credentials.
- Revocation and expiry stop future authorized fetches without removing source history. Already downloaded public bytes cannot be promised to disappear.

**How to check:** Check private access, copied links, expiry, revocation, cache behavior, and hostile game requests in a real browser; verify digest and origin separation.

**Components:** Signed link service; CDN policy; isolated game origin; access checks

**Test environment:** Private object storage and staging delivery origin with cache logs

**Expected output:** Artifact-to-URL proof, browser isolation report, and link lifecycle tests

### AF-CLD-032

**Export a portable ownership package**

Give the creator a usable archive of source, builds, manifests, licenses, and asset origins.

Priority: **P0** · Size: **M** · Role: **release-engineer** · Status: **Proposed**

Depends on: AF-CLD-023, AF-CLD-030.

**Acceptance criteria**

- The archive includes source commit/digest, toolchain versions, dependencies, attribution, and reproducibility notes.
- Secrets, internal tenant IDs, and absolute local paths are excluded. Assets that lack the necessary release rights are excluded with an explicit report or block export.
- The archive works on a clean machine and includes a machine-readable manifest. Portability does not imply exclusive copyright in all AI-generated output.

**How to check:** Export a project with permitted and blocked assets, inspect for secrets and internal identifiers, then rebuild and play the allowed package outside AgentFactory.

**Components:** Portable exporter; manifest writer; source/build and rights checks

**Test environment:** Clean download/rebuild environment and licensed sample assets

**Expected output:** Portable archive, manifest, license report, and independent rebuild evidence

### AF-CLD-033

**Add operations visibility and recovery drills**

Support Cloud incidents and recovery while collecting only the personal data needed to operate the service.

Priority: **P0** · Size: **L** · Role: **site-reliability-engineer** · Status: **Proposed**

Depends on: AF-CLD-022, AF-CLD-023, AF-CLD-025, AF-CLD-026.

**Acceptance criteria**

- Traces, metrics, and logs link tenant, project, run, task, worker, and build without exposing secrets or unnecessary prompt content.
- Support bundles are redacted, visible to the user, and shared only with explicit consent. Retention and access are defined.
- Backups, restore, incident response, and RPO/RTO targets are documented and verified through fresh database/object-store restore and worker-loss drills. Accepted artifact hashes, source/build identities, and audit continuity are compared before and after recovery. Alerts cover queues, failures, capacity, and budget anomalies.

**How to check:** Trigger a failed build and worker loss, inspect redacted diagnostics, and restore database plus objects into a fresh environment against the agreed recovery targets.

**Components:** Telemetry; alerts; support bundle builder; backup and incident runbooks

**Test environment:** Private telemetry and backup stores; separate recovery environment

**Expected output:** Operations dashboard specification, redaction evidence, recovery metrics, and drill report

### AF-CLD-034

**Accept the private Cloud alpha**

Prove the complete hosted game journey with a small invited group before opening the service to the public.

Priority: **P0** · Size: **L** · Role: **release-manager** · Status: **Proposed**

Depends on: AF-CLD-020, AF-CLD-021, AF-CLD-022, AF-CLD-023, AF-CLD-024, AF-CLD-025, AF-CLD-026, AF-CLD-027, AF-CLD-028, AF-CLD-029, AF-CLD-030, AF-CLD-031, AF-CLD-032, AF-CLD-033.

**Acceptance criteria**

- At least three isolated test tenants complete idea, AI connection, build, play, feedback, version 2, restore, and source export through the invited-creator path without operator-only steps in the normal journey.
- Tenant isolation, sandboxing, credential protection, hard budget limits, cancellation, restart, backup/restore, and artifact access all have current evidence.
- The pilot report records first-playable success, observed time and cost, failures, support effort, and usability findings against targets agreed before the pilot.
- Any 12+ participation meets AF-CLD-021. The owner reviews the evidence and unresolved issues; server ownership or a successful demo alone cannot pass M2.

**How to check:** Run the private alpha acceptance script with approved participants and deliberate failures; independently review each release criterion and its exact build evidence.

**Components:** Hosted acceptance suite; approved pilot plan; issue triage; release decision

**Test environment:** Qualified private staging and worker pool, test accounts, and fixed pilot budget

**Expected output:** Pilot report, cost and reliability baseline, open-risk list, and signed M2 gate decision


## M3: Open publishing, discovery, and Remix

**Epic:** AF-CLD-E3. Let people find, play, and remix permitted releases with privacy, moderation, and asset rights checks.

### AF-CLD-035

**Add releases and visibility controls**

Creators will publish a chosen build as a release, separately from their changing working build.

Priority: **P1** · Size: **M** · Role: **backend-engineer** · Status: **Proposed**

Depends on: AF-CLD-034.

**Acceptance criteria**

- Releases will support Private, Unlisted and Public visibility, with Private as the default.
- Before publishing, the creator will see the exact build, metadata, permissions, assets, licences and a preview of the changes.
- Cancellation will create no external publication. Revocation will remove active publication state and links under AgentFactory's control, while retaining required audit records; the UI will explain that already downloaded copies cannot be recalled.

**How to check:** Test every visibility transition with a creator, another account and a signed-out visitor, including direct artifact URLs. Interrupt and retry publication, cancellation and revocation; verify the exact build digest and the absence of unintended active public state.

**Components:** Planned release registry and publication state machine; Planned release preview, access rules and revocation controls

**Test environment:** Isolated tenants, versioned artifact storage and a test delivery endpoint

**Expected output:** Release and visibility contracts with the publication preview flow; Transition, access-control and interrupted-publication evidence

### AF-CLD-036

**Add creator profiles and libraries**

Creators will have a public profile and a private library for their games, drafts, releases, remixes and purchases.

Priority: **P1** · Size: **M** · Role: **fullstack-engineer** · Status: **Proposed**

Depends on: AF-CLD-021, AF-CLD-035.

**Acceptance criteria**

- Privacy controls will separate the public profile from the private creator workspace.
- The library will show owned, created, remixed, liked and purchased items without exposing another tenant's private data.
- Documented rules will cover existing purchases and remixes when an account is deleted or banned.

**How to check:** Check profile and library views across owner, visitor, buyer and unrelated-tenant accounts. Use account-deletion and ban fixtures to verify the agreed treatment of purchased releases and remix history.

**Components:** Planned profile and library views; Planned privacy rules and account-lifecycle handling

**Test environment:** Multi-tenant test accounts with private, public, purchased and remixed releases

**Expected output:** Profile and library specifications with privacy defaults; Account-lifecycle policy and access-control test evidence

### AF-CLD-037

**Add game pages with browser Play**

Players will open a published game page, see its creator, version, controls and licence, and play its Web build.

Priority: **P1** · Size: **M** · Role: **frontend-engineer** · Status: **Proposed**

Depends on: AF-CLD-031, AF-CLD-035.

**Acceptance criteria**

- The game page will always launch the published release digest, never the mutable latest working build.
- Age and content labels, attribution, Report and telemetry privacy controls will be visible.
- Crash and performance telemetry will not collect arbitrary game payloads or personal data without valid consent under the applicable age policy.

**How to check:** Publish one build, change the working build and verify that Play still launches the published digest. Check the browser journey, visible labels and controls, crash handling, and telemetry payloads with consent enabled and disabled.

**Components:** Planned public game page and sandboxed Web player; Planned release resolution and consent-aware telemetry

**Test environment:** Supported-browser test matrix, isolated game origin and synthetic crash fixtures

**Expected output:** Game-page and Play flow with release identity and privacy controls; Browser compatibility, digest-pinning and telemetry evidence

### AF-CLD-038

**Add Discover, search and tags**

Players will find public releases by genre, engine, platform, language and popularity through clear browsing and search controls.

Priority: **P1** · Size: **M** · Role: **search-engineer** · Status: **Proposed**

Depends on: AF-CLD-035, AF-CLD-037.

**Acceptance criteria**

- Search will index only metadata approved for public discovery and will update after revocation or moderation.
- Basic ranking signals will be explained, and simple play-count spam will not raise a game's ranking.
- Pagination and filters will work against a large fixture catalogue without manipulative interface patterns.

**How to check:** Search a large seeded catalogue and verify filters, stable pagination and exclusion of private, unlisted and restricted releases. Revoke a release and replay fraudulent play events; verify index removal and ranking-abuse controls.

**Components:** Planned discovery index and search API; Planned filter interface and documented ranking rules

**Test environment:** Search test service and a large synthetic release catalogue with moderation and abuse fixtures

**Expected output:** Discovery and ranking specification with measurable index-update expectations; Search, pagination, removal and ranking-abuse test evidence

### AF-CLD-039

**Add share links and embed controls**

Creators will share Unlisted or Public releases without granting access to source files, build tools or their account.

Priority: **P1** · Size: **S** · Role: **fullstack-engineer** · Status: **Proposed**

Depends on: AF-CLD-035, AF-CLD-037.

**Acceptance criteria**

- Share controls will preview the target and support expiry or revocation where applicable; shared access will not inherit build permissions.
- Embeds will use a sandbox, a Content Security Policy and an explicit list of permitted capabilities.
- Copying an internal URL will not make a Private release public.

**How to check:** Open shared, expired, revoked and internal URLs as signed-out and unrelated users. Test an embedded game that requests blocked navigation, storage and network capabilities; confirm only declared capabilities are available.

**Components:** Planned share-link service and target preview; Planned embed policy and release access checks

**Test environment:** Separate host and game origins, test embedding pages and short-lived link fixtures

**Expected output:** Sharing and embed capability contracts; Expiry, revocation, private-link and browser sandbox test evidence

### AF-CLD-040

**Add Remix and Fork with source history**

Players will turn an explicitly remixable release into their own project, ask agents to change it and publish a permitted derivative.

Priority: **P1** · Size: **L** · Role: **backend-engineer** · Status: **Proposed**

Depends on: AF-CLD-032, AF-CLD-035, AF-CLD-036.

**Acceptance criteria**

- Remix will require an author setting and licence that grant the necessary rights; no-remix or missing permission will deny the action. Source and asset permissions will be checked separately.
- A fork will create a workspace owned by the new tenant with an immutable reference to the parent release. It will not copy private prompts, credentials or unrelated creator context.
- Attribution and the chain of parent releases will survive later remixes. Revocation rules will not rewrite that history.

**How to check:** Run permitted, no-remix, missing-licence and mixed-asset-rights cases through both UI and API. Create several remix generations across tenants, revoke a parent and verify immutable references, attribution and absence of private source context or secrets.

**Components:** Planned remix permission checks and project forking; Planned immutable release lineage and attribution records

**Test environment:** Multi-tenant remix fixtures with mixed licences, private context and revoked parent releases

**Expected output:** Remix-rights and revocation policy with a lineage data contract; Permission, private-data exclusion and multi-generation remix evidence

### AF-CLD-041

**Add likes, bookmarks and basic play statistics**

Players will give simple feedback and creators will see useful play statistics, without adding a full social network.

Priority: **P2** · Size: **M** · Role: **analytics-engineer** · Status: **Proposed**

Depends on: AF-CLD-037, AF-CLD-038.

**Acceptance criteria**

- Privacy-aware events will be idempotent and distinguish page load, game start, meaningful play and crash.
- Rate limits will reduce like and bookmark abuse. Creators will see aggregate statistics rather than player identities by default.
- Statistics will identify the published release and version they describe.

**How to check:** Replay duplicate and out-of-order load, start, play and crash events; compare the resulting per-release aggregates with known fixture totals. Check abuse limits, bookmark privacy and creator access using unrelated accounts.

**Components:** Planned feedback endpoints and event definitions; Planned aggregate analytics and abuse limits

**Test environment:** Synthetic event stream, multiple release versions and privacy test accounts

**Expected output:** Event definitions and creator statistics specification; Duplicate-event, aggregate-accuracy, privacy and abuse-limit evidence

### AF-CLD-042

**Add age-aware moderation and reporting**

The public portal will screen content and executable builds, let users report problems, and support review and takedown for an audience aged 12 and above.

Priority: **P0** · Size: **L** · Role: **trust-safety-engineer** · Status: **Proposed**

Depends on: AF-CLD-026, AF-CLD-035, AF-CLD-037.

**Acceptance criteria**

- Before publication, checks will cover metadata, assets, executable and Web behaviour, and malware policy, using the approved age and content rules. Passing checks will not publish automatically.
- Report, triage, restriction and appeal will form a documented workflow with immutable evidence and separate roles. Reporting and takedown controls will be understandable for users aged 12 and above.
- Emergency unpublishing will retain required legal and audit evidence. Moderators will not gain access to private source without a documented reason and authorised access.

**How to check:** Use benign and policy-violating metadata, asset and executable fixtures to test pre-publication decisions without exposing test users to harmful material. Walk through report, emergency takedown and appeal; verify role separation, evidence retention and restricted private-source access.

**Components:** Planned publication screening and moderation queue; Planned reports, appeals, takedown controls and audit access

**Test environment:** Isolated moderation environment, harmless detection fixtures and separate reporter, reviewer and administrator roles

**Expected output:** Age-aware content policy and report-to-appeal workflow; Moderation, takedown, access-control and evidence-retention test report

### AF-CLD-043

**Check asset origin and licences before release**

Publishing or selling will be blocked when the origin or licence of required art, audio, fonts or code is unknown or incompatible.

Priority: **P0** · Size: **L** · Role: **ip-compliance-engineer** · Status: **Proposed**

Depends on: AF-CLD-023, AF-CLD-035, AF-CLD-040.

**Acceptance criteria**

- Every asset will record its source, generator, model, licence, attribution and transformation history, or explicitly mark unknown fields.
- Unknown or incompatible licences will block Publish and Sell with a specific way to resolve the problem.
- Exports and releases will automatically include a NOTICE and attribution manifest.

**How to check:** Evaluate compatible, incompatible, missing and transformed-asset licence fixtures through publication and sale checks. Inspect exported packages to match NOTICE entries and attribution to the pinned asset manifest.

**Components:** Planned asset provenance registry and licence rules; Planned publication and sale checks with attribution generation

**Test environment:** Synthetic asset catalogue with known, unknown and conflicting licence fixtures

**Expected output:** Asset provenance schema and licence-resolution workflow; Exported attribution examples and licence-gate test evidence

### AF-CLD-044

**Approve a limited public creator beta**

A limited public group will test the complete Create, Publish, Play and Remix journey within the documented beta scope.

Priority: **P1** · Size: **L** · Role: **release-manager** · Status: **Proposed**

Depends on: AF-CLD-035, AF-CLD-036, AF-CLD-037, AF-CLD-038, AF-CLD-039, AF-CLD-040, AF-CLD-042, AF-CLD-043, AF-CLD-041.

**Acceptance criteria**

- Browser end-to-end checks will pass for Public, Unlisted, revoke, report and permitted remix journeys, including denied remix attempts.
- Load, sandbox-escape, malicious-upload, moderation, and release-lineage campaigns pass. Basic play analytics from AF-CLD-041 are verified and distinguish tests, bots, operators, and real players.
- Known limits, the moderation service commitment and the rollback plan will be published for the beta group before access opens.

**How to check:** Run the beta journey matrix with creator, player, minor-policy, moderator and unrelated-tenant accounts against pinned releases. Collect load and security campaign results, verify analytics or its approved deferral, and rehearse emergency rollback before owner approval.

**Components:** Planned beta release gate and evidence index; Planned creator, discovery, Play, remix and moderation workflows

**Test environment:** Bounded beta staging environment with production-like browser isolation and synthetic load

**Expected output:** Criterion-by-criterion beta acceptance report and approved scope; Beta limitations, moderation commitment and rollback runbook


## M4: Qualify marketplace payments

**Epic:** AF-CLD-E4. Sell licensed releases with eligible sellers, reliable access, reconciled payments, refunds, and payouts.

### AF-CLD-045

**Add seller setup and adult or guardian approval**

Creating games from age 12 will remain separate from legally significant selling and payout activities.

Priority: **P0** · Size: **L** · Role: **compliance-product-engineer** · Status: **Proposed**

Depends on: AF-CLD-036, AF-CLD-044.

**Acceptance criteria**

- Child accounts will not sell or receive payouts without a supported adult, guardian or business flow.
- Identity, customer-verification and tax steps will use a qualified payment provider; AgentFactory will avoid storing unnecessary identity documents.
- Seller eligibility, supported countries and recovery from failed setup will be explained before a paid listing can be created.

**How to check:** Test adult, child, guardian-managed, unsupported-country and incomplete-verification fixtures through UI and API. Use the payment provider's test environment to verify setup failure and recovery, and inspect stored data for unnecessary identity documents.

**Components:** Planned seller eligibility and guardian approval rules; Planned payment-provider onboarding handoff

**Test environment:** Payment-provider test environment and synthetic age, country and verification states

**Expected output:** Seller and guardian setup flow with eligibility policy; API gate, recovery and data-minimisation evidence

### AF-CLD-046

**Add sale listings, prices and licence choices**

Eligible creators will offer a downloadable release, source licence or commercial-use licence with clear purchase rights.

Priority: **P1** · Size: **M** · Role: **commerce-engineer** · Status: **Proposed**

Depends on: AF-CLD-035, AF-CLD-043, AF-CLD-045.

**Acceptance criteria**

- Each listing will pin the exact release, build and source scope, currency, price, licence text and refund terms.
- Changing a build, price or licence will create a new revision without changing earlier purchases retroactively.
- Sell will remain blocked until valid rights and asset provenance have been confirmed.

**How to check:** Create purchases against a listing revision, then change its build, price and licence and verify earlier purchase terms remain fixed. Attempt to list assets with missing or conflicting rights through both UI and API.

**Components:** Planned versioned listing and licence-product registry; Planned pricing controls and sale-rights checks

**Test environment:** Test seller accounts, pinned releases and mixed-rights asset fixtures

**Expected output:** Listing revision and licence-product contracts; Purchase-history and rights-gate test evidence

### AF-CLD-047

**Add checkout through a payment provider**

Buyers will pay through an external payment provider, with reliable event handling and no card-data storage in AgentFactory.

Priority: **P0** · Size: **L** · Role: **payments-engineer** · Status: **Proposed**

Depends on: AF-CLD-021, AF-CLD-046.

**Acceptance criteria**

- Checkout creation, success, decline, cancellation, retries and duplicate webhooks will not create duplicate purchases.
- Payment state, orders and access entitlements will reconcile and recover after an outage.
- Sensitive card data subject to PCI requirements will not pass through AgentFactory backend services or logs.

**How to check:** Use provider test payments for success, decline, cancel and retry, then replay duplicate and out-of-order webhooks. Interrupt processing before and after order creation; reconcile provider records and inspect request and log samples for sensitive card data.

**Components:** Planned checkout adapter and verified payment-event handler; Planned order reconciliation and entitlement handoff

**Test environment:** Payment-provider test mode, webhook replay fixtures and outage injection

**Expected output:** Checkout and payment-event state contracts; Duplicate-purchase, outage-recovery and card-data-boundary evidence

### AF-CLD-048

**Add purchase access and the buyer library**

A confirmed purchase will grant access to the exact release, package and licence that the buyer purchased.

Priority: **P0** · Size: **M** · Role: **backend-engineer** · Status: **Proposed**

Depends on: AF-CLD-046, AF-CLD-047.

**Acceptance criteria**

- An entitlement record will be immutable and tied to its order and licence revision; revocation will follow a defined policy and retain history.
- Download links will be signed and short-lived. Buyers will not receive access to the creator workspace or secrets.
- Rules will define repeat downloads, account recovery and continued access after seller removal.

**How to check:** Check purchased-package access, expired links and unrelated-account denial against several listing revisions. Exercise repeat downloads, account recovery, policy-based revocation and seller removal while verifying entitlement history.

**Components:** Planned entitlement registry and buyer library; Planned signed downloads and entitlement lifecycle rules

**Test environment:** Private artifact storage, test orders and buyer, seller and unrelated-user accounts

**Expected output:** Purchase-access and seller-removal policy with entitlement contract; Download security, recovery and entitlement-history evidence

### AF-CLD-049

**Add the revenue ledger, fees and payouts**

The marketplace will record sale amounts, taxes, processor fees, platform fees, refunds and creator balances using consistent fixed-precision accounting.

Priority: **P0** · Size: **L** · Role: **financial-systems-engineer** · Status: **Proposed**

Depends on: AF-CLD-045, AF-CLD-047, AF-CLD-048.

**Acceptance criteria**

- A double-entry, idempotent ledger will reconcile payment-provider events and support audit and export.
- Explicit rules will cover payout eligibility, reserves, currency conversion and negative balances.
- The creator dashboard will show pending, available, paid and refunded amounts with downloadable statements. Fee amounts will come from an approved pricing policy, not unvalidated planning estimates.

**How to check:** Replay known sale, fee, refund and payout fixtures, including duplicates and currency conversion, and verify balanced ledger entries and provider reconciliation. Compare dashboard totals and statements with the ledger across reserve release, negative-balance and failed-payout cases.

**Components:** Planned double-entry ledger and payout reconciliation; Planned balance dashboard, statement export and approved fee rules

**Test environment:** Payment-provider test mode and fixed-precision multi-currency accounting fixtures

**Expected output:** Ledger, fee, reserve and payout policy contracts; Balanced-ledger, reconciliation and statement-accuracy evidence

### AF-CLD-050

**Add refunds, disputes and fraud review**

The marketplace will handle refunds, disputes and suspicious activity without corrupting purchase access, payouts or creator records.

Priority: **P0** · Size: **L** · Role: **risk-engineer** · Status: **Proposed**

Depends on: AF-CLD-047, AF-CLD-048, AF-CLD-049.

**Acceptance criteria**

- A refund or dispute will update the order, entitlement and ledger exactly once under the agreed policy.
- Activity-rate, account, payment and download signals will trigger a review or hold rather than uncontrolled automatic penalties.
- Appeal and support actions will require the appropriate role and leave a complete audit trail.

**How to check:** Replay duplicate, delayed and conflicting refund and dispute events and reconcile all three records. Test suspicious-activity holds, legitimate-user false positives, appeals and unauthorised support actions.

**Components:** Planned refund and dispute coordinator; Planned fraud-review queue, hold controls and audited support actions

**Test environment:** Payment-provider dispute fixtures, synthetic activity signals and separated support roles

**Expected output:** Refund, dispute, hold and appeal policies; Exactly-once financial updates and role-audit evidence

### AF-CLD-051

**Approve the marketplace release**

The sell, buy, download, payout and refund journey will be qualified in a sandbox and then with a separately approved limited live group.

Priority: **P1** · Size: **L** · Role: **release-manager** · Status: **Proposed**

Depends on: AF-CLD-045, AF-CLD-046, AF-CLD-047, AF-CLD-048, AF-CLD-049, AF-CLD-050.

**Acceptance criteria**

- End-to-end order, entitlement, ledger and payout reconciliation will pass for both success and failure cases.
- Age, rights, tax, payment-provider and moderation gates will not be bypassable through the API.
- Finance, security and compliance owners will approve the evidence, rollback plan and incident runbook before the limited live release.

**How to check:** Run the complete commerce journey in provider test mode with retries, outages, refunds, disputes and disallowed seller cases. Obtain the required live-test approval, reconcile the bounded live pilot, and record independent review and owner acceptance before expanding access.

**Components:** Planned marketplace acceptance gate and reconciliation reports; Planned seller, checkout, entitlement, ledger and moderation workflows

**Test environment:** Provider sandbox and a separately authorised, bounded live pilot with qualified seller accounts

**Expected output:** Marketplace acceptance report with financial reconciliation evidence; Approved owner sign-offs, rollback procedure and incident runbook


## M5: Qualify more engines and distribution targets

**Epic:** AF-CLD-E5. Offer only engine and target combinations that have real build and run evidence; keep consoles conditional.

### AF-CLD-052

**Publish an EngineAdapter SDK and compatibility tests**

Maintainers will be able to add engines through a stable adapter contract without needing access to internal orchestration.

Priority: **P1** · Size: **L** · Role: **sdk-engineer** · Status: **Proposed**

Depends on: AF-CLD-005, AF-CLD-034.

**Acceptance criteria**

- The SDK will provide versioned interfaces, a manifest, declared capabilities and permissions, toolchain probes and test fixtures.
- An adapter will activate only when its pack is signed or approved under the trust policy and has passing conformance evidence.
- Compatibility, upgrade and rollback checks will protect existing Godot projects.

**How to check:** Run valid, incompatible, unsigned and over-permissioned adapter fixtures through activation and conformance checks. Upgrade and roll back the reference adapter while compiling and playing pinned existing Godot projects.

**Components:** Planned EngineAdapter SDK and conformance runner; Planned adapter manifest, capability registry and trust checks

**Test environment:** Isolated adapter test workers and pinned Godot regression projects

**Expected output:** Versioned SDK, reference adapter and extension guide; Adapter trust, conformance and Godot regression evidence

### AF-CLD-053

**Qualify the Unity adapter**

A supported Unity workflow will cover Hub and Editor setup, C# changes, batch tests and builds, Play and feedback within a tested compatibility matrix.

Priority: **P1** · Size: **L** · Role: **unity-engineer** · Status: **Proposed**

Depends on: AF-CLD-052.

**Acceptance criteria**

- Setup will respect creator account, licence and EULA requirements, with clear recovery steps for missing Editor versions or modules.
- Compilation, EditMode and PlayMode tests, builds, graphical runs, a second game version and rollback will pass.
- Unity failures will not regress Godot, and unsupported targets will not be marked ready.

**How to check:** Run a reference Unity game from qualified setup through compile, EditMode, PlayMode, build, graphical Play, feedback, version two and rollback. Test missing modules, licence handoff and unsupported targets, then run the existing Godot regression journey alongside Unity.

**Components:** Planned Unity adapter, toolchain probes and setup handoff; Planned Unity test, build and graphical-run validators

**Test environment:** Qualified Unity Hub and Editor workers, authorised licences and required target modules

**Expected output:** Unity support matrix, setup guidance and adapter package; Real compile, test, graphical-play, rollback and Godot-isolation evidence

### AF-CLD-054

**Prove Unreal feasibility and qualify its adapter**

The team will first measure reproducibility, worker needs, licensing and build cost, then claim support only for a proven Unreal workflow.

Priority: **P1** · Size: **L** · Role: **unreal-engineer** · Status: **Proposed**

Depends on: AF-CLD-052.

**Acceptance criteria**

- The feasibility study will publish supported project size, toolchain, operating system, GPU, storage, build-time limits and cost profile.
- The adapter will pass import, compile, test, package and graphical run on a small reference project before Unreal support is advertised.
- Unsupported plugins and targets will be rejected before an expensive build starts.
- The qualified editor path will create, save and reopen the project and level, author C++/Blueprint behavior, detect and repair an injected compile error, then produce separate Development and Shipping evidence through a pinned MCP backend.
- A full Unreal plus Gameplay AI claim additionally requires one level, three NPCs and one objective in a Windows package played without Unreal Editor, save/load, an AI outage and a second accepted package after feedback with the first build retained. Basic editor support does not satisfy this conditional claim.

**How to check:** Repeat the small reference-project journey on clean qualified workers and measure storage, duration and cost. Test unsupported plugin and target rejection before resource allocation, and review whether the results justify the proposed support boundary. For the full gameplay-AI profile, execute the independent player checklist, delayed/invalid action and save-epoch checks, bounded inference outage and novice-creator trial defined in docs/unreal-gameplay-plan.md; retain actual artifact hashes, manual interventions and failed attempts.

**Components:** Planned Unreal feasibility probes and adapter; Planned plugin and target eligibility checks with build-cost evidence

**Test environment:** Qualified Unreal toolchain and licensed workers with measured GPU, memory and storage capacity

**Expected output:** Unreal feasibility report and explicit go/no-go decision; If qualified, an adapter package, support matrix and real build/run evidence

**Delivery plan:** [Architecture, separate editor/gameplay slices and acceptance](unreal-gameplay-plan.md). Split editor and gameplay delivery into narrow upstream contract and implementation claims using the plan; do not reserve all Unreal or UI files in one claim. Keep the existing AF-CLD-052 prerequisite and Godot gates.

### AF-CLD-055

**Add Android builds and Google Play preparation**

Creators will prepare AAB or APK packages signed with their own identity, test them on Android and review store metadata before any submission.

Priority: **P1** · Size: **L** · Role: **mobile-release-engineer** · Status: **Proposed**

Depends on: AF-CLD-052, AF-CLD-043.

**Acceptance criteria**

- A scoped credential broker will protect keystores and credentials; AgentFactory will not own the creator's signing identity.
- The target matrix will check SDK versions, permissions, orientation, performance, installation and execution on supported devices or emulators.
- Store submission will have a preview and a separate explicit human approval. Store review will not be bypassed, and rejection will return actionable evidence.

**How to check:** Build and install signed reference packages on the declared device and emulator matrix; inspect permissions, orientation and performance. Test missing or expired signing access and submission cancellation in an isolated profile; verify no store mutation occurs before approval.

**Components:** Planned Android target adapter and signing handoff; Planned device validation and Google Play preparation connector

**Test environment:** Qualified Android SDK workers, emulators or test devices and creator-authorised signing access

**Expected output:** Android compatibility matrix, package metadata and signing workflow; Install/run evidence and store-preview, approval and rejection-recovery tests

### AF-CLD-056

**Add Apple builds and App Store preparation**

Qualified macOS workers will prepare macOS and iOS releases using creator-owned certificates and profiles, with a separate human review handoff.

Priority: **P1** · Size: **L** · Role: **apple-platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-052, AF-CLD-028, AF-CLD-043.

**Acceptance criteria**

- macOS and iOS builds will run only on qualified Apple build nodes with scoped, time-limited signing access.
- Provisioning, signing, notarisation, TestFlight and App Store preparation will have explicit human approvals and recovery steps.
- Certificates and provisioning profiles will not appear in source exports, game artifacts or logs.

**How to check:** Build and validate reference packages on qualified Apple workers, including expired profile and interrupted-signing cases. Scan artifacts, exports and logs for signing material, and verify each external submission or publication remains blocked until its specific approval.

**Components:** Planned Apple target adapter and signing broker integration; Planned provisioning and notarisation or store-preparation handoffs

**Test environment:** Qualified macOS build nodes, required Apple toolchains and creator-authorised certificates and profiles

**Expected output:** Apple build and signing support matrix with approval/recovery guidance; Package validation, secret-exclusion and approval-boundary evidence

### AF-CLD-057

**Add Steam release preparation**

Creators will prepare depots, build configuration, store assets and a release checklist, then approve upload or publication through their own Steamworks access.

Priority: **P1** · Size: **L** · Role: **store-integration-engineer** · Status: **Proposed**

Depends on: AF-CLD-032, AF-CLD-043, AF-CLD-046.

**Acceptance criteria**

- The connector will use creator-owned Steamworks access and will not make AgentFactory the publisher by default.
- The release will pin exact packages, the state of achievement and cloud-save integrations, and a compliance checklist.
- Upload and publication will be separate operations, each requiring explicit human approval; a dry-run preview will be available before any external change.

**How to check:** Generate a release preview from pinned packages and verify depot contents, metadata and integration-state declarations. Test missing access, cancelled approvals, upload failure and publish denial with connector fixtures; any live store check will require separately authorised creator access.

**Components:** Planned Steam preparation connector and depot mapping; Planned release preview and separate upload/publication approval records

**Test environment:** Isolated connector fixtures and, only for approved live qualification, creator-owned Steamworks access

**Expected output:** Steam release preparation package and creator checklist; Pinned-package, dry-run and external-action approval evidence

### AF-CLD-058

**Add a shared PC store packaging contract**

Target and Store adapters will prepare releases for channels such as Epic and itch.io without adding store-specific branches to Core.

Priority: **P2** · Size: **M** · Role: **store-integration-engineer** · Status: **Proposed**

Depends on: AF-CLD-052, AF-CLD-032.

**Acceptance criteria**

- A shared release manifest will map to each qualified channel's metadata, assets and packages.
- Every adapter will declare its authentication, external-change, review and rollback capabilities. External uploads and publication will require a preview and separate explicit human approval.
- Unsupported live publication will be reported as unsupported, never as simulated success.

**How to check:** Map one pinned release through representative store adapter fixtures and compare package identity and channel metadata. Test each declared capability, unsupported operation and denied approval; verify no unapproved external change or false success is reported.

**Components:** Planned common Store adapter contract and package mapper; Planned capability declarations and channel-specific preparation adapters

**Test environment:** Isolated store fixtures and separately authorised accounts only for declared live qualification

**Expected output:** Shared release-to-store mapping and capability matrix; Package mapping, unsupported-operation and approval-boundary evidence

### AF-CLD-059

**Plan optional console support behind partner approval**

An optional feasibility track will prepare for Xbox, PlayStation and Nintendo only within approved developer environments and partner terms.

Priority: **P2** · Size: **L** · Role: **platform-partnership-engineer** · Status: **Proposed**

Depends on: AF-CLD-052, AF-CLD-028.

**Acceptance criteria**

- A console target will activate only for a verified developer tenant and an isolated, approved worker profile.
- SDKs and documents covered by nondisclosure terms will not enter prompts, public logs, exports or open-source packs.
- Before partner qualification, the UI will show the roadmap and eligibility requirements rather than a guaranteed-build button. The track may conclude with a feasibility report; console shipping will not be promised or required for the main multi-engine release.

**How to check:** Use public capability stubs to test unqualified-tenant denial and absence of restricted material in shared outputs. If partner access is approved, review the isolated worker and information boundaries within that permitted environment; otherwise record the unresolved requirements without claiming a build.

**Components:** Planned console capability boundary and partner eligibility checks; Planned restricted-worker and information-handling policy

**Test environment:** Public test stubs initially; partner-approved isolated workers only after the required access and terms are confirmed

**Expected output:** Console feasibility and eligibility report with a go/no-go decision; Information-boundary design and, only when permitted, restricted qualification evidence

**Optional track:** Console partner feasibility and qualification; does not block M5 or basic GA.

### AF-CLD-060

**Approve the multi-engine and multi-target release**

The same creator workflow will be proven on Godot, Unity and a qualified minimal Unreal path, with supported targets and PC store preparation explicitly listed.

Priority: **P1** · Size: **L** · Role: **release-manager** · Status: **Proposed**

Depends on: AF-CLD-052, AF-CLD-053, AF-CLD-054, AF-CLD-055, AF-CLD-056, AF-CLD-057, AF-CLD-058.

**Acceptance criteria**

- The same GameBrief, Version, Build and Feedback API will work without engine-specific branches in clients.
- The published compatibility matrix will state measured engine, toolchain, operating-system, hardware and cost limits. It will include the qualified generic PC packaging from AF-CLD-058; optional console work will not be presented as shipping support.
- Upgrade, rollback and concurrent workloads across engines will pass regression and soak gates.

**How to check:** Run equivalent reference journeys through the common API on Godot, Unity and the qualified Unreal path, including supported target and PC packaging checks. Exercise concurrent engine workloads, upgrades and rollback; compare the evidence with every claim in the published support matrix.

**Components:** Planned cross-engine acceptance harness and compatibility registry; Planned common creator API, qualified engine adapters and target/store adapters

**Test environment:** Qualified workers for the stated engines and targets, plus synthetic concurrent workloads

**Expected output:** Multi-engine acceptance report and measured compatibility matrix; Cross-engine regression, soak, rollback and PC packaging evidence

**Scope rule:** The planned full M5 gate includes Unity, Unreal, mobile/Apple, and PC-store preparation. A no-go or missing external prerequisite blocks that full scope. A narrower support release needs a recorded scope/dependency revision and fresh validation before acceptance; basic Godot GA does not depend on this gate.


## M6: Accept a reliable service and expand carefully

**Epic:** AF-CLD-E6. Qualify the stated service scope, API, templates, and hybrid profiles; treat factory commerce and non-game work as optional expansion.

### AF-CLD-061

**Package reusable Agent Teams and Factory templates**

Creators will package roles, routing, packs, budgets, policies and acceptance patterns as a reusable Factory artifact.

Priority: **P2** · Size: **L** · Role: **agent-platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-009, AF-CLD-052.

**Acceptance criteria**

- The Factory manifest will be versioned and signed, with no provider secrets or tenant-specific paths.
- The installation preview will show tools, permissions, expected cost, supported engines and risks.
- Fork, upgrade and rollback will preserve source history and will not silently change active runs.

**How to check:** Export and import a reference Factory across tenants, scan for secrets and paths, and verify signature and permission checks. Fork, upgrade and roll back templates while a run is active; confirm the run keeps its approved version and policy.

**Components:** Planned Factory manifest and signing contract; Planned template preview, import and version lifecycle controls

**Test environment:** Multi-tenant template fixtures, signing test keys and active-run scenarios

**Expected output:** Portable Factory manifest and install-preview specification; Secret-exclusion, signature, lineage and active-run stability evidence

### AF-CLD-062

**Add an optional marketplace for Factories and packs**

A later optional marketplace track will let eligible creators sell qualified AI teams and workflow packs as well as games.

Priority: **P2** · Size: **L** · Role: **marketplace-engineer** · Status: **Proposed**

Depends on: AF-CLD-051, AF-CLD-061.

**Acceptance criteria**

- Each listing will pin the exact signed Factory or pack version, permissions, licence and qualification evidence.
- Buyers will run or fork purchased content without receiving seller credentials or private context.
- Review of malicious tools or packs, revocation and notification of affected users will work before this track opens. Its release will require its own approval and will not be required for the scoped game-platform GA gate.

**How to check:** Buy and import a pinned test pack in another tenant, verify version and permissions, and inspect all transferred content for seller secrets. Use harmless malicious-pack fixtures to rehearse review, revocation and affected-user notification without sending real messages during automated tests.

**Components:** Planned Factory and pack listings linked to commerce entitlements; Planned pack review, revocation and affected-user notification workflow

**Test environment:** Payment test mode, signed pack fixtures and isolated buyer/seller tenants

**Expected output:** Optional pack-marketplace scope and listing contract; Cross-tenant purchase, malicious-pack review and revocation evidence

**Optional track:** Factory/pack commerce; needs its own demand and marketplace gate.

### AF-CLD-063

**Let creators choose qualified models and team budgets**

Advanced creators will choose available, authorised providers and models for each role within tested capabilities, reviewer independence, age policy and hard spending limits.

Priority: **P2** · Size: **M** · Role: **agent-systems-engineer** · Status: **Proposed**

Depends on: AF-CLD-029, AF-CLD-061.

**Acceptance criteria**

- The UI will show available evidence for quality, cost, latency and privacy, plus the effective provider and model after routing.
- An invalid role or model substitution will be rejected before launch with an explanation. Safety rules, reviewer independence and hard budgets will remain enforced.
- Presets will include Cloud-first, Local-first, Cheapest qualified and Best quality. Quality and cost comparisons will be limited to tested, available models suitable for the role; local fit, data placement and any paid cloud fallback will require the relevant capability checks and existing user approval.

**How to check:** Route the same role through qualified local and cloud fixtures, unsupported models and unavailable providers; verify the effective model and rejection reasons. Test budget exhaustion, independent-review requirements, minor-account policy and local-only mode, including blocked unapproved paid or cloud fallbacks.

**Components:** Planned capability-aware role routing and model selection UI; Planned provider qualification, budget and policy checks

**Test environment:** Mock providers plus qualified local and cloud test profiles with explicit budget and data-placement limits

**Expected output:** Model-selection and preset contracts with evidence-qualified comparison rules; Routing, actual-model, budget, independence and fallback-control evidence

### AF-CLD-064

**Publish an API, SDK and signed webhooks**

External products will create projects, run Factories and receive build or release events through the same controlled platform boundaries.

Priority: **P2** · Size: **L** · Role: **api-platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-021, AF-CLD-025, AF-CLD-029, AF-CLD-061.

**Acceptance criteria**

- The API will enforce tenant boundaries, rate limits, idempotency and fine-grained tokens and scopes.
- Webhooks will be signed, protected against replay and safe to retry; SDKs will have contract tests.
- External clients will not bypass Publish, Sell or provider approval gates.

**How to check:** Run SDK contract tests with valid, expired, over-scoped and unrelated-tenant tokens, duplicate requests and rate-limit scenarios. Verify webhook signatures, replay rejection and retry behaviour, then attempt prohibited publishing, selling and provider actions through the public API.

**Components:** Planned versioned public API and scoped tokens; Planned SDKs, webhook signing and delivery records

**Test environment:** Isolated API clients, test webhook receivers and replay/outage fixtures

**Expected output:** API specification, SDK examples and webhook verification guide; Scope, idempotency, delivery and approval-gate test evidence

### AF-CLD-065

**Qualify self-hosted and hybrid deployment**

Studios will run the control plane and workers locally or across local and hosted systems while keeping artifacts and policies compatible.

Priority: **P2** · Size: **L** · Role: **deployment-engineer** · Status: **Proposed**

Depends on: AF-CLD-024, AF-CLD-025, AF-CLD-026, AF-CLD-033.

**Acceptance criteria**

- Single-node, hybrid and cluster profiles will have versioned manifests, upgrade and rollback procedures, and clear support boundaries.
- Local-only operation will demonstrate no cloud egress; hybrid operation will explicitly show where data is stored and processed.
- Verified export and import will move artifacts between profiles without identity collisions.

**How to check:** Install, upgrade and roll back each declared profile from clean fixtures and run a reference project through it. Capture local-only network traffic and test blocked egress; transfer conflicting-identity artifact fixtures between profiles and verify integrity and identity handling.

**Components:** Planned deployment profiles and compatibility checks; Planned data-placement controls and verified artifact transfer

**Test environment:** Isolated single-node, hybrid and cluster environments with network capture and controlled artifact storage

**Expected output:** Versioned deployment manifests, support matrix and upgrade/rollback guide; No-egress, data-placement and cross-profile artifact-transfer evidence

### AF-CLD-066

**Explore a later non-game executable pack**

After the gaming product is qualified, an optional website or app pack will test broader reuse within Core and Cloud without creating another product repository.

Priority: **P2** · Size: **L** · Role: **product-platform-engineer** · Status: **Proposed**

Depends on: AF-CLD-052, AF-CLD-061, AF-CLD-064.

**Acceptance criteria**

- The optional pack will define its own roles, validators, runtime and build targets, and acceptance journey.
- It will reuse Core APIs and objects without adding game-specific assumptions to the platform layer.
- A reference project will pass idea, build, preview, feedback and export. The track will need a separate scope decision and will not block the game-platform GA gate.

**How to check:** Review the proposed pack against Core's extension contracts and confirm it adds no product-specific assumptions to the platform. If the optional track is approved, run a real reference project through idea-to-export and repeat the existing game regression journey.

**Components:** Planned optional website or app pack using existing extension APIs; Planned pack-specific validators and preview/export target

**Test environment:** An isolated pack runtime and reference project only after the optional scope is approved

**Expected output:** Optional-pack scope decision and extension design; If approved, reference idea-to-export and game-regression evidence

**Optional track:** Non-game expansion; needs a separate demand and scope decision.

### AF-CLD-067

**Approve the defined general-availability scope**

The team will approve production readiness for a clearly defined set of game and Factory workflows, with measured limits and named support owners.

Priority: **P2** · Size: **L** · Role: **release-manager** · Status: **Proposed**

Depends on: AF-CLD-034, AF-CLD-044, AF-CLD-061, AF-CLD-063, AF-CLD-064, AF-CLD-065.

**Acceptance criteria**

- Capacity, a 72-hour soak, backup and restore, tenant isolation, security, accessibility and billing-reconciliation gates will pass for the declared release scope.
- A reference acceptance mission will use different qualified providers, worker replacement, human approvals and real executable artifacts.
- Runbooks, the evidence index, support ownership, service-level objectives and known limitations will be accepted. Optional console, Factory-marketplace and non-game tracks will not be required or advertised unless separately qualified.
- The signed release scope lists enabled features and verifies their conditional gates. Paid marketplace needs AF-CLD-051; expanded engine/store support needs AF-CLD-060; factory commerce needs AF-CLD-062; a non-game offering needs AF-CLD-066; any console claim needs actual AF-CLD-059 qualification.

**How to check:** Run the scoped acceptance mission and a 72-hour soak with provider failures and worker replacement, then verify restored artifacts and reconciled billing. Review security, accessibility, capacity and support evidence against every published release claim; obtain independent review and explicit owner acceptance.

**Components:** Planned scoped GA acceptance gate and evidence index; Planned operational monitoring, recovery and service ownership

**Test environment:** Production-like isolated environment sized for the declared scope, recovery storage and controlled failure/load fixtures

**Expected output:** Scoped GA acceptance report with 72-hour reliability and recovery evidence; Approved service objectives, runbooks, support owners and limitations
