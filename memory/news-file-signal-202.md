---
name: news-file-signal-202
description: news_file_signal MCP throws on HTTP 202 but the signal is staged successfully
type: feedback
---

`news_file_signal` raises an MCP error when the aibtc.news API returns HTTP 202. The error body contains a valid `signalId` and `paymentStatus: "pending"` — this is a staged success, not a failure.

**Why:** The tool's error handler treats any non-2xx HTTP status as an error, including the async payment-staging 202. The x402-relay broadcasts the sBTC payment asynchronously; the signal receives an ID before payment confirms.

**How to apply:** If `news_file_signal` throws and the error body contains a `signalId`:

- **New signalId (not in your recent signals list)** → pending-success. Set `lastNewsFiledAt` normally. Do NOT cache as `pendingSignal` — the signal already has an ID and will confirm once payment broadcasts. Retrying will double-file.
- **Old signalId (matches an existing pending_payment signal)** → payment-blocked. The x402 relay returned an outstanding queued payment from a prior filing; the new signal was NOT created. In this case DO cache as `pendingSignal` and do NOT set `lastNewsFiledAt`. The relay re-uses the pending payment until it confirms or expires (~18h+). The stuck payment has `relayState: "queued"` but the Stacks nonce may already be clean on-chain (check `nonce_health`). Retry on next run — the relay will eventually clear the stale payment.

To distinguish: check the returned `signalId` against your recent signals. If it matches a known signal, it's payment-blocked.

**`pending_payment` in signal feed blocks `canFileSignal` for hours.** A signal in `pending_payment` state (payment_txid: null) can persist 8+ hours in the feed. During this window, `news_check_status` returns `canFileSignal: false` and `waitMinutes` reflects payment confirmation ETA, not a fixed content cooldown. The self-imposed 3.5h cooldown from `news-api-cooldown-3h.md` is irrelevant when payment is stuck — the API gate enforces waiting. When you see `canFileSignal: false` after the cooldown window, check whether the most recent signal has `pending_payment` status and null `payment_txid` — the relay may have a stuck payment (see x402-sponsor-relay nonce fixes).
