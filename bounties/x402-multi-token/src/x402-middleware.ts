/**
 * x402 Multi-Token Payment Middleware for Hono
 *
 * Supports sBTC, STX, and USDCx payment in a single endpoint.
 * Returns HTTP 402 with accepts[] listing all three token options.
 */

import type { Context, Next } from 'hono';

// =============================================================================
// Types
// =============================================================================

export type TokenType = 'STX' | 'sBTC' | 'USDCx';

export interface TokenContract {
  address: string;
  name: string;
}

export interface TokenOption {
  amount: string;
  tokenType: TokenType;
}

export interface X402MultiConfig {
  options: TokenOption[];
}

export interface SettleResult {
  isValid: boolean;
  txId?: string;
  status?: string;
  sender?: string;
  senderAddress?: string;
  sender_address?: string;
  recipient?: string;
  error?: string;
  reason?: string;
  validationError?: string;
}

export interface X402Context {
  payerAddress: string;
  settleResult: SettleResult;
  signedTx: string;
  tokenType: TokenType;
}

interface PaymentOption {
  maxAmountRequired: string;
  resource: string;
  payTo: string;
  network: 'mainnet' | 'testnet';
  nonce: string;
  expiresAt: string;
  tokenType: TokenType;
  tokenContract?: TokenContract;
}

type PaymentErrorCode =
  | 'RELAY_UNAVAILABLE'
  | 'RELAY_ERROR'
  | 'PAYMENT_INVALID'
  | 'INSUFFICIENT_FUNDS'
  | 'PAYMENT_EXPIRED'
  | 'AMOUNT_TOO_LOW'
  | 'NETWORK_ERROR'
  | 'UNKNOWN_TOKEN'
  | 'UNKNOWN_ERROR';

interface PaymentErrorResponse {
  error: string;
  code: PaymentErrorCode;
  retryAfter?: number;
  tokenType?: TokenType;
  resource: string;
  details?: Record<string, string | undefined>;
}

// =============================================================================
// Token Contracts
// =============================================================================

const TOKEN_CONTRACTS: Record<'mainnet' | 'testnet', Record<'sBTC' | 'USDCx', TokenContract>> = {
  mainnet: {
    sBTC: { address: 'SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4', name: 'sbtc-token' },
    USDCx: { address: 'SP120SBRBQJ00MCWS7TM5R8WJNTTKD5K0HFRC2CNE', name: 'usdcx' },
  },
  testnet: {
    sBTC: { address: 'ST1F7QA2MDF17S807EPA36TSS8AMEFY4KA9TVGWXT', name: 'sbtc-token' },
    USDCx: { address: 'ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM', name: 'usdcx' },
  },
};

// =============================================================================
// Error Classification
// =============================================================================

function classifyPaymentError(error: unknown, settleResult?: SettleResult): {
  code: PaymentErrorCode;
  message: string;
  httpStatus: number;
  retryAfter?: number;
} {
  const errorStr = String(error).toLowerCase();
  const resultError = settleResult?.error?.toLowerCase() || '';
  const resultReason = settleResult?.reason?.toLowerCase() || '';
  const validationError = settleResult?.validationError?.toLowerCase() || '';
  const combined = `${errorStr} ${resultError} ${resultReason} ${validationError}`;

  if (combined.includes('fetch') || combined.includes('network') || combined.includes('timeout')) {
    return { code: 'NETWORK_ERROR', message: 'Network error with payment relay', httpStatus: 502, retryAfter: 5 };
  }
  if (combined.includes('503') || combined.includes('unavailable')) {
    return { code: 'RELAY_UNAVAILABLE', message: 'Payment relay temporarily unavailable', httpStatus: 503, retryAfter: 30 };
  }
  if (combined.includes('insufficient') || combined.includes('balance')) {
    return { code: 'INSUFFICIENT_FUNDS', message: 'Insufficient funds in wallet', httpStatus: 402 };
  }
  if (combined.includes('expired') || combined.includes('nonce')) {
    return { code: 'PAYMENT_EXPIRED', message: 'Payment expired, please sign a new payment', httpStatus: 402 };
  }
  if (combined.includes('amount') && (combined.includes('low') || combined.includes('minimum'))) {
    return { code: 'AMOUNT_TOO_LOW', message: 'Payment amount below minimum required', httpStatus: 402 };
  }
  if (combined.includes('invalid') || combined.includes('signature')) {
    return { code: 'PAYMENT_INVALID', message: 'Invalid payment signature', httpStatus: 400 };
  }
  return { code: 'UNKNOWN_ERROR', message: 'Payment processing error', httpStatus: 500, retryAfter: 5 };
}

// =============================================================================
// Multi-Token Middleware
// =============================================================================

type Env = {
  RECIPIENT_ADDRESS: string;
  NETWORK: string;
  RELAY_URL: string;
};

