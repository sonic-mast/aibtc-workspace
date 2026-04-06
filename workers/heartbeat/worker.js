/**
 * Sonic Mast Heartbeat Worker
 *
 * Cloudflare Worker that runs on a cron trigger every 15 minutes.
 * Signs "AIBTC Check-In | {timestamp}" with BIP-322 and POSTs to the heartbeat API.
 *
 * No AI needed — pure crypto + HTTP.
 *
 * Env vars required:
 * - AIBTC_MNEMONIC: BIP39 mnemonic phrase
 * - STATE_API_TOKEN: Bearer token for state API
 */

// We can't use npm modules in a plain Cloudflare Worker without a build step.
// Instead, we'll call the AIBTC MCP server's signing endpoint via a different approach:
// Use the state API to store the last heartbeat, and call the AIBTC API directly.
//
// For BIP-322 signing without npm, we need to use the Web Crypto API or inline the signing logic.
// The cleanest approach: run a small Node.js-compatible worker with the required crypto libs.
//
// Since Cloudflare Workers support npm packages via wrangler, let's use a wrangler-based approach.

export default {
  async scheduled(event, env, ctx) {
    try {
      const result = await doHeartbeat(env);
      console.log(result);
    } catch (err) {
      console.error("Heartbeat failed:", err.message);
    }
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      try {
        const state = await env.STATE_WORKER.fetch("https://state/state", {
          headers: { "Authorization": `Bearer ${env.STATE_API_TOKEN}` }
        }).then(r => r.json());
        return Response.json({
          agent: "Sonic Mast",
          address: "bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47",
          schedule: "every 15 minutes",
          lastHeartbeat: state.lastHeartbeatAt,
          unreadCount: state.unreadCount,
          newsSignalsToday: state.newsSignalsToday,
        });
      } catch {
        return Response.json({
          agent: "Sonic Mast",
          schedule: "every 15 minutes",
          status: "ok",
        });
      }
    }

    if (url.pathname === "/run") {
      try {
        const result = await doHeartbeat(env);
        return Response.json(result);
      } catch (err) {
        return Response.json({ error: err.message }, { status: 500 });
      }
    }

    return Response.json({ error: "not found" }, { status: 404 });
  }
};

async function doHeartbeat(env) {
  // 1. Derive key from mnemonic
  const { privateKey, address, publicKey, scriptPubKey } = await deriveKey(env.AIBTC_MNEMONIC);

  if (address !== "bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47") {
    throw new Error(`Address mismatch: got ${address}, expected bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`);
  }

  // 2. Create timestamp
  const now = new Date();
  const timestamp = now.toISOString().replace(/(\.\d{3})\d*Z/, "$1Z");

  // 3. Sign
  const message = `AIBTC Check-In | ${timestamp}`;
  const signature = bip322Sign(message, privateKey, scriptPubKey, publicKey);

  // 4. POST heartbeat
  const response = await fetch("https://aibtc.com/api/heartbeat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      signature,
      timestamp,
      btcAddress: address
    })
  });

  const data = await response.json();

  if (!data.success) {
    throw new Error(`Heartbeat failed: ${data.error || JSON.stringify(data)}`);
  }

  // 5. Update state API via Service Binding (direct Worker-to-Worker, no public URL needed)
  const authHeaders = {
    "Authorization": `Bearer ${env.STATE_API_TOKEN}`,
    "Content-Type": "application/json"
  };
  let stateStatus = "skipped";
  try {
    const stateWorker = env.STATE_WORKER;
    const getResp = await stateWorker.fetch("https://state/state", {
      headers: { "Authorization": `Bearer ${env.STATE_API_TOKEN}` }
    });
    if (getResp.ok) {
      const current = await getResp.json();
      current.lastHeartbeatAt = timestamp;
      current.unreadCount = data.orientation?.unreadCount ?? current.unreadCount ?? 0;
      const putResp = await stateWorker.fetch("https://state/state", {
        method: "PUT",
        headers: authHeaders,
        body: JSON.stringify(current)
      });
      stateStatus = putResp.ok ? "ok" : `put-failed:${putResp.status}`;
    } else {
      stateStatus = `get-failed:${getResp.status}`;
    }
  } catch (e) {
    stateStatus = `error:${e.message}`;
  }

  return {
    success: true,
    checkInCount: data.orientation?.checkInCount,
    level: data.orientation?.levelName,
    unread: data.orientation?.unreadCount,
    stateUpdate: stateStatus,
    timestamp
  };
}

