#!/usr/bin/env python3
"""Independent QA recompute of capacity. Usage: recompute_capacity.py normalized.json capacity_out.json
Deliberately written separately from scripts/capacity.py."""
import json
import math
import sys

d, w = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
s = d["sprint"]
net = sum((s["working_days"] - m.get("pto_days", 0)) * s["focus_hours_per_day"] * m.get("allocation", 1.0)
          for m in d["members"]) * (1 - s["ceremony_buffer_pct"])
h = d["history"][-6:]
cap = math.floor(net * sum(x["completed_points"] for x in h) / sum(x["net_hours"] for x in h))
cand = sum(t["points"] or 0 for t in d["candidates"])
over = round((cand - cap) / cap * 100, 1)
cut = round(max(cand - cap, 0) / cand * 100, 1)

errs = []
if abs(net - w["net_hours"]) > 0.01:
    errs.append(f"net_hours {w['net_hours']} != {net:.2f}")
if cap != w["predicted_points"]:
    errs.append(f"predicted_points {w['predicted_points']} != {cap}")
if over != w["over_commit_pct"]:
    errs.append(f"over_commit_pct {w['over_commit_pct']} != {over} (formula: (candidate-capacity)/capacity)")
if cut != w["scope_cut_pct"]:
    errs.append(f"scope_cut_pct {w['scope_cut_pct']} != {cut}")
for x in w["deductions"]:
    if x["type"] == "pto" and not x.get("source"):
        errs.append("PTO deduction without source")
    if x["type"] == "ceremony_buffer" and not x.get("rule"):
        errs.append("ceremony deduction without rule")
if len(h) < 3 and w.get("confidence") != "low":
    errs.append("fewer than 3 sprints but confidence is not low")
print(json.dumps({"check": "recompute_capacity", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
