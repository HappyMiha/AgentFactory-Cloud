# Roadmap

**Date:** 2026-09-05

**Status:** Proposed. Documentation only; implementation has not been authorized by this planning package.

This roadmap keeps the owner-supplied seven milestones, seven epics and 67 stable AF-CLD task IDs. It extends the 42-task AF-GC plan in Core. It does not mark that upstream work complete.

The sequence is:

**M0 contracts → M1 real Godot game loop → M2 private hosted alpha → M3 publishing and Remix → M4 commerce → M5 more engines and stores → M6 factory ecosystem**

Milestones are capability gates, not calendar promises. The source package contained rough timing ideas; there is not enough verified delivery capacity, server evidence or benchmark data to turn them into commitments. Re-estimate after M0 and M1. The sequence shows the product expansion order; it is not a rule that scoped GA must include every optional expansion. Paid commerce and later engine support may remain deferred without invalidating a successful Godot product.

## 1. Milestone map

| Milestone | Scope | Tasks | Exit gate |
| --- | --- | --- | --- |
| M0 | Product boundary, domain model, upstream bridge, UI split and shared contracts | AF-CLD-001–006 | All six tasks accepted |
| M1 | Godot 2D: idea → Play → export → feedback → v2 → rollback | AF-CLD-007–020 | AF-CLD-020 |
| M2 | Private hosted alpha with accounts, isolated workers, storage and budget control | AF-CLD-021–034 | AF-CLD-034 |
| M3 | Public/unlisted release, Discover, safe sharing, Remix and moderation | AF-CLD-035–044 | AF-CLD-044 |
| M4 | Qualified sellers, listings, purchases, buyer access and reconciled payouts | AF-CLD-045–051 | AF-CLD-051 |
| M5 | Adapter SDK, qualified engines and external distribution targets | AF-CLD-052–060 | AF-CLD-060 |
| M6 | Factory templates, API, hybrid profiles and a possible first non-game product | AF-CLD-061–067 | AF-CLD-067 |

P0 means a blocker within the task's milestone. A P0 payment task does not outrank the earlier P0 first-game proof. Size S/M/L is a planning estimate, not an elapsed-time promise; split large tasks into reviewable work before implementation.

## 2. M0 — agree on the product and prove the bridge

**Purpose:** Decide what belongs where and identify what can actually be reused.

Recommended first batch:

**AF-CLD-001 → 002 → 003 → 005 → 006 → 004**

This order is a practical review sequence; the machine-readable internal dependencies remain authoritative.

Deliverables:

- A two-repository decision: neutral open-source Core with optional game/engine/target packs; commercial Cloud with Games and Marketplace modules that use those packs.
- A domain/API resource model for briefs, runs, source versions, builds, checkpoints, releases, rights and later commerce.
- A capability bridge to the existing AF-GC tasks and Core code. Mark each dependency verified, partial, missing or blocked.
- EngineAdapter, TargetAdapter and GamePack contracts, including versioning, compatibility and failure behavior.
- One pack/adapter implementation owner in Core, outside the neutral scheduler. Cloud owns hosted integration and game-product behavior; it does not duplicate the adapters in its Games module.
- Separate Creator and Operator journeys. The creator should see a game, progress, budget and next action; the operator needs jobs, leases and incidents.
- An evidence ladder and release rules. Define exactly when “Ready,” “Supported” and “Accepted” may be used.

The design review also records launch-country and age/guardian questions, model-route permissions, minimum safety controls, license ownership and cost assumptions. Identify owners for unresolved decisions.

Create a server evidence inventory from information the owner chooses to provide: hardware, OS, storage, network, access model, existing services, backups and capacity. Do not access or change a server as part of this documentation task. Server availability remains separate from proof of the game pipeline.

**Exit:** Every M0 decision has an owner, acceptance evidence or explicit blocker. Core consumers have a stated version/evidence requirement. No marketplace or multi-engine implementation begins.

## 3. M1 — prove the first real game loop

**Purpose:** Demonstrate value before scaling infrastructure or building a public platform.

Main streams:

