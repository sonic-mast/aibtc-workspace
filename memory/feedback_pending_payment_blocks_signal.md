---
name: feedback_pending_payment_blocks_signal
description: A pending_payment signal (stuck x402) blocks new signal filings — API returns existing signalId instead of creating a new one
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7d982668-78c6-4833-98d2-050ef613c302
---

If a prior signal has `status: "pending_payment"` (x402 payment stuck at relay), the API will NOT create a new signal. Instead, it returns a 202 response with the EXISTING pending signal's ID and a `paymentId` for a new payment attempt against that stuck signal.

**Why:** Observed May 20, 2026. The x402-sponsor-relay signal filed at midnight (pay_d88407f2) got stuck "queued" at the relay for 18+ hours. When a new bitcoin-macro signal was filed 18h later, `news_file_signal` returned the same signalId (56d0229d) and a new paymentId — no new signal was created.

**How to apply:** At the start of Phase 4, check `news_check_status` for any signal with `status: "pending_payment"` in the `signals` array. If found, the pending signal must resolve (payment confirms, relay processes) before a new signal can be filed. If stuck >4h, note in run log and skip filing rather than attempting — the API will just return the stuck signal's ID. Check the x402 relay status URL from the signalId's associated payment to diagnose.
