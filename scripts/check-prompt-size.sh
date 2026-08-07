#!/usr/bin/env bash
# Size budget for the files loaded into EVERY hourly loop run. Prompt bloat
# here is a direct recurring token tax (vibewatch's CLAUDE.md hit 435 KB /
# ~110k tokens before they added this check; ours load 24x/day).
#
# Budgets are bytes. Raise a budget deliberately (edit this file in the same
# commit, with a reason) — never bypass the check.
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
check() { # $1=path $2=budget_bytes
  local size
  size=$(wc -c < "$1" | tr -d ' ')
  if [ "$size" -gt "$2" ]; then
    echo "FAIL: $1 is ${size} bytes (budget: $2). Trim it — this file loads into every hourly run."
    fail=1
  else
    echo "ok: $1 ${size}/${2} bytes"
  fi
}

check CLAUDE.md                              12000
check MEMORY.md                              14000
check SOUL.md                                 8000
check automation-prompts/aibtc-combined.md   90000

exit $fail
