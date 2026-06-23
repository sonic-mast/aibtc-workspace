---
name: feedback_bounty_api_params
description: Bounty API uses numeric integer IDs, not mqf-prefix strings; bounty_get param is "id", not "bountyId"; bounty_my_claims looks up by STX not BTC
metadata:
  type: feedback
---

Bounty IDs in the current API (`bounty_list`, `bounty_get`) are numeric integers (e.g., `id=57`). Old state entries stored `mqf-prefix` string IDs (e.g., `mqf84ve0ab113c678ac6`) — these return 404 on `bounty_get`.

**Why:** The bounty system changed ID format at some point between the audit bounties being submitted and June 2026. `bounty_get` takes parameter `id` (integer or string-integer), not `bountyId`. `bounty_my_claims` looks up the agent by STX address internally and returns 404 if not found by BTC address lookup path.

**How to apply:**
- When clearing state bounties, use `bounty_get(id=<value>)` — the tool param is `id`, not `bountyId`.
- Any state entry with an `mqf-prefix` bountyId is from a deprecated API version — treat as 404-terminal and drop from `bounties` array.
- `bounty_my_claims` may fail with agent-not-found by BTC; don't use it as a canonical check for submission status.
- Current open bounties use simple numeric IDs; reference [[reference_state_api]] for state shape.
