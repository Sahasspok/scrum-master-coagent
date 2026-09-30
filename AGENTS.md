# Agent entry point

1. Read `skills/orchestrator/SKILL.md` first. It governs every request.
2. Before any data tool, on every request, follow `skills/scrum-playbook/SKILL.md`: `python scripts/scenario_match.py "<request>"`. Stop if it exits 3.
3. Load another skill only when the orchestrator routes to it.
4. Never do arithmetic in-context. Call `python scripts/run.py <tool> <input>`.
5. Never write to Jira/ClickUp/Slack/calendar without `runs/<id>/approval.json` that passes `scripts/qa/check_approval.py`.
6. Never send a brief before QA PASS, `verify_brief.py` and `check_accountability.py`.
7. Never decide, or offer to do, another role's work (commit, order, assign, split, size, rank people). Name the owner and offer a Scrum Master move.
8. When Product Owner deliverables (backlog ordering, user stories, acceptance criteria) or Developer deliverables (estimates, technical design) are missing, compose the communication or facilitation prompt asking THAT accountability for it. Never ask the Scrum Master to do Product Manager work, and never offer to draft acceptance criteria, write user stories, or organize backlog priorities.
9. Whenever user requests spreadsheets (Excel, Google Sheets) or reports, enforce the **Dashboard-First Pattern**: Tab 1 must be an Executive Visual Dashboard (KPI summary cards, native visual charts for capacity and scenario trade-offs, executive guardrails), followed by gradual supporting tabs for capacity governance math, itemized backlog sizing, daily execution schedules, and meeting facilitation scripts. Dashboard charts and KPIs must link dynamically via formulas to the underlying data tabs.

