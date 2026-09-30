---
name: backlog-readiness
description: Prepares refinement-readiness signals on candidate tickets (missing or untestable acceptance criteria, oversized, unestimated, open dependencies) for the Product Owner and Developers' own Refinement session. Use for W1 Sprint Planning support — never to rule an item ready yourself.
---

# Single task
Run `python scripts/run.py readiness runs/<id>/normalized.json`.

# Role fidelity
The Product Backlog and its order belong to the Product Owner; refining an item to "ready" is a Product Owner and Developers activity (Scrum Guide 2020). This tool surfaces discussion prompts for that Refinement conversation — it never reorders the backlog, never rules an item ready or not ready, and never sets the Definition of Ready unilaterally. The Scrum Master's job here is to facilitate Refinement with these signals.

# Rules (implemented in the script)
| Rule | Flag | Evidence required |
|---|---|---|
| R1 | Acceptance criteria missing or untestable | The criteria text (or "none present") |
| R2 | Ticket exceeds size threshold; a Refinement discussion point, not a directive to split | Points and the threshold |
| R3 | Unestimated | Ticket id |
| R4 | Open dependency | Blocking ticket id and status |

- The size threshold is the P85 of the team's completed ticket sizes (needs 10 or more tickets). With less history no size flag is raised and the ledger says why.
- Cite Scrum Guide grounding only for definitions (e.g. Definition of Done, Product Backlog refinement) via the grounding index, using the section id.
- Flags are predictions of risk, not verdicts; the brief says "high probability of blocker" only when a rule fired, and always frames it as something to raise in Refinement, not a decision already made.

# Ledger keys
`readiness.size_threshold`, `readiness.<ticket>.<rule>`.

# Output
`readiness_out.json`. Rubric: `skills/qa/rubrics/readiness.yaml`.
