"""Deterministic Sprint 14 fixtures. Expected: capacity 34 SP, over-commit 41.2%, scope cut 29.2%,
flags #104 (R1) and #112 (R2), mean completion 84.2%, top bottleneck 'Waiting for API mockup' mean 22.0h."""
import json
import sys
from datetime import datetime, timedelta

POINTS = {101: 3, 102: 2, 103: 3, 104: 5, 105: 2, 106: 1, 107: 2, 108: 3, 109: 2, 110: 1,
          111: 3, 112: 13, 113: 2, 114: 1, 115: 2, 116: 1, 117: 1, 118: 1}  # 18 tickets, 48 SP
AC = "Given a valid input when the action runs then the result is shown within 2 seconds"
FE_WAIT = [18, 20, 22, 24, 26, 19, 21, 23, 22, 25, 20, 24]   # mean 22.0
REVIEW = [4, 6, 5, 7, 6, 5, 4, 6, 7, 5, 6, 5]


def build():
    cands = [{"id": str(i), "title": f"Ticket {i}", "points": p,
              "acceptance_criteria": [] if i == 104 else [AC], "blocked_by": [], "status": "To Do"}
             for i, p in POINTS.items()]
    cands[3]["title"] = "Payment Gateway Webhook"
    cands[11]["title"] = "Refactor User Session"

    tickets = []
    for k in range(12):
        t = datetime(2026, 9, 1 + (k // 4) * 7, 9)
        hist = []
        for status, dur in (("To Do", 2), ("Waiting for API mockup", FE_WAIT[k]), ("In Progress", 8),
                            ("In Review", REVIEW[k]), ("Done", 0)):
            hist.append({"status": status, "ts": t.isoformat()})
            t += timedelta(hours=dur)
        tickets.append({"id": f"F{k}", "sprint": 11 + k // 4, "assignee": f"dev{k % 4 + 1}", "history": hist})

    return {
        "meta": {"source": "fixture", "jql_hash": "fixture", "fetched_at": "2026-10-05T09:00:00", "total_expected": 18},
        "sprint": {"name": "Sprint 14", "start": "2026-10-07", "working_days": 10,
                   "focus_hours_per_day": 8, "ceremony_buffer_pct": 0.15},
        "members": [{"ref": "dev1", "allocation": 1.0, "pto_days": 3, "pto_source": "calendar:fixture-1"},
                    {"ref": "dev2", "allocation": 1.0, "pto_days": 0},
                    {"ref": "dev3", "allocation": 1.0, "pto_days": 0},
                    {"ref": "dev4", "allocation": 1.0, "pto_days": 0}],
        "history": [{"sprint": 11, "completed_points": 33, "net_hours": 248},
                    {"sprint": 12, "completed_points": 34, "net_hours": 250},
                    {"sprint": 13, "completed_points": 34, "net_hours": 248}],
        "candidates": cands,
        "ticket_points_history": [1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 5, 5, 5, 5, 8, 8, 8, 8, 13],
        "sprints": [{"sprint": 11, "committed_points": 40, "completed_points": 33},
                    {"sprint": 12, "committed_points": 40, "completed_points": 34},
                    {"sprint": 13, "committed_points": 40, "completed_points": 34}],
        "tickets": tickets,
        "wait_states": ["Waiting for API mockup", "In Review"],
    }


if __name__ == "__main__":
    json.dump(build(), sys.stdout, indent=1)
