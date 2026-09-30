#!/usr/bin/env python3
"""capacity.py v1.0.0 - deterministic sprint capacity forecast (no LLM math).
Usage: capacity.py normalized.json   -> JSON on stdout"""
import hashlib
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ledger import make_row  # noqa: E402

VERSION = "1.0.0"
MIN_SPRINTS = 3
HISTORY_WINDOW = 6
METHOD = ("net=(gross-PTO)x(1-ceremony%); rate=sum(points)/sum(net hours) over last <=6 sprints; "
          "points=floor(net x rate); over_commit=(candidate-capacity)/capacity")


def forecast(d, sha):
    ref = f"capacity.py@{VERSION}#{sha[:12]}"
    s, team = d["sprint"], d["members"]
    hpd, days, cer = s["focus_hours_per_day"], s["working_days"], s["ceremony_buffer_pct"]
    gross = sum(days * hpd * m.get("allocation", 1.0) for m in team)
    pto_lines = [{"type": "pto", "member_ref": m["ref"],
                  "hours": round(m["pto_days"] * hpd * m.get("allocation", 1.0), 2),
                  "source": m.get("pto_source", "calendar")}
                 for m in team if m.get("pto_days", 0)]
    pto = sum(x["hours"] for x in pto_lines)
    ceremony = (gross - pto) * cer
    net = gross - pto - ceremony

    hist = d.get("history", [])[-HISTORY_WINDOW:]
    pts = sum(h["completed_points"] for h in hist)
    hrs = sum(h["net_hours"] for h in hist)
    rate = pts / hrs if hrs else None
    cap = math.floor(net * rate) if rate else None

    cand = sum(t["points"] or 0 for t in d["candidates"])
    unest = [t["id"] for t in d["candidates"] if t["points"] is None]
    over = round((cand - cap) / cap * 100, 1) if cap else None
    cut = round(max(cand - cap, 0) / cand * 100, 1) if cap and cand else None

    if len(hist) >= MIN_SPRINTS and rate:
        conf, why = "high", ""
    else:
        conf, why = "low", f"only {len(hist)} historical sprint(s); need {MIN_SPRINTS}"

    rows = [
        make_row("capacity.pto_hours", f"PTO deduction = {pto:.1f} hours", "script", ref,
                 "sum(pto_days x focus hours x allocation) from calendar events", "high", value=pto),
        make_row("capacity.net_hours", f"Net focus hours = {net:.1f} after {pto:.1f} PTO hours and {cer:.0%} ceremony buffer",
                 "script", ref, METHOD, "high", value=round(net, 2)),
    ]
    if rate:
        rows.append(make_row("capacity.rate", f"Historical rate = {rate:.4f} SP per net hour over {len(hist)} sprints",
                             "script", ref, METHOD, conf, why, value=round(rate, 6)))
    if cap is not None:
        rows.append(make_row("capacity.points", f"Predicted sprint capacity = {cap} SP", "script", ref, METHOD, conf, why, value=cap))
        rows.append(make_row("capacity.overcommit",
                             f"Candidate backlog of {cand} SP is {over}% over capacity of {cap} SP",
                             "script", ref, METHOD, conf, why, value=over))
        rows.append(make_row("capacity.scope_cut", f"Fitting capacity requires cutting {cut}% of the {cand} SP candidate scope",
                             "script", ref, METHOD, conf, why, value=cut))
    return {
        "tool": "capacity.py", "version": VERSION, "input_sha": sha,
        "gross_hours": round(gross, 2),
        "deductions": pto_lines + [{"type": "ceremony_buffer", "hours": round(ceremony, 2),
                                    "rule": f"{cer:.0%} of post-PTO hours"}],
        "net_hours": round(net, 2), "rate_sp_per_hour": rate, "history_sprints": len(hist),
        "predicted_points": cap, "candidate_points": cand, "unestimated_tickets": unest,
        "over_commit_pct": over, "scope_cut_pct": cut, "formula": METHOD,
        "confidence": conf, "confidence_reason": why, "ledger_rows": rows,
    }


if __name__ == "__main__":
    raw = pathlib.Path(sys.argv[1]).read_bytes()
    print(json.dumps(forecast(json.loads(raw), hashlib.sha256(raw).hexdigest()), indent=1))
