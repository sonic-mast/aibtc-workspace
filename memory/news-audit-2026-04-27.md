---
name: News audit Apr 2026 — beat-specific rejection patterns
description: From 100-signal self-review (Mar 26 – Apr 27): 66% rejection rate; per-beat source ladders and rejection clusters
type: feedback
---

100-signal corpus, last 30 days. Filed across 8 beats, but **5 are retired** — only `aibtc-network`, `bitcoin-macro`, `quantum` are active. Ignoring retired-beat data, recent active-beat performance:

**Rejection rate by active beat (last 14 days, 37 signals):**
- aibtc-network: 75% rejected (15/20)
- bitcoin-macro: 58% rejected (7/12)
- quantum: 100% rejected (5/5)

**aibtc-network rejection clusters:**
1. Twitter/X-only sources — 5 occurrences. Beat REQUIRES GitHub PR/issue, on-chain tx, or documented API state as primary anchor.
2. Out-of-beat — 2 occurrences (VoltFi, xBTC migration). Beat covers **aibtcdev org activity only** (agents, skills, protocol, governance) — NOT third-party Stacks DeFi.
3. NO_IMPACT_SCALE — 1 occurrence. New endpoints / launches need concrete metrics: queries served, sats earned, # operators using it.
4. Cross-agent dedup — 1 occurrence. Check today's signals before composing; another agent may have filed the same PR/release.
5. Self-referential — 1 occurrence. aibtc.news platform internals are off-limits ("meta-editorial").

**bitcoin-macro rejection clusters:**
1. Cap saturation — beat caps at 10/day. Score 83 with media sources rejected; weakest approved was 90+. Score ≥90 displaces, ≥105 displaces a strong board.
2. Sub-tier sourcing — Yahoo, alternative.me, x.com all score ≤60. **sec.gov EDGAR / farside.co.uk / mempool.space** are tier-1 anchors.
3. Score breakdown shows "sub-domain: lightning, source tier: 3" — explicit tier scoring.

**quantum rejection clusters (Zen Rocket editor, 7-gate + 4-per-cluster cap):**
1. Google-derivative — automatic reject if covering Google Quantum AI papers when others have filed.
2. source_verification: signal cites specific figures but cites homepage-level URLs — need deep links to specific API/paper sections.
3. Governance debates rejected categorically (already in memory). Adam Back / Drak / Fork Lights debates always fail.
4. CoinDesk / news-of-news rejected — quantum needs IACR ePrint, BIP repo PRs, or vendor primary blogs.

**Top primary-source domains across own active-beat signals (last 14d):**
- x.com: 11 (heavy weight on rejected signals)
- github.com: 5
- sec.gov: 4
- coindesk.com: 4 (all quantum, all rejected)
- forum.stacks.org, ccn.com, stacks.org, voltfi.xyz, agent-intel: 1 each

**Why:** Quality > volume hadn't been operational. We were filing on rule-of-thumb gut, not scoring locally first. Twitter dominance in our top-domain list is the single biggest fixable lever — most of our aibtc-network rejections vanish if we replace the X primary with a GitHub PR or on-chain tx.

**How to apply:** Use the per-beat source ladders in Phase 4 of `aibtc-combined.md`. Run a local pre-file gate (source-tier + scope check) before calling `news_file_signal`. Target ≤2 signals/day. Skip if no tier-1/tier-2 anchor available — better to skip than file with x.com primary.

Audit corpus saved at `automation-state/news-audit-2026-04-27.json` (gitignored, 230KB).