| Stream | Tasks | Result |
| --- | --- | --- |
| Idea and scope | 007–008 | Editable Game Brief and a small first-playable plan |
| Game team and engine | 009–011, 013–014 | Optional Core Godot/role packs, live coding route and real validators integrated into the Cloud game journey |
| Versions and outputs | 012, 015–016 | Last known good source/build, browser Play, Windows and source export |
| Feedback and control | 017–019 | Version-linked change request, v2, rollback, a private licensed-sample fork, budget and Pause/Resume/Stop |
| End-to-end acceptance | 020 | Three reference games accepted on a clean supported environment |

Use Godot + GDScript, small 2D games, a supported Windows host path, one qualified coding route and an independent reviewer. A platformer, top-down collection game and simple puzzle are a proposed reference set to define before testing.

Cloud task IDs describe product outcomes across the two repositories. Generic or optional open-source pack/adapter work is implemented once in Core through the AF-GC capability bridge; Cloud work implements the creator-facing integration. A Cloud backlog ID is not a rule that every changed file must live in Cloud.

Before any real model/build execution, verify upstream credential isolation, provider entitlement, bounded budget, review independence, workspace safety and minimum sandbox behavior. If these foundations are missing, fix the upstream blocker first. The later multi-tenant milestone does not waive them.

M1 uses an adult/internal cohort unless the age/guardian and privacy path has already been qualified. AF-CLD-004 defines those requirements; AF-CLD-021 must prove hosted access controls before a minor pilot.

**Exit evidence for AF-CLD-020:**

1. A new creator describes a small game without JSON, CLI or task IDs.
2. The creator agrees to the brief, scope and hard limit.
3. A real qualified coding worker changes source.
4. Godot imports the project; required validators and independent review pass.
5. Browser Play works with the stated controls.
6. The Windows package runs and the source opens outside AgentFactory.
7. Feedback identifies the build played; a verified v2 changes the requested behavior.
8. v1 remains playable and can be restored with matching source/assets.
9. Stop, reconnect, worker restart and a failed build preserve the last good version and do not duplicate an accepted action or charge.
10. All three reference games complete the same journey.
11. Provider/model identity, source/build digests, cost and test levels are truthful.
12. The owner plays the results and accepts the demonstrated limits.

AF-CLD-018 also tests a small private fork of an owned or explicitly licensed sample: preserve its parent version, request a change, build and play the derivative, and keep both originals. This gives early evidence for the Remix idea without opening public community content. Full public Remix, rights enforcement and moderation remain in M3.

Measure time, cost and repair rate now. Choose later SLOs from these results. A simulation, headless unit test or agent success message does not pass this gate.

## 4. M2 — move the proven loop into a private Cloud alpha

**Entry:** M1 is accepted. Earlier schema/security design may be done in parallel when dependencies allow; do not let broad hosting work replace the first playable proof.

Delivery areas:

- **Identity and state:** AF-CLD-021–023 — tenant roles, durable state and private object storage.
- **Execution:** AF-CLD-024–026 — remote worker registration, fenced job leases, durable workflows and isolated runners.
- **Providers and budget:** AF-CLD-027–029 — a clear connection wizard, cloud credential broker, quotas and cost accounting.
- **Creator delivery:** AF-CLD-030–032 — hosted portal, signed artifact delivery and an ownership/export package.
- **Operations:** AF-CLD-033 — redacted support information, observability, backup and tested restore.
- **Acceptance:** AF-CLD-034.

The owner-supplied architecture proposes PostgreSQL, object storage and Temporal. Select a versioned hosted profile and validate it; their names alone do not prove readiness.

Cloud controls must include tenant checks on source, jobs, previews and artifacts; a separate untrusted game origin; bounded upload/compute/network use; and quarantine before atomic artifact promotion. API/provider keys never enter games or downloadable output.

Alpha participants are deliberately limited. The source package suggested 10–30 creators; treat this as a capacity hypothesis, not an existing cohort or recruitment result. Start smaller if support or verified resources require it. Minors join only after the age/guardian/data plan is approved; an adult pilot can proceed independently.

Baseline content and asset controls apply to the closed pilot. Use owned/licensed starters, a reporting path and an operator stop mechanism. Do not wait for public beta to address a known unsafe private build.

**Exit evidence for AF-CLD-034:**

- Real creators complete the M1 loop through the hosted portal.
- Cross-tenant, secret leakage, stale worker and resource-limit tests pass.
- Refresh, retry, cancel and worker failure are reconciled without double charging.
- Private source export and preview authorization are correct.
- A backup is restored into an isolated environment; the project can be played again.
- Cost, queue delay and support needs are measured with synthetic traffic excluded.
- The owner accepts a documented participant limit, known constraints and incident plan.

