# Creator and Operator design flows

Version 1 is a clickable, synthetic design proposal. It separates the creator's
journey from service operations. It implements no accounts, builds, publishing,
payments, provider calls or production authorization. The single task registry
records merged engineering delivery separately from human product acceptance.

From the repository root, preview only the prototype directory on loopback:

```bash
python -m http.server 8766 --bind 127.0.0.1 --directory prototypes/creator-operator
```

Open `http://127.0.0.1:8766/`. Use made-up ideas, never child data or private briefs.
The preview uses localStorage only for its own versioned draft key; it sends no
draft to a server. Draft saving failures are visible and do not claim persistence.
The preview settings choose synthetic scenarios, role examples and age-path
examples. They are outside the future product journey and confer no real rights.

## Creator journey

| Screen/state | Plain-language status | Primary next action | Preserved state |
| --- | --- | --- | --- |
| My Games, first visit | Your idea starts here | Create a game | Private draft |
| Create | What would you like to make? | Review the sample plan | Name and idea on this device |
| Plan preview | Review before starting | Edit your idea | Submitted idea; fixed sample plan explicitly identified |
| Play without accepted proof | Not yet playable | Review next step | Saved idea; no fake Play success |
| Change after failure | We couldn't finish this version | Edit the next version | Last saved draft; no automatic retry |
| Return after closing/refreshing | Your draft is waiting | Continue your draft | Same validated draft values |
| Cancelled attempt | Your work has stopped | Revisit your saved idea | Draft kept; new real attempt would need a new approval |
| Publish | Private until you decide | Review what is missing | No automatic sharing, listing or sale |

Navigation is My Games, Create, Play, Change and Publish. No task IDs, provider
credentials, JSON or worker leases are required in the main creator path. Optional
details describe evidence limitations without asking the creator to operate a
scheduler. The landscape is a concept illustration, explicitly not a game build.

A real build-start screen must show the agreed plan, bounded cost, funding owner,
source version and cancellation behavior before explicit confirmation. This
prototype leaves that action unavailable because there is no connected qualified
provider, billing contract or accepted engine profile. Changing the idea never
silently approves spending. The sample plan is deterministic presentation text,
not an AI interpretation or task decomposition of the submitted idea.

Background sample-status updates preserve the same form nodes, focus, selection
and in-progress text. Refresh restores the versioned local draft. Cancellation
and deletion require a native dialog. Escaping or choosing Go back makes no
change. Deletion removes only this prototype's local key and explains that scope;
it is not an account-erasure or commerce-retention implementation.

## Operator separation and service contract

The Operator example contains approvals, evidence, workers, audit and diagnostics.
Creator mode hides its navigation and denies direct fragment navigation to its
content. This checks presentation separation only. Browser code and fixtures are
public sample material and cannot establish real authorization.

The implementing service must derive current role and tenant grants from a
trusted authenticated context, as defined by the versioned API/domain contract.
Never accept a role selector, client JSON or URL fragment as authorization. Check
permissions on each read and mutation, including retries. Revoked roles lose
access; cached privileged views must be cleared. Independent reviewer and owner
approval are distinct from a successful worker run. Operator permission must not
turn missing evidence into a green creator status.

The publishing checklist follows the existing Cloud contract: current playable
proof bound to the exact version, rights/attribution, moderation, an authorized
owner decision and applicable funding authority. AF-CLD-006 owns the detailed
evidence-level rules; this task consumes the distinction and does not create a
second evidence authority. Its fixtures remain `product_acceptance: not-accepted`.

## Accessibility and review

The prototype has a skip link, visible keyboard focus, named navigation, labelled
inputs, native select/dialog controls, plain status text and no color-only gate.
It uses text in addition to status pills and respects narrow screens without
horizontal document scrolling. Confirmations restore interaction without erasing
a draft. Operator details are outside the creator's primary navigation.

Automated Chromium checks cover routes, persistence through reload, background
updates/caret, cancellation, deletion, missing play/publish evidence, minor-path
blocking, presentation-role isolation, script-like draft text and narrow layout.
These checks do not replace adult usability review, screen-reader testing, zoom
and contrast assessment or owner acceptance. Those reviews are explicitly pending.

For adult-only review, ask testers to find Create, describe a made-up first game,
return to a draft after refresh, recover from the failure scenario, cancel without
losing input and identify why publishing is unavailable. Record version, browser,
keyboard/screen-reader profile, task outcome and confusing wording. Store no
participant identifiers in the repository. An independent node code review is
not an adult-user study. A minor pilot must first satisfy
[the separate entry gates](minor-pilot-entry.md).
