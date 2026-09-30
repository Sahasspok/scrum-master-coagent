#!/usr/bin/env python3
"""verify_brief.py v2.1.0 - QA gate for the composer's four-part reply contract
(Answer, Data supporting this, Recommendation, Questions to keep moving).
Usage: verify_brief.py brief.md ledger.jsonl
Checks: required sections in order, no placeholders, every ledger tag exists, every number has
a tag, low-confidence wording, human-context labels, Insight/What-I'd-look-into-next present,
numbered forward questions, Provenance footer, body length.
v2.1.0: numbers that only name a move ("move 1"), an option, or a Guide section (SG-08) are not facts and need no ledger tag."""
import json
import re
import sys

REQUIRED = ["Answer", "Data supporting this", "Recommendation", "Questions to keep moving"]
MAX_WORDS = 500

brief = open(sys.argv[1]).read()
rows = {r["id"]: r for r in (json.loads(x) for x in open(sys.argv[2]) if x.strip())}
errs = []

if "{{" in brief:
    errs.append("unfilled placeholder '{{'")

positions = []
for sec in REQUIRED:
    m = re.search(r"(?m)^## " + re.escape(sec) + r"\b", brief)
    if not m:
        errs.append(f"missing section: {sec}")
    else:
        positions.append((sec, m.start()))
if [p[0] for p in sorted(positions, key=lambda p: p[1])] != [s for s in REQUIRED if any(s == p[0] for p in positions)]:
    errs.append("sections are out of order; must be Answer, Data supporting this, Recommendation, Questions to keep moving")

if "**Provenance:**" not in brief:
    errs.append("missing Provenance footer after part 4")
if "**Insight:**" not in brief:
    errs.append("Recommendation is missing an **Insight:** line")
if "**What I'd look into next:**" not in brief:
    errs.append("Recommendation is missing a **What I'd look into next:** line")

qm = re.search(r"(?ms)^## Questions to keep moving\n(.*?)(?:\n---|\Z)", brief)
if not qm or not re.search(r"^\d+\.\s", qm.group(1), re.M):
    errs.append("Questions to keep moving has no numbered question")
elif not re.search(r"i['’]ll|i will", qm.group(1), re.I):
    errs.append("Questions to keep moving doesn't name the next action the agent will take ('...once confirmed, I'll ...')")

NUM = re.compile(r"(?<![\w.#-])\d+(?:\.\d+)?%?")
words, in_provenance = 0, False
for n, line in enumerate(brief.splitlines(), 1):
    s = line.strip()
    if s == "---":
        in_provenance = True
        continue
    if not s or s.startswith("#") or re.fullmatch(r"[|\-: ]+", s):
        continue
    tags = re.findall(r"\[(E-\d{3})\]", s)
    for t in tags:
        if t not in rows:
            errs.append(f"line {n}: unknown ledger id {t}")
        elif rows[t]["confidence"] == "low" and "low confidence" not in s.lower():
            errs.append(f"line {n}: cites low-confidence {t} without saying 'low confidence'")
        elif rows[t]["source_type"] == "human_context" and "(human context)" not in s.lower():
            errs.append(f"line {n}: cites human context {t} without '(human context)' label")
    if not s.startswith("|") and not in_provenance:
        words += len(s.split())
    if in_provenance or "Data as of" in s:
        continue
    body = re.sub(r"\[E-\d{3}\]|Sprint \d+|#\d+|\d{4}-\d{2}-\d{2}|^\d+\.\s|\b[Mm]oves? \d+|\b[Oo]ption \d+|\b(?:SG|SX)-\d+", "", s)
    if NUM.search(body) and not tags:
        errs.append(f"line {n}: number without ledger tag: {s[:70]}")
if words > MAX_WORDS:
    errs.append(f"body is {words} words; limit {MAX_WORDS} (excluding tables and provenance)")

print(json.dumps({"check": "verify_brief", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
