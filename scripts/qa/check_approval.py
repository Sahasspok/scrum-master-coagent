#!/usr/bin/env python3
"""check_approval.py v1.0.0 - validates runs/<id>/approval.json against the facilitation allow-list.
Usage: check_approval.py approval.json
Fails on: missing fields, expired approval, an op outside the allow-list, a payload that touches
backlog order, estimates, assignees, status or Sprint scope, duplicate action ids, or more than
10 actions without "second_approval": true. Exit 0 pass, 1 fail. Prints one JSON line."""
import datetime
import json
import sys

ALLOWED_OPS = {"log_impediment", "comment", "schedule_event", "post_message", "create_improvement_item"}
ALLOWED_TOOLS = {"jira", "clickup", "calendar", "slack"}
FORBIDDEN_KEYS = {"points", "story_points", "estimate", "assignee", "assign", "rank", "order",
                  "priority", "status", "transition", "sprint", "sprint_backlog", "parent", "split"}
REQUIRED = ("run", "approved_by", "approved_at", "expires_at", "actions")


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}".lstrip("."), k
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def parse(ts):
    d = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


errs = []
try:
    a = json.load(open(sys.argv[1]))
except (OSError, ValueError) as e:
    print(json.dumps({"check": "check_approval", "verdict": "FAIL", "defects": [f"unreadable approval.json: {e}"]}))
    sys.exit(1)

for k in REQUIRED:
    if k not in a:
        errs.append(f"missing field: {k}")

if "expires_at" in a:
    try:
        if parse(a["expires_at"]) <= datetime.datetime.now(datetime.timezone.utc):
            errs.append("approval has expired")
    except ValueError:
        errs.append("expires_at is not an ISO timestamp")

actions = a.get("actions") or []
if not actions:
    errs.append("no actions listed")
if len(actions) > 10 and not a.get("second_approval"):
    errs.append(f"{len(actions)} actions need second_approval: true")

seen = set()
for i, act in enumerate(actions, 1):
    aid = act.get("id")
    if not aid:
        errs.append(f"action {i}: missing id")
    elif aid in seen:
        errs.append(f"action {aid}: duplicate id")
    seen.add(aid)
    if act.get("tool") not in ALLOWED_TOOLS:
        errs.append(f"action {aid or i}: tool '{act.get('tool')}' not allowed")
    if act.get("op") not in ALLOWED_OPS:
        errs.append(f"action {aid or i}: op '{act.get('op')}' is outside the Scrum Master facilitation allow-list "
                    f"({', '.join(sorted(ALLOWED_OPS))})")
    for where, key in walk(act.get("payload", {})):
        if key.lower() in FORBIDDEN_KEYS:
            errs.append(f"action {aid or i}: payload field '{where}' changes something the Scrum Master does not own")

print(json.dumps({"check": "check_approval", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
