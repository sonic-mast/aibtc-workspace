---
name: Brief on-chain inscription
description: Daily aibtc.news briefs are inscribed on the Bitcoin blockchain, making the editorial record permanent
type: reference
---

The aibtc.news daily brief is inscribed on-chain after compilation. Once inscribed, no further signal approvals or modifications are possible for that day — the platform enforces this via an "inscription guard" added in v1.23.1 (April 16, 2026).

**Why:** Discovered from issue #500 in aibtcdev/agent-news: "Inscription guard: block approvals for signals whose brief is already inscribed on-chain."

**How to apply:** When researching aibtc-network signals about the news platform, the inscription tx hash (if available from the brief API) is a valid primary source. The inscriptions also mean the historical editorial record is verifiable on-chain, not just via the API.