## 5. M3 — add public creation, discovery and Remix

**Entry:** Private Cloud alpha is accepted.

Delivery areas:

- AF-CLD-035–039: immutable releases, visibility, creator libraries, game pages, Discover, links and embed controls.
- AF-CLD-040: versioned Remix into a new authorized workspace.
- AF-CLD-041: likes, bookmarks and honest play analytics.
- AF-CLD-042–043: moderation, reporting, asset provenance and license checks.
- AF-CLD-044: public creator beta acceptance.

Public release is a separate gate from successful generation. Keep the first catalog curated. Add moderation before opening new content to unknown players.

The source task order can build Remix mechanics before the full license system exists. Test those mechanics only with owned/licensed fixtures. Public Remix stays disabled until both rights and moderation gates pass. A task's internal dependency list is not permission to publish early.

**Required Remix behavior:** select a source release that grants the required rights; preview change scope and budget; create a new workspace; preserve immutable parent lineage and asset attribution; build and play privately; publish only after a separate decision. Private parent credentials and unrelated versions never cross into a fork.

Withdrawal and takedown rules must distinguish ordinary parent removal from a rights violation. The service must locate affected descendants, decide their access based on the license, retain required evidence and allow review. Unknown or incompatible rights block Publish/Sell.

**Exit evidence for AF-CLD-044:**

- Private/unlisted/public behavior is clear and enforced, including links, embeds and cache behavior.
- An incomplete publish cannot replace the last good release; removal has a tested access outcome.
- Play → Remix → Create → Publish → Play works on permitted content with correct lineage.
- Report, moderation review, urgent removal and appeal paths work.
- Age-appropriate exposure and profile privacy match the approved audience.
- Analytics separate real players from tests, bots and demo counters.
- Public capacity, on-call ownership and response procedures are accepted.

Marketplace payments, chat and broad social networking remain out of scope.

## 6. M4 — introduce money only after trust and economics

**Entry:** Public beta is accepted; launch jurisdictions, seller eligibility, licenses, payment responsibilities and unit economics have explicit decisions.

- AF-CLD-045: adult/guardian/business seller eligibility and onboarding.
- AF-CLD-046: listings, price presentation and versioned license products.
- AF-CLD-047–048: qualified payment integration, buyer entitlement and library.
- AF-CLD-049–050: revenue ledger, fees, payouts, refunds, disputes and fraud controls.
- AF-CLD-051: marketplace acceptance.

Free access, subscriptions, AI credits and purchased games have separate entitlements. If paid subscriptions or credit purchases are introduced before game sales, they still require the relevant payment, age, tax, ledger, refund and cost gates. M2 quota accounting alone is not permission to take money.

The suggested CHF 15/39/99 plans and 10–30% fee are hypotheses. Set prices only after measuring model/build/storage/delivery/support/moderation costs. Grants and free provider credits should be shown separately from normal operating economics.

**Exit evidence for AF-CLD-051:**

- Ineligible sellers and unsupported jurisdictions are blocked with a clear explanation.
- Buyers know what license, version and access they purchase.
- Replayed payment callbacks and retries do not create a second charge, credit or entitlement.
- Refunds and chargebacks reconcile access, platform fees, creator balances and payout reserves.
- Ledger totals reconcile to payment-provider records and seller statements.
- Fraud and rights disputes have responsible operators and tested handling.
- A limited paid launch is accepted on measured cost and support capacity.

Do not infer a royalty obligation from Remix lineage. Creator shares for derivative work require agreed license terms.

## 7. M5 — qualify each engine and distribution target

**Entry:** The Godot product and shared contracts are stable. Begin SDK design when upstream dependencies allow; release each new capability only after its own qualification.

- AF-CLD-052: EngineAdapter SDK and conformance suite.
- AF-CLD-053: Unity qualification.
- AF-CLD-054: Unreal feasibility review, followed by qualification only if feasible.
- AF-CLD-055–056: Android/Google Play and macOS/iOS/App Store preparation.
- AF-CLD-057–058: Steam and generic PC-store packaging.
- AF-CLD-059: partner-gated console research and qualification.
- AF-CLD-060: multi-engine/multi-target acceptance.

