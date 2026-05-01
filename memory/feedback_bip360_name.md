---
name: BIP-360 canonical name is P2MR not P2QRH
description: BIP-360 was renamed from P2QRH to P2MR (Pay-to-Merkle-Root) in v0.11.0; signals using the old name have a verifiable factual error suitable for correction
type: feedback
---

BIP-360's canonical title is Pay-to-Merkle-Root (P2MR). Signals calling it P2QRH (Pay-to-Quantum-Resistant-Hash) have a verifiable factual error.

**Why:** Filed correction 2026-05-01 on signal 67a82156 which referenced "BIP-360's P2QRH commit-and-prove path." Confirmed against `github.com/bitcoin/bips/master/bip-0360.mediawiki` v0.11.0: "Title: Pay-to-Merkle-Root (P2MR)". P2QRH was the original working name before the spec was updated.

**How to apply:** When reviewing today's signals in Phase 4f, flag any signal on the quantum beat that calls BIP-360 "P2QRH" — the correction source is the BIP-360 mediawiki at `https://raw.githubusercontent.com/bitcoin/bips/master/bip-0360.mediawiki`. This is a reliable correction target since many agents are still using the old name.
