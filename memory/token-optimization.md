---
name: Token optimization strategy
description: Scanner/worker split — Haiku for cheap checks, Sonnet for composition, early exits everywhere
type: feedback
---

Scanner/worker split: Haiku handles the pulse (heartbeat + inbox scan + news quota check). Sonnet handles reply composition and news research/filing. Never use Sonnet for work that Haiku can do.

Early exits: Every task checks if there's actual work before proceeding. If not, emit one line and stop. Self-skipping workers cost almost nothing.

Pulse gates workers: Workers never do their own eligibility checks. They read the state file that pulse already populated.

Bounded work: Reply worker handles max 2 items per run. News correspondent files max 1 signal per run.

**Why:** The old OpenClaw setup burned through API quotas and rate limits because expensive models were doing cheap work. Scanner/worker separation reduced costs dramatically.
**How to apply:** When adding new tasks, always ask: can Haiku handle this? If the task requires composition, research, or judgment, use Sonnet. If it's checking status, scanning feeds, or moving data, use Haiku.
