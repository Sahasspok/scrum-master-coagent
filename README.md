# Scrum Master Co-Agent

Open-source co-agent that helps a Scrum Master make sprint decisions with data. Grounded in the Scrum Guide (2020, scrumguides.org). It recommends; the human decides.

## Architecture

```
HUMAN (Scrum Master)
   |  ask: decide / report / anything
   v
MASTER SKILL: orchestrator          routes, enforces evidence, gates output
   |-- Data Layer   : MCP Connector (Jira / ClickUp / Calendar / Slack)
   |-- Work agents  : Capacity | Backlog Readiness | Flow Analyst | Research | Context | Executor
   |-- QA-Agent     : owns the benchmark, pass/fail authority, forces rework
   '-- Composer     : Decision Brief / Sprint Report (final, human-readable)
```

Nothing reaches the human unless QA passed it and `verify_brief.py` passed the brief.

## Principles

| Principle | Mechanism |
|---|---|
| Human decides | Agents recommend; writes to trackers need `approval.json` |
| Fact-supported | Evidence ledger: every number in a brief carries `[E-nnn]` |
| Deterministic math | `scripts/` compute; the LLM never does arithmetic |
| One agent, one task | Each agent has one SKILL.md and one output |
| QA owns quality | QA sets the benchmark before work, loops rework up to 3 times |
| External evidence | Research agent: peer-reviewed, DOI-verified only |
| Systems, not people | No individual performance ranking anywhere |

## Scope

In this repo (free): Sprint Capacity Forecasting, Team Performance Evaluation (flow), Backlog Readiness, plus orchestrator, QA and composer.
Not in this repo: cross-team dependency mapping, multi-squad coordination, Jira-to-CI/CD automation, executive risk governance.

## Quickstart

```
pip install -r requirements.txt
pytest -q
# place the Scrum Guide 2020 text (CC BY-SA 4.0) in grounding/scrum-guide-2020/source.md, then:
python scripts/build_grounding_index.py build
cp mcp/config.example.json mcp/config.json     # credentials via environment variables only
```

Run a tool: `python scripts/run.py capacity runs/<id>/normalized.json`
Verify a brief: `python scripts/qa/verify_brief.py runs/<id>/brief.md runs/<id>/ledger.jsonl`

## Run folder

```
runs/<yyyymmdd-hhmm>/
  normalized.json  normalized.adjusted.json (only if human context applied)
  contract-<agent>.json  <tool>_out.json  ledger.jsonl
  qa/verdicts.jsonl  brief.md  approval.json (only for writes)
```

## Token minimization

Script library instead of generated code; math in code; compact normalized JSON between agents; grounding retrieved by section; progressive skill loading; cache by content hash (`.cache/`); QA returns defect lists, not rewrites; context changes re-run only affected tools.
