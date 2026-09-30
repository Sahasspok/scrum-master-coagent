#!/usr/bin/env python3
"""check_accountability.py v1.0.0 - role-fidelity gate for the composer's reply.
Usage: check_accountability.py brief.md
Fails a reply that (a) does not say whose call the matter is, (b) does not ground itself in a retrieved
Scrum Guide section, (c) offers moves outside the Scrum Master vocabulary, (d) decides or does another
role's work, or (e) evaluates individuals. Exit 0 pass, 1 fail. Prints one JSON line."""
import json
import re
import sys

OWNERS = ["developers", "product owner", "scrum team", "scrum master"]
VERBS = ("Facilitate", "Coach", "Teach", "Make transparent", "Remove impediment",
         "Shield", "Ask", "Escalate", "Do nothing")

# (pattern, defect). Applied to every non-table line outside the Provenance footer.
OVERSTEP = [
    (r"\bcommit(?:ting)?\s+to\s+\d+", "states a Sprint commitment; the Developers forecast and commit"),
    (r"\b(?:should|must|need to|needs to)\s+commit\b", "tells the team to commit"),
    (r"\b(?:split|break down|decompose)\s+(?:#?\d+|the (?:ticket|story|item)|this (?:ticket|story|item))",
     "directs a ticket split; that is a Product Owner and Developers refinement decision"),
    (r"\b(?:re-?rank|re-?order|re-?prioriti[sz]e|de-?scope)\b|\bdrop\s+#?\d+|\bmove\s+#?\d+\s+(?:up|down|out)",
     "changes backlog or Sprint scope; the Product Owner orders, the Developers select"),
    (r"\b(?:re-?)?assign(?:ed|ing)?\s+(?:#?\d+|the (?:ticket|story|task))",
     "assigns work; the Developers self-manage"),
    (r"\b(?:re-?point|re-?estimate|(?:set|change)\s+(?:the\s+)?(?:story\s+)?points)\b",
     "sets or changes estimates; the Developers size"),
    (r"\b(?:mark|rule|declare|deem)\b.{0,25}\bready\b",
     "rules an item ready; refinement is a Product Owner and Developers activity"),
    (r"\btell\s+(?:the\s+)?(?:team|developers|product owner|po)\s+to\b",
     "instructs another role instead of facilitating"),
    (r"\b(?:slowest|underperform\w*|weakest|lowest velocity)\b|\brank(?:ing)?\s+(?:the\s+)?(?:developers|members|people)\b"
     r"|\bvelocity of (?:dev|member|person|engineer)\w*", "evaluates individuals"),
    (r"\b(?:gantt|critical path|resource allocation|risk register|work breakdown)\b",
     "project-management artifact; not part of Scrum"),
    (r"\bI['’]ll\s+(?:split|re-?rank|re-?order|assign|estimate|re-?point|rewrite|"
     r"draft the (?:sub-?tickets?|acceptance criteria|stor(?:y|ies))|"
     r"organize\s+(?:the\s+)?(?:backlog|sprint)\b|"
     r"prioritize\s+(?:the\s+)?(?:backlog|candidate|tickets?)\b)",
     "the agent offers to do another role's work"),
    (r"\b(?:draft|write|author|define)\s+(?:the\s+)?acceptance criteria\b",
     "directs creating acceptance criteria; that is the Product Owner's accountability with Developers"),
    (r"\b(?:organize|setup|set up)\s+(?:the\s+)?(?:sprint|backlog)\s+(?:list|board|priorities)\b",
     "attempts to organize/reorder backlog priorities; that is the Product Owner's accountability"),
]
EXEMPT = re.compile(r"(?:their|the developers['’]|the product owner['’]s|the team['’]s)\s+(?:call|decision|choice|accountability|work|role)"
                    r"|not\s+(?:mine|ours|the scrum master['’]s)\s+to|out of remit"
                    r"|(?:ask|prompt|request|coach)\s+(?:the\s+)?(?:product owner|po|developers?)"
                    r"|(?:memo|email|message|prompt|request)\s+(?:to|for)\s+(?:the\s+)?(?:product owner|po)", re.I)

text = open(sys.argv[1]).read()
errs = []


def line_with(label):
    m = re.search(r"(?m)^\*\*" + re.escape(label) + r":\*\*(.*)$", text)
    return m.group(1).strip() if m else None


whose = line_with("Whose call")
owner = None
if whose is None:
    errs.append("missing **Whose call:** line")
else:
    low = whose.lower()
    owner = next((o for o in OWNERS if o in low), None)
    if owner is None:
        errs.append("**Whose call:** must name Developers, Product Owner, Scrum Team or Scrum Master")

says = line_with("What Scrum says")
if says is None:
    errs.append("missing **What Scrum says:** line")
elif not re.search(r"\bSG-\d+\b", says):
    errs.append("**What Scrum says:** must cite a retrieved Scrum Guide section (SG-nn)")

mm = re.search(r"(?ms)^\*\*Scrum Master moves:\*\*\s*\n(.*?)(?=^\*\*[A-Z]|^## |^---|\Z)", text)
if not mm:
    errs.append("missing **Scrum Master moves:** block")
else:
    moves = re.findall(r"(?m)^\d+\.\s+(.*)$", mm.group(1))
    if len(moves) < 2:
        errs.append("Scrum Master moves needs at least 2 numbered moves")
    for n, mv in enumerate(moves, 1):
        if not re.match(r"\*\*(?:" + "|".join(VERBS) + r")\b", mv):
            errs.append(f"move {n} must open with a bolded Scrum Master verb ({', '.join(VERBS)})")

dec = line_with("Decision for you")
if dec is None:
    errs.append("missing **Decision for you:** line")
elif not re.search(r"\bmove\s+\d", dec, re.I):
    errs.append("**Decision for you:** must name which move (e.g. 'move 1') the Scrum Master chooses")

if owner in ("developers", "product owner", "scrum team") and line_with("Questions to put to the team") is None:
    errs.append("owner is not the Scrum Master: add **Questions to put to the team:** so the decision goes back to its owner")

in_footer = False
for n, raw in enumerate(text.splitlines(), 1):
    s = raw.strip()
    if s == "---":
        in_footer = True
    if in_footer or not s or s.startswith("|") or s.startswith("#"):
        continue
    if EXEMPT.search(s):
        continue
    for pat, why in OVERSTEP:
        if re.search(pat, s, re.I):
            errs.append(f"line {n}: {why}: {s[:80]}")

print(json.dumps({"check": "check_accountability", "owner": owner,
                  "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
