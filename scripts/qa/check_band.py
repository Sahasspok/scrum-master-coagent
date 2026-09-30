#!/usr/bin/env python3
"""check_band.py v1.0.0 - verifies meta-qa's stated bands ('within band' / 'drifting') against
scorecard.yaml thresholds. Usage: check_band.py <meta_qa_out.json> <scorecard.yaml>"""
import json
import sys

import yaml

report = json.load(open(sys.argv[1]))
bands = yaml.safe_load(open(sys.argv[2]))
c = report.get("calibration", {})
stated = report.get("bands", {})
errs = []


def check(within, key):
    label = stated.get(key)
    if label is None:
        errs.append(f"{key}: no band stated")
    elif within and label != "within band":
        errs.append(f"{key}: recomputed value is within threshold but reported '{label}'")
    elif not within and label == "within band":
        errs.append(f"{key}: recomputed value exceeds threshold but reported 'within band'")


if report.get("closed_runs", 0) < bands["min_closed_runs_for_trend"]:
    if any(v == "drifting" for v in stated.values()):
        errs.append("fewer than min_closed_runs_for_trend closed runs but a 'drifting' band was stated")
else:
    if c.get("capacity"):
        check(c["capacity"]["mean_abs_pct_error"] <= bands["capacity_mape_max_pct"], "capacity")
    if c.get("readiness"):
        check(c["readiness"]["precision_pct"] >= bands["readiness_precision_min_pct"], "readiness")
    if c.get("flow"):
        check(c["flow"]["confirmation_rate_pct"] >= bands["flow_confirmation_min_pct"], "flow")

print(json.dumps({"check": "check_band", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
