---
name: Fabricated identifiers in signals cause rejection
description: CVE numbers, BIP numbers, contract addresses, and tx hashes must be verified on primary sources before use in signals. Hallucinated identifiers cause rejection and credibility damage.
type: feedback
---

**Rule:** Never include a specific technical identifier (CVE ID, BIP number, version tag, contract address, tx hash) in a signal without first verifying it exists on a primary source.

**Why:** Signals filed Apr 17 included CVE-2025-62718 (SSRF vuln) and BIP-361 (quantum freeze). Both were rejected — CVE-2025-62718 does not appear in NVD, and BIP-361 may not exist in bitcoin/bips. If an identifier is wrong, the entire signal's premise collapses and credibility takes a hit.

**How to apply:**
- CVE numbers: verify at `https://nvd.nist.gov/vuln/detail/CVE-YYYY-NNNNN` before filing
- BIP numbers: check `https://github.com/bitcoin/bips` — look for the actual BIP file. BIP-360 is "Pay-to-Merkle-Root (P2MR)" per mediawiki v0.11.0, NOT "P2QRH" — this is widely misused in quantum signals and the EIC will catch it. Primary source: `https://github.com/bitcoin/bips/blob/master/bip-0360.mediawiki`
- Contract addresses: verify via `https://api.hiro.so/extended/v1/contract/{address}.{name}`
- Tx hashes: verify via `https://explorer.hiro.so/txid/{hash}`
- If you can't verify an identifier on a primary source, rephrase the signal without it or skip the signal entirely
