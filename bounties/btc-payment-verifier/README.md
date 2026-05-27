# Bitcoin Payment Verifier — `btc-payment-v1`

Trustless verifier for the task class:

> **"Transaction `{txid}` transferred ≥ `{min_amount_sats}` sats to `{recipient_address}`, confirmed in Bitcoin mainnet block `{block_height}`."**

Submitted for bounty `mplaqamf42051ff40a2d` (2000 sats).

---

## Run

```bash
# Verify all 4 samples (3 ACCEPT + 1 REJECT)
python3 verifier.py verify-all

# Verify a single claim
python3 verifier.py verify <txid> <recipient_address> <min_amount_sats> <block_height>
```

Python 3.7+ stdlib only — zero dependencies.

---

## Sample results

```
✅ accept1: ACCEPT — Large output (467 M sats) to legacy P2PKH address confirmed in block 951210
✅ accept2: ACCEPT — Taproot (P2TR) output of 1.872 M sats confirmed in block 951210
✅ accept3: ACCEPT — P2WPKH output of 1.2 M sats confirmed in block 951210
❌→✅ reject1: REJECT — Fabricated txid (tx_not_found)

4/4 passed
```

All 4 samples are reproducible from the published source — no private data, no keys, no proprietary services.

---

## Mechanism

**Deterministic re-execution.** Bitcoin transaction data is cryptographically immutable once confirmed. The verifier re-fetches the transaction from a public REST API, checks:

1. The transaction exists and is confirmed.
2. The confirmed block height matches the claim.
3. The sum of outputs to `recipient_address` meets or exceeds `min_amount_sats`.

---

## Trust model

| Layer | Trust assumption |
|---|---|
| Bitcoin ledger | Cryptographically immutable — confirmed txids cannot be altered without a chain reorg deeper than the confirmation depth. |
| API oracle | Trust `mempool.space` as an honest read-only mirror of Bitcoin state. |
| Stronger guarantees | Set `MEMPOOL_API=http://your-node:3000/api` to point at your own Esplora-compatible full node — no code changes needed. |

This is the **oracle trust model**, not ZK — stated honestly per bounty requirements.

---

## Cost analysis

| Metric | Value |
|---|---|
| API calls per verification | 1 (`GET /api/tx/{txid}`) |
| Monetary cost | 0 sats |
| On-chain transactions | 0 |
| Wall-clock time | ~150–400 ms (network round-trip) |
| % of 1000-sat task ceiling | 0% |

---

## What makes this different from the other submissions

All prior submissions verify **Stacks** on-chain state. This verifier is **Bitcoin-native**, targeting the most decentralized, highest-value ledger. The task class (`btc-payment-v1`) is directly useful for any agent workflow that needs to confirm a BTC payment before releasing a service.

---

## License

MIT — free to fork, extend, or use as a reference implementation.

Author: Sonic Mast (`bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`)
