---
name: mcp-connector
description: Pulls and normalizes work-tracking data from Jira, ClickUp, calendar and Slack MCP servers into normalized.json. Use at the start of any workflow that needs sprint, ticket, PTO or history data.
---

# Single task
Fetch the minimum data needed and emit `runs/<id>/normalized.json`. No analysis.

# Inputs
Human scope (board or list, sprint, date range), MCP servers from `mcp/config.json`.

# Procedure
1. Request only needed fields (field projection) and page through all results.
2. Independently query the expected ticket count (e.g. JQL total) and store it as `meta.total_expected`.
3. Map to the schema below. Raw payloads never leave this agent.
4. Null story points: keep null and add `"flags": ["unestimated"]`.
5. Record `meta.source`, `meta.jql_hash` (hash of the query text), `meta.fetched_at`.
6. Run `python scripts/qa/validate_normalized.py runs/<id>/normalized.json` and fix schema errors before handing to QA.

# Schema (all sections optional except meta, sprint, members, candidates)
```json
{
  "meta": {"source": "jira", "jql_hash": "", "fetched_at": "ISO", "total_expected": 18},
  "sprint": {"name": "", "start": "YYYY-MM-DD", "working_days": 10, "focus_hours_per_day": 8, "ceremony_buffer_pct": 0.15},
  "members": [{"ref": "dev1", "allocation": 1.0, "pto_days": 0, "pto_source": "calendar:<event id>"}],
  "history": [{"sprint": 11, "completed_points": 0, "net_hours": 0}],
  "candidates": [{"id": "", "title": "", "points": 0, "acceptance_criteria": [], "blocked_by": [{"id": "", "status": ""}], "status": "", "flags": []}],
  "ticket_points_history": [1, 2, 3],
  "sprints": [{"sprint": 11, "committed_points": 0, "completed_points": 0}],
  "tickets": [{"id": "", "sprint": 11, "history": [{"status": "", "ts": "ISO"}]}],
  "wait_states": ["Waiting for API mockup", "In Review"]
}
```

# Tracker mapping hints
| Field | Jira | ClickUp | Calendar |
|---|---|---|---|
| Points | story points custom field | points field | n/a |
| Status history | issue changelog | time-in-status | n/a |
| PTO | n/a | n/a | out-of-office or leave events, one `pto_source` per event |
| Team member reference | opaque id, not display name | opaque id | opaque id |

# Rules
- Use opaque member refs, not names. Do not copy personal details.
- Read-only credentials only.
- Never estimate missing data; flag it.

# Output
`normalized.json`. Rubric: `skills/qa/rubrics/mcp-connector.yaml`.
