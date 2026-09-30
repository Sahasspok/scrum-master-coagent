#!/usr/bin/env python3
"""Schema check for normalized.json. Usage: validate_normalized.py normalized.json [expected_candidate_count]"""
import json
import sys
from datetime import datetime

d = json.load(open(sys.argv[1]))
errs = []
for k in ("meta", "sprint", "members", "candidates"):
    if k not in d:
        errs.append(f"missing section {k}")
for k in ("name", "working_days", "focus_hours_per_day", "ceremony_buffer_pct"):
    if k not in d.get("sprint", {}):
        errs.append(f"sprint.{k} missing")
for t in d.get("candidates", []):
    if t.get("points") is None and "unestimated" not in t.get("flags", []):
        errs.append(f"#{t.get('id')}: null points without 'unestimated' flag")
for t in d.get("tickets", []):
    for h in t.get("history", []):
        try:
            datetime.fromisoformat(h["ts"])
        except Exception:
            errs.append(f"ticket {t.get('id')}: bad timestamp {h.get('ts')}")
if "raw" in d:
    errs.append("raw payload present")
if len(sys.argv) > 2 and len(d.get("candidates", [])) != int(sys.argv[2]):
    errs.append(f"expected {sys.argv[2]} candidates, found {len(d.get('candidates', []))}")
print(json.dumps({"check": "validate_normalized", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
