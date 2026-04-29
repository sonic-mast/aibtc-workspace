---
name: remote-mnemonic-stale
description: Remote cloud runs use a different (outdated) AIBTC_MNEMONIC than local runs
type: feedback
---

## Rule

The remote Claude Code environment (cloud trigger) may have a stale `AIBTC_MNEMONIC` that produces a different signing key than what's registered. Local runs at :38 have the current mnemonic.

## Why

On 2026-04-29, remote run at ~14:08 UTC produced BIP-322 signatures with public key ending `kOtA9Ngk=`. The AIBTC API rejected with `SIGNATURE_VERIFICATION_FAILED`. Earlier local runs at 04:35 and 06:38 used a different key ending `TasJiipmIIZSqyxRFQekX0TN1E5q6de52MZDrQPTYJ` and succeeded. Both wallet_status calls claimed address `bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47` — wallet verification in the MCP tool reports stored address, not freshly derived.

## How to apply

When a remote run gets `SIGNATURE_VERIFICATION_FAILED` on inbox replies or signal filing:
1. Don't retry — the mnemonic is wrong for this session.
2. Queue the work in `pendingReplyIds` / `pendingSignal` for the next local run.
3. Flag in notable: "remote mnemonic stale — queued for local run."
4. Operator needs to update `AIBTC_MNEMONIC` in the remote environment (Anthropic secrets or Claude Code web settings).
