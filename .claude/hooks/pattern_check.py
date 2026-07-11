#!/usr/bin/env python3
"""
AIBTC in-session pattern check (PreToolUse hook).

Loads .claude/security-patterns.yaml at the project root and applies its
deterministic regex/substring rules to the content being written by Claude
on every Edit / Write / MultiEdit tool use. On match, emits the rule's
reminder to stderr and exits with code 2 — Claude Code interprets exit
code 2 as "block the tool call" and feeds the stderr text back into
Claude's context for the next step.

Ported from the vibewatch-app review pipeline. Failure mode is fail-open:
if PyYAML is unavailable, the YAML file is missing, or any rule errors
out, the hook exits 0 (allow tool) rather than blocking. The Gemini
pre-push gate (aibtc-combined.md Phase 5) is the safety net.
"""

import fnmatch
import json
import os
import re
import sys
from pathlib import Path


PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
PATTERNS_FILE = Path(PROJECT_DIR) / ".claude" / "security-patterns.yaml"
PATTERNS_FILE_JSON = Path(PROJECT_DIR) / ".claude" / "security-patterns.json"
STATE_DIR = Path.home() / ".claude"
MAX_RULES = 50


def _load_security_patterns():
    """Load the hand-authored security patterns.

    Precedence: YAML first (source of truth). If PyYAML is not importable
    under the python3 Claude Code hooks run with, fall back to the sibling
    .json compiled by scripts/compile-security-patterns.py. Fail-open on
    any error (return []).
    """
    data = None
    yaml_err = None
    if PATTERNS_FILE.exists():
        try:
            import yaml  # noqa: PLC0415
            with open(PATTERNS_FILE) as f:
                data = yaml.safe_load(f) or {}
        except ImportError as e:
            yaml_err = e  # fall through to JSON fallback below
        except Exception:
            return []
    if data is None and PATTERNS_FILE_JSON.exists():
        try:
            with open(PATTERNS_FILE_JSON) as f:
                data = json.load(f)
        except Exception:
            return []
    if data is None:
        if yaml_err is not None and PATTERNS_FILE.exists():
            print(
                "aibtc pattern_check: PyYAML missing and no JSON fallback at "
                f"{PATTERNS_FILE_JSON}. Run scripts/compile-security-patterns.py "
                "or `pip3 install pyyaml` to activate the in-session security layer.",
                file=sys.stderr,
            )
        return []
    patterns = data.get("patterns", []) if isinstance(data, dict) else []
    if not isinstance(patterns, list):
        return []
    return patterns[:MAX_RULES]


def load_patterns():
    """diff_review.py imports this too, so the per-edit (PreToolUse) and
    end-of-turn (Stop) hooks scan the same ruleset."""
    return _load_security_patterns()


def path_matches(file_path, paths_globs):
    """Check if file_path matches any of the glob patterns."""
    if not paths_globs:
        return True
    rel = file_path
    try:
        rel = str(Path(file_path).resolve().relative_to(Path(PROJECT_DIR).resolve()))
    except (ValueError, OSError):
        rel = file_path.lstrip(os.sep)
    for glob in paths_globs:
        normalized = glob.replace("**/", "*/").replace("/**", "/*")
        if fnmatch.fnmatch(rel, glob) or fnmatch.fnmatch(rel, normalized):
            return True
        try:
            if Path(rel).match(glob):
                return True
        except (ValueError, TypeError):
            pass
    return False


def extract_content(tool_name, tool_input):
    """Extract the new content from the tool input."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", []) or []
        return "\n".join(e.get("new_string", "") for e in edits)
    if tool_name == "NotebookEdit":
        return tool_input.get("new_source", "")
    return ""


def check_rule(rule, file_path, content):
    """Return True if rule matches the file/content.

    Supports optional `must_not_match` (rule fires only when regex/substrings
    match AND must_not_match does NOT) and `blocking: true` (hard tripwire:
    fires on every match, skipping the once-per-file-per-session dedup).
    """
    paths = rule.get("paths") or []
    exclude = rule.get("exclude_paths") or []
    if paths and not path_matches(file_path, paths):
        return False
    if exclude and path_matches(file_path, exclude):
        return False

    hit = False
    substrings = rule.get("substrings") or []
    if substrings and content:
        for s in substrings:
            if s in content:
                hit = True
                break
    regex = rule.get("regex")
    if not hit and regex and content:
        try:
            if re.search(regex, content):
                hit = True
        except re.error:
            return False
    if not hit:
        return False

    must_not = rule.get("must_not_match")
    if must_not and content:
        try:
            if re.search(must_not, content):
                return False  # mitigation present — suppress the finding
        except re.error:
            pass
    return True


_SAFE_SESSION_RE = re.compile(r"[^A-Za-z0-9_-]")


def _safe_session_id(raw):
    """Sanitize the session id so it can never break out of STATE_DIR."""
    if not raw or not isinstance(raw, str):
        return "default"
    cleaned = _SAFE_SESSION_RE.sub("_", raw)[:64]
    return cleaned or "default"


def state_file(session_id):
    return STATE_DIR / f"aibtc_pattern_state_{_safe_session_id(session_id)}.json"


def load_state(session_id):
    f = state_file(session_id)
    if not f.exists():
        return set()
    try:
        return set(json.loads(f.read_text()))
    except (json.JSONDecodeError, OSError):
        return set()


def save_state(session_id, shown):
    f = state_file(session_id)
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(sorted(shown)))
    except OSError:
        pass


def main():
    if os.environ.get("AIBTC_PATTERN_CHECK_DISABLE") == "1":
        sys.exit(0)

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        sys.exit(0)  # fail-open on malformed input

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        sys.exit(0)

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not file_path:
        sys.exit(0)

    # Skip files outside the project (auto-memory writes, /tmp scratch).
    try:
        Path(file_path).resolve().relative_to(Path(PROJECT_DIR).resolve())
    except (ValueError, OSError):
        sys.exit(0)

    content = extract_content(tool_name, tool_input)
    if not content:
        sys.exit(0)

    patterns = load_patterns()
    if not patterns:
        sys.exit(0)

    session_id = payload.get("session_id", "default")
    shown = load_state(session_id)

    for rule in patterns:
        name = rule.get("rule_name") or rule.get("ruleName")
        reminder = rule.get("reminder")
        if not name or not reminder:
            continue
        if not check_rule(rule, file_path, content):
            continue
        key = f"{file_path}::{name}"
        blocking = bool(rule.get("blocking"))
        if not blocking:
            if key in shown:
                continue  # don't repeat the same warning for the same file this session
            shown.add(key)
            save_state(session_id, shown)
        msg = reminder[:1024]
        print(f"⚠️  AIBTC security pattern: {name}\n{msg}", file=sys.stderr)
        sys.exit(2)  # block the tool call; Claude sees the warning in context

    sys.exit(0)


if __name__ == "__main__":
    main()
