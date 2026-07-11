# REVIEW.md — review calibration for the Sonic Mast workspace

Single source of truth for what code review means in this repo. Consumed by the
Gemini pre-push gate (`automation-prompts/aibtc-combined.md`, Phase 5), by any
`/code-review` or ad-hoc review session, and by human reviewers. Pattern
borrowed from the vibewatch-app review pipeline.

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

## Skip

- `memory/**`, `MEMORY.md` — memory notes, not code.
- `logs/**`, `automation-state/**` — machine-written.
- Prose-only changes in `automation-prompts/**/*.md` — but review embedded
  code blocks (bash / python snippets the loop executes) like code.