Every supported matrix row needs a pinned engine/toolchain version, worker OS, target, reference project, license/account prerequisites, build evidence and real run evidence. Mobile signing credentials need a scoped path. Store upload remains separate from store approval.

The currently planned full M5 gate requires AF-CLD-052 through AF-CLD-058: the SDK, Unity, Unreal, Android, Apple targets, Steam and generic PC packaging. AF-CLD-059 console work is optional. A no-go for a required engine or target leaves the full M5 gate blocked; finishing a feasibility report does not satisfy its missing qualification.

A narrower M5 release requires a recorded scope decision, an explicit revision of dependency and acceptance requirements, and renewed backlog validation. Preserve the source task IDs and record what remains deferred or blocked. Do not silently pass the original broad gate by publishing a shorter compatibility table.

Console work can end in a documented no-go without blocking M5. It depends on platform-holder access and qualified hardware; it is not a generic exporter promise, and no console shipping claim is allowed without actual qualification.

**Exit:** The accepted support matrix states exactly which engine/target combinations work and which are experimental, deferred or blocked. Existing Godot workflows still pass.

## 8. M6 — expand into a factory ecosystem

**Entry:** A game product has demonstrated real user value, reliable operation and a qualified support envelope.

- AF-CLD-061–062: publishable AI-team/factory templates and a pack marketplace.
- AF-CLD-063–064: advanced routing/budgets and public API/SDK/signed webhooks.
- AF-CLD-065: qualified self-hosted and hybrid deployment.
- AF-CLD-066: a possible first non-game executable product.
- AF-CLD-067: general-availability acceptance.

General availability is a separate reliability gate for the accepted support scope. Factory commerce (062) and a non-game product (066) are optional expansion tracks, not automatic prerequisites for a reliable game-product GA. Preserve their IDs and defer them explicitly if their own demand or readiness gates fail.

The current AF-CLD-067 gate requires 034, 044, 061, 063, 064 and 065. Factory templates in 061 depend on 009 and 052; they do not require the full M5 release. The signed GA scope must also apply conditional gates: paid marketplace needs 051, expanded engine/store support needs 060, factory commerce needs 062, a non-game offering needs 066, and any console claim needs actual 059 qualification. A limited GA cannot advertise features whose conditional gates have not passed.

Templates are executable supply-chain inputs. Require declared permissions, tools, licenses, versions, provenance and checks; a signature does not prove a template is safe. Buying a pack does not authorize its tools to publish, spend or access secrets.

A local or hybrid route needs device pairing, revocation, resource checks, a verified tool/model installation plan and clear behavior when a device goes offline. It must not silently send private work or keys to Cloud as a fallback.

Do not add a non-game product simply to complete the list. Choose it only when game results and an independent demand case justify it. No unrelated named product is part of this roadmap.

**Exit:** The supported product scope, operations, economics, compatibility and limits are published and accepted. General availability applies to that defined scope; it does not mean every engine, device or arbitrary task is supported.

## 9. Dependency and evidence rules

The [machine-readable backlog](../examples/agentfactory-cloud-backlog.json) owns internal dependency links. The [human backlog](backlog.md) provides a readable review surface. Stable IDs are retained from the supplied package.

AF-CLD-003 links Cloud work to upstream AF-GC requirements, including the full Godot path, local/hybrid qualification, Unity qualification and export/share. Core remains the source of those earlier tasks. There should be one implementation owner per capability, not two copies built independently.

Apply these upstream requirements by phase and feature. A Godot-only milestone must not wait for future Unity or hybrid qualification that it does not use. A new engine or local route must not inherit Godot's qualification merely because it shares the same adapter interface.

The current loader cannot enforce cross-repository readiness. Before starting a dependent task, record the upstream task/contract, repository, verified commit, evidence, owner and date. A completed planning document, placeholder component or passing schema check does not satisfy an implementation gate.

For every release decision:

1. Check internal dependencies and external capability evidence.
2. Define the exact supported scope and failure/recovery cases.
3. Keep producer and independent reviewer identities separate.
4. Map evidence to each acceptance criterion.
5. Include a real owner playtest where the gate concerns a game.
6. Record accepted limits and remaining blockers.
7. Obtain a separate decision for publish, payments, store submission or other external actions.

All tasks remain **proposed** in this planning revision. This work creates no application, deployment, payment integration or automatic task execution.
