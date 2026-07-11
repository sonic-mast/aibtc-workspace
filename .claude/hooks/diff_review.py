#!/usr/bin/env python3
"""
AIBTC end-of-turn diff scan (Stop hook).

After each Claude turn, scan the working-tree diff against HEAD for any
deterministic-pattern violations that the per-edit pass missed — e.g.
violations introduced via the Bash tool, edits split across multiple tool
calls, or files the per-edit hook deduplicated.

Ported from the vibewatch-app review pipeline. Emits one consolidated
message to stderr at end of turn; exit 2 re-prompts Claude with the
findings. Fail-open on any error.
"""

import codecs
import json
import os
import subprocess
import sys
from pathlib import Path

# Re-use the pattern_check module by importing it.
HOOK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOK_DIR))
try:
    from pattern_check import (  # type: ignore
        PROJECT_DIR,
        check_rule,
        load_patterns,
    )
except ImportError:
    sys.exit(0)

MAX_FILES = 30
MAX_FINDINGS_REPORTED = 12


def _parse_plus_header(line):
    """Parse a `+++ ` diff header into its b/-relative path (handles
    git-quoted names with non-ASCII / special characters)."""
    body = line[4:].strip()
    if body.startswith('"') and body.endswith('"') and len(body) >= 2:
        try:
            body = (
                codecs.escape_decode(body[1:-1].encode())[0]
                .decode("utf-8", errors="replace")
            )
        except Exception:
            return None
    if body.startswith("b/"):
        return body[2:]
    return None  # /dev/null (deleted file) or unrecognized header


def added_content_per_file():
    """Return {file_path: added_lines_joined} for files changed this turn.

    Only feeds *added* lines (the `+` side of a unified diff against HEAD)
    plus the full content of untracked files — whole-file scans false-positive
    on pre-existing content.
    """
    result = {}
    try:
        diff_out = subprocess.check_output(
            ["git", "-C", PROJECT_DIR, "diff", "--unified=0", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).decode(errors="ignore")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        diff_out = ""

    current_file = None
    added_lines = []
    for line in diff_out.splitlines():
        if line.startswith("diff --git "):
            if current_file and added_lines:
                result.setdefault(current_file, []).extend(added_lines)
            current_file = None
            added_lines = []
            continue
        if line.startswith("+++ "):
            current_file = _parse_plus_header(line)
            continue
        if line.startswith("+") and current_file:
            added_lines.append(line[1:])
    if current_file and added_lines:
        result.setdefault(current_file, []).extend(added_lines)

    # Untracked files: every line is "added."
    try:
        untracked = subprocess.check_output(
            ["git", "-C", PROJECT_DIR, "ls-files", "--others", "--exclude-standard"],
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).decode(errors="ignore").splitlines()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        untracked = []
    for rel in untracked[:MAX_FILES]:
        if not rel:
            continue
        full = Path(PROJECT_DIR) / rel
        try:
            if full.is_file():
                result[rel] = full.read_text(errors="ignore").splitlines()
        except OSError:
            continue

    return {f: "\n".join(lines) for f, lines in list(result.items())[:MAX_FILES] if lines}


def main():
    if os.environ.get("AIBTC_DIFF_REVIEW_DISABLE") == "1":
        sys.exit(0)

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        sys.exit(0)

    # Avoid re-firing in a loop: if Claude is being re-prompted because of
    # a previous Stop-hook nudge, exit immediately.
    if payload.get("stop_hook_active"):
        sys.exit(0)

    patterns = load_patterns()
    if not patterns:
        sys.exit(0)

    file_added = added_content_per_file()
    if not file_added:
        sys.exit(0)

    findings = []  # list of (file, rule_name, reminder)
    for f, added in file_added.items():
        if len(findings) >= MAX_FINDINGS_REPORTED:
            break
        full_path = str(Path(PROJECT_DIR) / f)
        for rule in patterns:
            if len(findings) >= MAX_FINDINGS_REPORTED:
                break
            name = rule.get("rule_name") or rule.get("ruleName")
            reminder = rule.get("reminder")
            if not name or not reminder:
                continue
            if check_rule(rule, full_path, added):
                findings.append((f, name, reminder[:512]))

    if not findings:
        sys.exit(0)

    lines = [
        "⚠️  AIBTC end-of-turn pattern scan found violations in the working tree:",
        "",
    ]
    seen = set()
    for f, name, reminder in findings:
        key = (f, name)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"  • {f} — {name}")
        lines.append(f"    {reminder}")
    lines.append("")
    lines.append(
        "Fix these before pushing — the Gemini pre-push gate (Phase 5) and PR review bots will flag them again."
    )
    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
