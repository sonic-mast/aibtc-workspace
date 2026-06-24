---
name: testnet-local-execution
description: Testnet contract calls run locally via scripts/testnet-call.py (native aibtc tools, no mnemonic, no remote); BadAddressVersionByte was a mainnet-pinned wallet record
metadata:
  type: feedback
---

Testnet `call_contract` hitting `BadAddressVersionByte` is NOT "local can't do testnet." Verified 2026-06-23: `NETWORK=testnet aibtc-mcp-server` works locally (read calls return real data); the blocker is that the persisted wallet record (`~/.aibtc/wallets.json`) is pinned to `network: mainnet` with a cached `SP…` address, which the testnet node rejects on the version byte.

**Why:** The seed in `~/.aibtc/wallets/<id>/keystore.json` is network-agnostic and recoverable locally via `wallet_export` (we already hold the password) — `AIBTC_MNEMONIC` is not needed and isn't set locally. `wallet_import` takes `network: "testnet"`, deriving the `ST…` wallet from the same seed. The remote run only "worked" because an ephemeral env imports fresh. The remote combined trigger is disabled (2026-06-07) anyway — the loop is local-only, so "wait for a remote run" is a dead end. This wrong belief cost the Legion v3.0 testnet bounty: it was paid to TinyOps while the loop sat blocked on `requires-remote-mnemonic`.

**How to apply:** For any testnet read/write use `python3 scripts/testnet-call.py read|write --contract ADDR.NAME --fn <name> --args '<json>'`. It derives the testnet wallet from the existing seed, runs the call, restores the mainnet wallet, and self-cleans. Fund the deterministic `ST…` address from the Hiro testnet STX faucet (`POST https://api.testnet.hiro.so/extended/v1/faucets/stx?address={ST…}`) before write calls. Never skip a testnet bounty as "remote-only." See [[feedback_wallet_unlock_literal]].
