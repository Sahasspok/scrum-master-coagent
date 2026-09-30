#!/usr/bin/env python3
"""audit_calibration.py v1.0.0 - independently recomputes system calibration from closed runs.
A run counts as closed only if runs/<id>/actuals.json exists. This script is the ground-truth
source: meta-qa calls it to build its report, and QA calls it again to verify that report.
Usage: audit_calibration.py <runs_dir>"""
import json
import pathlib
import statistics
import sys


def load_closed(runs_dir):
    out = []
    root = pathlib.Path(runs_dir)
    if not root.exists():
        return out
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        act = d / "actuals.json"
        if not act.exists():
            continue
        cap = d / "capacity_out.json"
        rdy = d / "readiness_out.json"
        out.append({
            "id": d.name,
            "actuals": json.loads(act.read_text()),
            "capacity": json.loads(cap.read_text()) if cap.exists() else None,
            "readiness": json.loads(rdy.read_text()) if rdy.exists() else None,
        })
    return out


def capacity_calibration(runs):
    errs = []
    for r in runs:
        c, a = r["capacity"], r["actuals"].get("capacity")
        if c and a and c.get("predicted_points"):
            pred, actual = c["predicted_points"], a["actual_completed_points"]
            errs.append(abs(pred - actual) / pred)
    if not errs:
        return None
    return {"n": len(errs), "mean_abs_pct_error": round(statistics.mean(errs) * 100, 1),
            "max_abs_pct_error": round(max(errs) * 100, 1)}


def readiness_calibration(runs):
    tp = fp = 0
    for r in runs:
        flagged = {f["ticket"] for f in (r["readiness"] or {}).get("flags", [])}
        outcomes = {o["ticket"]: o["did_block"] for o in r["actuals"].get("readiness", [])}
        for ticket, blocked in outcomes.items():
            if ticket in flagged and blocked:
                tp += 1
            elif ticket in flagged and not blocked:
                fp += 1
    if tp + fp == 0:
        return None
    return {"flagged_and_checked": tp + fp, "true_positives": tp, "false_positives": fp,
            "precision_pct": round(tp / (tp + fp) * 100, 1)}


def flow_calibration(runs):
    calls = [r["actuals"].get("flow", {}).get("bottleneck_confirmed_next_sprint")
             for r in runs if "flow" in r["actuals"]]
    calls = [c for c in calls if c is not None]
    if not calls:
        return None
    return {"n": len(calls), "confirmation_rate_pct": round(sum(calls) / len(calls) * 100, 1)}


if __name__ == "__main__":
    runs = load_closed(sys.argv[1])
    out = {"closed_runs": len(runs), "capacity": capacity_calibration(runs),
           "readiness": readiness_calibration(runs), "flow": flow_calibration(runs)}
    print(json.dumps(out, indent=1))