// ============================================================================
// BIP-322 signing (ported from @aibtc/mcp-server/src/utils/bip322.ts)
// ============================================================================

// We need these from @scure/bip39, @scure/bip32, @scure/btc-signer
// Cloudflare Workers with wrangler support npm imports, so this will work
// when deployed with wrangler and a package.json

import { mnemonicToSeedSync } from "@scure/bip39";
import { HDKey } from "@scure/bip32";
import { Transaction, Script, RawWitness, RawTx, p2wpkh, NETWORK as BTC_MAINNET } from "@scure/btc-signer";
import { sha256 } from "@noble/hashes/sha2.js";
import { secp256k1 } from "@noble/curves/secp256k1.js";
import { concatBytes } from "@noble/hashes/utils.js";

function doubleSha256(data) {
  return sha256(sha256(data));
}

function bip322TaggedHash(message) {
  const tagBytes = new TextEncoder().encode("BIP0322-signed-message");
  const tagHash = sha256(tagBytes);
  const msgBytes = new TextEncoder().encode(message);
  return sha256(concatBytes(tagHash, tagHash, msgBytes));
}

function bip322BuildToSpendTxId(message, scriptPubKey) {
  const msgHash = bip322TaggedHash(message);
  const scriptSig = concatBytes(new Uint8Array([0x00, 0x20]), msgHash);

  const rawTx = RawTx.encode({
    version: 0,
    inputs: [{
      txid: new Uint8Array(32),
      index: 0xffffffff,
      finalScriptSig: scriptSig,
      sequence: 0,
    }],
    outputs: [{
      amount: 0n,
      script: scriptPubKey,
    }],
    lockTime: 0,
  });

  return doubleSha256(rawTx).reverse();
}

function bip322Sign(message, privateKey, scriptPubKey, compressedPubKey) {
  const toSpendTxid = bip322BuildToSpendTxId(message, scriptPubKey);

  const toSignTx = new Transaction({ version: 0, lockTime: 0, allowUnknownOutputs: true });

  toSignTx.addInput({
    txid: toSpendTxid,
    index: 0,
    sequence: 0,
    witnessUtxo: { amount: 0n, script: scriptPubKey },
  });
  toSignTx.addOutput({ script: Script.encode(["RETURN"]), amount: 0n });

  toSignTx.signIdx(privateKey, 0);
  toSignTx.finalizeIdx(0);

  const input = toSignTx.getInput(0);
  if (!input.finalScriptWitness) {
    throw new Error("BIP-322 signing failed: no witness produced");
  }

  const encodedWitness = RawWitness.encode(input.finalScriptWitness);
  // Convert to base64
  let binary = "";
  for (let i = 0; i < encodedWitness.length; i++) {
    binary += String.fromCharCode(encodedWitness[i]);
  }
  return btoa(binary);
}

async function deriveKey(mnemonic) {
  // Normalize whitespace — extra spaces between words cause "Invalid mnemonic"
  mnemonic = mnemonic.trim().replace(/\s+/g, " ");
  const seed = mnemonicToSeedSync(mnemonic);
  const masterKey = HDKey.fromMasterSeed(seed);

  // BIP84 path: m/84'/0'/0'/0/0 (mainnet)
  const child = masterKey.derive("m/84'/0'/0'/0/0");

  if (!child.privateKey) throw new Error("Failed to derive private key");

  const privateKey = child.privateKey;
  const publicKeyBytes = secp256k1.getPublicKey(privateKey, true); // compressed

  // Build P2WPKH scriptPubKey
  const p2wpkhOutput = p2wpkh(publicKeyBytes, BTC_MAINNET);
  const scriptPubKey = p2wpkhOutput.script;
  const address = p2wpkhOutput.address;

  return { privateKey, address, publicKey: publicKeyBytes, scriptPubKey };
}
