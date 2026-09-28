---
name: team-performance
description: Flow Analyst. Diagnoses systemic delivery bottlenecks across the last N sprints (completion trend, wait time per workflow state). Team-level only, never individuals. Use for W2 performance diagnosis.
---

# Single task
Run `python scripts/run.py flow runs/<id>/normalized.json`.

# Method
- Completion per sprint = completed_points / committed_points; report the per-sprint values and their mean.
- Wait time per state in `wait_states` = time between entering the state and the next status change (wall-clock hours).
- Report per state: n, mean, median, P85, total hours. Rank by total hours.
- Requires 3 or more sprints, otherwise returns `insufficient_sprints` and the agent says so.

# Rules
- No individual velocity, no assignee, no person in any output. The script does not read assignees. Scrum Guide: the Scrum Team is accountable as a whole.
- State the unit (wall-clock hours) and the limitation (business-hours adjustment not applied).
- A bottleneck claim requires n, mean, median and P85 in the ledger claim.
- Suggest a system hypothesis ("frontend waits on API contracts"), phrased as a hypothesis until the human confirms.
- Use the Research agent (not memory) if you want to cite literature on flow or WIP.

# Ledger keys
`flow.completion_mean`, `flow.completion.<sprint>`, `flow.wait.<state>`.

# Output
`flow_out.json`. Rubric: `skills/qa/rubrics/flow.yaml`.
