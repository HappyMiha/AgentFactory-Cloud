# Cloud API contract, version 1

This is a design for later implementation, with an in-memory state-command
reference model. It is not a deployed API. Read the [domain model](domain-model.md)
and its [field catalogue](../contracts/v1/domain.json) together with this document.

## Tenant boundary and endpoints

Private routes start with `/api/v1/tenants/{tenant_id}`. Authenticate the caller,
resolve current membership and permissions for this tenant, then resolve records.
Use the same 404 for a missing resource and a resource outside that tenant.
Authentication context is trusted server input, never request JSON. Scope grants
are tenant-specific; a role in one team gives no rights in another team.

The reference model represents this explicitly as trusted server context:
`tenant_grants: {"tenant_a": ["projects:delete"], "tenant_b": ["projects:read"]}`.
An actor in both teams can delete in A but cannot delete in B. Replaying a receipt
rechecks the grant for the receipt's tenant. A flat scopes list plus a membership
list is not an accepted context. This map is injected by a verifier in the design;
it is never accepted from client JSON.

Collections are `users`, `projects`, `game-briefs`, `factory-blueprints`,
`agent-teams`, `runs`, `source-versions`, `builds`, `play-sessions`, `feedback`,
`releases`, `listings`, `purchases` and `entitlements`. Tenant account operations
use `/api/v1/tenants/{tenant_id}` itself. Registration and provider login flows are
outside this task; credentials must not travel in these domain records.

| Method and path suffix | Rule |
| --- | --- |
| GET `/projects/{id}` | Return the authorized representation and a strong ETag. Hidden/deleted record: 404. |
| GET `/projects?cursor=...&limit=20` | Return tenant-filtered items and an opaque next cursor. Bind cursors to tenant, caller/filter and sort. Limit 1–100. |
| POST `/projects` | Require Idempotency-Key; server assigns ID, tenant, timestamps, revision 1 and draft state. Return 201, Location and ETag. |
| PATCH `/projects/{id}` | Require If-Match and Idempotency-Key; allow only documented editable fields, such as draft project name. Return 200 and new ETag. |
| POST `/runs/{id}/actions/start` | Apply `run.start` and all its guards atomically. Empty JSON body. |
| POST `/releases/{id}/actions/approve` | Apply `release.approve`; creator-supplied proof fields are forbidden. |
| DELETE `/projects/{id}` | Apply `project.delete`; return 204 with ETag. Published content first needs withdrawal. |

Create/read/edit patterns above are normative for future services. Only named
state commands in [transitions.json](../contracts/v1/transitions.json) execute in
the reference model. Unsupported lifecycle operations must remain unavailable
until their specific validation, access and recovery behavior is implemented.
Internal state, revision, identity, price verification, proof and ownership fields
cannot be edited through a general PATCH endpoint.

For a command `entity.action`, use the entity's collection, ID and
`/actions/{action}`. Project deletion uses DELETE instead. Required command scopes
are in the transition catalogue. Future create/read/edit routes use explicit
tenant-scoped service policies; they must not default to allowing every member.

## Examples

Create a project:

```http
POST /api/v1/tenants/tenant_a/projects
Content-Type: application/json
Idempotency-Key: create-mars-project-01

{"name":"Mars robots","owner_user_id":"user_a"}
```

```http
HTTP/1.1 201 Created
Location: /api/v1/tenants/tenant_a/projects/project_a
ETag: "r1"
Content-Type: application/json

{"id":"project_a","tenant_id":"tenant_a","revision":1,"state":"draft","name":"Mars robots","owner_user_id":"user_a","remix_parent_source_id":null,"created_at":"2026-09-05T12:00:00Z","updated_at":"2026-09-05T12:00:00Z","deleted":false}
```

After the run's private qualification workflow reports ready:

```http
POST /api/v1/tenants/tenant_a/runs/run_a/actions/start
If-Match: "r1"
Idempotency-Key: start-run-a-attempt-1
Content-Type: application/json

{}
```

Success returns 200, `ETag: "r2"` and the updated Run. If another command already
changed it to revision 2, a new request using `"r1"` returns:

```http
HTTP/1.1 412 Precondition Failed
Content-Type: application/json

{"error":{"code":"revision_conflict","message":"This item changed. Reload it before editing.","request_id":"example-request"}}
```

Missing playable evidence returns 409 `evidence_missing_or_duplicate`; stale,
failed or simulated evidence returns 409 `evidence_not_current`. The UI explains
what must be checked and offers an authorized retry. It never turns a denial into
a green Ready badge. Error details may name authorized check categories but must
not expose secrets or another tenant's record.

## Mutation, conflict and retry order

1. Check authentication, current tenant membership, active tenant and operation
   permission. Repeat these checks even for a previously successful request.
2. Require a nonempty Idempotency-Key of at most 128 characters. Scope the receipt
   to tenant, actor, operation, target resource (or collection for create) and key.
3. Fingerprint canonical JSON body and original If-Match. An identical successful
   request returns its stored response and ETag without executing again, even if
   the original mutation advanced the resource revision. A changed body or
   precondition with that key returns 409 `idempotency_conflict`.
