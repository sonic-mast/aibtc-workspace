#!/usr/bin/env python3
"""
Bitcoin Payment Verifier — task class: btc-payment-v1

Task class: "Transaction {txid} transferred >= {min_amount_sats} sats to
{recipient_address}, confirmed in Bitcoin mainnet block {block_height}."

Mechanism: Deterministic re-execution via Bitcoin REST API (mempool.space).

Trust model: Trust mempool.space as a Bitcoin chain oracle. Substitute any
Esplora-compatible Bitcoin full node (Blockstream, self-hosted) for zero-trust
operation — same API surface, drop-in replacement via MEMPOOL_API env var.

License: MIT
Author: Sonic Mast (bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47)
"""

import json
import sys
import os
import urllib.request
import urllib.error
from typing import Any

MEMPOOL_API = os.environ.get("MEMPOOL_API", "https://mempool.space/api")


def _fetch(path: str) -> Any:
    url = f"{MEMPOOL_API}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "btc-payment-verifier/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def verify(txid: str, recipient: str, min_amount_sats: int, block_height: int) -> dict:
    """
    Verify a Bitcoin payment claim.

    Returns:
        {"verdict": "ACCEPT", "evidence": {...}}
        or
        {"verdict": "REJECT", "reason": "...", "evidence": {...}}
    """
    # Validate inputs
    if not txid or len(txid) != 64:
        return {"verdict": "REJECT", "reason": "invalid_txid_format"}
    if not recipient:
        return {"verdict": "REJECT", "reason": "invalid_recipient"}
    if min_amount_sats <= 0:
        return {"verdict": "REJECT", "reason": "invalid_amount"}
    if block_height <= 0:
        return {"verdict": "REJECT", "reason": "invalid_block_height"}

    # Fetch the transaction
    try:
        tx = _fetch(f"/tx/{txid}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"verdict": "REJECT", "reason": "tx_not_found", "evidence": {"txid": txid}}
        return {"verdict": "REJECT", "reason": f"api_error_{e.code}"}
    except Exception as e:
        return {"verdict": "REJECT", "reason": f"fetch_failed: {type(e).__name__}"}

    # Check confirmation status
    status = tx.get("status", {})
    if not status.get("confirmed"):
        return {
            "verdict": "REJECT",
            "reason": "tx_unconfirmed",
            "evidence": {"txid": txid, "mempool_status": "unconfirmed"},
        }

    actual_height = status.get("block_height")
    if actual_height != block_height:
        return {
            "verdict": "REJECT",
            "reason": "block_height_mismatch",
            "evidence": {
                "txid": txid,
                "claimed_height": block_height,
                "actual_height": actual_height,
            },
        }

    # Sum outputs to the claimed recipient
    total_to_recipient = sum(
        vout.get("value", 0)
        for vout in tx.get("vout", [])
        if vout.get("scriptpubkey_address") == recipient
    )

    if total_to_recipient < min_amount_sats:
        return {
            "verdict": "REJECT",
            "reason": "amount_below_claim",
            "evidence": {
                "txid": txid,
                "recipient": recipient,
                "claimed_min_sats": min_amount_sats,
                "actual_sats": total_to_recipient,
            },
        }

    return {
        "verdict": "ACCEPT",
        "evidence": {
            "txid": txid,
            "recipient": recipient,
            "amount_sats": total_to_recipient,
            "block_height": actual_height,
            "block_hash": status.get("block_hash"),
            "fee_sats": tx.get("fee", 0),
        },
    }


SAMPLES = [
    {
        "id": "accept1",
        "description": "Large output (467 M sats) to legacy P2PKH address confirmed in block 951210",
        "claim": {
            "txid": "a49983f5391a99e5f8934c98091921a175bf9852c4b164de242a0edbdf7d3c99",
            "recipient": "1P8hzUnQn1VYbDwsGkNmbiHXLJWS6v9JEs",
            "min_amount_sats": 467335240,
            "block_height": 951210,
        },
        "expected": "ACCEPT",
    },
    {
        "id": "accept2",
        "description": "Taproot (P2TR) output of 1.872 M sats confirmed in block 951210",
        "claim": {
            "txid": "2cf36d13c390e9f3c5a5f685ad356db14d7bf2fc62e0a750b86052a21ff6aa6e",
            "recipient": "bc1p6tnnsrg6vhhv64tlvrs9p46qxpjllz6t9vpezx0rec9drgmgfd5q5ahuw8",
            "min_amount_sats": 1872000,
            "block_height": 951210,
        },
        "expected": "ACCEPT",
    },
    {
        "id": "accept3",
        "description": "P2WPKH output of 1.2 M sats confirmed in block 951210",
        "claim": {
            "txid": "3175119bde90b2993016ca89aba9a630fac43a118019d9afa4d1e7e35d71544a",
            "recipient": "bc1q5pzd6w2el4srcgfrugpmwjsuw0afal6wg263ql",
            "min_amount_sats": 1200000,
            "block_height": 951210,
        },
        "expected": "ACCEPT",
    },
    {
        "id": "reject1",
        "description": "Fabricated txid — verifier must return REJECT (tx_not_found)",
        "claim": {
            "txid": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "recipient": "bc1q5pzd6w2el4srcgfrugpmwjsuw0afal6wg263ql",
            "min_amount_sats": 1000000,
            "block_height": 951210,
        },
        "expected": "REJECT",
    },
]


def run_samples() -> None:
    passed = 0
    failed = 0
    for s in SAMPLES:
        result = verify(**s["claim"])
        ok = result["verdict"] == s["expected"]
        icon = "✅" if ok else "❌"
        print(f"{icon} {s['id']}: {result['verdict']} — {s['description']}")
        if not ok:
            print(f"   Expected {s['expected']}, got: {json.dumps(result, indent=2)}")
            failed += 1
        else:
            passed += 1
    print(f"\n{passed}/{len(SAMPLES)} passed")
    if failed:
        sys.exit(1)


def run_single(txid: str, recipient: str, amount: int, height: int) -> None:
    result = verify(txid, recipient, amount, height)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "verify-all":
        run_samples()
    elif args[0] == "verify" and len(args) == 5:
        run_single(args[1], args[2], int(args[3]), int(args[4]))
    else:
        print(
            "Usage:\n"
            "  python3 verifier.py verify-all\n"
            "  python3 verifier.py verify <txid> <recipient> <min_amount_sats> <block_height>"
        )
        sys.exit(1)
