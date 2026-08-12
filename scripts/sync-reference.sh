#!/usr/bin/env bash
# sync-reference.sh — keep reference/ in step with the upstream docs it mirrors.
#
# The files under reference/ are hand-vendored snapshots of live platform docs.
# Nothing kept them current: every one landed in b3b4477 (2026-08-06) and sat
# there while upstream moved. aibtc.news/skill.md drifted within six days and
# started telling the loop to use an sBTC token that does not exist on-chain.
#
# This fetches each mirror, compares it to origin/main, and lands the changed
# ones as ONE commit built in a temporary git index — the working tree and the
# real index are never touched, so Phase 0's `git pull --ff-only` still
# fast-forwards (same discipline as scripts/memory-commit.sh, and the same
# reason: a dirty tree freezes the loop on stale code).
#
# Cost on the common path is one conditional GET per mirror and no writes.
#
# Usage:
#   scripts/sync-reference.sh            # fetch, land changes on main, report
#   scripts/sync-reference.sh --check    # report drift only, write nothing (rc 1 if drift)
#   scripts/sync-reference.sh --allow-shrink   # accept bodies that shrank >50%
#
# Output contract (last line, parsed by the loop):
#   SYNC NOOP                         every mirror already current
#   SYNC PUSHED <sha> changed=<paths> landed on main; Phase 0 picks it up next run
#   SYNC DRIFT changed=<paths>        --check only: mirrors are stale
#   SYNC PUSH_FAILED changed=<paths>  fetch worked, push did not — retry next run
# Per-mirror lines precede it: CHANGED/UNCHANGED/SHRANK/FAILED <path> [detail]
#
# SHRANK is a guard, not a failure: a mirror losing more than half its bytes is
# usually an error page or a wholesale upstream replacement, and both deserve a
# human look rather than a silent overwrite. Re-run with --allow-shrink to take
# it. (This is not hypothetical — it is how the retired bff.army/agents.txt
# mirror was caught being swapped for an unrelated doc.)
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"

# path <TAB> url — the mirror set. Add a line to vendor another doc.
MANIFEST=$(cat <<'EOF'
reference/aibtc.com/llms.txt	https://aibtc.com/llms.txt
reference/aibtc.com/llms-full.txt	https://aibtc.com/llms-full.txt
reference/aibtc.com/skill.md	https://aibtc.com/skill.md
reference/aibtc.news/llms.txt	https://aibtc.news/llms.txt
reference/aibtc.news/skill.md	https://aibtc.news/skill.md
EOF
)

TMP=$(mktemp -d "${TMPDIR:-/tmp}/refsync.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

die() { echo "REFUSED: $*" >&2; exit 1; }

mode=sync
allow_shrink=0
for arg in "$@"; do
  case "$arg" in
    --check) mode=check ;;
    --allow-shrink) allow_shrink=1 ;;
    *) die "unknown arg '$arg' (want --check and/or --allow-shrink)" ;;
  esac
done

# reference/<host>/<file> only — no traversal, no writes outside the mirror tree
allowed_path() {
  case "$1" in
    */../*|*/..|../*|*..*) return 1 ;;
    reference/*/*/*) return 1 ;;
    reference/*/*) return 0 ;;
  esac
  return 1
}

git fetch --quiet origin main || die "git fetch origin main failed"

changed=""    # space-separated paths whose upstream differs from origin/main
staged=""     # dest=src pairs for build_commit
n_unchanged=0 n_shrank=0 n_failed=0

while IFS=$'\t' read -r path url; do
  [ -n "${path:-}" ] || continue
  allowed_path "$path" || die "path not allowed: $path (want reference/<host>/<file>)"

  body="$TMP/$(echo "$path" | tr '/' '_')"
  rc=0
  curl -fsSL --proto '=https' --max-redirs 3 --max-time 20 -o "$body" "$url" || rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAILED $path curl-exit-$rc $url"
    n_failed=$((n_failed + 1))
    continue
  fi

  new_size=$(wc -c <"$body" | tr -d ' ')
  if [ "$new_size" -eq 0 ]; then
    echo "FAILED $path empty-body $url"
    n_failed=$((n_failed + 1))
    continue
  fi

  new_blob=$(git hash-object "$body")
  old_blob=$(git rev-parse -q --verify "origin/main:$path" 2>/dev/null || echo none)
  if [ "$new_blob" = "$old_blob" ]; then
    echo "UNCHANGED $path"
    n_unchanged=$((n_unchanged + 1))
    continue
  fi

  if [ "$old_blob" != none ] && [ "$allow_shrink" -eq 0 ]; then
    old_size=$(git cat-file -s "$old_blob")
    # >50% loss: error page or wholesale replacement, not an edit
    if [ "$((new_size * 2))" -lt "$old_size" ]; then
      echo "SHRANK $path ${old_size}->${new_size} (skipped; --allow-shrink to accept)"
      n_shrank=$((n_shrank + 1))
      continue
    fi
  fi

  echo "CHANGED $path"
  changed="$changed$path "
  staged="$staged$path=$body "
done <<EOF
$MANIFEST
EOF

changed_list=$(echo "$changed" | tr -s ' ' | sed 's/ $//;s/ /,/g')

if [ -z "$changed" ]; then
  echo "SYNC NOOP unchanged=$n_unchanged shrank=$n_shrank failed=$n_failed"
  exit 0
fi

if [ "$mode" = check ]; then
  echo "SYNC DRIFT changed=$changed_list unchanged=$n_unchanged shrank=$n_shrank failed=$n_failed"
  exit 1
fi

# Build the commit in a temp index off origin/main — working tree untouched.
head=$(git rev-parse origin/main)
export GIT_INDEX_FILE="$TMP/index"
rm -f "$GIT_INDEX_FILE"
git read-tree "$head"
for pair in $staged; do
  dest="${pair%%=*}"; src="${pair#*=}"
  blob=$(git hash-object -w "$src")
  git update-index --add --cacheinfo "100644,$blob,$dest"
done
tree=$(git write-tree)
unset GIT_INDEX_FILE

if [ "$tree" = "$(git rev-parse "$head^{tree}")" ]; then
  echo "SYNC NOOP unchanged=$n_unchanged shrank=$n_shrank failed=$n_failed"
  exit 0
fi

msg="reference: sync $changed_list from upstream"
commit=$(git commit-tree "$tree" -p "$head" -m "$msg")
[ -n "$commit" ] || die "commit-tree produced no sha"

if git push --quiet origin "$commit:refs/heads/main" 2>"$TMP/push.err"; then
  echo "SYNC PUSHED $commit changed=$changed_list unchanged=$n_unchanged shrank=$n_shrank failed=$n_failed"
  exit 0
fi

cat "$TMP/push.err" >&2
echo "SYNC PUSH_FAILED changed=$changed_list unchanged=$n_unchanged shrank=$n_shrank failed=$n_failed"
exit 1
