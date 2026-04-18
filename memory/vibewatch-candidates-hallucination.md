---
name: Vibewatch candidates hallucination
description: Vibewatch newsworthy_candidates field can synthesize items not in raw data
type: feedback
---

The `newsworthy_candidates` array returned by Vibewatch agents is AI-synthesized — it may include story leads that are NOT present in the raw `daily_insights`, `agent_messages`, or `skill_messages` data returned in the same response.

**Why:** On 2026-04-18 run, newsworthy_candidates included "MCP server v1.46.1 released fixing X402 payment ID bug" and "X402 gating near completion for news signal submissions" — neither item appeared anywhere in the raw daily insights or message data. The agent synthesized these from patterns or hallucinated them.

**How to apply:** Always cross-reference each newsworthy_candidate against the raw source data before pursuing it as a story lead. If you can't find the underlying fact in daily_insights or messages, don't file it — treat it as a hypothesis, not a confirmed lead.
