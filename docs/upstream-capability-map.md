# Pinned Core-to-Cloud capability map

AF-CLD-003. Map schema 1; planning evidence inventory, **not product or release acceptance**.

The [machine-readable map](upstream-capability-map.json) covers all **67 Cloud tasks** and **42 AF-GC requirements**. It fixes one implementation owner, an upstream version, a reuse decision, evidence limitations and a concrete integration acceptance scenario for every Cloud capability. The original manifests retain their IDs, dependencies and proposed labels; live engineering claims remain in Core `team-state`.

## Versions and evidence boundaries

- Core baseline: [`d097ac0b04445183c647012a0c92a9d6348135b6`](https://github.com/HappyMiha/AgentFactory/tree/d097ac0b04445183c647012a0c92a9d6348135b6); [42-task manifest](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/examples/game-creator-backlog.json).
- Cloud planning baseline: [`720c79b3530cf2dddfd8b0351094a0763f757a63`](https://github.com/HappyMiha/AgentFactory-Cloud/tree/720c79b3530cf2dddfd8b0351094a0763f757a63); [67-task manifest](https://github.com/HappyMiha/AgentFactory-Cloud/blob/720c79b3530cf2dddfd8b0351094a0763f757a63/examples/agentfactory-cloud-backlog.json).
- Supported integration interface: **unqualified at this pin**. Godot, Unity and Unreal pack versions are **unknown**, represented by `null`. A Core commit is a reproducible source reference; it is not a supported engine/toolchain/profile declaration. AF-CLD-002/005/006 must establish those contracts and evidence.
- Every capability's `core_version` repeats the exact Core pin. `source-inventory` evidence identifies existing source and test definitions. Resolving these Git blobs does not execute the tests or demonstrate the described product behavior.
- The separate merged engineering records cover Core AF-GC-001 (portable CI), AF-GC-003 (confirmation behavior) and AF-GC-006 (effective model binding). They do not complete the full game journey, role qualification or Cloud integration. PR5 later made the Python matrix manual-only; skipped matrix jobs are not passing executions.
- The September product audit predates those three engineering repairs. Its unresolved consumer/engine/hosting findings remain relevant; its historical fixed-bug findings are not used to deny the recorded repairs.

`verified` would require accepted evidence for an exact supported version and profile. This snapshot contains **no verified Cloud capability**. `partial` means a reusable foundation or reviewed engineering repair exists but the listed integration remains unaccepted. `missing` means the required capability outcome lacks accepted implementation evidence at the baseline. `blocked` identifies an external prerequisite, currently console partner qualification. Missing evidence is not evidence that every related source module is absent.

Each `integration_test` is a concrete acceptance scenario with status `not-accepted`. This means no accepted result is supplied by this map; it does not assert that no one has ever attempted the test. Local map regression tests validate this planning artifact, not the games, providers, hosted deployment or commercial workflows in these scenarios.

## Ownership and reuse decisions

`implementation_owner` names the single destination of the capability, not the repository containing its historical task ID. `Core` owns neutral mechanisms; `Core.Packs` owns optional adapters/templates/target operations outside the scheduler. `Cloud.Platform`, `Cloud.Games`, `Cloud.Community` and `Cloud.Marketplace` are modules of one Cloud repository. Cloud remains the consumer and accepts its own integration.

For example, Cloud 011/014/052 consume Core-owned engine/validator/SDK work; they must not create a second engine implementation in Cloud. Cloud 053 consumes the Core Unity adapter, while the complete consumer Unity journey remains a Cloud acceptance reference. Implementation in another repository needs its own coordinated upstream claim, not an undeclared edit under a Cloud claim. The map assigns responsibility without creating new task IDs or taking ownership of future work.

Decisions mean: **reuse** an already sufficient contract after consumer qualification; **extend** an existing foundation in its owning repository; **migrate** Creator presentation responsibility to Cloud through supported Core contracts, preserving existing operator behavior; **build** a currently unqualified capability at the named owner. No row claims unconditional reuse is already sufficient. These decisions do not authorize deleting or moving current source.

Core retains scheduling, retries, provider execution, generic evidence, worktrees, accepted source identities and provenance mechanics. Cloud owns hosted account boundaries, customer policy, public release, legal-rights decisions and commerce. **AF-CLD-043 is the single shared Cloud rights-policy capability** used by export, remix, Community and Marketplace; those consumers do not each implement a competing rights service. Core provenance records do not establish legal title.

## Cloud traceability table

Full planned test scenarios, gaps and pinned evidence identifiers are in the corresponding JSON records. An empty upstream list means no direct AF-GC requirement implements that product outcome; the listed generic foundations may still be useful.

| Cloud task / capability | Implementation owner | Decision | Qualification | AF-GC references |
| --- | --- | --- | --- | --- |
| AF-CLD-001 — Agree on the Core and Cloud product boundaries | Cloud.Platform | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-002 — Define the shared data model and API contracts | Cloud.Platform | extend | partial | AF-GC-020, AF-GC-023, AF-GC-039 |
| AF-CLD-003 — Map Cloud work to the existing Core backlog | Cloud.Platform | build | missing | AF-GC-026, AF-GC-031, AF-GC-034, AF-GC-037 |
| AF-CLD-004 — Design separate Creator and Operator views | Cloud.Games | migrate | partial | AF-GC-003, AF-GC-004, AF-GC-007, AF-GC-024, AF-GC-025, AF-GC-040 |
| AF-CLD-005 — Define engine, build target, and game pack interfaces | Core.Packs | extend | partial | AF-GC-016, AF-GC-017, AF-GC-033 |
| AF-CLD-006 — Define evidence levels and release gates | Cloud.Platform | extend | partial | AF-GC-002, AF-GC-020 |
| AF-CLD-007 — Turn a plain-language idea into a Game Brief | Cloud.Games | extend | partial | AF-GC-005, AF-GC-008 |
| AF-CLD-008 — Keep the first playable version small | Cloud.Games | extend | partial | AF-GC-008, AF-GC-012 |
| AF-CLD-009 — Assemble a visible AI game team | Cloud.Games | extend | partial | AF-GC-006, AF-GC-041, AF-GC-042 |
| AF-CLD-010 — Prepare a small Godot 2D starter pack | Core.Packs | build | missing | AF-GC-016 |
| AF-CLD-011 — Connect a real Godot engine adapter | Core.Packs | build | missing | AF-GC-002, AF-GC-013, AF-GC-014, AF-GC-017 |
| AF-CLD-012 — Keep source versions and working game checkpoints | Core | extend | partial | AF-GC-020 |
| AF-CLD-013 — Connect live coding workers to game tasks | Core | extend | partial | AF-GC-019, AF-GC-041, AF-GC-042 |
| AF-CLD-014 — Check the rules of the generated game | Core.Packs | extend | partial | AF-GC-017 |
| AF-CLD-015 — Build a Web version and add Play | Cloud.Games | extend | partial | AF-GC-017, AF-GC-021 |
| AF-CLD-016 — Export a Windows game and the full source | Cloud.Games | extend | partial | AF-GC-017, AF-GC-037 |
| AF-CLD-017 — Turn play feedback into a change plan | Cloud.Games | extend | partial | AF-GC-022 |
| AF-CLD-018 — Create version 2, restore version 1, and try a private remix | Cloud.Games | extend | partial | AF-GC-020, AF-GC-022, AF-GC-035 |
| AF-CLD-019 — Show progress and enforce budget and stop controls | Cloud.Games | extend | partial | AF-GC-018, AF-GC-023 |
| AF-CLD-020 — Accept three real reference games | Cloud.Games | build | missing | AF-GC-026, AF-GC-040 |
| AF-CLD-021 — Add account boundaries, roles, and the 12+ access gate | Cloud.Platform | build | missing | AF-GC-025, AF-GC-039 |
| AF-CLD-022 — Use PostgreSQL for hosted state | Cloud.Platform | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-023 — Store source, builds, and assets as protected objects | Cloud.Platform | extend | partial | AF-GC-020, AF-GC-035 |
| AF-CLD-024 — Qualify server resources and register remote workers | Cloud.Platform | extend | partial | AF-GC-002, AF-GC-011, AF-GC-013, AF-GC-014, AF-GC-015, AF-GC-029 |
| AF-CLD-025 — Make hosted workflows survive restarts | Cloud.Platform | extend | partial | AF-GC-019, AF-GC-023 |
| AF-CLD-026 — Isolate agent and build jobs | Cloud.Platform | extend | partial | AF-GC-019, AF-GC-029 |
| AF-CLD-027 — Guide creators through AI connections | Cloud.Games | extend | partial | AF-GC-009, AF-GC-010, AF-GC-027, AF-GC-028, AF-GC-042 |
| AF-CLD-028 — Keep Cloud credentials outside game work | Cloud.Platform | extend | partial | AF-GC-010 |
| AF-CLD-029 — Enforce Cloud quotas and track usage | Cloud.Platform | extend | partial | AF-GC-006, AF-GC-018, AF-GC-023, AF-GC-030 |
| AF-CLD-030 — Provide the hosted Creator Portal | Cloud.Games | migrate | partial | AF-GC-003, AF-GC-004, AF-GC-007, AF-GC-024, AF-GC-025, AF-GC-040 |
| AF-CLD-031 — Serve protected playable builds | Cloud.Platform | build | missing | AF-GC-021, AF-GC-039 |
| AF-CLD-032 — Export a portable ownership package | Cloud.Games | extend | partial | AF-GC-035, AF-GC-037 |
| AF-CLD-033 — Add operations visibility and recovery drills | Cloud.Platform | extend | partial | AF-GC-023, AF-GC-038 |
| AF-CLD-034 — Accept the private Cloud alpha | Cloud.Platform | build | missing | AF-GC-026, AF-GC-039 |
| AF-CLD-035 — Add releases and visibility controls | Cloud.Community | build | missing | AF-GC-003, AF-GC-037 |
| AF-CLD-036 — Add creator profiles and libraries | Cloud.Community | build | missing | AF-GC-007 |
| AF-CLD-037 — Add game pages with browser Play | Cloud.Community | build | missing | AF-GC-021, AF-GC-024 |
| AF-CLD-038 — Add Discover, search and tags | Cloud.Community | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-039 — Add share links and embed controls | Cloud.Community | build | missing | AF-GC-037 |
| AF-CLD-040 — Add Remix and Fork with source history | Cloud.Community | extend | partial | AF-GC-020, AF-GC-035, AF-GC-037 |
| AF-CLD-041 — Add likes, bookmarks and basic play statistics | Cloud.Community | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-042 — Add age-aware moderation and reporting | Cloud.Community | build | missing | AF-GC-025, AF-GC-035 |
| AF-CLD-043 — Check asset origin and licences before release | Cloud.Platform | extend | partial | AF-GC-035 |
| AF-CLD-044 — Approve a limited public creator beta | Cloud.Community | build | missing | AF-GC-037, AF-GC-040 |
| AF-CLD-045 — Add seller setup and adult or guardian approval | Cloud.Marketplace | build | missing | AF-GC-025 |
| AF-CLD-046 — Add sale listings, prices and licence choices | Cloud.Marketplace | build | missing | AF-GC-035, AF-GC-037 |
| AF-CLD-047 — Add checkout through a payment provider | Cloud.Marketplace | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-048 — Add purchase access and the buyer library | Cloud.Marketplace | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-049 — Add the revenue ledger, fees and payouts | Cloud.Marketplace | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-050 — Add refunds, disputes and fraud review | Cloud.Marketplace | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-051 — Approve the marketplace release | Cloud.Marketplace | build | missing | AF-GC-025, AF-GC-035 |
| AF-CLD-052 — Publish an EngineAdapter SDK and compatibility tests | Core.Packs | extend | partial | AF-GC-016, AF-GC-017, AF-GC-033 |
| AF-CLD-053 — Qualify the Unity adapter | Core.Packs | build | missing | AF-GC-032, AF-GC-033, AF-GC-034 |
| AF-CLD-054 — Prove Unreal feasibility and qualify its adapter | Core.Packs | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-055 — Add Android builds and Google Play preparation | Core.Packs | build | missing | AF-GC-013, AF-GC-014, AF-GC-035, AF-GC-037 |
| AF-CLD-056 — Add Apple builds and App Store preparation | Core.Packs | build | missing | AF-GC-010, AF-GC-013, AF-GC-014, AF-GC-035, AF-GC-037 |
| AF-CLD-057 — Add Steam release preparation | Cloud.Games | build | missing | AF-GC-035, AF-GC-037 |
| AF-CLD-058 — Add a shared PC store packaging contract | Core.Packs | build | missing | AF-GC-037 |
| AF-CLD-059 — Plan optional console support behind partner approval | Cloud.Platform | build | blocked | AF-GC-010, AF-GC-013, AF-GC-014 |
| AF-CLD-060 — Approve the multi-engine and multi-target release | Cloud.Games | build | missing | AF-GC-034, AF-GC-036 |
| AF-CLD-061 — Package reusable Agent Teams and Factory templates | Core | extend | partial | AF-GC-006, AF-GC-041, AF-GC-042 |
| AF-CLD-062 — Add an optional marketplace for Factories and packs | Cloud.Marketplace | build | missing | AF-GC-035 |
| AF-CLD-063 — Let creators choose qualified models and team budgets | Cloud.Games | extend | partial | AF-GC-006, AF-GC-012, AF-GC-027, AF-GC-028, AF-GC-029, AF-GC-030, AF-GC-031, AF-GC-041, AF-GC-042 |
| AF-CLD-064 — Publish an API, SDK and signed webhooks | Cloud.Platform | extend | partial | AF-GC-039 |
| AF-CLD-065 — Qualify self-hosted and hybrid deployment | Cloud.Platform | extend | partial | AF-GC-011, AF-GC-015, AF-GC-027, AF-GC-028, AF-GC-029, AF-GC-030, AF-GC-031, AF-GC-038 |
| AF-CLD-066 — Explore a later non-game executable pack | Core.Packs | build | missing | None; Cloud/pack-specific outcome |
| AF-CLD-067 — Approve the defined general-availability scope | Cloud.Platform | build | missing | AF-GC-001, AF-GC-031, AF-GC-038, AF-GC-041, AF-GC-042 |

## Review of every upstream requirement

These are responsibility and evidence assessments at the pin. “Merged” means the identified engineering change was integrated with a review; it is not a product-release state. Proposed requirements are not promoted merely because a module or a similarly named historical task exists. Forward links in Cloud rows and reverse consumer links in the JSON must agree.

| Upstream task | Implementation owner | Engineering record | Evidence qualification | Cloud consumers |
| --- | --- | --- | --- | --- |
| AF-GC-001 | Core | merged | partial | AF-CLD-067 |
| AF-GC-002 | Core | planned | missing | AF-CLD-006, AF-CLD-011, AF-CLD-024 |
| AF-GC-003 | Core | merged | partial | AF-CLD-004, AF-CLD-030, AF-CLD-035 |
| AF-GC-004 | Core | planned | missing | AF-CLD-004, AF-CLD-030 |
| AF-GC-005 | Core | planned | missing | AF-CLD-007 |
| AF-GC-006 | Core | merged | partial | AF-CLD-009, AF-CLD-029, AF-CLD-061, AF-CLD-063 |
| AF-GC-007 | Cloud.Games | planned | missing | AF-CLD-004, AF-CLD-030, AF-CLD-036 |
| AF-GC-008 | Cloud.Games | planned | missing | AF-CLD-007, AF-CLD-008 |
| AF-GC-009 | Core | planned | missing | AF-CLD-027 |
| AF-GC-010 | Core | planned | missing | AF-CLD-027, AF-CLD-028, AF-CLD-056, AF-CLD-059 |
| AF-GC-011 | Core | planned | missing | AF-CLD-024, AF-CLD-065 |
| AF-GC-012 | Core.Packs | planned | missing | AF-CLD-008, AF-CLD-063 |
| AF-GC-013 | Core | planned | missing | AF-CLD-011, AF-CLD-024, AF-CLD-055, AF-CLD-056, AF-CLD-059 |
| AF-GC-014 | Core | planned | missing | AF-CLD-011, AF-CLD-024, AF-CLD-055, AF-CLD-056, AF-CLD-059 |
| AF-GC-015 | Core | planned | missing | AF-CLD-024, AF-CLD-065 |
| AF-GC-016 | Core.Packs | planned | missing | AF-CLD-005, AF-CLD-010, AF-CLD-052 |
| AF-GC-017 | Core.Packs | planned | missing | AF-CLD-005, AF-CLD-011, AF-CLD-014, AF-CLD-015, AF-CLD-016, AF-CLD-052 |
| AF-GC-018 | Core | planned | missing | AF-CLD-019, AF-CLD-029 |
| AF-GC-019 | Core | planned | missing | AF-CLD-013, AF-CLD-025, AF-CLD-026 |
| AF-GC-020 | Core | planned | missing | AF-CLD-002, AF-CLD-006, AF-CLD-012, AF-CLD-018, AF-CLD-023, AF-CLD-040 |
| AF-GC-021 | Cloud.Games | planned | missing | AF-CLD-015, AF-CLD-031, AF-CLD-037 |
| AF-GC-022 | Cloud.Games | planned | missing | AF-CLD-017, AF-CLD-018 |
| AF-GC-023 | Core | planned | missing | AF-CLD-002, AF-CLD-019, AF-CLD-025, AF-CLD-029, AF-CLD-033 |
| AF-GC-024 | Core | planned | missing | AF-CLD-004, AF-CLD-030, AF-CLD-037 |
| AF-GC-025 | Cloud.Games | planned | missing | AF-CLD-004, AF-CLD-021, AF-CLD-030, AF-CLD-042, AF-CLD-045, AF-CLD-051 |
| AF-GC-026 | Cloud.Games | planned | missing | AF-CLD-003, AF-CLD-020, AF-CLD-034 |
| AF-GC-027 | Core | planned | missing | AF-CLD-027, AF-CLD-063, AF-CLD-065 |
| AF-GC-028 | Core | planned | missing | AF-CLD-027, AF-CLD-063, AF-CLD-065 |
| AF-GC-029 | Core | planned | missing | AF-CLD-024, AF-CLD-026, AF-CLD-063, AF-CLD-065 |
| AF-GC-030 | Core | planned | missing | AF-CLD-029, AF-CLD-063, AF-CLD-065 |
| AF-GC-031 | Cloud.Games | planned | missing | AF-CLD-003, AF-CLD-063, AF-CLD-065, AF-CLD-067 |
| AF-GC-032 | Core.Packs | planned | missing | AF-CLD-053 |
| AF-GC-033 | Core.Packs | planned | missing | AF-CLD-005, AF-CLD-052, AF-CLD-053 |
| AF-GC-034 | Cloud.Games | planned | missing | AF-CLD-003, AF-CLD-053, AF-CLD-060 |
| AF-GC-035 | Core | planned | missing | AF-CLD-018, AF-CLD-023, AF-CLD-032, AF-CLD-040, AF-CLD-042, AF-CLD-043, AF-CLD-046, AF-CLD-051, AF-CLD-055, AF-CLD-056, AF-CLD-057, AF-CLD-062 |
| AF-GC-036 | Cloud.Games | planned | missing | AF-CLD-060 |
| AF-GC-037 | Cloud.Games | planned | missing | AF-CLD-003, AF-CLD-016, AF-CLD-032, AF-CLD-035, AF-CLD-039, AF-CLD-040, AF-CLD-044, AF-CLD-046, AF-CLD-055, AF-CLD-056, AF-CLD-057, AF-CLD-058 |
| AF-GC-038 | Core | planned | missing | AF-CLD-033, AF-CLD-065, AF-CLD-067 |
| AF-GC-039 | Core | planned | missing | AF-CLD-002, AF-CLD-021, AF-CLD-031, AF-CLD-034, AF-CLD-064 |
| AF-GC-040 | Cloud.Games | planned | missing | AF-CLD-004, AF-CLD-020, AF-CLD-030, AF-CLD-044 |
| AF-GC-041 | Core | planned | missing | AF-CLD-009, AF-CLD-013, AF-CLD-061, AF-CLD-063, AF-CLD-067 |
| AF-GC-042 | Core | planned | missing | AF-CLD-009, AF-CLD-013, AF-CLD-027, AF-CLD-061, AF-CLD-063, AF-CLD-067 |

## Evidence index

Source entries resolve at the Core baseline; engineering reviews retain their own merged version. Test-definition links below are **not new test execution reports**. Every evidence record includes its limitations in JSON.

| Evidence | Versioned source / review | Type |
| --- | --- | --- |
| ownership | [docs/core-cloud-backlog.md](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/docs/core-cloud-backlog.md), [docs/core-cloud-boundaries.md](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/docs/core-cloud-boundaries.md) | source-inventory |
| audit | [docs/product-audit-2026-09-05.md](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/docs/product-audit-2026-09-05.md), [examples/game-creator-backlog.json](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/examples/game-creator-backlog.json) | source-inventory |
| api | [src/agent_factory/api_contract.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/api_contract.py), [docs/api-contract.md](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/docs/api-contract.md) | source-inventory |
| storage | [src/agent_factory/tenant_storage.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/tenant_storage.py), [tests/test_tenant_storage.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_tenant_storage.py) | source-inventory |
| dialog | [src/agent_factory/static/app.js](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/static/app.js), [tests/test_dialog_confirmation.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_dialog_confirmation.py) | source-inventory |
| intake | [src/agent_factory/mission_intake.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/mission_intake.py), [tests/test_mission_intake.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_mission_intake.py) | source-inventory |
| environment | [src/agent_factory/environment_bootstrap.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/environment_bootstrap.py), [tests/test_environment.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_environment.py) | source-inventory |
| packs | [src/agent_factory/packs.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/packs.py), [tests/test_packs.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_packs.py), [src/agent_factory/validators.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/validators.py) | source-inventory |
| versions | [src/agent_factory/worktrees.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/worktrees.py), [src/agent_factory/candidate_changes.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/candidate_changes.py), [tests/test_worktrees.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_worktrees.py) | source-inventory |
| model | [src/agent_factory/application.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/application.py), [tests/test_model_binding.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_model_binding.py), [tests/test_reviewer_routing.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_reviewer_routing.py) | source-inventory |
| runtime | [src/agent_factory/worker_runtime.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/worker_runtime.py), [src/agent_factory/coding_delivery.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/coding_delivery.py), [docs/coding-delivery-loop.md](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/docs/coding-delivery-loop.md) | source-inventory |
| sandbox | [src/agent_factory/sandbox.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/sandbox.py), [tests/test_sandbox.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_sandbox.py) | source-inventory |
| control | [src/agent_factory/autonomous_authorization.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/autonomous_authorization.py), [src/agent_factory/execution_telemetry.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/execution_telemetry.py), [tests/test_execution_controls.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_execution_controls.py) | source-inventory |
| credentials | [src/agent_factory/credentials.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/credentials.py), [tests/test_credentials.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_credentials.py) | source-inventory |
| durable | [src/agent_factory/orchestration/temporal/workflows.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/orchestration/temporal/workflows.py), [tests/test_temporal_workflows.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_temporal_workflows.py) | source-inventory |
| recovery | [src/agent_factory/chaos_recovery.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/src/agent_factory/chaos_recovery.py), [tests/test_chaos_recovery.py](https://github.com/HappyMiha/AgentFactory/blob/d097ac0b04445183c647012a0c92a9d6348135b6/tests/test_chaos_recovery.py) | source-inventory |
| ci-merged | [Engineering review](https://github.com/HappyMiha/AgentFactory/pull/3) at `b1b477916c479e59fbf579259526350910efec1d` | merged-engineering-review |
| dialog-merged | [Engineering review](https://github.com/HappyMiha/AgentFactory/pull/2#issuecomment-5554477771) at `f1a78c154d4e127620143a059f3dbb6d3033ef07` | merged-engineering-review |
| model-merged | [Engineering review](https://github.com/HappyMiha/AgentFactory/pull/4#issuecomment-5554417635) at `4a50bcc3ca4ea3c72027d1a163f4eb0a7142835e` | merged-engineering-review |

## Milestone-specific acceptance links

These are evidence references, **not executable scheduling dependencies**:

- **AF-GC-026 → Godot:** AF-CLD-020 demonstrates the real reference-game journey; AF-CLD-034 adds hosted tenant and operational qualification. Core lower-level capabilities are accepted independently before Cloud integrates them. Do not demand an already accepted duplicate Godot journey as a prerequisite for the Cloud journey that supplies its evidence.
- **AF-GC-031 → local/hybrid:** AF-CLD-063 qualifies offered model/routing choices and AF-CLD-065 qualifies deployment/data placement. Neither blocks the first Cloud-first Godot result. Local-only must prove no cloud egress.
- **AF-GC-034 → Unity:** AF-CLD-053 qualifies its adapter and AF-CLD-060 accepts the advertised multi-engine matrix. Unity does not block Godot or require blanket completion of all AF-GC tasks.
- **AF-GC-037 → export/share:** AF-CLD-016 covers the initial Windows/source export, AF-CLD-032 the portable ownership package, and AF-CLD-039 explicit sharing controls. Private export is not public publication.

Cloud executable dependencies remain exactly its canonical manifest. Upstream dependency edges remain references within the upstream manifest. There is no reverse Core scheduling edge to Cloud release acceptance. The validator checks both DAGs, rejects foreign executable dependencies and checks that the first Godot gate has no later-phase prerequisite. The original AF-GC dependencies are preserved for audit; the bridge does not turn their whole transitive closure into a new Cloud scheduler barrier.

Do not add `AF-CLD-040 → AF-CLD-043`: the manifest already has `043 → 040`. Remix must validate its input rights through the common policy contract; the later provenance/release qualification integrates those checks. The signed GA scope, not this map, determines conditional commerce/target/console/non-game release gates.

## Unresolved integrations

Every capability has its own unresolved gap and required acceptance scenario. Cross-cutting issues are:

- **version-contract** — Cloud.Platform; AF-CLD-002, AF-CLD-005, AF-CLD-006. Agree versioned API/engine/target/evidence contracts, select actual pack versions and pin accepted integration results; this map cannot grant readiness.
- **godot-delivery** — Cloud.Games; AF-CLD-010, AF-CLD-011, AF-CLD-013, AF-CLD-020. Complete Core-owned packs/delivery with their own evidence, then accept real Godot consumer games. Do not wait for Unity or require the same journey twice.
- **hosted-isolation** — Cloud.Platform; AF-CLD-021, AF-CLD-022, AF-CLD-024, AF-CLD-026, AF-CLD-034. Qualify real server resources, PostgreSQL, tenant/account/age boundaries, secret protection and hostile workloads; local SQLite contracts and server availability do not qualify hosting.
- **rights-policy** — Cloud.Platform; AF-CLD-032, AF-CLD-040, AF-CLD-043, AF-CLD-046. Use one Cloud rights decision service with source/asset provenance. Core owns neutral digest/lineage mechanics, not legal rights. Check remix inputs without adding 040 -> 043 and creating a cycle.
- **optional-targets** — Core.Packs; AF-CLD-053, AF-CLD-054, AF-CLD-055, AF-CLD-056, AF-CLD-058, AF-CLD-059, AF-CLD-065. Obtain actual engine/toolchain/hardware/partner evidence only for supported profiles. Local-only requires no-egress proof; Unity and console remain outside the first Godot gate.
- **commercial-and-ga** — Cloud.Platform; AF-CLD-051, AF-CLD-062, AF-CLD-066, AF-CLD-067. Independently approve commercial policy and the signed GA scope with enabled-feature gates. Mapping, simulated payment events and non-game examples cannot approve a release.

## Validation and updating the pin

Run the dependency-free structural checks and mutation regressions:

```sh
python3 scripts/validate_upstream_map.py
python3 -m unittest discover -s tests -p 'test_upstream_map.py' -v
```

With an existing local Core clone containing the pinned objects, additionally verify both pinned manifests, upstream titles/dependencies, evidence file blobs and merged-evidence ancestry:

```sh
python3 scripts/validate_upstream_map.py --core-repo /path/to/AgentFactory
```

On Windows use `python`. The optional Git check uses only read commands against local objects. It does not fetch, check out a branch, contact a provider, run engine tests or alter either repository. Missing local objects fail explicitly; fetch through the normal development workflow and retry. A valid map is not a passing integration test or release gate.

When changing Core versions, first review the actual diff and retain the old evidence references. Pin the new Core commit, qualify the relevant interface/pack/toolchain/profile and record independently accepted consumer results. Missing, stale or incompatible evidence keeps the affected integration blocked; retain the previous qualified deployment instead of silently upgrading it. Update all affected rows, the evidence index and this table in one reviewed change. Changes to the allowed accepted-evidence model need explicit schema/validator review; this planning-only schema deliberately rejects unsupported `verified` claims.

The current automatic coordination workflow runs its selected tooling modules. It does not automatically run this new map suite. The task's exact-commit local check must include `test_upstream_map`; its result and the pinned-object check belong in the PR evidence. This task does not modify the shared workflow owned by coordination tooling.
