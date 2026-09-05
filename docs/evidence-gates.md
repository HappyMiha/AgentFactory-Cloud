# Evidence levels and separate release gates

AF-CLD-006 defines policy version **1.0.0** alongside domain contract 1.0.0. It adds
an evidence envelope and decision rules; it does not replace the
[domain/API contracts](domain-model.md) or claim that a Cloud runtime exists.
The [policy](../contracts/v1/evidence-policy.json) and
[synthetic examples](../contracts/v1/evidence-scenarios.json) can be checked by
the reference evaluator. No example is a real tested game or a release approval.

## Five different questions

| Gate | What a positive result means | Required checks |
| --- | --- | --- |
| Ready | The selected path can start now | Real selected tools, services, model and workspace probes |
| Playable | This exact artifact can be played on the selected target | Code checks, engine build, runtime smoke check and an actual playtest |
| Exportable | The supported playable package can leave Cloud | Playable, portable package check, component notices and rights for export |
| Publishable | This version has approval for the requested publication | Playable, moderation, publish rights, independent reviewer approval and explicit owner acceptance |
| Sellable | This exact offer may be listed for sale | Publishable, sell rights, seller eligibility and approved sale terms |

These are eligibility decisions, not proof that an action already happened.
Ready does not mean Playable. A passing API or unit test proves neither. Playable
does not require a public listing. Export permission does not imply permission to
publish or sell. Failed seller checks must not block an otherwise permitted
private play session.

Ready can be evaluated before a Build exists. Its binding omits Build ID and
artifact digest; it still binds the source, run attempt and complete selected
engine/toolchain/target/pack profile. Artifact gates require a Build ID and digest.
An environment outage can deny a new run while an already verified artifact stays
playable on a healthy hosting runtime. The hosting service must separately check
availability and access before serving it.

Exportable here means an advertised playable ownership package. Downloading one's
permitted raw source or a diagnostic archive is a separate action; a broken build
must not silently lock the owner out of their source. An exported game's normal
engine/target dependencies are allowed. Hidden Cloud login, payment or credential
dependencies are not a portable-package success.

## Levels are different kinds of evidence

| Level | What it can support | What it cannot establish |
| --- | --- | --- |
| simulation | A dry run or policy rehearsal | Any live eligibility gate |
| code_check | Syntax, unit or static checks | Successful engine export or real play |
| environment_probe | Installed tools, selected route and workspace availability | Game quality or a finished artifact |
| engine_build | Named toolchain produced the exact artifact | A working game loop |
| runtime_test | Exact artifact was executed, with traceable results | Owner acceptance, rights or sale approval |
| export_check | A package opens/runs outside Cloud with its declared dependencies | Permission for every public or commercial use |
| policy_review | An authorized service decided one specific use | Engine execution or legal certainty from a bare assertion |
| independent_review | A qualified, independent reviewer accepted this candidate | The product owner's final decision |
| owner_acceptance | An authorized human owner explicitly accepted this candidate | Permission to skip other checks |

Levels are not a numeric ranking. An owner click cannot substitute for a skipped
playtest. A successful build cannot substitute for rights review. The evaluator
requires the correct level for each named check.

## Exact version and profile binding

Every build evidence envelope records:

- Tenant, Project, Run and attempt, SourceVersion ID and source SHA-256.
- Build ID and artifact SHA-256.
- Engine adapter ID/version and actual engine version.
- Toolchain ID/version and binary or environment digest.
- Target ID/profile version and GamePack ID/version/digest.

`binding_fields` in the policy is the exact required field set. No floating `main`,
unqualified “latest works”, or source-path-only proof can qualify a release.
Producers must resolve immutable actual identities before submitting evidence.
The structural evaluator checks presence, types, digests and equality; it cannot
prove that a reported version string identifies a real installed engine.

Every check has `check`, `status`, `mode`, `level`, `binding`, `checked_at`,
`expires_at`, `issuer_id` and a protected `evidence_ref`. Evidence must be passed,
live, current, complete and bound to the requested subject. Missing, duplicate,
skipped, failed, simulated, future-dated, stale or differently bound records deny
the affected gate. We do not choose an arbitrary latest record from duplicates.

The environment verifier must prove all required tools/services/model/workspace
checks for the selected path. Unselected providers must not block it. A build
verifier records the actual process exit result, version, artifact digest and
validator results. The playtest verifier records the exact runtime, scenario,
observed result and diagnostic references. Merely opening an HTML page or creating
an empty file does not satisfy these producer contracts.

