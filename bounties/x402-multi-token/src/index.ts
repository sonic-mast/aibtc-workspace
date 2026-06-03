// BigInt.toJSON polyfill
(BigInt.prototype as unknown as { toJSON: () => string }).toJSON = function () {
  return this.toString();
};

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { Context, Next } from 'hono';
import { createHash } from 'node:crypto';

type Env = {
  RECIPIENT_ADDRESS: string;
  NETWORK: string;
  RELAY_URL: string;
};

type Variables = {
  x402?: {
    payerAddress: string;
    txId: string;
    tokenType: string;
    amount: string;
  };
};

// x402v2 format: network identifiers
const NETWORKS: Record<string, string> = {
  mainnet: 'stacks:1',
  testnet: 'stacks:2147483648',
};

const TOKEN_CONFIG = {
  sBTC: {
    asset: 'SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4.sbtc-token',
    contract: { address: 'SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4', name: 'sbtc-token' },
    amount: '1000',
    label: '1000 sats sBTC',
    tokenType: 'sBTC',
  },
  STX: {
    asset: 'STX',
    contract: null as null,
    amount: '1000000',
    label: '1 STX (1000000 microSTX)',
    tokenType: 'STX',
  },
  USDCx: {
    asset: 'SP120SBRBQJ00MCWS7TM5R8WJNTTKD5K0HFRC2CNE.usdcx',
    contract: { address: 'SP120SBRBQJ00MCWS7TM5R8WJNTTKD5K0HFRC2CNE', name: 'usdcx' },
    amount: '1000000',
    label: '1 USDCx (Velar, 6 decimals)',
    tokenType: 'USDCx',
  },
} as const;

type TokenType = keyof typeof TOKEN_CONFIG;

const app = new Hono<{ Bindings: Env; Variables: Variables }>();

app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  allowHeaders: ['X-PAYMENT', 'X-PAYMENT-TOKEN-TYPE', 'Authorization', 'Content-Type', 'payment-signature'],
  exposeHeaders: ['X-PAYMENT-RESPONSE', 'X-PAYER-ADDRESS', 'payment-required', 'payment-response'],
}));

app.get('/', (c) => c.json({
  service: 'sonic-mast/x402-multi-token',
  version: '1.0.0',
  x402Version: 2,
  bounty: 'mpmvuqlz8bfc9790ad94',
  agent: 'Sonic Mast',
  btcAddress: 'bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47',
  stxAddress: 'SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47',
  endpoints: [{ path: '/api/quote', method: 'GET', accepts: ['sBTC', 'STX', 'USDCx'] }],
  usage: 'GET /api/quote  → 402 + payment-required header listing all 3 token options',
}));

