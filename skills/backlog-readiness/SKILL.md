---
name: backlog-readiness
description: Flags risky candidate tickets before sprint planning: missing or untestable acceptance criteria, oversized, unestimated, open dependencies. Use for W1 sprint planning.
---

# Single task
Run `python scripts/run.py readiness runs/<id>/normalized.json`.

# Rules (implemented in the script)
| Rule | Flag | Evidence required |
|---|---|---|
| R1 | Acceptance criteria missing or untestable | The criteria text (or "none present") |
| R2 | Ticket exceeds size threshold; recommend splitting | Points and the threshold |
| R3 | Unestimated | Ticket id |
| R4 | Open dependency | Blocking ticket id and status |

- The size threshold is the P85 of the team's completed ticket sizes (needs 10 or more tickets). With less history no size flag is raised and the ledger says why.
- Cite Scrum Guide grounding only for definitions (e.g. Definition of Done, Product Backlog refinement) via the grounding index, using the section id.
- Flags are predictions of risk, not verdicts; the brief says "high probability of blocker" only when a rule fired.

# Ledger keys
`readiness.size_threshold`, `readiness.<ticket>.<rule>`.

# Output
`readiness_out.json`. Rubric: `skills/qa/rubrics/readiness.yaml`.
