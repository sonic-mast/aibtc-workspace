# Vibewatch Stacks M3 bounty programme — Sonic Mast is the POSTER, not a hunter

Since 2026-09-08 Sonic Mast posts, watches, and (only on operator sign-off) judges and pays a set of bounties on the aibtc board for Vibewatch's Stacks Vibe Index M3 adoption window (Vibewatch-io/vibewatch-app#875). Operator brief + verbatim copy + exact posted bodies live outside this repo:
`~/Documents/Coding/Vibewatch/stacks-m3-handoff/` (`sonic-mast-bounty-brief.md`, `bounty-copy-v3.md`, `bounty-drafts-2026-09-08.json`).

## Posted so far

| Tier | bountyId | reward | expires |
|---|---|---|---|
| Tier 0 — paywall bug bounty | `mtt3jab204ba31f85ab0` | 15,000 sats | 2026-09-29T20:02Z |
| Tier 1 (1 of 5) — first paid query | `mtt3jjrgcf0aa8fb225c` | 5,000 sats | **PAID 2026-09-09** to Celestial Shark `SP2YTGB7CDQP1E4T79CQMJ1DT7JB3VH4JMMEB4KEJ` (payout txid `0x4b97ff85…9a9a`) |
| Tier 1 (2 of 5) — first paid query | `mttjxw940faa8df06de7` | 5,000 sats | **PAID 2026-09-11** to Tall Sword `SP275DCZBMP7MZRB0BEYGCF99D83K2BEE4GEDBD1S` (STX-path payer; payout txid `0xac8513c7…28e7`) |
| Tier 1 (3 of 5) — first paid query | `mtwd044j16ce91c68417` | 5,000 sats | 2026-09-25T03:00Z |
| Tier 1 (4 of 5) — first paid query | `mtwd0cet93a16ab82498` | 5,000 sats | 2026-09-25T03:00Z |
| Tier 1 (5 of 5) — first paid query | `mtwd0kcs90cb2cfcf830` | 5,000 sats | 2026-09-25T03:00Z |

Tier-1 winners so far (ineligible for the remaining T1 slots): `SP2YTGB7CDQP1E4T79CQMJ1DT7JB3VH4JMMEB4KEJ` (Celestial Shark), `SP275DCZBMP7MZRB0BEYGCF99D83K2BEE4GEDBD1S` (Tall Sword). Previous winners keep re-submitting to later slots; that crowds the board (a slot with visible submissions reads as taken), so later slots name them in "Not eligible" and the loop marks their submissions `fail:already-won-tier1` without pinging. Winners/decisions are also tracked in the `postedBountyWatch` KV (`winners.tier1[]`).

Slots 3–5 name the two previous winners in "Not eligible" and point at Tier 2 (operator decision 2026-09-11; both winners were also thanked + invited to T2 via paid inbox). Remaining set (not yet posted): T2 1–3 (10k each, 21d, must post by ~2026-09-20), T3 (25k, 21d).

## Outreach

2026-09-11 (operator-directed, interactive): paid inbox pitch for T1 slots 3-5 sent to 7 agents picked by actual bounty track record (accepted submissions on the paid board, not descriptions): Grim Seraph `SP1KVZTZCTCN9TNA1H5MHQ3H0225JGN1RJHY4HA9W` (6 wins/35k), Proud Haven `SP3JAKMVVQ7VFGV4S8CRWPJFT7829K10ARRSR6P54` (36k), Cold Quinn `SPB2NAB38RKKM32N5SEJB86YCFMWFR70R9YK12V2` (won the aibtc x402 endpoint census), Hardy Ren `SP16GAEDHSAEYM7QGQE46BRMKBKJH20WRSJXEZNW4` (4 wins), Icy Garuda `SP2ATXSFKRCXF5H95107FK1K07FJ8KKXHCNCX9QE0`, Digital Sprite `SP2R8QAY2RK8DW1BRYTY7Y72ZAX1136SSYFKQ7G4M`, Violet Swift `SP2ND36P97MBV2VMG8JC4AT3JKQ1RA6AJ9NQZNJ6S`. 700 sats total. Do not re-pitch these seven for this tier — a second ping is spend with no new information. Winner tallies came from `GET /api/bounties/{id}/submissions` matched against `acceptedSubmissionId` from `bounty_list status=paid`; the agents list and the earnings endpoint are NOT a track-record signal (earnings there are ~100-sat inbox receipts).

## Rules for the loop

- **Never hunt these.** Phase 4.5 B already filters `posterBtcAddress == ours`; `bounty_submit` must never target our own posting.
- **Poster-side work in the loop is read-only**: detect new submissions, run the Hiro pre-check, record in `postedBountyWatch` KV, log `notable`, ping the operator. That's the "Posted-bounty watch" block in Phase 4.5.
- **Never `bounty_accept`, pay, `bounty_cancel`, or post a new slot autonomously.** Every acceptance and every posting needs the operator's explicit "qualifies" / "post it" in an interactive session. Payout is an sBTC transfer to the winner's STX address for exactly `rewardSats`, memo `BNTY:{bountyId}`, then `POST /api/bounties/{id}/paid`, within 7 days of accepting.
- Tier 0 deliverables are vibewatch-mcp issues; the operator judges them against the index's payment ledger — the loop does not.
- Pre-check facts: index payTo `SP3PHGPE8G09FFBSH6NVM3J5S2118M8YA825HWQY1`; sBTC contract `SM3VDXK3WZZSA84XXFKAFAF15NNZX32CTSG82JFQ4.sbtc-token`; a query is ≥ 100 sats sBTC or ≥ 300,000 µSTX; ineligible senders = any wallet operated by Vibewatch (ours `SPG6VGJ5GTG5QKBV2ZV03219GSGH37PJGXQYXP47`, the payTo, the operator's smoke payer — ask if unsure); one win per agent per tier.
- The copy is payment-agnostic on purpose: if asked in a thread how to pay, point at the 402 challenge + `https://api.vibewatch.io/.well-known/x402.json`; never explain sponsorship/relay/gas mechanics, and never edit a live posting's promise (post a new one instead).
- A submission that reports a real defect (Tier 0, or a T1 paragraph describing a wrong 402/422, a payload served with no settled payment, wrong docs) freezes the next slot until the operator says it's fixed.
