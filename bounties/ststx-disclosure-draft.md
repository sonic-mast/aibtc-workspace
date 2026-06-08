# stSTX↔STX Stableswap — Responsible Disclosure Draft

**Status:** DRAFT — awaiting send by operator. Do NOT call `bounty_submit` for
`mpwj216i51b1ad3c6731` until this has been sent and the timestamp/channel are
recorded below.

**Finding severity:** CRITICAL → the bounty (`mpwj216i51b1ad3c6731`) mandates
private disclosure to **both** the pool deployer and the StackingDAO team
**before** public submission, citing the disclosure timestamp + channel in the
submission message. Skipping this auto-disqualifies the submission.

> Note: this same fee-inversion has already been submitted publicly to the
> bounty by 4+ other agents (classified high/critical), and bounty submissions
> are public — so the bug is effectively already in the open. We still follow
> the documented disclosure step because the bounty rules require it of *our*
> submission regardless of what others did.

---

## Documented disclosure channels (from the bounty text)

Send the message below to all reachable channels, then record what was sent where.

**Pool deployer** — `SPQC38PW542EQJ5M11CR25P7BS1CA6QT4TBXGB3M`
- No registered AIBTC inbox (confirmed — another submitter noted the same). The
  contract is a Bitflow stableswap, so the deployer is reachable via Bitflow's
  channels below.

**StackingDAO** (stSTX issuer — peg integrity stake)
- Site: stackingdao.com
- X: @StackingDao
- GitHub: Trust-Machines / stacking-dao (open a private security advisory, or DM a maintainer)

**Bitflow** (stableswap operator / deployer)
- Site: bitflow.finance
- X: @Bitflow_Finance
- GitHub: bitflowfinance (private security advisory)
- Discord: discord.gg/DY4yNyHyhT

Preferred order: GitHub private security advisory (timestamped, written record)
→ X DM → Discord. Capture a timestamp + the channel used for each.

---

## Disclosure message (send as Sonic Mast)

> **Subject: Responsible disclosure — inverted fee conditional in stableswap-stx-ststx-v-1-2 (non-admins swap fee-free)**
>
> Hi — this is Sonic Mast (AIBTC agent, BTC `bc1qd0z0a8z8am9j84fk3lk5g2hutpxcreypnf2p47`), reaching out privately before any public write-up.
>
> While reviewing `SPQC38PW542EQJ5M11CR25P7BS1CA6QT4TBXGB3M.stableswap-stx-ststx-v-1-2` I found what looks like an inverted fee-exemption conditional in both swap paths. I wanted you to see it before it's discussed publicly.
>
> **Where:** `swap-x-for-y` (lines ~332–344) and `swap-y-for-x` (lines ~454–466). All three fee components (LPs, StackingDAO, Bitflow) — 6 conditionals total.
>
> **What:** The branch that's meant to give *admins* a fee exemption is reversed. The code reads:
> ```clarity
> ;; Admins pay no fees on swaps
> (swap-fee-lps (if (is-some (index-of (var-get admins) tx-sender))
>     (get lps (var-get buy-fees))          ;; admin IS in list → pays full fees
>     (get lps (var-get admin-swap-fees))   ;; NOT in list → admin-swap-fees = 0
> ))
> ```
> So when `tx-sender` is an admin the predicate is `true` and they take the first branch (full `buy-fees`/`sell-fees`); everyone else falls to the second branch where `admin-swap-fees` is all zeros. The comment ("Admins pay no fees on swaps") is the opposite of the behavior.
>
> **Impact:** 100% of non-admin (i.e. essentially all retail) swap volume currently collects **zero** fees — no LP fee, no StackingDAO fee (including the ~195 bps stSTX exit fee), no Bitflow protocol fee. Not a fund-theft path, but it zeroes LP/protocol revenue and the stSTX peg-exit fee for the life of the current deployment.
>
> **Fix:** swap the two branches:
> ```clarity
> (swap-fee-lps (if (is-some (index-of (var-get admins) tx-sender))
>     (get lps (var-get admin-swap-fees))   ;; admin → 0 bps
>     (get lps (var-get buy-fees))          ;; non-admin → configured fee
> ))
> ```
> Apply to all 6 conditionals across both swap functions.
>
> **Verify:** call `get-dy y-token lp-token u1000000` with and without the caller in `admins` — non-admins currently get the zero-fee output.
>
> If a corrected contract is redeployed, the fee revenue lost on the current deployment may be worth reconstructing from swap history.
>
> Happy to share the full static-analysis report privately. I plan to submit it to the AIBTC audit bounty after you've had a chance to look; let me know if you'd like me to hold. Thanks for building on Stacks.
>
> — Sonic Mast

---

## Record before submitting (fill in after sending)

- Disclosed to StackingDAO via: __________  at __________ (ISO ts)
- Disclosed to Bitflow via: __________  at __________ (ISO ts)
- Then submit `mpwj216i51b1ad3c6731` with gist `https://gist.github.com/sonic-mast/e59dcb76b34dce5684a03ef8096d1219` (make public first) and cite the timestamps/channels above in the `message`.
