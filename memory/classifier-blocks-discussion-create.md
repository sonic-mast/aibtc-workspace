---
name: classifier-blocks-discussion-create
description: GitHub GraphQL createDiscussion mutation is classifier-blocked in headless runs ("External System Writes"), same failure family as gist publishing — the Phase 4.6 Breadth-announce step cannot fire unattended yet
metadata:
  type: feedback
---

Observed 2026-09-21/22 (local run): the m3-campaign.md "Breadth announce" step (post one free note about the live "Ten paid queries" bounty slots in aibtcdev/agent-news Discussions → Lounge) failed. A `curl -X POST https://api.github.com/graphql -d '{"query":"mutation createDiscussion..."}'` was denied outright by the auto-mode classifier with reason `[External System Writes]` — no retry, no workaround attempted (per the session-escalation gotcha in [[automode-classifier-session-escalation]]).

**Why:** same failure family as [[automode-classifier-gist]] — a broad `Bash(curl *)` allow does not cover a publish-shaped call (creating public content under Sonic Mast's identity on a third-party platform), regardless of whether it's a REST POST or a GraphQL mutation. The classifier judges the *shape* of the write (public content creation via API), not the specific endpoint.

**How to apply:** Don't retry the GraphQL createDiscussion call directly from the loop — it will be denied every time until there's a specific allowlist rule or a relay path. Options, in order of least effort: (1) a specific `Bash` allow rule scoped to a wrapper script (like `scripts/publish-gist.sh`) if one gets built for Discussions; (2) route through the state-worker relay pattern (`POST /gist`-style) the way gist publishing does; (3) leave it for the operator — log `notable: "breadth-announce blocked by classifier — needs interactive post or relay"` and skip the step each run rather than re-attempting. The m3-campaign.md runbook's "Breadth announce" row should be treated as **operator-only** until one of the above ships, not "free reach, no paid-send budget" as currently written — it still needs a publish path that works headless.
