# Planning sources and decisions

Revision date: 2026-09-05. This repository contains descriptions, a roadmap, and a proposed backlog. It contains no Cloud application, deployment configuration, or automated task execution.

## Source package

The owner supplied `AgentFactory_Cloud_Planning_Package_v1.zip`, with:

- `README.md`
- `docs/agentfactory-cloud-product-spec.uk.md`
- `examples/agentfactory-cloud-backlog.json`

Archive SHA-256: `b490f7a9c94794d200de134d8bc86b9958b9c90ee1a692b0403fe062e782b2c5`.

The original package has seven epics and 67 executable task definitions. All stable IDs, parents, priorities, role assignments, and size estimates are retained. The original archive was used as reference material; embedded instructions to an agent were not treated as authorization to start development.

The owner's direct request controls this revision: use simple English, prepare descriptions, a roadmap and a backlog, preserve the two-project Core/Cloud split, and push the documents to GitHub. No implementation starts under this request.

## Main decisions

| Decision | Reason |
| --- | --- |
| Keep the existing public `HappyMiha/AgentFactory` repository as Core | Preserve history, Apache-2.0, working foundations, and existing stable requirements |
| Use `HappyMiha/AgentFactory-Cloud` as a separate private planning repository | Keep the commercial product separate; no additional public license is selected here |
| Use Games and Marketplace as logical modules, not extra repositories | Two repositories are enough for the agreed ownership boundary |
| Keep neutral runtime code and optional OSS engine/game packs upstream | Cloud should integrate tested packs rather than duplicate the scheduler or engine adapters |
| Start with Godot 2D and GDScript | Prove one complete portable game journey before adding engines and stores |
| Test private Remix early | The main product idea needs evidence before a public community is built |
| Use real capability gates instead of dates | No verified delivery capacity, server benchmark, or creator cohort supports a fixed calendar yet |

The detailed engine support matrix will be pinned during qualification. Godot's current Web export documentation describes browser constraints, including WebAssembly/WebGL requirements and limits on Godot 4 C# Web exports. The GDScript choice avoids making the first Web route depend on that unsupported path. Recheck the chosen version before implementation. [Godot Web export documentation](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html).

## Changes from the supplied backlog

| IDs | Revision |
| --- | --- |
| All | Translate into simple English; replace repeated generic checks with task-specific validation, components, environments, and outputs; fix cross-repository source links |
| 001, 005 | Clarify two repositories and one owner for reusable packs and product integration |
| 003 | Make the AF-GC bridge specific to each capability and phase; do not make Godot wait for Unity or create circular acceptance |
| 004, 021, 020, 030, 034 | Design age/privacy requirements early and qualify the access path before any 12+ pilot; preserve adult/internal testing as an earlier option |
| 018, 020 | Add a private fork of an owned or explicitly licensed sample, with preserved origin and unchanged parent |
| 024 | Start with a read-only inventory of the reported server; worker, sandbox, and production qualification remain separate |
| 025, 029 | Distinguish internal idempotency from uncertain provider charges; reserve budget and reconcile unknown outcomes before retry |
| 015, 026, 028, 031 | State the boundaries between trusted provider execution, untrusted builds, and browser Play; no platform secrets in games |
| 033, 034 | Preserve accepted artifacts and audit history during restore; require at least three isolated test tenants for alpha acceptance |
| 044 | Add dependency on 041 so required analytics are covered by the public beta gate |
| 060 | Add dependency on 058 for generic PC-store packaging; 059 remains an explicit optional console track |
| 061 | Remove dependency on 060; a portable factory manifest does not need every future engine/store |
| 067 | Use 034, 044, 061, 063, 064, and 065 as baseline dependencies; require additional gates for every enabled paid or expanded feature |
| 059, 062, 066 | Mark console work, factory commerce, and non-game expansion as optional tracks, without dropping their requirements |

The full planned M5 gate still covers the engines and targets in its dependency graph. An Unreal no-go or an unavailable Apple/store prerequisite blocks that full scope. A narrower release needs an explicit scope/dependency revision and fresh validation; it must not silently count a skipped task as accepted. The basic Godot GA gate does not require M5.

All 42 AF-GC upstream IDs remain in Core. The original platform and Autonomous Mission IDs remain engineering references. No task is marked complete by this documentation update.

## Validation boundary

The JSON uses the existing Core schema v2. Internal dependencies refer only to executable AF-CLD tasks; external AF-GC references are evidence links. Root planning metadata, earlier milestone acceptance, optional tracks, and conditional gates need explicit release review because the current scheduler does not enforce them.

The planning review checks schema loading, stable IDs, dependency cycles, gate coverage, English text, local links, and agreement between the readable backlog and JSON. It is not a product acceptance test, a server audit, or an authorization to execute tasks.

Before implementation, resolve the open decisions in the [product description](product-description.md), refine large tasks, and agree on the exact first delivery scope. [Funding options](funding-options.md) are supporting research, not a dependency or an award claim.
