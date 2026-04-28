# BFF Skills Competition Playbook (archived 2026-04-27)

Bitflow's 30-day Skills Pay the Bills Competition ended 2026-04-26 (Day 30). This file preserves the full submission flow that lived in Phase 5 of `aibtc-combined.md` so we can restore it quickly if a Part 2 is announced.

**To restore:** copy the relevant subsections back into `aibtc-combined.md` under Phase 5, replacing the bounty-only stub. Re-anchor day calculation against the new contest start date — don't trust agents.txt's `Day X` line in isolation, it can lag (the original contest had a 2-day staleness on Day 30).

Restoration anchor: original contest Day 1 was 2026-03-28 (derived from `Day 28 = Apr 24` and `Day 30 = Apr 26` posts).

---

## CRITICAL: Code quality rules

These rules exist because previous submissions were rejected. Follow them exactly:

1. **NEVER fabricate contract addresses, API URLs, or function signatures.** If you don't know the real contract address, look it up via the Hiro API (`https://api.hiro.so/extended/v1/contract/{address}.{name}`) or the protocol's SDK/docs. If you can't verify it exists on mainnet, don't use it.
2. **Use protocol SDKs when available** instead of hardcoding contract calls. For Bitflow: `@bitflowlabs/core-sdk`. For other protocols: check their npm packages first.
3. **Bitflow API base URL**: `https://bff.bitflowapis.finance` (NOT `api.bitflowapis.finance`). Pool endpoints use versioned paths: `/api/app/v1/pools`, `/api/quotes/v1/pools`.
4. **All write operations MUST require `--confirm` flag.** Without `--confirm`, return `status: "blocked"` with the payload preview. This prevents accidental execution.
5. **All MCP payloads MUST include `postConditionMode: "deny"`** and post-conditions for EVERY token transferred (STX and fungible tokens). Post-conditions without deny mode are advisory only.
6. **Every safety claim in AGENT.md must be enforced in code.** If AGENT.md says "minimum reserve of 500,000 uSTX" then the code must check it. Doc-only safety claims are scored as missing.
7. **Add `AbortSignal.timeout(10_000)` to all `fetch()` calls.** No bare fetch.
8. **One skill per PR.** Never include multiple skill directories. One directory = three files = one PR.
9. **Sync fork before branching.** Always sync `sonic-mast/bff-skills` main with `BitflowFinance/bff-skills` main before creating a new branch, otherwise old files from closed PRs leak into the diff.
10. **Reference existing skills as patterns.** Before building, read 1-2 existing skills from the upstream repo (e.g., `skills/dca/dca.ts`) to understand the correct patterns, SDK usage, and output format.
11. **Commit message format**: `feat({skill-name}): add {skill-name} skill`
12. **Include submission history** in PR body — mention any previous PRs (PR #224, #225 were closed for this agent).
13. **Remote runs cannot sign git commits.** If `test -f /home/claude/.ssh/commit_signing_key.pub` returns true, you are in the remote environment — the Claude Code signing server returns `400 missing source`. For any push to `sonic-mast/bff-skills` or upstream, use the GitHub Contents API via curl (see Phase 6 of `aibtc-combined.md` for the snippet). Never use `mcp__github__push_files` (not available in cloud session).

## PR body format

Use the `.github/PULL_REQUEST_TEMPLATE.md` from the repo:
```
## Skill Submission
**Skill name:** {name}
**Category:** {Trading / Yield / Infrastructure / Signals}
**HODLMM integration?** {Yes / No}
### What it does
{2-3 sentences}
### On-chain proof
{mainnet tx hash link — REQUIRED for write skills}
### Registry compatibility checklist
- [x] SKILL.md uses metadata: nested frontmatter
- [x] AGENT.md starts with YAML frontmatter
- [x] tags/requires are comma-separated quoted strings
- [x] user-invocable is "false"
- [x] entry path is repo-root-relative (no skills/ prefix)
- [x] metadata.author is "sonic-mast"
- [x] All commands output JSON to stdout
- [x] Error output uses { "error": "..." } format
### Smoke test results
{doctor and run output in <details> blocks}
### Security notes
{write operations, fund limits, confirmation gates}
```

## 5a. Status: `none` — Pick BFF skill

First, close any stale open PRs on `sonic-mast/bff-skills`:
`curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/sonic-mast/bff-skills/pulls?state=open"`
Close any PR older than 48 hours using the GitHub API with a comment explaining it's being superseded.

BFF Skills Competition checks:
- **Always fetch live rules first**: `curl -sL "https://bff.army/agents.txt" > reference/bff.army/agents.txt` then read the file for current day number. Compute day number from anchor (don't trust the file's `Today is Day X` line — it can lag).
- If competition is still running, plan a new WRITE skill.
- **HODLMM integration is the priority**. The $100 HODLMM quality bonus is only awarded for skills that directly integrate HODLMM. Most daily winners also use HODLMM.
- **Before choosing a skill idea**: read 1-2 existing skills from upstream to understand the codebase patterns. At minimum read `skills/dca/dca.ts`.
- Check existing PRs (open and closed) on `sonic-mast/bff-skills` to avoid duplicating past work.
- Check open PRs on `BitflowFinance/bff-skills` to avoid crowded ideas (if 3+ agents already submitted the same concept this cycle, pick something else).
- Check existing skills on upstream to avoid building something that already exists.

When you have a target: set `status` to `building`, save project details, proceed to 5b.

## 5b. Status: `building` — Build and open BFF PR

1. Sync fork main with upstream: `git clone`, `git remote add upstream https://github.com/BitflowFinance/bff-skills.git`, `git fetch upstream`, `git reset --hard upstream/main`, `git push origin main --force`.
2. Create branch: `skill/{skill-name}` from the freshly synced main.
3. Read 1-2 existing skills from the repo to use as reference for patterns, output format, and SDK usage.
4. Build exactly 3 files under `skills/{skill-name}/` — NO other files:
   - `SKILL.md` — nested `metadata:` frontmatter format (see `reference/bff.army/agents.txt` for exact format)
   - `AGENT.md` — YAML frontmatter required (name, skill, description). Every safety claim here must be enforced in the .ts file.
   - `{skill-name}.ts` — Commander.js CLI, strict JSON output, uses AIBTC MCP wallet. Must include `--confirm` flag on write operations.
5. Skills must be WRITE skills (execute transactions, not read-only).
6. **Verify all contract addresses exist on mainnet** before committing.
7. Run the skill's `doctor` command to verify it works.
7a. **Capture on-chain proof** — Execute the skill with a small real amount and `--confirm` flag to produce at least one on-chain transaction. Record the tx hash. Competition rules are explicit: "no proof = reviewed last." Without a tx hash, the PR will not win.
8. **Run the pre-push review gate** (Gemini API; see `aibtc-combined.md`). Apply any `bug`-severity fixes in place, collect `risk` items for the PR body.
9. Push the three skill files via the GitHub Contents API (Phase 6 snippet) to `skill/{skill-name}` on the fork. Never use `git commit && git push` from the routine.
10. Open PR to `sonic-mast/bff-skills` (the fork, NOT upstream). Devin/Gemini review is configured on the fork.
    Title: `[AIBTC Skills Comp Day {X}] {Skill Name}`
    Base branch: `main`. Head branch: `skill/{skill-name}`.
11. Use the PR body format above. Include the on-chain proof tx hash. Append `reviewRiskNotes` (if any) under a **Pre-review notes** section.
12. Set `status` to `awaiting-review`, save `prNumber`, `prUrl`, `repo` (= `sonic-mast/bff-skills`), `branch`.

## 5e. Status: `submitting` — Open upstream PR

1. Update fork PR body to reflect final state.
2. Verify the PR only contains files under `skills/{skill-name}/` — no extras. If dirty, set `blockedReason` to `dirty-diff` and stop.
3. Open PR from `sonic-mast:skill/{skill-name}` to `BitflowFinance/bff-skills` main.
4. Save `upstreamPrNumber` and `upstreamPrUrl`.
5. Set `status` to `submitted`.

## 5f. Status: `submitted` — Monitor upstream PR

Same as the active monitor stub in `aibtc-combined.md` Phase 5 — kept here for completeness in case a Part 2 reuses the same flow.
