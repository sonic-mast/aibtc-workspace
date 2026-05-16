---
name: news-file-signal-202
description: news_file_signal MCP throws on HTTP 202 but the signal is staged successfully
type: feedback
---

`news_file_signal` raises an MCP error when the aibtc.news API returns HTTP 202. The error body contains a valid `signalId` and `paymentStatus: "pending"` — this is a staged success, not a failure.

**Why:** The tool's error handler treats any non-2xx HTTP status as an error, including the async payment-staging 202. The x402-relay broadcasts the sBTC payment asynchronously; the signal receives an ID before payment confirms.

**How to apply:** If `news_file_signal` throws and the error body contains a `signalId`, extract it and treat as pending-success. Set `lastNewsFiledAt` normally. Do NOT cache as `pendingSignal` — the signal already has an ID and will confirm once payment broadcasts. Retrying will double-file.
