#!/usr/bin/env python3
"""flow.py v1.0.0 - systemic flow analysis across sprints. Team level only; assignees are never read.
Usage: flow.py normalized.json"""
import hashlib
import json
import math
import pathlib
import statistics
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger import make_row  # noqa: E402

VERSION = "1.0.0"
MIN_SPRINTS = 3


def pctl(vals, p):
    v = sorted(vals)
    return v[max(0, math.ceil(p / 100 * len(v)) - 1)]


def analyze(d, sha):
    ref = f"flow.py@{VERSION}#{sha[:12]}"
    sp = d.get("sprints", [])
    if len(sp) < MIN_SPRINTS:
        return {"error": "insufficient_sprints", "have": len(sp), "need": MIN_SPRINTS}
    comp = [{"sprint": s["sprint"],
             "completion_pct": round(s["completed_points"] / s["committed_points"] * 100, 1)}
            for s in sp if s["committed_points"]]
    mean_c = round(sum(c["completion_pct"] for c in comp) / len(comp), 1)

    waits = {st: [] for st in d["wait_states"]}
    for t in d["tickets"]:
        h = t["history"]
        for a, b in zip(h, h[1:]):
            if a["status"] in waits:
                dt = (datetime.fromisoformat(b["ts"]) - datetime.fromisoformat(a["ts"])).total_seconds() / 3600
                waits[a["status"]].append(dt)

    ranked = []
    for st, v in waits.items():
        if v:
            ranked.append({"state": st, "n": len(v), "mean_h": round(statistics.mean(v), 1),
                           "median_h": round(statistics.median(v), 1), "p85_h": round(pctl(v, 85), 1),
                           "total_h": round(sum(v), 1)})
    ranked.sort(key=lambda r: r["total_h"], reverse=True)

    method = "wait = time from entering a wait state to the next status change, wall-clock hours; P85 nearest-rank"
    rows = [make_row("flow.completion_mean",
                     f"Mean sprint completion = {mean_c}% across {len(comp)} sprints", "script", ref,
                     "completed_points / committed_points per sprint, then mean", "high", value=mean_c)]
    for c in comp:
        rows.append(make_row(f"flow.completion.{c['sprint']}",
                             f"Sprint {c['sprint']} completion = {c['completion_pct']}%", "script", ref,
                             "completed_points / committed_points", "high", value=c["completion_pct"]))
    for r in ranked:
        n = r["n"]
        conf, why = ("high", "") if n >= 10 else (("medium", f"n={n}; 10 or more preferred") if n >= 5 else ("low", f"n={n}; fewer than 5 observations"))
        slug = r["state"].lower().replace(" ", "_")
        rows.append(make_row(f"flow.wait.{slug}",
                             f"'{r['state']}' wait: n={n}, mean={r['mean_h']}h, median={r['median_h']}h, P85={r['p85_h']}h",
                             "script", ref, method, conf, why, value=r["mean_h"]))
    return {"tool": "flow.py", "version": VERSION, "input_sha": sha, "sprints_analyzed": len(sp),
            "completion": comp, "mean_completion_pct": mean_c, "bottlenecks": ranked,
            "unit": "wall-clock hours", "limitation": "business-hours adjustment not applied",
            "note": "system-level only; no individual metrics computed", "ledger_rows": rows}


if __name__ == "__main__":
    raw = pathlib.Path(sys.argv[1]).read_bytes()
    out = analyze(json.loads(raw), hashlib.sha256(raw).hexdigest())
    print(json.dumps(out, indent=1))
    sys.exit(2 if "error" in out else 0)
