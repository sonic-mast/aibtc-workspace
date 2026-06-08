// BigInt.toJSON polyfill for JSON.stringify compatibility
(BigInt.prototype as unknown as { toJSON: () => string }).toJSON = function () {
  return this.toString();
};

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { x402MultiMiddleware } from './x402-middleware';
import type { X402Context } from './x402-middleware';

type Env = {
  RECIPIENT_ADDRESS: string;
  NETWORK: string;
  RELAY_URL: string;
};

type Variables = {
  x402?: X402Context;
};

const app = new Hono<{ Bindings: Env; Variables: Variables }>();

// CORS — expose x402 headers
app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  allowHeaders: ['X-PAYMENT', 'X-PAYMENT-TOKEN-TYPE', 'Authorization', 'Content-Type'],
  exposeHeaders: ['X-PAYMENT-RESPONSE', 'X-PAYER-ADDRESS'],
}));

// Startup validation
app.use('*', async (c, next) => {
  if (c.req.path === '/health') return next();
  if (!c.env.RECIPIENT_ADDRESS) {
    return c.json({
      error: 'Server configuration error',
      message: 'Missing required secret: RECIPIENT_ADDRESS',
      hint: 'Run: wrangler secret put RECIPIENT_ADDRESS',
    }, 503);
  }
  await next();
});

// Service info (free)
app.get('/', (c) => {
  return c.json({
    service: 'x402-multi-token',
    version: '1.0.0',
    description: 'x402 endpoint accepting sBTC, STX, and USDCx',
    endpoints: ['/api/quote'],
    health: '/health',
    payment: {
      tokens: ['sBTC', 'STX', 'USDCx'],
      header: 'X-PAYMENT',
      tokenTypeHeader: 'X-PAYMENT-TOKEN-TYPE',
      probe: 'GET /api/quote (no X-PAYMENT header) → 402 with accepts[]',
    },
  });
});

// Health check (free)
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    network: c.env.NETWORK || 'mainnet',
  });
});

// Multi-token premium endpoint
// Returns 402 with accepts[] on probe; settles any of the 3 tokens on payment.
app.get('/api/quote',
  x402MultiMiddleware({
    options: [
      { tokenType: 'sBTC', amount: '1000' },       // 1,000 sats
      { tokenType: 'STX',  amount: '100000' },     // 0.1 STX (100,000 microSTX)
      { tokenType: 'USDCx', amount: '100000' },    // 0.1 USDCx (100,000 micro-USDCx, 6 decimals)
    ],
  }),
  async (c) => {
    const payment = c.get('x402');
    return c.json({
      success: true,
      quote: {
        btcUsd: 66500,
        stxUsd: 0.92,
        sbtcUsd: 66500,
        timestamp: new Date().toISOString(),
        source: 'x402-multi-token demo endpoint',
      },
      payment: {
        txId: payment?.settleResult?.txId,
        sender: payment?.payerAddress,
        tokenType: payment?.tokenType,
      },
    });
  }
);

export default app;