/**
 * Multi-token x402 Payment Middleware
 *
 * Flow:
 * 1. No X-PAYMENT header → return 402 with accepts[] listing all configured tokens
 * 2. X-PAYMENT-TOKEN-TYPE header → route to matching settlement option
 * 3. On valid settlement → attach X402Context and continue to handler
 */
export function x402MultiMiddleware(config: X402MultiConfig) {
  return async (c: Context<{ Bindings: Env; Variables: { x402?: X402Context } }>, next: Next) => {
    const env = c.env;
    const network = (env.NETWORK || 'testnet') as 'mainnet' | 'testnet';
    const relayUrl = env.RELAY_URL || (network === 'mainnet' ? 'https://x402-relay.aibtc.com' : 'https://x402-relay.aibtc.dev');
    const recipientAddress = env.RECIPIENT_ADDRESS;

    const signedTx = c.req.header('X-PAYMENT');
    const expiresAt = new Date(Date.now() + 5 * 60 * 1000).toISOString();
    const nonce = crypto.randomUUID();

    if (!signedTx) {
      // Return 402 with all payment options
      const accepts: PaymentOption[] = config.options.map(opt => {
        const option: PaymentOption = {
          maxAmountRequired: opt.amount,
          resource: c.req.path,
          payTo: recipientAddress,
          network,
          nonce,
          expiresAt,
          tokenType: opt.tokenType,
        };
        if (opt.tokenType === 'sBTC' || opt.tokenType === 'USDCx') {
          option.tokenContract = TOKEN_CONTRACTS[network][opt.tokenType];
        }
        return option;
      });

      return c.json({ accepts }, 402);
    }

    // Determine which token type the payer selected
    const headerTokenType = c.req.header('X-PAYMENT-TOKEN-TYPE');
    const normalised = headerTokenType?.trim().toUpperCase();
    const tokenType: TokenType | undefined =
      normalised === 'SBTC' ? 'sBTC' :
      normalised === 'STX' ? 'STX' :
      normalised === 'USDCX' ? 'USDCx' :
      undefined;

    if (!tokenType) {
      const errorResponse: PaymentErrorResponse = {
        error: 'Unknown or missing token type. Set X-PAYMENT-TOKEN-TYPE to sBTC, STX, or USDCx.',
        code: 'UNKNOWN_TOKEN',
        resource: c.req.path,
      };
      return c.json(errorResponse, 400);
    }

    // Find matching option
    const option = config.options.find(o => o.tokenType === tokenType);
    if (!option) {
      const errorResponse: PaymentErrorResponse = {
        error: `Token type ${tokenType} not accepted by this endpoint.`,
        code: 'UNKNOWN_TOKEN',
        resource: c.req.path,
      };
      return c.json(errorResponse, 400);
    }

    // Verify payment via relay
    let settleResult: SettleResult;
    try {
      const relayResponse = await fetch(`${relayUrl}/settle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10_000),
        body: JSON.stringify({
          signedTx,
          expectedRecipient: recipientAddress,
          minAmount: option.amount,
          tokenType,
          network,
        }),
      });

      if (!relayResponse.ok) {
        const errorText = await relayResponse.text().catch(() => relayResponse.statusText);
        throw new Error(`Relay returned ${relayResponse.status}: ${errorText}`);
      }

      settleResult = (await relayResponse.json()) as SettleResult;
    } catch (error) {
      const classified = classifyPaymentError(error);
      const errorResponse: PaymentErrorResponse = {
        error: classified.message,
        code: classified.code,
        retryAfter: classified.retryAfter,
        tokenType,
        resource: c.req.path,
        details: { exceptionMessage: String(error) },
      };
      if (classified.retryAfter) {
        c.header('Retry-After', String(classified.retryAfter));
      }
      return c.json(errorResponse, classified.httpStatus as 400 | 402 | 500 | 502 | 503);
    }

    if (!settleResult.isValid) {
      const classified = classifyPaymentError(
        settleResult.validationError || settleResult.error || 'invalid',
        settleResult
      );
      const errorResponse: PaymentErrorResponse = {
        error: classified.message,
        code: classified.code,
        retryAfter: classified.retryAfter,
        tokenType,
        resource: c.req.path,
        details: {
          settleError: settleResult.error,
          settleReason: settleResult.reason,
          validationError: settleResult.validationError,
        },
      };
      if (classified.retryAfter) {
        c.header('Retry-After', String(classified.retryAfter));
      }
      return c.json(errorResponse, classified.httpStatus as 400 | 402 | 500 | 502 | 503);
    }

    const payerAddress = settleResult.senderAddress || settleResult.sender_address || settleResult.sender || 'unknown';

    c.set('x402', {
      payerAddress,
      settleResult,
      signedTx,
      tokenType,
    });

    c.header('X-PAYMENT-RESPONSE', JSON.stringify(settleResult));
    c.header('X-PAYER-ADDRESS', payerAddress);

    await next();
  };
}
