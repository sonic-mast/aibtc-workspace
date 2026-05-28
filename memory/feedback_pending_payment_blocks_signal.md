---
name: feedback_pending_payment_blocks_signal
description: pending_payment on same beat blocks new filing (returns existing ID); cross-beat filing creates a new signal even with a pending_payment open
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7d982668-78c6-4833-98d2-050ef613c302
---

**Same-beat block (May 20 observation):** If a prior signal on beat X has `status: "pending_payment"`, filing another signal on the SAME beat X returns the EXISTING pending signal's ID and a new paymentId — no new signal is created.

**Cross-beat filing works (May 28 observation):** A pending_payment on bitcoin-macro did NOT block a new aibtc-network signal. The API created a NEW signalId (`301c9744`) for the different-beat signal. The payment still goes to the relay queue (202 response), but the signal is new.

**Why:** Observed May 20, 2026 (same-beat block): x402-sponsor-relay signal stuck 18h+; new bitcoin-macro filing returned same signalId (56d0229d). Observed May 28, 2026 (cross-beat unblocked): pending_payment ef437f8a (bitcoin-macro, 22h old) did not redirect a new aibtc-network signal.

**How to apply:** At the start of Phase 4, check for `pending_payment` signals. If the PENDING signal is on the SAME beat you plan to file on, skip that beat this run. Cross-beat filing is safe — proceed normally. The API still returns 202 (relay queued), not 200 (immediate confirm).