app.get('/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }));

type TokenCfg = typeof TOKEN_CONFIG[TokenType];
type PayReqs = Record<string, unknown>;

async function settlePayment(
  parsedPayment: Record<string, unknown>,
  paymentRequirements: PayReqs,
  txHex: string,
  relayUrl: string,
  recipientAddress: string,
  tokenCfg: TokenCfg,
  tokenType: TokenType,
): Promise<{ ok: true; txId: string; payerAddress: string } | { ok: false; error: Record<string, string>; status: number }> {
  // Compute txid (SHA-512/256 of serialized tx bytes — Stacks standard)
  let txId = '';
  if (txHex.startsWith('0x')) {
    try { txId = createHash('sha512-256').update(Buffer.from(txHex.slice(2), 'hex')).digest('hex'); } catch { txId = ''; }
  }

  // Try /verify (local validation, no broadcast)
  let payerAddress = '';
  try {
    const verifyRes = await fetch(`${relayUrl}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paymentPayload: parsedPayment, paymentRequirements }),
      signal: AbortSignal.timeout(20000),
    });
    if (verifyRes.status < 500) {
      const vr = await verifyRes.json() as { isValid: boolean; invalidReason?: string; payer?: string };
      if (vr.isValid) {
        payerAddress = String(vr.payer ?? 'unknown');
      } else {
        const reason = String(vr.invalidReason || 'invalid').toLowerCase();
        if (reason.includes('unsupported_scheme') || reason.includes('unrecognized_asset')) {
          // fall through to /relay fallback
        } else if (reason.includes('expired') || reason.includes('nonce')) {
          return { ok: false, error: { error: 'Payment expired', code: 'PAYMENT_EXPIRED' }, status: 402 };
        } else if (reason.includes('amount') || reason.includes('insufficient')) {
          return { ok: false, error: { error: 'Payment amount too low', code: 'AMOUNT_TOO_LOW' }, status: 402 };
        } else if (reason.includes('mismatch') || reason.includes('recipient')) {
          return { ok: false, error: { error: 'Payment recipient mismatch', code: 'PAYMENT_INVALID', detail: reason }, status: 400 };
        } else {
          return { ok: false, error: { error: 'Payment invalid', code: 'PAYMENT_INVALID', detail: reason }, status: 400 };
        }
      }
    }
  } catch { /* fall through to /relay */ }

  // Fallback: /relay broadcast+verify (for assets relay can't verify locally)
  if (!payerAddress && txHex.startsWith('0x')) {
    try {
      const relayRes = await fetch(`${relayUrl}/relay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction: txHex,
          settle: { expectedRecipient: recipientAddress, minAmount: tokenCfg.amount, tokenType },
        }),
        signal: AbortSignal.timeout(30000),
      });
      const rr = await relayRes.json() as { success: boolean; txid?: string; error?: string; code?: string };
      if (rr.success) {
        txId = String(rr.txid || txId);
        payerAddress = 'unknown';
      } else {
        const errCode = String(rr.code || rr.error || 'invalid').toLowerCase();
        if (errCode.includes('amount') || errCode.includes('low')) {
          return { ok: false, error: { error: 'Payment amount too low', code: 'AMOUNT_TOO_LOW' }, status: 402 };
        }
        return { ok: false, error: { error: 'Payment invalid', code: 'PAYMENT_INVALID', detail: errCode }, status: 400 };
      }
    } catch (err: unknown) {
      const e = err as Error;
      if (e.name === 'TimeoutError' || e.name === 'AbortError') {
        return { ok: false, error: { error: 'Relay timeout', code: 'RELAY_UNAVAILABLE' }, status: 503 };
      }
      return { ok: false, error: { error: 'Network error', code: 'NETWORK_ERROR', detail: String(err) }, status: 502 };
    }
  }

  if (!payerAddress) {
    return { ok: false, error: { error: 'Payment could not be verified', code: 'PAYMENT_INVALID' }, status: 400 };
  }

  return { ok: true, txId, payerAddress };
}

