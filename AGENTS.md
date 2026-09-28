# Agent entry point

1. Read `skills/orchestrator/SKILL.md` first. It governs every request.
2. Load another skill only when the orchestrator routes to it.
3. Never do arithmetic in-context. Call `python scripts/run.py <tool> <input>`.
4. Never write to Jira/ClickUp/Slack without `runs/<id>/approval.json`.
5. Never send a brief to the human before QA PASS.
