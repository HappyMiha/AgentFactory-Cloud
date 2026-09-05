# Contributing

Read [AGENTS.md](AGENTS.md) and the [three-computer workflow](docs/team-workflow.md).

The worker names are HappyDucky02, HappySnowman, and HappyHahahaker. Configure each clone with the correct worker, inspect the shared register, and claim a ready task before starting. Use your own `team/<worker>/...` branch and declare the files you plan to change.

Commit a focused change, fetch and incorporate current `main`, and run `python scripts/team_checks.py`. The pre-push hook checks the current claim, dependencies, scope, branch history, and exact-commit evidence. Do not force-push or bypass hooks.

Use one PR per task. Include actual tests and known failures. HappyDucky02 coordinates merges initially; another worker reviews the result. A dependency is ready only after its work is merged and recorded, not merely pushed. Product acceptance still follows the source backlog.

The Cloud product remains planned. Coordination scripts and checks are development tools; they do not implement game generation, hosting, payments, or a product task. Public repository visibility does not choose a Cloud software license; those terms remain an owner decision.
