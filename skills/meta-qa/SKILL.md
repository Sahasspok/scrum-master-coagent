---
name: meta-qa
description: Periodically audits closed runs (where real outcomes are now known) to check every agent's predictions against what actually happened, and resamples QA's own judgment calls for agreement. Reports system calibration via the same four-part contract. Use when the human asks how accurate or reliable the system has been, when closing a sprint with actuals, or on a recurring cadence.
---

# Single task
Answer one question with numbers: is the system's output still trustworthy. Never audits an open or in-flight run — only runs with `actuals.json`.

# Trigger
- Human supplies actuals for a run ("Sprint 14 actually completed 33 points; #104 did block; #112 held after splitting") -> write `runs/<id>/actuals.json`, then run this agent for that run.
- Human asks "how accurate have we been", "run a calibration check", "audit QA" -> run across every closed run under `runs/`.
- This architecture has no autonomous scheduler; recommend triggering meta-qa after every sprint closes, or on whatever cadence the human's own scheduler (cron, CI, calendar) supports.

# Procedure
1. **Close a run:** write `runs/<id>/actuals.json` (schema below). Never edit the original prediction files — actuals are additive.
2. **Recompute calibration:** `python scripts/qa/audit_calibration.py runs/` to get, across all closed runs:
   - Capacity: mean and max absolute percent error vs `actual_completed_points`.
   - Readiness: precision (true positives / flagged-and-checked) using `did_block` outcomes.
   - Flow: confirmation rate of prior bottleneck hypotheses, from human-supplied `bottleneck_confirmed_next_sprint`.
3. **Band the result:** compare each figure to `skills/meta-qa/scorecard.yaml` and label "within band" or "drifting" — the label must match the number, QA re-checks this.
4. **Judgment resample:** pick at least 20% (minimum 3) of past PASS verdicts that included a judgment-type (non-script) check. Re-review each independently, blind to the original verdict, against the same rubric. Record every disagreement by check id.
5. **Research resample:** re-run `doi_check.py` on at least 20% of previously cited DOIs; confirm none now resolve as retracted or reclassified.
6. Write `meta_qa_out.json` (ledger rows below), hand to Composer for the four-part reply, then QA.

# actuals.json schema
```json
{
  "run": "<id>", "closed_at": "ISO",
  "capacity": {"actual_completed_points": 33},
  "readiness": [{"ticket": "104", "did_block": true}, {"ticket": "112", "did_block": false}],
  "flow": {"bottleneck_confirmed_next_sprint": true}
}
```

# Rules
- Needs at least `min_closed_runs_for_trend` closed runs (see scorecard.yaml) before stating a trend; below that, report the raw numbers only, labeled low confidence, and make no drift claim.
- A drift finding is reported as a fact with a ledger id. It never auto-changes a rubric or the scorecard — those are human edits only.
- Every judgment-resample disagreement goes to the human by check id and both verdicts, never compressed into a single aggregate score.
- Findings are framed at the system or rubric level ("readiness threshold may be miscalibrated"), never as blame on a QA run or a worker agent.
- QA structurally gates the report and independently re-runs `audit_calibration.py` and `check_band.py` against it; QA does not re-judge meta-qa's own judgment-resample calls — that loop's backstop is the human reading the disagreement list.

# Ledger keys
`meta.capacity_mape`, `meta.readiness_precision`, `meta.flow_confirmation_rate`, `meta.qa_agreement_rate`, `meta.research_integrity`.

# Output
`meta_qa_out.json`. Rubric: `skills/qa/rubrics/meta-qa.yaml`.
