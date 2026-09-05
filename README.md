# AgentFactory Cloud

**Planning only. No Cloud application or deployment has been built as part of this work.**

**Three-computer development:** [team workflow](docs/team-workflow.md) · [live shared task register](https://github.com/HappyMiha/AgentFactory/blob/team-state/team-state.json). Each worker claims a task and uses an owned branch with checks before push and a pull request into `main`.

AgentFactory Cloud is a planned game creation platform powered by [AgentFactory Core](https://github.com/HappyMiha/AgentFactory).

A creator will describe a game, agree on a small first version, let an AI team build and test it, play the result and ask for changes. The creator should receive the source project and supported builds to use outside AgentFactory.

**The first proof:** Godot 2D + GDScript → browser Play → Windows/source download → feedback → verified v2 → rollback.

**The wider product loop:** Play → Remix → Create → Publish → Play.

## Two projects

- **Core:** the existing Apache-2.0, provider-neutral orchestration engine. It remains usable without Cloud.
- **Cloud:** the commercial creator experience, hosted execution, game delivery, publishing and later commerce.

Games, Community and Marketplace are modules within Cloud. They are not additional repositories. Core owns shared engine-neutral contracts and optional open-source game, engine and target packs outside its neutral runtime. Cloud's Games module uses those packs for the creator experience, project settings, play feedback and release policies; it does not build a second set of adapters.

The intended audience includes creators aged 12+ and adults. Actual access, public sharing and commerce depend on a qualified age/guardian, privacy and provider-permission model. The first internal pilot can use adults until those requirements are met.

## Read the plan

1. [Product description](docs/product-description.md) — users, journeys, MVP, architecture, Remix, safety and economics.
2. [Roadmap](docs/roadmap.md) — M0–M6 with evidence-based release gates.
3. [Backlog](docs/backlog.md) — readable tasks and acceptance criteria.
4. [Machine-readable backlog](examples/agentfactory-cloud-backlog.json) — seven epics and 67 stable AF-CLD tasks, schema v2.

The plan is based on the owner's supplied Cloud planning package. It extends the 42 AF-GC tasks in Core and preserves their upstream role. All new work remains **proposed**. A task entry or valid JSON file is not evidence of implementation and does not authorize coding.

The [Core/Cloud responsibility contract](docs/core-cloud-boundary.md) adds the AF-CLD-001 ownership map, rights records and design walkthroughs. It remains subject to integration and owner review.

## Scope and evidence

Start with a small reliable Godot game. Add hosted multi-tenancy next, then public publishing and Remix, then qualified commerce. Other engines, stores, factory templates and hybrid profiles require separate evidence before they are called supported.

The owner reports that a server is available. This plan does not claim a verified deployed game pipeline, customers, revenue or funding. The candidate domain `agentfactory.ai`, CHF 15/39/99 subscription examples and 10–30% marketplace fee remain hypotheses.

Cloud is a separate public repository for a planned commercial product, made public at the owner's request. Public visibility does not select a software license. Cloud license terms remain an owner decision; Core keeps Apache-2.0.
