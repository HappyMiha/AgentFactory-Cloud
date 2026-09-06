# Turn an idea into an editable game brief

Task: `cloud:AF-CLD-007`. This is the first working local creator intake. It
stores real data through Core and provides a browser editor. It does not yet
start a game build, choose a development team, or publish a game.

## What the creator can do

1. Write an idea in English or Ukrainian and save it. The original words,
   including spaces and line breaks, stay unchanged.
2. Edit eight short fields: kind of game, player activity, controls, winning
   and losing, visual style, platform, first playable version, and ideas for later.
3. Optionally ask an installed local AI to organize the original sentences.
   Check its choices: a correct quote can still be in the wrong field.
4. Answer up to three short questions about missing player activity, platform,
   or controls. Choose a suggested answer or write your own.
5. Save a new version and open earlier versions and clarification answers.

The AI cannot rewrite saved human choices. Clear a field and save it if it
should be filled again. When another tab saves first, a stale save is rejected
and the current unsaved text remains on screen. Navigation inside the workspace
asks before discarding edits. Unsaved edits are not an automatic backup and can
be lost when the browser is closed or refreshed.

## Run the local workspace

Use Python 3.11 or newer and Git. From this repository, install into a virtual
environment with `python -m pip install -e .`. The package pins the accepted
Core commit `29f67dce01719a4bc14fa09b1aa33bb58a51e549`, including its web extra.
Installation requires network access to obtain dependencies. It does not
install Unreal, Godot, Ollama, or any model.

On Windows, after activating the environment:

```powershell
agentfactory-brief --data "$env:LOCALAPPDATA/AgentFactory/briefs"
```

On Ubuntu:

```bash
agentfactory-brief --data "$HOME/.local/share/agentfactory/briefs"
```

Open `http://127.0.0.1:8767`. The server listens only on the local loopback
address. Use one server process and a private data directory outside Git.
The directory contains `briefs.sqlite3` and `core-intake.sqlite3`; both are
needed to preserve the complete intake record. This profile has no retention
or user-deletion workflow yet.

This is one trusted local operator, not a hosted account system. Core's
`AGENT_FACTORY_API_ACTOR` selects that operator. Without
`AGENT_FACTORY_API_TOKEN`, the profile is local-open: processes and browsers
on this computer may access it. Configure a private token before launch to
require the local unlock screen. Enter the token only into local settings or
the unlock screen, not into a brief, Git, or a shared command example.
Core provides the cookie, origin, host and scope checks. There is no cloud
tenant authentication or approved child-account flow here.

## Optional local AI

The default is manual editing. To enable a local suggestion, Ollama must
already be running with a supported model already installed. The installed
model inventory is checked before a request; this feature does not download
or start models.

Windows:

```powershell
$env:OLLAMA_HOST = 'http://127.0.0.1:11434'
agentfactory-brief --data "$env:LOCALAPPDATA/AgentFactory/briefs" --enable-local-ai --model qwen2.5-coder:7b
```

Ubuntu:

```bash
OLLAMA_HOST=http://127.0.0.1:11434 agentfactory-brief \
  --data "$HOME/.local/share/agentfactory/briefs" \
  --enable-local-ai --model qwen2.5-coder:7b
```

The pinned Core profile also allows `qwen2.5-coder:14b`; that model was not
evaluated for this feature. Remote Ollama hosts and arbitrary model names are
rejected. The model route cannot be changed in an HTTP request.

Each confirmed action allows one local CLI call through Core, with a 90-second
process limit, bounded prompt/output, and no paid provider. There is no hard
token counter for this CLI route. Concurrent suggestions on this server are
rejected rather than queued. Model inventory checks use a fixed local endpoint,
no proxy or redirect, and a five-second timeout. The model digest must match
before and after inference.

An attempt is recorded before inference. A repeated request identity cannot
automatically rerun a failed or interrupted attempt. A new attempt requires a
new explicit action. A stale response cannot replace a newer human edit.
Failures preserve the last saved version and leave manual editing available.

