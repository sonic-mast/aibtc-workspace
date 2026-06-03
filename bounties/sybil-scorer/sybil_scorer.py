#!/usr/bin/env python3
"""
stacks-sybil-scorer — Open-source sybil-likelihood scorer for Stacks/AIBTC agent addresses.
Scores 0-100 from 7 public on-chain signals. MIT License.

Usage:
  python3 sybil_scorer.py SP1... [SP2...] [--seed SPSYBIL1...] [--btc BC1...] [--pretty]
  python3 sybil_scorer.py --demo

Signals (max pts):
  wallet_age      (22) — days since first on-chain transaction
  tx_diversity    (18) — unique contracts called
  funding         (22) — first STX funder shared with peer/seed cluster
  aibtc_identity  ( 8) — AIBTC level 0/1/2+
  nft_timing      (12) — identity NFT minted within 10 blocks of a peer
  btc_anchor      ( 8) — BTC L1 activity via mempool.space
  seed_proximity  (10) — address is in the known-sybil seed set

Labels: LIKELY_CLEAN (<38) / MODERATE_RISK (38-67) / HIGH_SYBIL_RISK (>=68)

Data sources: api.hiro.so, aibtc.com/api, mempool.space/api (all public, no API keys)
"""

import json
import sys
import time
import argparse
import urllib.request
import urllib.error
from typing import Optional

HIRO = "https://api.hiro.so"
AIBTC = "https://aibtc.com/api"
MEMPOOL = "https://mempool.space/api"
TIMEOUT = 15


