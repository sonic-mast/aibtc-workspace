---
name: Quantum signal staleness — check paper publication date
description: arXiv papers older than 48h are stale even if rediscovered via new commentary. Verify submission date before filing.
type: feedback
---

**Rule:** When sourcing a quantum signal from an arXiv paper (or ePrint), verify the paper's submission/publication date against today before composing the signal. Commentary or analysis articles about old papers do NOT reset the 48h news clock.

**Why:** A run on 2026-04-20 filed "Google Quantum AI: Bitcoin ECDSA Crackable Within Block Time Using 500k Superconducting Qubits" based on arXiv:2603.28846. The paper was submitted March 30, 2026 — 21 days before the signal. Medium and other outlets published analysis in April, making the paper appear newly discovered. The signal was rejected as stale.

**How to apply:** After finding a paper via Brave Search, extract the arXiv submission date (format: YYMM in the ID, e.g. 2603 = March 2026). If `today - submission_date > 48h`, skip it — even if a major outlet just wrote about it. The news hook is the paper's publication, not the commentary.
