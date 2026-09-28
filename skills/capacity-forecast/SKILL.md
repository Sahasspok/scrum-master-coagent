---
name: capacity-forecast
description: Predicts a realistic sprint commitment from team availability, PTO, ceremony buffer and historical throughput, and computes over-commit against the candidate backlog. Use for sprint planning decisions.
---

# Single task
Run `python scripts/run.py capacity runs/<id>/normalized.json` and hand over the JSON.

# Formula (stated in output)
```
gross      = sum(working_days x focus_hours x allocation)
net_hours  = (gross - PTO_hours) x (1 - ceremony_buffer_pct)
rate       = sum(completed_points) / sum(net_hours)   over last <=6 sprints
capacity   = floor(net_hours x rate)                  (round down, conservative)
over_commit_pct = (candidate_points - capacity) / capacity
scope_cut_pct   = (candidate_points - capacity) / candidate_points
```
Use the two percentages with their exact names; they are different numbers.

# Rules
- Every deduction traces to a source (PTO calendar event, ceremony rule).
- Fewer than 3 historical sprints: confidence low, reason stated.
- Unestimated candidates are listed; they count as 0 points and are not guessed.
- Do not recommend which tickets to drop; that is the human's call. Provide the numbers.

# Ledger keys
`capacity.net_hours`, `capacity.pto_hours`, `capacity.rate`, `capacity.points`, `capacity.overcommit`, `capacity.scope_cut`.

# Output
`capacity_out.json`. Rubric: `skills/qa/rubrics/capacity.yaml`.