## How facts and authority are preserved

Core's `AutonomousMissionIntakeService.create_from_text` stores the original
as an authoritative source and creates a `DRAFT` mission. It grants no
development approval or budget. The Cloud database records that mission/source
identity, the original checksum, immutable brief versions, answers, and
model evidence. A retry after a Core-only commit reuses the same Core command.

The current AI method is `source-statement-selection-v1`. The host splits the
original into numbered statements. The model may return only eight integer
statement selections; zero means unknown. The host copies the selected text
from the original. Invalid shapes or selections are rejected. This prevents
the model from inventing new wording or quantities in an accepted field. It
does not prove that the selected sentence describes the right field or that
every requirement was selected. The unchanged source remains available for
review and is not replaced by the shorter brief.

Missing-field questions and suggested answers are fixed product copy, not
facts extracted by AI. The user must choose or edit an answer. The versioned
format keeps assumptions separate; this extractive adapter creates none.

Model evidence records the provider, model/digest, Core profile checksum,
input version/checksum, method, start/end time and limits. This evidence covers
brief organization only. It is not a readiness receipt for development, a
claim of game quality, or approval to run a generated project.

## Intake evaluation report

Evaluated on 2026-09-06 using the installed `local:qwen2.5-coder:7b` through
the pinned Core CLI provider. No inference was mocked in these three cases.
The inputs below are synthetic examples, not private user briefs.

| Example | Actual result | Limit found by review |
| --- | --- | --- |
| English: Windows garden game, arrow keys, three seeds, no fighting, green pixel art, win by bringing all seeds home | Valid selections, exact original retained, selected quantities unchanged | Player activity was mapped to the winning sentence; genre was left blank |
| Ukrainian: Windows cat game, arrows, three stars, no fighting, warm pixel art, win by bringing all stars home | Valid selections, exact Ukrainian source retained, no translation or changed quantity | Player activity was left blank, so one Ukrainian clarification question appeared |
| English: a fun game, kind and platform undecided | All fields left unknown; three focused questions with answer options | No invented platform, genre, timer or loss condition |

All three passed structural validation and exact-source preservation. This
small evaluation supports optional, human-reviewed source organization only.
It does not qualify unattended semantic planning or the full age-12+ creator
experience. A broader multilingual quality evaluation and actual creator
usability sessions remain necessary before making those claims.

Model digest:
`dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
Provider profile SHA-256:
`b7d6198d0677a6ca30ae98caac09f7a499b0cbf2e45a256957b61783a04090f2`.

Earlier free-text experiments changed item counts and added unrequested loss
rules. A stricter quote-only prompt then failed validation on all three cases.
Those approaches were rejected. The accepted method limits output to source
indices and copies the text in application code; successful JSON alone is
never treated as successful understanding.

## Verification and next integration

The three `test_game_brief*` modules exercise actual Core intake, durable
versions, interrupted commands, concurrent edits, actor isolation, HTTP
boundaries, and five real Chromium journeys including mobile layout. Their
model responses are explicitly labelled synthetic fixtures. They do not count
as live model qualification.

With test dependencies installed, including `playwright` and its Chromium:

```bash
python -m unittest discover -s tests -p 'test_game_brief*.py' -v
```

Cloud008 owns the next planning/scope step. Cloud021 owns hosted identity and
tenant policy; its reviewed principal must be wired in before this local
editor can become a hosted feature. This local intake document is not the
tenant-bound `GameBrief` API record in `contracts/v1/domain.json`: that contract
also requires a server-owned Project, tenant and lifecycle state. Downstream
integration must resolve those records and map the reviewed requirements and
version explicitly; it must not invent tenant or project authority from a local
actor name. Engine execution, Unreal editor control,
packaging a Windows game, and AI systems inside the shipped game remain
separate downstream capabilities. This intake cannot certify any of them.
