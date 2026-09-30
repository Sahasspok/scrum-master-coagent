---
name: context
description: Absorbs context the human supplies (e.g. "the backend lead was out during the API refactor"), labels it as human_context, applies it as an overlay and triggers re-runs of affected metrics only. Use for W3.
---

# Single task
Turn a human note into a structured overlay; never alter raw system data, and never let a note be used to decide a Developers' or Product Owner's matter on their behalf — it only adjusts the data those conversations will use.

# Overlay types
| Type | Effect | Affected tool |
|---|---|---|
| `availability_change` | Adjusts `pto_days` or allocation in `normalized.adjusted.json` | capacity |
| `exclude_window` | Flags a date range or sprint as anomalous; `flow` reports raw and adjusted | flow |
| `annotate` | Note shown in the reply only | composer |

# Procedure
1. Parse the note into `{type, scope, effect, dates, affected_tools, note_as_given}`.
2. If scope is ambiguous, ask one question. Otherwise proceed and state the interpretation.
3. Copy `normalized.json` to `normalized.adjusted.json`, apply the overlay; keep the raw file untouched.
4. Append a ledger row: `source_type: human_context`, `confidence: medium`, reason "supplied by human, not system-verified".
5. Re-run only `affected_tools` via `run.py` (cache handles the rest). Both raw and adjusted values go to the composer.

# Privacy
Record the minimum: "reduced availability (unplanned absence)". Do not store medical or personal reasons even if the human gave them.

# Output
`context_overlay.json`, `normalized.adjusted.json`. Rubric: `skills/qa/rubrics/context.yaml`.
