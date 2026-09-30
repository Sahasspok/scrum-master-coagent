#!/usr/bin/env python3
"""readiness.py v1.0.0 - backlog readiness flags.  Usage: readiness.py normalized.json"""
import hashlib
import json
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger import make_row  # noqa: E402

VERSION = "1.0.0"
MIN_HISTORY = 10
TESTABLE = re.compile(r"\b(given|when|then|must|shall|returns?|displays?|within)\b|\d", re.I)
RULES = {"R1": "Acceptance criteria missing or untestable",
         "R2": "Exceeds team size threshold; recommend splitting",
         "R3": "Unestimated",
         "R4": "Open dependency"}


def pctl(vals, p):
    v = sorted(vals)
    return v[max(0, math.ceil(p / 100 * len(v)) - 1)]


def audit(d, sha):
    ref = f"readiness.py@{VERSION}#{sha[:12]}"
    hist = d.get("ticket_points_history", [])
    thr = pctl(hist, 85) if len(hist) >= MIN_HISTORY else None
    rows, flags = [], []
    if thr is not None:
        rows.append(make_row("readiness.size_threshold",
                             f"Single-ticket size threshold = {thr} SP (P85 of {len(hist)} completed tickets)",
                             "script", ref, "nearest-rank P85 of team ticket-size history", "high", value=thr))
    else:
        rows.append(make_row("readiness.size_threshold",
                             "No size threshold: not enough ticket history", "script", ref,
                             f"requires {MIN_HISTORY} or more completed tickets", "low",
                             f"only {len(hist)} completed tickets in history"))

    def add(t, rule, evidence):
        flags.append({"ticket": t["id"], "title": t["title"], "rule": rule,
                      "rule_text": RULES[rule], "evidence": evidence})
        rows.append(make_row(f"readiness.{t['id']}.{rule}", f"#{t['id']} {t['title']}: {RULES[rule]}. {evidence}",
                             "script", ref, RULES[rule], "high", value=rule))

    for t in d["candidates"]:
        ac = [x for x in t.get("acceptance_criteria", []) if x.strip()]
        if not ac:
            add(t, "R1", "No acceptance criteria present")
        elif not any(TESTABLE.search(x) for x in ac):
            add(t, "R1", "Criteria not testable: " + ac[0][:80])
        if t["points"] is None:
            add(t, "R3", "Points are null")
        elif thr is not None and t["points"] > thr:
            add(t, "R2", f"{t['points']} SP exceeds threshold {thr} SP")
        open_deps = [b["id"] for b in t.get("blocked_by", []) if b["status"] != "Done"]
        if open_deps:
            add(t, "R4", "Blocked by " + ", ".join(open_deps))
    return {"tool": "readiness.py", "version": VERSION, "input_sha": sha, "size_threshold": thr,
            "candidates_audited": len(d["candidates"]), "flags": flags,
            "flagged_ticket_count": len({f["ticket"] for f in flags}), "ledger_rows": rows}


if __name__ == "__main__":
    raw = pathlib.Path(sys.argv[1]).read_bytes()
    print(json.dumps(audit(json.loads(raw), hashlib.sha256(raw).hexdigest()), indent=1))
