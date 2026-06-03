# x402 Multi-Token Endpoint

**Live URL:** `https://x402-multi-token.brandonmarshall.workers.dev`  
**Agent:** Sonic Mast — `SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47` / `bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`  
**Stack:** Hono.js on Cloudflare Workers (always-on, no sleep)  
**Bounty:** `mpmvuqlz8bfc9790ad94`

---

## Endpoints

| Path | Description |
|------|-------------|
| `GET /` | Service info |
| `GET /health` | Health check |
| `GET /api/quote` | Price quote — accepts **sBTC, STX, or USDCx** |
| `GET /api/quote/stx` | Same quote — STX only |
| `GET /api/quote/usdcx` | Same quote — USDCx only |

---

## Token Contracts (mainnet)

| Token | Contract | Amount |
|-------|----------|--------|
| sBTC | `SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4.sbtc-token` | 1000 sats |
| STX | native | 1,000,000 microSTX (1 STX) |
| USDCx | `SP120SBRBQJ00MCWS7TM5R8WJNTTKD5K0HFRC2CNE.usdcx` (Velar) | 1,000,000 micro-USDCx (1 USDCx) |

Recipient: `SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47`  
Relay: `https://x402-relay.aibtc.com`  
Network: `stacks:1` (mainnet)

---

## Probe (no payment)

```bash
curl https://x402-multi-token.brandonmarshall.workers.dev/api/quote
```

Returns HTTP 402 with `payment-required` header (base64 JSON) and body:

```json
{
  "x402Version": 2,
  "resource": { "url": "...", "description": "...", "mimeType": "application/json" },
  "accepts": [
    { "scheme": "exact", "network": "stacks:1", "amount": "1000",    "asset": "SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4.sbtc-token", "payTo": "SPG6..." },
    { "scheme": "exact", "network": "stacks:1", "amount": "1000000", "asset": "STX",                                                      "payTo": "SPG6..." },
    { "scheme": "exact", "network": "stacks:1", "amount": "1000000", "asset": "SP120SBRBQJ00MCWS7TM5R8WJNTTKD5K0HFRC2CNE.usdcx",          "payTo": "SPG6..." }
  ]
}
```

---

## Payment (x402 V2)

The endpoint accepts two payment header formats:

- **`payment-signature`** — aibtc `execute_x402_endpoint` client format (base64 JSON with `x402Version`, `resource`, `accepted`, `payload.transaction`, `extensions`)
- **`X-PAYMENT`** — standard x402 V2 client format (base64 JSON paymentPayload)

Payment verification:
1. Calls `POST /verify` on the relay for local validation (no broadcast) — works for STX and sBTC
2. Falls back to `POST /relay` for assets the relay can't verify locally (USDCx) — broadcasts and settles

On success, returns HTTP 200:
```json
{
  "ok": true,
  "quote": { "btcUsd": 66300, "stxUsd": 2.15, "sbtcPerBtc": 1.0, "fetchedAt": "...", "note": "Indicative prices" },
  "payment": { "txId": "...", "payer": "SP...", "token": "sBTC|STX|USDCx", "amount": "..." }
}
```

---

## Live Demo Payments (mainnet)

| Token | txid | Amount |
|-------|------|--------|
| sBTC | `f713cc7fe4b1c589fd46f016040f024ce9b483994a38b75f39fa2c6b908c5f64` | 1000 sats |
| STX | `16fa24e5500d25fa47780a08839ddefa7d2532d15f8ad6063a2ddf5ee429ed7d` | 1,000,000 microSTX |
| USDCx | `12c0327a872aa612d11cc65a2beb7e38ad4b5a018ab7fb4cf88f6ef464e2ec26` | 1,000,000 micro-USDCx |

All three payments from `SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47` to `SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47` (self-pay demo).

---

## Error Codes

| HTTP | Code | Condition |
|------|------|-----------|
| 402 | — | No payment header — returns full `accepts[]` |
| 400 | `PAYMENT_INVALID` | Cannot decode payment header or bad signature |
| 400 | `UNKNOWN_TOKEN` | Asset not recognized |
| 402 | `PAYMENT_EXPIRED` | Stale nonce / expired window |
| 402 | `AMOUNT_TOO_LOW` | Transferred amount below minimum |
| 400 | `PAYMENT_INVALID` | Recipient mismatch |
| 503 | `RELAY_UNAVAILABLE` | Relay returned 5xx or timed out — `Retry-After: 30` |
| 502 | `NETWORK_ERROR` | Network error reaching relay — `Retry-After: 5` |

---

## Deploy

```bash
npm install
npx wrangler deploy
```

Set `RECIPIENT_ADDRESS`, `NETWORK`, and `RELAY_URL` in `wrangler.jsonc` or as Cloudflare secrets.
