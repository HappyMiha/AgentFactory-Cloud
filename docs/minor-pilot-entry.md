# Entry requirements for a supervised 12+ pilot

Status: **blocked, not approved**. This is a product design and review checklist,
not a statement of legal compliance or provider permission. No minors may enter
this prototype as a study, and no child information is collected by this task.
Adult reviewers use synthetic age-path examples only.

The intended design has these paths:

| Age-path example | Current behavior | Requirement before real access |
| --- | --- | --- |
| Under 12 | Input/build/publication unavailable | A separate age-appropriate product decision; this design does not offer this path. |
| 12–17 | Input and plan-start unavailable; explain the supervised gate | Approved provider/account path, applicable privacy/consent review, verified guardian process where required and supervised usability plan. |
| 18+ | Synthetic local design review only | Real accounts, provider access, costs and product acceptance remain separate implementation gates. |

Do not infer age from a name, photo, writing style or account appearance. Collect
only the minimum eligibility result required by the approved process. Exact birth
date, government identity documents, school, location and contact information do
not belong in prompts, game briefs, public fixtures or the shared task registry.
The preview selector is not age verification and its value is not persisted.

## Approval record required before recruitment

Every row remains pending. The product owner must record a reviewed versioned
artifact and an accountable human decision before changing the pilot status.

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Provider and account eligibility | Named supported provider/product, official current terms and account/age restrictions, checked date and version, authorized account owner, permitted minor/guardian flow | Pending; no provider route qualified for minors |
| Privacy and applicable consent | Human review for the intended audience and jurisdictions, minimum data fields, consent/withdrawal method and purpose | Pending; no compliance conclusion |
| Guardian involvement | Trusted verification process where required; guardian can review scope and revoke participation; a child-facing checkbox cannot grant authority | Pending |
| Spending | Authorized adult funding owner; bounded amount/currency/provider/expiry and revocation; no minor self-approval or saved payment details in creator UI | Pending; no payment methods connected |
| Private defaults | Private projects, restricted sharing/discovery, no behavioral advertising or public child profiles | Proposed; service enforcement unimplemented |
| Minimization and deletion | Data-flow inventory, retention/erasure decisions, guardian/user deletion path, separate audit/commerce retention policy | Pending; local prototype deletion only |
| Study protocol | Supervision, age-appropriate materials, stopping/withdrawal process, safeguarding contact and adult-only rehearsal findings resolved | Pending |
| Product readiness | Exact browser/engine/evidence profile, independent review and owner acceptance | Not accepted |

The provider review must use official, current sources at the time of pilot
approval. No list of consumer chat subscriptions is treated as API access or
permission to involve a minor. No provider's current age policy has been verified
or approved by this design task. If a route is unavailable or its terms cannot be
confirmed, show unavailable and choose a reviewed alternative; never route around
an account restriction.

The future product should let a creator request a change while the authorized
adult controls any resulting spend. Spending consent and permission to publish
are separate, bounded decisions. Revoking either blocks new actions. A request to
delete private source must not silently decide buyer entitlements or required
payment/audit retention; those need the explicit commerce policy from the domain
contract before those features ship.

No minor pilot, recruitment message, data collection, account creation or payment
is authorized by merging these design files. Human acceptance and the live entry
record remain required product gates, not additional permission for ordinary
repository development or synthetic regression tests.
