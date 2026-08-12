# REVIEW.md — review calibration for the Sonic Mast workspace

Single source of truth for what code review means in this repo. Consumed by the
Gemini pre-push gate (`automation-prompts/aibtc-combined.md`, Phase 5), by any
ad-hoc review session, and by human reviewers. Pattern borrowed from the
vibewatch-app review pipeline.

## Review layers (and who pays)

Reviews of Sonic Mast's code run on Sonic Mast's own accounts or free tiers —
**never on the operator's billed accounts** (operator preference, 2026-07-11;
the operator's CodeRabbit / Claude credits are reserved for vibewatch etc.).

1. **In-session hooks** (`.claude/hooks/` + `security-patterns.yaml`) —
   deterministic, zero-cost, fire on every edit.
2. **Gemini pre-push gate** (Phase 5 of the combined prompt) — `GEMINI_API_KEY`
   free tier, pipes this file in as system context. Runs before any push.
3. **Cubic** (`cubic-dev-ai[bot]`, [cubic.dev](https://cubic.dev) GitHub app on
   the sonic-mast account, free tier ~20 reviews/mo) — the **PR review of
   record**. Installed by the operator 2026-07. Devin
   (`devin-ai-integration[bot]`) and Gemini Code Assist
   (`gemini-code-assist[bot]`, consumer bot sunsets 2026-07-17) still comment
   while they last.

Do not invoke operator-billed reviewers (`/code-review` → CodeRabbit,
ultrareview, etc.) on Sonic Mast work.

**Local-first (operator directive, 2026-08-07).** Reviews happen locally and
the work improves BEFORE anything is submitted — before `bounty_submit`,
before `git push`, before a PR exists. Layer 2 runs via
`scripts/gemini-review.py` (ONE API request per review — never an agentic
`gemini` CLI loop, which burns 10-25 free-tier requests per review): fix
`bug` findings, re-run once to confirm, then ship. Cubic on the PR is the
catch layer, not the first look.

**Feedback ratchet.** When a later layer catches what an earlier layer missed
— cubic flags something material the Gemini gate passed, or a bounty poster
rejects for a reason no layer flagged — that's a calibration bug in this
file. Add the failure shape to the Always-check list below (or to
`.claude/security-patterns.yaml` if it's mechanically greppable) in the same
session that fixes the finding. The next regression of that shape should die
at layer 1 or 2, not on a public PR.

## Risk tiers (which layers run)

| Tier | Diff | Layers |
|---|---|---|
| **T0 — docs/memory** | `memory/**`, `MEMORY.md`, prose-only `*.md` | Hooks only (memory-commit.sh guardrails). No Gemini call, no cubic. |
| **T1 — code deliverables** | Bounty deliverables, skills, gists with code, embedded prompt code blocks | Hooks + Gemini gate (fix `bug`s, one confirm re-run) before submit/push; cubic if it lands as a PR. |
| **T2 — loop-executed / wallet-touching** | `scripts/**`, `.github/workflows/**`, `automation-prompts/**` code blocks, anything calling wallet/signing/contract tools | T1, and hold findings to "near-certain and severe" — these run with the agent's full trust, so a missed bug costs funds, not review rounds. Never merge same-run as authored; leave for cubic or the operator when uncertain. |

Cubic's free tier is ~20 reviews/month — spend it on T1/T2 PRs, never on
memory or docs pushes.

## Severity

- **Blocking 🔴** — will get the PR rejected or lose funds: fabricated contract
  addresses or API URLs, write operations without a `--confirm` gate, missing
  `postConditionMode: "deny"` or per-token post-conditions, secrets / tokens /
  mnemonics in committed content, actual logic bugs (wrong operator, swapped
  args, missing await, off-by-one).
- **Important 🟡** — a safety claim in AGENT.md/docs not enforced in code, bare
  `fetch()` without `AbortSignal.timeout`, hardcoded contract calls where a
  protocol SDK exists, unbounded retries against paid or rate-limited APIs.
- **Nit ⚪** — style, naming, comment phrasing. Report at most 5 Nits per
  review. If everything found is a Nit, lead with "No blocking issues."

## Always check

1. Every contract address / API URL is verifiable on-chain or in the protocol's
   docs (Hiro: `api.hiro.so/extended/v1/contract/{address}.{name}`). Fabricated
   addresses are the #1 historical rejection reason (PR #225).
2. Every write operation is gated behind `--confirm`; without it the code
   returns `status: "blocked"` with a payload preview.
3. Every MCP payload includes `postConditionMode: "deny"` plus post-conditions
   for every token transferred (STX and fungible tokens).
4. Every safety claim in AGENT.md is enforced in code — doc-only safety claims
   count as missing.
5. Every `fetch()` carries `AbortSignal.timeout(10_000)`. No bare fetch.
6. No secrets (API tokens, keys, mnemonics, passwords) in any committed file,
   including markdown, prompt, and memory files.
7. Behavior claims need a `file:line` citation in the source, not inference
   from naming.
8. Address / encoding round-trips are tested across the *short* case, not one
   happy-path value. A c32 encoder that padded to a fixed width shipped past
   this gate in PR #53 and was caught by Devin + cubic: it was verified against
   a single address that happened to be 41 chars, while ~19% of real Stacks
   addresses are 40 and came out with a spurious leading `0` — a wrong contract,
   silently. Any codec touching addresses, amounts, or hex needs vectors that
   include the boundary (leading zero bytes, minimum length, empty), and
   "I verified it on the live value" is not coverage.

## Skip

- `memory/**`, `MEMORY.md` — memory notes, not code.
- `logs/**`, `automation-state/**` — machine-written.
- Prose-only changes in `automation-prompts/**/*.md` — but review embedded
  code blocks (bash / python snippets the loop executes) like code.