// Multi-token x402v2 middleware
async function multiTokenMiddleware(
  c: Context<{ Bindings: Env; Variables: Variables }>,
  next: Next,
) {
  const env = c.env;
  const network = (env.NETWORK || 'mainnet') as 'mainnet' | 'testnet';
  const networkId = NETWORKS[network] || 'stacks:1';
  const relayUrl = env.RELAY_URL || 'https://x402-relay.aibtc.com';
  const recipientAddress = env.RECIPIENT_ADDRESS;
  const resource = c.req.url;

  // Accept both payment-signature (aibtc execute_x402_endpoint) and X-PAYMENT (standard x402 clients)
  const paymentHeader = c.req.header('payment-signature') || c.req.header('X-PAYMENT') || c.req.header('x-payment');

  if (!paymentHeader) {
    // Build x402v2 payment requirements
    const payReq = {
      x402Version: 2,
      resource: {
        url: resource,
        description: 'Premium BTC/STX price quote - multi-token x402 endpoint',
        mimeType: 'application/json',
      },
      accepts: [
        {
          scheme: 'exact',
          network: networkId,
          amount: TOKEN_CONFIG.sBTC.amount,
          asset: TOKEN_CONFIG.sBTC.asset,
          payTo: recipientAddress,
          maxTimeoutSeconds: 300,
          extra: { label: TOKEN_CONFIG.sBTC.label, tokenType: 'sBTC', tokenContract: TOKEN_CONFIG.sBTC.contract },
        },
        {
          scheme: 'exact',
          network: networkId,
          amount: TOKEN_CONFIG.STX.amount,
          asset: TOKEN_CONFIG.STX.asset,
          payTo: recipientAddress,
          maxTimeoutSeconds: 300,
          extra: { label: TOKEN_CONFIG.STX.label, tokenType: 'STX' },
        },
        {
          scheme: 'exact',
          network: networkId,
          amount: TOKEN_CONFIG.USDCx.amount,
          asset: TOKEN_CONFIG.USDCx.asset,
          payTo: recipientAddress,
          maxTimeoutSeconds: 300,
          extra: { label: TOKEN_CONFIG.USDCx.label, tokenType: 'USDCx', tokenContract: TOKEN_CONFIG.USDCx.contract },
        },
      ],
    };

    const encoded = btoa(JSON.stringify(payReq));
    c.header('payment-required', encoded);
    return c.json(payReq, 402);
  }

  // Parse payment header (base64 JSON)
  let parsedPayment: Record<string, unknown>;
  try {
    parsedPayment = JSON.parse(atob(paymentHeader)) as Record<string, unknown>;
  } catch {
    return c.json({ error: 'Cannot decode payment header', code: 'PAYMENT_INVALID' }, 400);
  }

  // Determine token type: prefer accepted.asset (payment-signature format), then header hint, then asset inference
  const accepted = parsedPayment?.accepted as Record<string, unknown> | undefined;
  const acceptedAsset = String(accepted?.asset || '');
  const headerHint = c.req.header('X-PAYMENT-TOKEN-TYPE')?.toUpperCase() ?? '';

  let tokenType: TokenType;
  const assetToCheck = acceptedAsset || headerHint;
  if (assetToCheck.includes('sbtc-token') || assetToCheck === 'SBTC' || assetToCheck === 'SBTC-TOKEN') {
    tokenType = 'sBTC';
  } else if (assetToCheck.toUpperCase() === 'STX') {
    tokenType = 'STX';
  } else if (assetToCheck.includes('usdcx') || assetToCheck === 'USDCX') {
    tokenType = 'USDCx';
  } else if (acceptedAsset === '') {
    tokenType = 'STX';
  } else {
    return c.json({
      error: 'Unknown token — set X-PAYMENT-TOKEN-TYPE to sBTC, STX, or USDCx',
      code: 'UNKNOWN_TOKEN',
    }, 400);
  }

  const tokenCfg = TOKEN_CONFIG[tokenType];

  const paymentRequirements = accepted && accepted.network && accepted.amount && accepted.asset && accepted.payTo
    ? { scheme: accepted.scheme || 'exact', network: accepted.network, amount: accepted.amount, asset: accepted.asset, payTo: accepted.payTo, maxTimeoutSeconds: accepted.maxTimeoutSeconds || 300 }
    : { scheme: 'exact', network: networkId, amount: tokenCfg.amount, asset: tokenCfg.asset, payTo: recipientAddress, maxTimeoutSeconds: 300 };

  const txHex = String((parsedPayment.payload as Record<string, unknown>)?.transaction ?? '');
  const settle = await settlePayment(parsedPayment, paymentRequirements, txHex, relayUrl, recipientAddress, tokenCfg, tokenType);
  if (!settle.ok) return c.json(settle.error!, settle.status as 400 | 402 | 502 | 503);
  const { txId, payerAddress } = settle;

  c.set('x402', { payerAddress, txId, tokenType, amount: tokenCfg.amount });
  c.header('payment-response', btoa(JSON.stringify({ x402Version: 2, isValid: true, txId, token: tokenType })));
  c.header('X-PAYMENT-RESPONSE', JSON.stringify({ isValid: true, txId, token: tokenType }));
  c.header('X-PAYER-ADDRESS', payerAddress);

  await next();
}

