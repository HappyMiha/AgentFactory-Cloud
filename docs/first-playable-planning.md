# Plan a small first playable

Task: `cloud:AF-CLD-008`. This adds a working scope-planning step to the
[local game-idea editor](game-brief-intake.md). It creates a proposal from a saved
brief, preserves the original source and separates the first milestone from
the longer-term roadmap. It makes no AI calls and starts no development.

## Creator flow

1. Save an idea and its editable brief. Choose **Plan the first playable version**.
2. Create a draft. The proposal uses a small template, so check its assumptions.
3. Edit the goal, controls, winning rule, visual direction, assumptions,
   exclusions and future roadmap. Choose the engine and target for this slice.
4. Save to refresh the six leaf tasks, their checks and the estimated AI usage.
5. Read the estimate and limitations, then agree to the saved scope. The
   confirmation records this version only. Development, spending and publishing
   still need their own readiness checks and authority.

There is one plan history per brief. New drafts, edits and agreements append
immutable versions. New drafts from a changed brief retain old plan versions.
Two tabs cannot silently overwrite each other. A stale edit stays on screen;
load the latest version or copy the edit before continuing. Internal navigation
asks before discarding edits. Unsaved text is not a backup and can be lost if
the browser is closed or refreshed.

If the brief changes, the old plan is marked stale and cannot be agreed to or
edited as if it described the new brief. Create a new draft explicitly. Every
plan version records the brief revision/checksum and original source checksum.
The source itself is never rewritten by scope planning.

## Capability boundary

`small-2d-scope-v1` is a planning template with one player, one 2D room, one
playable goal and a Windows or web target. Its fixed machine-readable limits
exclude online multiplayer, new agentic runtime systems and public publishing.
Editing the text of an exclusion does not add a supported capability.

The only proposed route is Godot 2D / GDScript. Unreal, Unity and another engine
can be selected to preserve intent, but scope agreement is blocked for them.
The interface offers a separate small Godot slice; the creator must choose
that alternative explicitly. Actual Godot, worker, toolchain and model
qualification remain pending: every result has `execution_ready: false`.
This template is not an engine adapter and does not duplicate Core's adapter
or evidence authority. It consumes the engine/target distinctions established
by Cloud005 without turning synthetic capability contracts into live evidence.

Simple English/Ukrainian word hints identify examples such as multiplayer,
MMORPG, open-world and AAA requests. A large request receives a proposed
one-room marker-collection goal with explicit assumptions and exclusions. The
original vision and editable future roadmap remain separate. A goal that
still mentions these unsupported features blocks agreement. Empty essential
fields and unsupported target values are also rejected.

This is bounded template planning, not general language understanding or a
proof that an arbitrary request is feasible. Word hints do not cover every
language, synonym or contradiction. A creator/reviewer must check whether the
proposed goal is coherent and fits the fixed limits. Game-specific design,
independent review and actual build/play evidence remain downstream work.

## Actionable work and budget estimate

The plan has six leaf tasks with dependency order: project, player controls,
goal/win rule, readable level, playtest, and target package. Acceptance checks
include the chosen goal, controls and win rule, an incomplete attempt, reset
and replay, asset rights, and the exact packaged build outside the editor.
These are future checks to execute, not passing test receipts. Cloud009 will
bind tasks to a qualified AI team; this feature creates no agent grant or run.

The budget basis `synthetic-small-slice-usage-v1` is explicit:

| Assumption | Value |
| --- | --- |
| Leaf tasks | 6 |
| Input per attempt | 2,000 tokens |
| Output per attempt | 600 tokens |
| Attempts per task | 1–2 |
| Estimated usage | 15,600–31,200 tokens |
| Initial editable allowance | 40,000 tokens |
| Paid API fee on the local-model assumption | CHF 0.00 |

The allowance can be set from 1,000 to 200,000 tokens. Agreement is blocked if
it is below the upper template estimate. This is a visible planning choice,
not an enforced runtime limit or evidence that the model will finish within
it. The estimate is not measured usage, a vendor price quote, or a prediction
for all games. It excludes hardware, electricity, hosting, assets and human
review. A paid or hosted provider requires a new route-specific estimate and
separate budget permission. No actual token balance or payment is changed.

## Persistence, API and integration

`ScopePlans` uses `scope_plans`, `scope_versions` and `scope_commands` in the
existing private briefs database. Each mutation validates the local owner,
source revision, plan revision and bounded input inside a write transaction.
Stable command identities make retries idempotent. Conflicting requests cannot
reuse an identity for another action. Immutable records preserve prior scope
and agreement history. After an agreement, a new edit returns to draft state.

The local HTTP service exposes:

- `GET/POST /api/briefs/{id}/scope`: current plan/catalogue or new draft.
- `GET /api/briefs/{id}/scope/{plan_id}?revision=N`: a saved plan version.
- `POST .../{plan_id}/edit`: bounded fields and exact expected versions.
- `POST .../{plan_id}/agree`: exact versions plus literal `confirmed: true`.

These routes reuse Core's loopback authentication, origin/host and write-scope
boundary, plus the existing body limit. Caller-supplied authority/provider fields
are rejected. A foreign plan or wrong brief association is unavailable.
The HTML uses plain text rendering; no text becomes code or a provider command.
Hosted tenant/Project binding remains a separate integration, as in Cloud007.

Scope agreement stores a review decision with `execution_authority: false`.
The Core mission stays DRAFT and has no backlog approval. A later consumer must
resolve the correct tenant/project, validate source and plan versions, qualify
its engine/model/workers, estimate the actual chosen route and obtain proper
execution and budget authority. Never promote the local scope agreement into
one of those permissions.

## Scope evaluation

The tests use synthetic ideas and estimated usage fixtures with actual SQLite,
Core intake, HTTP and Chromium. They make no live model or provider calls.

| Case | Checked result |
| --- | --- |
| Small garden idea | One playable template goal, six ordered tasks, checks, exclusions and visible estimate; source unchanged |
| Ukrainian Unreal/MMORPG/open-world request | Original retained, separate small slice proposed, Unreal blocks agreement until explicit Godot alternative |
| Still-oversized playable goal | Agreement blocked; move unsupported work to the future roadmap |
| Too-small token allowance | Draft remains editable; agreement blocked against the visible estimate |
| Conflicting tab or changed source brief | Stale operation rejected, saved state intact; current unsaved browser edit retained |
| Repeated agreement and restart | No duplicate version or execution grant; stored history reloads |
| Malformed/foreign request | Bounded input or ownership rejection, no saved mutation |

The scope browser suite also repeats inherited brief navigation journeys to
catch regressions at the handoff. Desktop/mobile screenshots are inspected
separately. Passing fixtures prove this component's behavior only; broader
multilingual design quality, actual model cost, generated gameplay, hosted
launch and age-12+ usability still need their own evidence.
