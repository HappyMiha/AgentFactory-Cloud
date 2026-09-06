# Cloud identity, account and tenant access

AF-CLD-021 supplies reusable identity persistence, lifecycle operations, a tenant
policy and an optional FastAPI router. It adds **no second product server** and
is not mounted into the brief application in this change. The control-plane
owner keeps its package metadata and transport. Hosted brief access remains
unavailable until reviewed tenant/resource binding is implemented.

## One authenticated principal

`IdentityStore(path)` owns the `identity_*` SQLite tables. `IdentityService` uses
that store and an operator-supplied, finite-expiry `AccessPolicy`. Policy version
and the exact jurisdiction/provider-route pair must match the account's trusted
eligibility record. An empty route set denies access. Policy changes and expiry
are checked at every session authentication and authorization.

Only a trusted verified identity integration calls `provision(Eligibility(...))`.
There is no public signup, role assignment, age declaration or policy-override
endpoint. The provisioning integration must authenticate the external identity,
verify the minimal eligibility result and safely deliver the new credentials.
This module does not implement identity-document collection, email delivery,
OAuth/OIDC verification or consumer-provider login. Do not substitute browser
claims for those checks.

Provisioning generates separate 32-byte random opaque login and recovery secrets.
These are machine-generated credentials, **not human passwords**; replacing them
with short passwords would invalidate the SHA-256 storage design. Only hashes
are stored. Secrets are returned once to the trusted provisioning caller and must
be delivered through its protected channel. Never put them in URLs, logs, browser
persistent storage, prompts, repository fixtures or the shared task registry.

`authenticate(token)` returns a server-resolved `Principal`. Every
`authorize(principal, action, Resource(...))` call rechecks the current account,
session, policy and membership for the resource's tenant. A cached principal does
not retain revoked membership or account rights. Resource tenant, owner, kind,
visibility and support-ticket grants must come from protected server records.
Do not construct them from untrusted body/query fields.

A host handler must authenticate first, resolve the resource with its current
tenant boundary, then authorize before reading or mutating data. Missing and
foreign resources use the same 404. Apply this to artifacts, worker-result blobs,
previews, support views, collection queries and receipt replay, not just projects.
Worker authentication/result provenance remains a separate machine-service
integration; a human principal is not a worker lease or permission to fabricate
results. The included HTTP fixture verifies the resource pattern, not a deployed
artifact/download service.

## Role matrix

Membership is a set of roles **per tenant**. No role, including Admin, grants
access to a different tenant. The trusted `membership` administration method is
not exposed as an unauthenticated HTTP operation.

| Role | Permitted scope within its tenant | Still denied |
| --- | --- | --- |
| Creator | Read/write/play own project, artifact, result, preview and build resources | Another creator's private resources; support/moderation; spending or publication approval |
| Player | Read/play public build or preview | Private source/artifact/results; mutation |
| Moderator | Read/moderate redacted moderation representations | Raw private artifacts and source; account administration |
| Support | Read a redacted support representation with a current explicit ticket grant for this support account | Raw payloads, unrelated tickets, generic project reads |
| Admin | Recognized resource operations within its tenant; redacted support through its dedicated action | Cross-tenant access, unknown actions, raw support payloads; implicit spend/rights/release approval |

`spend`, publish, sell and arbitrary invented actions are not granted by this
matrix. Existing domain/evidence authorities decide those separately. A public
flag never bypasses tenant checks; cross-tenant public discovery/entitlements need
their own accepted integration. New resources/actions default to denied.

## Session and recovery lifecycle

Login returns an opaque bearer session, with an absolute 900-second lifetime by
default and a configurable maximum of one hour. It does not extend on activity.
Only a token hash, account generation and expiry are persisted. At most eight
sessions per account are retained. Sessions survive process restart, while each
use still checks current account generation and policy. Logout removes the exact
session; replay fails. Membership revocation is effective on the next action.

Recovery requires the separate high-entropy recovery secret. A successful
transaction rotates both login/recovery factors, increments account generation
and revokes all sessions. The old recovery code cannot be replayed. A failed
recovery does not revoke a legitimate session. Recovery returns the new factors
once with `Cache-Control: no-store`. If that response is lost, do not retry an old
factor expecting it to reveal new secrets: a separately reviewed verified human
recovery process is required. This change does not invent email reset or support
impersonation. An ordinary Support role cannot reset another user's credentials.

Login, recovery, logout and deletion have durable rate counters: eight attempts
per account/action and forty per network peer/action over five minutes. The peer
counter is checked before inserting invented account keys. Counters persist even
when authentication fails and survive a restart; the table has a 4096-key cap and
expired rows are pruned. A new forwarded header cannot reset the source key.
The in-process service trusts its `client_key` argument; the router derives it
from the ASGI peer and does not read `X-Forwarded-For`. A reverse-proxy deployment
must configure trusted proxy handling, body/header limits and network abuse
controls separately. This is not a distributed rate-limiter qualification.