def _get(url: str) -> dict:
    """Fetch JSON from url. Returns dict with '_err' key on failure."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "sonic-mast/sybil-scorer/1.0"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_err": f"HTTP {e.code}: {url}"}
    except Exception as e:
        return {"_err": f"{type(e).__name__}: {e}"}


def _txs(stx: str, limit: int = 50) -> list:
    d = _get(f"{HIRO}/extended/v1/address/{stx}/transactions?limit={limit}")
    return d.get("results", []) if not d.get("_err") else []


def _nfts(stx: str, limit: int = 50) -> list:
    d = _get(f"{HIRO}/extended/v1/address/{stx}/nft_events?limit={limit}")
    return d.get("results", []) if not d.get("_err") else []


def _aibtc_level(stx: str) -> Optional[int]:
    d = _get(f"{AIBTC}/verify/{stx}")
    if d.get("_err"):
        return None
    return d.get("level", 0)


def _btc_tx_count(btc: str) -> Optional[int]:
    d = _get(f"{MEMPOOL}/address/{btc}")
    if d.get("_err"):
        return None
    return d.get("chain_stats", {}).get("tx_count", 0)


def score_address(
    stx: str,
    btc: Optional[str] = None,
    seeds: Optional[list] = None,
    peers: Optional[list] = None,
) -> dict:
    """
    Score a Stacks address for sybil-cluster membership likelihood.

    Returns:
        dict with keys: address, score, label, top_signals, all_signals, facts
    """
    seeds = seeds or []
    peers = [p for p in (peers or []) if p != stx]
    sig: dict[str, tuple[int, str]] = {}  # name -> (score, reason)
    facts: dict = {}
    now = time.time()

    # ── Signal 1: Wallet Age (22 pts) ──────────────────────────────────────
    txs = _txs(stx)
    facts["tx_count"] = len(txs)
    if txs:
        oldest_ts = min(t.get("burn_block_time", now) for t in txs)
        age_days = (now - oldest_ts) / 86400
        facts["wallet_age_days"] = round(age_days, 1)
        if age_days < 3:
            pts, note = 22, f"Only {age_days:.1f}d old — freshly created"
        elif age_days < 14:
            pts, note = 14, f"{age_days:.1f}d old — new wallet"
        elif age_days < 30:
            pts, note = 7, f"{age_days:.1f}d old — recent"
        else:
            pts, note = 0, f"{age_days:.1f}d old — established"
    else:
        facts["wallet_age_days"] = None
        pts, note = 22, "No on-chain transactions"
    sig["wallet_age"] = (pts, note)

    # ── Signal 2: Transaction Diversity (18 pts) ───────────────────────────
    contracts = {
        t.get("contract_call", {}).get("contract_id", "")
        for t in txs
        if t.get("tx_type") == "contract_call"
    }
    contracts.discard("")
    div = len(contracts)
    facts["unique_contracts"] = div
    if div == 0:
        pts, note = 18, "Zero contract interactions"
    elif div < 3:
        pts, note = 12, f"Only {div} unique contracts called"
    elif div < 10:
        pts, note = 5, f"{div} unique contracts — limited"
    else:
        pts, note = 0, f"{div} unique contracts — diverse"
    sig["tx_diversity"] = (pts, note)

    # ── Signal 3: Funding Source / Cluster (22 pts) ───────────────────────
    funder = None
    for tx in sorted(txs, key=lambda t: t.get("burn_block_time", now)):
        if tx.get("tx_type") == "token_transfer" and tx.get("sender_address") != stx:
            funder = tx["sender_address"]
            break
    facts["first_stx_funder"] = funder

    shared_with = None
    if funder:
        for peer in peers + seeds:
            peer_txs = _txs(peer, limit=50)
            for tx in sorted(peer_txs, key=lambda t: t.get("burn_block_time", now)):
                if tx.get("tx_type") == "token_transfer" and tx.get("sender_address") == funder:
                    shared_with = peer
                    break
            if shared_with:
                break
    facts["funder_shared_with"] = shared_with

    if funder is None:
        sig["funding"] = (10, "No inbound STX transfer found — unfunded")
    elif shared_with:
        sig["funding"] = (22, f"First funder {funder[:20]}... shared with peer/seed")
    else:
        sig["funding"] = (0, f"Unique first funder: {funder[:20]}...")

    # ── Signal 4: AIBTC Identity Level (8 pts) ────────────────────────────
    level = _aibtc_level(stx)
    facts["aibtc_level"] = level
    if level is None:
        sig["aibtc_identity"] = (4, "AIBTC API unavailable — could not verify")
    elif level == 0:
        sig["aibtc_identity"] = (8, "Not registered on AIBTC (level 0)")
    elif level == 1:
        sig["aibtc_identity"] = (3, "Level 1 only — basic registration")
    else:
        sig["aibtc_identity"] = (0, f"Level {level} — established identity")

    # ── Signal 5: Identity NFT Batch Timing (12 pts) ─────────────────────
    id_blocks = [
        e["block_height"]
        for e in _nfts(stx)
        if "identity" in (e.get("asset_identifier") or "").lower()
    ]
    facts["identity_nft_blocks"] = id_blocks[:3]

    batch_peer = None
    if id_blocks and peers:
        my_block = id_blocks[0]
        for peer in peers:
            peer_evs = _nfts(peer)
            for ev in peer_evs:
                if "identity" in (ev.get("asset_identifier") or "").lower():
                    if abs(ev.get("block_height", 0) - my_block) <= 10:
                        batch_peer = peer
                        break
            if batch_peer:
                break
    sig["nft_timing"] = (
        (12, f"Identity NFT in same 10-block window as {batch_peer[:16]}...")
        if batch_peer
        else (0, "No identity NFT batch timing detected")
    )

    # ── Signal 6: BTC L1 Anchor (8 pts) ──────────────────────────────────
    if btc:
        btc_count = _btc_tx_count(btc)
        facts["btc_tx_count"] = btc_count
        if btc_count is None:
            sig["btc_anchor"] = (4, "mempool.space unavailable")
        elif btc_count == 0:
            sig["btc_anchor"] = (8, "Zero BTC L1 transactions — no anchor")
        elif btc_count < 5:
            sig["btc_anchor"] = (3, f"Only {btc_count} BTC txs — minimal anchor")
        else:
            sig["btc_anchor"] = (0, f"{btc_count} BTC txs — active L1 anchor")
    else:
        sig["btc_anchor"] = (0, "No BTC address supplied — skipped")

    # ── Signal 7: Seed Proximity (10 pts bonus) ───────────────────────────
    if stx in seeds:
        sig["seed_proximity"] = (10, "Address is in the provided known-sybil seed set")

    # ── Final score ────────────────────────────────────────────────────────
    total = min(100, sum(v[0] for v in sig.values()))
    if total >= 68:
        label = "HIGH_SYBIL_RISK"
    elif total >= 38:
        label = "MODERATE_RISK"
    else:
        label = "LIKELY_CLEAN"

    top3 = sorted(sig.items(), key=lambda x: -x[1][0])[:3]

    return {
        "address": stx,
        "score": total,
        "label": label,
        "top_signals": [
            {"signal": k, "score": v[0], "reason": v[1]} for k, v in top3
        ],
        "all_signals": {k: {"score": v[0], "reason": v[1]} for k, v in sig.items()},
        "facts": facts,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Stacks agent sybil-likelihood scorer (0-100, public APIs only)"
    )
    parser.add_argument("addresses", nargs="*", metavar="STX", help="Addresses to score")
    parser.add_argument("--seed", nargs="*", default=[], metavar="STX",
                        help="Known-sybil seed addresses for cluster detection")
    parser.add_argument("--btc", nargs="*", default=[], metavar="BTC",
                        help="BTC addresses (index-matched to positional addresses)")
    parser.add_argument("--demo", action="store_true",
                        help="Score two demo addresses (known-clean + unregistered)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    if args.demo:
        # Quasar Garuda (bounty poster, known clean) vs. synthetic low-activity address
        demo = [
            ("SP20GPDS5RYB2DV03KG4W08EG6HD11KYPK6FQJE1", None),
            ("SP1SC59Y3G1A0WNY5837R9HDCEPWRJSF852YM7GEW", None),
        ]
        results = [score_address(stx, btc=btc) for stx, btc in demo]
    elif args.addresses:
        btcs = list(args.btc) + [None] * len(args.addresses)
        results = [
            score_address(
                stx,
                btc=btcs[i] if i < len(btcs) else None,
                seeds=args.seed,
                peers=args.addresses,
            )
            for i, stx in enumerate(args.addresses)
        ]
    else:
        parser.print_help()
        sys.exit(0)

    out = results if len(results) != 1 else results[0]
    print(json.dumps(out, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
