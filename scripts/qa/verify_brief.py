#!/usr/bin/env python3
"""verify_brief.py v1.0.0 - QA gate for the Decision Brief / Sprint Report.
Usage: verify_brief.py brief.md ledger.jsonl
Checks: required sections, no placeholders, every ledger tag exists, every number has a tag,
low-confidence wording, human-context labels, body length."""
import json
import re
import sys

REQUIRED = ["Recommendation", "Options and trade-offs", "Evidence", "Context and assumptions",
            "Risks", "Open questions for you", "Provenance"]
MAX_WORDS = 450

brief = open(sys.argv[1]).read()
rows = {r["id"]: r for r in (json.loads(x) for x in open(sys.argv[2]) if x.strip())}
errs = []

if "{{" in brief:
    errs.append("unfilled placeholder '{{'")
for sec in REQUIRED:
    if not re.search(r"(?m)^## " + re.escape(sec) + r"\b", brief):
        errs.append(f"missing section: {sec}")

NUM = re.compile(r"(?<![\w.#-])\d+(?:\.\d+)?%?")
words, section = 0, ""
for n, line in enumerate(brief.splitlines(), 1):
    s = line.strip()
    m = re.match(r"## (.+)", s)
    if m:
        section = m.group(1)
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
    if not s.startswith("|"):
        words += len(s.split())
    if section == "Provenance" or "Data as of" in s:
        continue
    body = re.sub(r"\[E-\d{3}\]|Sprint \d+|#\d+|\d{4}-\d{2}-\d{2}|^\d+\.\s", "", s)
    if NUM.search(body) and not tags:
        errs.append(f"line {n}: number without ledger tag: {s[:70]}")
if words > MAX_WORDS:
    errs.append(f"body is {words} words; limit {MAX_WORDS} (excluding tables)")

print(json.dumps({"check": "verify_brief", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