## Deletion, audit and retention

Deletion requires an active session, the current login factor, JSON
`confirmed: true` and `X-Identity-Confirm: true`. The transaction immediately sets
`deletion_pending`, destroys credential hashes, revokes all sessions and removes
memberships. It stores a durable pending deletion job and returns **202**, not a
claim that all product data disappeared.

A trusted worker invokes `finish_deletion(account_id, erase_owned_resources)`.
The eraser must be idempotent, preserve other users' and shared-tenant resources,
apply approved retention/ownership rules and return exactly `True` only after
verified completion. Failure or an uncertain result leaves the job pending. The
worker can replay after a crash; a completed job is not executed again. No such
product-resource eraser is wired in this change. Do not mark product deletion
complete using a dummy callback.

Audit records contain opaque account ID where known, event, outcome and timestamp,
not raw secrets, eligibility fields, IP addresses or request bodies. Events cover
provisioning, membership changes, session login/logout, authorization,
recovery/rotation, deletion request/completion and one rate-limit event per
rejected window. Eligibility fields are cleared when deletion completes; the
minimal account tombstone, deletion state and audit remain for traceability.
They are still potentially personal data. Production audit/commerce retention,
erasure deadlines, backups and access policy need explicit owner review; no legal
retention period is asserted here. Expired session/rate cleanup is implemented;
long-term audit purge is a separate retention integration and must not be implied.

Protect the SQLite path with service-account filesystem permissions. The module
stores hashed random secrets but is not disk encryption or protection against a
privileged database writer. SQLite transactions serialize concurrent lifecycle
changes; transport, deployment secret storage and external identity assurance
remain the host's responsibilities.

## Router integration contract

`identity_router(service)` returns an APIRouter with:

| Route | Operation |
| --- | --- |
| POST `/identity/sessions` | `{account_id, secret}` to exchange a login factor for a session |
| GET `/identity/session` | Resolve bearer session, expose only authenticated account ID |
| DELETE `/identity/session` | Revoke that bearer session |
| POST `/identity/recovery` | `{account_id, secret}` using the separate recovery factor |
| POST `/identity/account/deletion` | `{login_secret, confirmed}` plus bearer and confirmation header |

Bodies are limited to 4096 bytes, reject duplicate/extra fields and return generic
errors without echoing credentials. Success and handled errors are no-store.
Duplicate Authorization headers are rejected. No credential is read from a URL or
an ambient cookie. A future browser integration needs reviewed HttpOnly/Secure
session handling or a bounded in-memory bearer flow; this router does not persist
tokens in browser storage. HTTPS and the host's origin/transport boundary are
required before remote deployment. The current loopback Core principal is not
a Cloud tenant principal and must never be silently converted into one.

The dependency file records the tested FastAPI/Pydantic versions independently.
Cloud007 owns pyproject/package/bootstrap wiring. No brief handler is changed here;
until explicit integration lands, the identity service cannot enable hosted brief
access. The access seam must also be used when a future handler replays a stored
receipt or follows an artifact link; do not authorize only the initial page.

## Age and provider decision record

The [machine-readable policy](../contracts/v1/identity-policy.json) keeps unknown,
under-12 and 12–17 routes blocked. A self-selected age, guardian checkbox or
synthetic policy test cannot unlock them. Adult provisioning also requires the
trusted current policy's explicitly reviewed jurisdiction/provider pair. The
repository ships no approved real pair and no current provider/legal permission.

Before any 12+ recruitment, the owner must record approved provider/account terms,
jurisdiction/privacy review, guardian verification and withdrawal where required,
private defaults, minimization/deletion/retention, a supervised protocol and
separate bounded adult spending authority. See [minor-pilot-entry.md](minor-pilot-entry.md).
Unknown or unsupported paths show `access_route_unapproved` and remain unavailable;
the alternative is an approved adult-operated route or postponing access pending
review. This engineering change cannot approve those external policy decisions.

## Validation and remaining acceptance

The tests use disposable SQLite stores, synthetic identities, synthetic adult
policy pairs and FastAPI HTTP requests. They cover each role across tenant
boundaries, ownership/public/redaction/ticket checks, revoked principals, expiry,
recovery replay, rate limits, pending deletion/retry and secret handling. There
are no real users, minor data, payments or provider calls.

Hosted application integration, verified external provisioning/recovery channels,
resource erasure/retention, deployment hardening and approved minor-pilot records
remain explicit acceptance gates. Independent source review and a merged PR prove
the tested component behavior only; they are not a hosted or minor-access launch.