4. For a new request, resolve the visible record and its nondeleted parent.
   Existing-resource mutations require exactly the current strong `"rN"` ETag.
   Missing If-Match: 428. Mismatch: 412. Create has no existing ETag and rejects
   If-Match with 422 `invalid_fields`.
5. Validate fields, immutable identity, allowed transition and current evidence
   against the same snapshot. A command body is `{}`; it cannot inject state or
   checks. Reject unknown editable fields with 422 `invalid_fields`.
6. Commit the mutation, receipt and outgoing work event in one transaction.
   Increment revision once, then return the response. Dispatchers use that event
   identity to avoid duplicate builds or charges. A crash must not leave a saved
   mutation with an absent receipt or vice versa.

The successful response can be replayed for 24 hours. After that, retain a compact
used-key marker and return 409 `idempotency_expired`; never treat an expired key as
a new command. Marker retention/compaction is a service design prerequisite. A
caller must reconcile the resource before deliberately using a new key.

Replay is a receipt for a past action, not a fresh readiness assertion. It may
return the historical result after evidence expires or a resource is tombstoned,
but only to a caller who still has tenant and operation access. New GET and new
commands use current visibility and evidence. The UI must refresh current state
before offering Play or Publish.

Validation/conflict denials have no mutation and are not stored as successful
receipts. The caller may correct input and retry. For an unknown transport/server
outcome, repeat the exact request/key first. Do not guess success from a timeout.
The in-memory example is sequential; transaction isolation and concurrent request
deduplication require database integration tests in the implementing task.

## Cancellation, deletion and cross-tenant commerce

Cancel a Run through `run.cancel`. A cancelled run cannot start again in place.
`run.retry` creates the next attempt in draft and clears evidence; qualification
must be repeated for that attempt. Retry does not silently change model, source
or budget. Changing those immutable inputs creates a new Run.

Project deletion is conditional and idempotent. A published Listing returns 409
`publication_exists`. A successful deletion creates a tombstone and hides private
children. The same delete key replays 204; a new key sees 404. Never cascade into
another tenant's Purchase or Entitlement. Public withdrawal and paid access must
follow the later, explicit commerce retention/refund policy.

Public discovery is a separate read projection with public identifiers and
moderated fields only; it is not an exception to private tenant authorization.
Buying uses a verified, expiring public offer snapshot. Its price, currency,
seller, listing revision, release and license become immutable purchase inputs.
A provider-verified payment event must match the purchase, amount and currency
before paid status; deduplicate provider event IDs. An Entitlement must match the
paid Purchase's buyer, public release and license. Failed/refunded payments never
create a new active entitlement. These payment/entitlement transitions and offer
signature checks are requirements, not implemented by the fixture evaluator.

## Error catalogue

Responses use `{ "error": { "code": "...", "message": "...", "request_id": "..." } }`.
The reference evaluator returns compact `status`/`code` values rather than HTTP.

| HTTP | Code | Caller action |
| --- | --- | --- |
| 400 | `unknown_operation`, `idempotency_key_required` | Correct the request. |
| 401 | `authentication_required` | Sign in or refresh the expired session. |
| 403 | `permission_denied`, `tenant_inactive` | Ask an authorized account owner; do not retry unchanged. |
| 404 | `resource_not_found` | Treat as missing or inaccessible; do not reveal which. |
| 409 | `invalid_transition`, `inputs_not_ready`, `release_not_approved` | Refresh state and finish prerequisites. |
| 409 | `evidence_missing_or_duplicate`, `evidence_not_current`, `rights_not_cleared` | Run the missing check or resolve the rights decision. |
| 409 | `publication_exists` | Withdraw publication before deleting. |
| 409 | `idempotency_conflict`, `idempotency_expired` | Reconcile the original result; do not blindly issue another key. |
| 412 | `revision_conflict` | Reload and reconcile edits before retrying with a new key. |
| 422 | `invalid_fields`, `unexpected_command_fields` | Correct fields; do not overwrite immutable input. |
| 428 | `precondition_required` | Read the resource and send its current ETag. |
| 429 | `rate_limited` | Follow Retry-After; preserve the original key for an uncertain mutation. |
| 503 | `temporarily_unavailable` | Retry with backoff and the same key for an uncertain mutation. |

Do not disclose detailed validation before checking tenant access. The future HTTP
parser may reject malformed syntax before authorization, but must not look up or
reveal any resource while doing so.

## Compatibility and implementation handoff

The design version is `1.0.0`; the major HTTP path is `/api/v1`. New optional
response fields are additive. Clients must tolerate unknown response fields and
display unknown states as unavailable, never as success. Request writers use the
versioned accepted field set; unknown mutation fields are rejected. The fixture
validator intentionally rejects fields outside its pinned catalogue.

Changing required fields, state meaning, tenant boundaries, evidence binding,
idempotency or money semantics is a breaking change: use a reviewed new major
contract and migration. Evidence contracts need their own explicit version pins;
do not assume an arbitrary Core commit implements this Cloud design.

Before implementation, choose durable storage/transactions, evidence verifiers,
tenant membership enforcement, used-key marker retention, outbox recovery and
public projection rules. Before public release, test actual worker execution,
isolation, access revocation, deletion, moderation and payment behavior. Those
requirements remain in the backlog; these examples do not certify them.
