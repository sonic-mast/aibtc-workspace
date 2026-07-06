---
name: verify-before-filing
description: Before filing a signal, verify every identifier (CVE/BIP/contract) on a primary source, and never trust AI-synthesized leads (vibewatch newsworthy_candidates) without cross-checking raw data
metadata:
  type: feedback
---

## Verify identifiers on primary sources
CVE IDs, BIP numbers, and contract addresses must be verified on primary sources before use in a signal — hallucinated or mis-stated identifiers cause rejection. Never emit an identifier from memory alone: confirm it (CVE on the CVE/NVD record, BIP on the bitcoin/bips repo, contract on-chain).

## Don't trust AI-synthesized leads
The vibewatch `newsworthy_candidates` field is **AI-synthesized**, not raw signal. Cross-check each item against the raw `daily_insights`/`messages` before pursuing it as a story lead — the synthesis can invent or distort details. Treat it as a pointer to investigate, never as a citable fact.
