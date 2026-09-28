#!/usr/bin/env python3
"""Independent QA check of flow output. Usage: check_flow.py normalized.json flow_out.json"""
import json
import statistics
import sys
from datetime import datetime

d, w = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
errs = []
if len(d.get("sprints", [])) < 3:
    errs.append("fewer than 3 sprints")


def p85(v):
    v = sorted(v)
    return v[-(-85 * len(v) // 100) - 1]


durations = {}
for t in d["tickets"]:
    ts = [(h["status"], datetime.fromisoformat(h["ts"])) for h in t["history"]]
    for (st, a), (_, b) in zip(ts, ts[1:]):
        if st in d["wait_states"]:
            durations.setdefault(st, []).append((b - a).total_seconds() / 3600)

for b in w.get("bottlenecks", []):
    for k in ("n", "mean_h", "median_h", "p85_h"):
        if k not in b:
            errs.append(f"{b.get('state')}: missing {k}")
    v = durations.get(b["state"], [])
    if len(v) != b.get("n"):
        errs.append(f"{b['state']}: n {b.get('n')} != {len(v)}")
        continue
    for k, val in (("mean_h", statistics.mean(v)), ("median_h", statistics.median(v)), ("p85_h", p85(v))):
        if abs(b[k] - val) > 0.06:
            errs.append(f"{b['state']}: {k} {b[k]} != {val:.2f}")

blob = json.dumps(w).lower()
for banned in ('"assignee"', '"owner"', '"member', '"developer"', '"person"'):
    if banned in blob:
        errs.append(f"individual-level key found: {banned}")
print(json.dumps({"check": "check_flow", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
