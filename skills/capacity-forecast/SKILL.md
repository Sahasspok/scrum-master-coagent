---
name: capacity-forecast
description: Prepares a realistic sprint-capacity signal from team availability, PTO, ceremony buffer and historical throughput, for the Developers' own Sprint Planning conversation. Use for W1 Sprint Planning support — never to decide the commitment yourself.
---

# Single task
Run `python scripts/run.py capacity runs/<id>/normalized.json` and hand over the JSON.

# Role fidelity
The Sprint Backlog and its commitment belong to the Developers (Scrum Guide 2020). This tool produces a descriptive signal for that conversation — it never states a commitment as decided, and the Scrum Master's job with this output is only to facilitate Sprint Planning with it, not to tell the Developers what to take on.

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
- Never recommend which tickets to drop or what to commit to — that is the Developers' call. Provide the numbers only; the composer frames the facilitation action.

# Ledger keys
`capacity.net_hours`, `capacity.pto_hours`, `capacity.rate`, `capacity.points`, `capacity.overcommit`, `capacity.scope_cut`.

# Output
`capacity_out.json`. Rubric: `skills/qa/rubrics/capacity.yaml`.
