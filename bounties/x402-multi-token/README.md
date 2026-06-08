# x402-multi-token

x402-enabled API endpoints on Cloudflare Workers.

Built using patterns from:
- [x402-api](https://github.com/aibtcdev/x402-api)
- [stx402](https://github.com/whoabuddy/stx402)

## Quick Start

```bash
# Install dependencies
npm install

# Set your recipient address for local dev
# Edit .dev.vars and replace YOUR_STACKS_ADDRESS_HERE with your address

# Start local dev server
npm run dev
```

The server will start at http://localhost:8787

## Payment Tokens

This API accepts payments in:
- sBTC

## Endpoints

### GET /
- **Description:** Service info
- **Cost:** Free

### GET /health
- **Description:** Health check endpoint
- **Cost:** Free

### GET /api/quote
- **Description:** Multi-token premium data endpoint — accepts sBTC, STX, or USDCx
- **Cost:** 0.0001 sBTC
- **Payment Required:** Yes

## Deployment

### Set Production Secrets

```bash
# Set your recipient address (where payments will be sent)
wrangler secret put RECIPIENT_ADDRESS
# Enter: SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47
```

### Deploy

```bash
# Deploy to staging (testnet)
npm run deploy:staging

# Deploy to production (mainnet)
npm run deploy:production
```

## x402 Payment Flow

1. Client makes request without payment header
2. Server returns HTTP 402 with payment requirements:
   ```json
   {
     "maxAmountRequired": "1000",
     "resource": "/api/endpoint",
     "payTo": "SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47",
     "network": "testnet",
     "tokenType": "STX",
     "nonce": "uuid",
     "expiresAt": "2024-01-01T00:05:00Z"
   }
   ```
3. Client signs payment transaction (does NOT broadcast)
4. Client retries request with `X-PAYMENT` header containing signed tx
5. Server verifies and settles payment via relay
6. Server returns actual response

## Testing with curl

```bash
# Service info (free)
curl http://localhost:8787/

# Health check (free)
curl http://localhost:8787/health

# Protected endpoint (returns 402)
curl http://localhost:8787/api/quote
```

## Token Type Selection

Clients can specify which token to pay with using the `X-PAYMENT-TOKEN-TYPE` header:

```bash
# Pay with sBTC instead of STX
curl -H "X-PAYMENT-TOKEN-TYPE: sBTC" http://localhost:8787/api/quote
```

Supported values: `STX`, `sBTC`, `USDCx`

## Error Codes

The API returns structured error responses for payment failures:

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INSUFFICIENT_FUNDS` | Wallet needs funding | 402 |
| `PAYMENT_EXPIRED` | Sign a new payment | 402 |
| `AMOUNT_TOO_LOW` | Payment below minimum | 402 |
| `PAYMENT_INVALID` | Bad signature/params | 400 |
| `NETWORK_ERROR` | Transient error | 502 |
| `RELAY_UNAVAILABLE` | Try again later | 503 |

---

Generated with [@aibtc/mcp-server](https://www.npmjs.com/package/@aibtc/mcp-server) scaffold tool.
