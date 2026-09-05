# Release review and owner acceptance

Copy this template into a protected review record. Keep private briefs, credentials
and personal data out of public task records. Unfilled fields mean **not accepted**.
This template itself is not evidence that a release exists or passed any check.

## Candidate

| Field | Recorded value |
| --- | --- |
| Tenant / Project | Pending |
| Release ID and revision | Pending |
| Run ID and attempt | Pending |
| SourceVersion ID and SHA-256 | Pending |
| Build ID and artifact SHA-256 | Pending |
| Engine adapter ID/version and engine version | Pending |
| Toolchain ID/version and digest | Pending |
| Target ID and profile version | Pending |
| GamePack ID/version and digest | Pending |
| Evidence policy and domain contract version | Pending |
| Intended audience and visibility | Pending |
| Rights revision and moderation-policy version | Pending |

## Checks and gate results

For every required check, record its level, live/simulation mode, result, exact
binding, checked time, expiry, authenticated issuer and protected evidence link.
Missing, failed, skipped, stale or unrelated evidence is a blocker.

| Gate | Decision | Evidence record / blockers / next action |
| --- | --- | --- |
| Ready for the selected path | Not evaluated | Pending |
| Playable on the named target | Not evaluated | Pending |
| Exportable playable package | Not evaluated | Pending |
| Publishable for the requested audience | Not evaluated | Pending |
| Sellable offer, if applicable | Not evaluated | Pending |

Verify that original source and each included asset have provenance and permission
for the specific requested use. Record notice/license checks and unresolved claims.
For sale, record Listing revision, exact price/currency/license, seller eligibility
revision and applicable adult/guardian authority. No sale approval authorizes an
AI spend or a charge by itself.

## Independent reviewer decision

- Authenticated reviewer identity and tenant role: Pending.
- Reviewer model identity, if AI-assisted: Pending or explicitly human-only.
- Producer identities/models and independence check: Pending.
- Scenarios actually executed and observed results: Pending.
- Failures, limitations and untested targets: Pending.
- Decision: **Pending**; select approve or reject only after review.
- Bound candidate/decision-context digest and protected evidence reference: Pending.
- Decision timestamp and expiry: Pending.

## Human owner decision

- Authenticated authorized owner identity and authority record: Pending.
- Exact candidate reviewed and requested audience/visibility: Pending.
- Product requirements accepted or rejected, with reasons: Pending.
- Decision: **Pending**; select accept or reject explicitly.
- Decision-context digest, timestamp and expiry: Pending.

An independent reviewer cannot fill the owner's decision by implication. A green
CI run or merged PR is not owner acceptance of a playable or sellable game.

## Action-time recheck and recovery

- Re-evaluated policy, subject, current rights/permissions and gate result: Pending.
- Authorized action and its idempotency/audit reference: Pending.
- Actual resulting artifact, URL or listing state: Pending.
- Cancellation, withdrawal, rollback and support owner: Pending.

If the action failed, record the real outcome and retain the previous known-good
version. Do not mark publication or sale complete from a timeout or a planned URL.