Issuers and their tenant-specific roles are injected from trusted verifier state.
They are not read from browser claims. An inactive issuer, wrong tenant or wrong
role cannot qualify a check. Evidence references alone are not verified evidence:
a production implementation still needs authenticated producers, protected blobs,
signature/content verification, transaction isolation and revocation handling.

## Reviews, rights and offers

Publication decisions also bind Release ID/revision, intended audience and
visibility, rights revision and moderation-policy version. Changing any of these
requires new decisions. The independent reviewer's actor cannot be a producer;
a different agent using the same canonical producer model is also not independent.
Canonical model identity must come from Core's qualified routing evidence; this
reference policy does not implement model discovery or alias resolution.

The trusted reviewer record declares `review_mode`: `human_only` requires a human
actor and no model identity; `ai_assisted` requires an explicitly qualified model
identity such as `local:example-model-v1`, including when a human used AI assistance.
An absent mode or unknown service/model identity denies review eligibility.
Deterministic checks belong to their named check levels; they cannot stand in for
the independent release reviewer. The synthetic positive example explicitly uses
a human-only reviewer, separate from its authorized human owner.

Owner acceptance must come from the explicitly authorized human owner. A service,
model answer or unrelated owner with a similar role cannot replace that decision.
Keep the review and owner-acceptance records separate. The
[release review template](release-review-template.md) records both.

Rights decisions name the requested use: export, publish or sell. The shared Cloud
rights service must check source and every included asset, license version,
attribution and current disputes. It must deny unknown or unsupported uses.
The gate consumes that decision; it does not create a second rights service.

Sale decisions additionally bind Listing ID/revision, positive price in minor
currency units, currency, license version and seller-eligibility revision. Free
publication remains separate from paid sale. A changed price, license, guardian
authority or seller eligibility requires a fresh decision. Sellable grants no
permission to charge a payment method, spend AI credits or bypass refund rules.
Provider/account age rules and guardian/spending policy remain required checks in
their owning services before a minor pilot or commercial release.

## Failure, cancellation and recovery

Each denied gate returns a plain-language status, blockers and one next action.
For example, a skipped playtest shows “Playable: checks needed” and asks for the
failed or skipped check to be rerun. Optional technical detail can show the exact
check and evidence version. A UI must never infer success from an empty error list
when the gate evaluation itself failed or was unavailable.

A cancelled operation supplies no successful proof. It must not create a Playable
badge. A retry increments the Run attempt; old evidence does not transfer to that
attempt. Changed source or artifact creates a new immutable version, not a renamed
old proof. Re-run affected checks and obtain new decisions for changed inputs.
Policy/role revocation and expiry are evaluated again on each new decision.

Publishing, serving, exporting and listing must re-evaluate the relevant gate and
permissions at action time against one consistent snapshot. Persist the evaluated
subject, policy version, evidence references, issuer decisions and timestamp as
an audit record. A cached label is not authorization. A withdrawal or new rights
denial must stop new affected actions, even if an older decision passed.

This policy checks eligibility only. Production crash recovery must atomically
store decisions and queued actions, enforce budgets/cancellation, deduplicate
retries and avoid issuing a public URL or charge after a failed gate. Those are
implementation requirements in the worker, hosting and commerce tasks.

## Conformance and handoff

```bash
python scripts/validate_evidence_gates.py
python -m unittest discover -s tests -p test_evidence_gates.py -v
```

The examples cover good evidence, failed builds, stale source, skipped/missing
playtests, simulation, code-only checks, expiry, missing owner/sale/export decisions
and readiness before a build exists. Mutation tests cover every bound version,
issuer/tenant revocation, reviewer independence and changed release/offer terms.
All “passed/live” fixture labels are fabricated test inputs, explicitly marked as
synthetic. The evaluator never runs an engine, accesses a provider or accepts a
product. Existing Cloud domain and upstream-map tests check the adjacent contracts.

Before implementation, map each check to a real authenticated producer and a
versioned evidence format. Qualify concrete engines/targets and define validity
windows per supported profile. Before UI integration, bind these labels to the
actual service decision and test missing/error responses. An incompatible change
to binding, required checks or decision meaning needs a new reviewed policy
version; old approvals are not silently promoted to it.