function quoteHandler(c: Parameters<typeof multiTokenMiddleware>[0]) {
  const payment = c.get('x402');
  return c.json({
    ok: true,
    quote: {
      btcUsd: 66300,
      stxUsd: 2.15,
      sbtcPerBtc: 1.0,
      fetchedAt: new Date().toISOString(),
      note: 'Indicative prices',
    },
    payment: {
      txId: payment?.txId,
      payer: payment?.payerAddress,
      token: payment?.tokenType,
      amount: payment?.amount,
    },
  });
}

app.get('/api/quote', multiTokenMiddleware, (c) => quoteHandler(c));

// Single-token endpoints for per-token payment testing
function singleTokenMiddleware(tokenType: TokenType) {
  return async (c: Context<{ Bindings: Env; Variables: Variables }>, next: Next) => {
    const env = c.env;
    const network = (env.NETWORK || 'mainnet') as 'mainnet' | 'testnet';
    const networkId = NETWORKS[network] || 'stacks:1';
    const relayUrl = env.RELAY_URL || 'https://x402-relay.aibtc.com';
    const recipientAddress = env.RECIPIENT_ADDRESS;
    const resource = c.req.url;
    const tokenCfg = TOKEN_CONFIG[tokenType];

    const paymentHeader = c.req.header('payment-signature') || c.req.header('X-PAYMENT') || c.req.header('x-payment');

    if (!paymentHeader) {
      const payReq = {
        x402Version: 2,
        resource: { url: resource, description: `${tokenCfg.label} payment required`, mimeType: 'application/json' },
        accepts: [{
          scheme: 'exact',
          network: networkId,
          amount: tokenCfg.amount,
          asset: tokenCfg.asset,
          payTo: recipientAddress,
          maxTimeoutSeconds: 300,
          extra: { label: tokenCfg.label, tokenType, ...(tokenCfg.contract ? { tokenContract: tokenCfg.contract } : {}) },
        }],
      };
      c.header('payment-required', btoa(JSON.stringify(payReq)));
      return c.json(payReq, 402);
    }

    let parsedPayment: Record<string, unknown>;
    try {
      parsedPayment = JSON.parse(atob(paymentHeader)) as Record<string, unknown>;
    } catch {
      return c.json({ error: 'Cannot decode payment header', code: 'PAYMENT_INVALID' }, 400);
    }

    const accepted = parsedPayment?.accepted as Record<string, unknown> | undefined;
    const paymentRequirements = accepted && accepted.network && accepted.amount && accepted.asset && accepted.payTo
      ? { scheme: accepted.scheme || 'exact', network: accepted.network, amount: accepted.amount, asset: accepted.asset, payTo: accepted.payTo, maxTimeoutSeconds: accepted.maxTimeoutSeconds || 300 }
      : { scheme: 'exact', network: networkId, amount: tokenCfg.amount, asset: tokenCfg.asset, payTo: recipientAddress, maxTimeoutSeconds: 300 };

    const txHex = String((parsedPayment.payload as Record<string, unknown>)?.transaction ?? '');
    const settle = await settlePayment(parsedPayment, paymentRequirements, txHex, relayUrl, recipientAddress, tokenCfg, tokenType);
    if (!settle.ok) return c.json(settle.error!, settle.status as 400 | 402 | 502 | 503);
    const { txId, payerAddress } = settle;
    c.set('x402', { payerAddress, txId, tokenType, amount: tokenCfg.amount });
    c.header('payment-response', btoa(JSON.stringify({ x402Version: 2, isValid: true, txId, token: tokenType })));
    c.header('X-PAYMENT-RESPONSE', JSON.stringify({ isValid: true, txId, token: tokenType }));
    c.header('X-PAYER-ADDRESS', payerAddress);
    await next();
  };
}

app.get('/api/quote/stx', singleTokenMiddleware('STX'), (c) => quoteHandler(c));
app.get('/api/quote/usdcx', singleTokenMiddleware('USDCx'), (c) => quoteHandler(c));

export default app;
