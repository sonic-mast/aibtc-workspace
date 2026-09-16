---
name: posted-bounty-duplicate-txid
description: A0 posted-bounty watch's Hiro pre-check passes a mechanically-valid tx even when the same txid was already used to claim a sibling bounty slot; flag reuse explicitly
metadata:
  type: feedback
---

The A0 posted-bounty precheck (Phase 4.5) verifies a submission's txid is anchored, pays the right asset/amount to the right payTo, and isn't from our own or an already-won address — but it does not check whether that same txid was already submitted to a *different* bounty in the same series. On 2026-09-16, submitter SP3QJZBCXQW9XFK5K07C74TS68SZ545XSP0FNX39B submitted the identical sBTC-payment txid (`0xb385d8...2acfc8`) to both "First paid query ... (4 of 5)" (`mtwd0cet93a16ab82498`) and "(3 of 5)" (`mtwd044j16ce91c68417`) within 30 minutes — one 100-sat payment used to try to claim two separate 5,000-sat slots.

**Why:** the per-bounty precheck only reasons about that one bounty's `postedBountyWatch` entry; it has no cross-bounty view, so a receipt reused across sibling slots reads as `pass` twice with nothing flagging the overlap for the operator.

**How to apply:** when running A0 across multiple sibling bounty slots (same series, same payTo/verification rule) in one run, diff each new submission's txid against every other slot's recorded txids in `postedBountyWatch` before logging `precheck`. If a txid repeats across slots, keep `precheck: "pass"` (mechanically true) but add an explicit `note` on both entries naming the other bounty id, and say so plainly in the operator ping — this is a double-dip attempt, not a normal duplicate-submission case, and needs an operator decision on which (if either) to accept before either is paid.
