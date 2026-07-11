#!/usr/bin/env python3
"""Regenerate .claude/security-patterns.json from the YAML source of truth.

The hooks (.claude/hooks/pattern_check.py) prefer the YAML but fall back to
the JSON on machines whose system python3 lacks PyYAML. Run this after any
edit to .claude/security-patterns.yaml.
"""
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required to compile: pip3 install pyyaml")

root = Path(__file__).resolve().parents[1]
src = root / ".claude" / "security-patterns.yaml"
dst = root / ".claude" / "security-patterns.json"

data = yaml.safe_load(src.read_text()) or {}
patterns = data.get("patterns", [])
if not isinstance(patterns, list):
    sys.exit(f"{src}: `patterns` must be a list")

dst.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {dst} ({len(patterns)} rules)")
