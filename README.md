# Scrum Master Co-Agent

Open-source co-agent for a **Scrum Master** — not a project manager. It helps you facilitate Scrum well, coach the team, remove impediments, and protect the team from interference, grounded in the Scrum Guide (2020, scrumguides.org).

It is a **decision partner for the Scrum Master**: for every situation it looks up what Scrum says, names whose call the matter is, and offers a small set of Scrum Master moves (facilitate, coach, teach, make transparent, remove an impediment, shield, ask, escalate) with a recommendation. The Scrum Master decides among the moves; the decisions that belong to the Developers or the Product Owner go back to them through the Scrum Master's facilitation.

**What it is not:** it does not decide what the Developers commit to, does not order or reorder the Product Backlog, does not assign tasks, does not split or re-scope tickets, and does not evaluate individuals. Those are the Developers' and Product Owner's accountabilities. The co-agent prepares facts for those conversations and recommends what *you*, the Scrum Master, can do: facilitate an event, coach a practice, raise an impediment, or bring data to the people who own the decision.

## Architecture

```
HUMAN (Scrum Master)
   |  ask: decide / report / anything
   v
MASTER SKILL: orchestrator          routes, enforces evidence, enforces role boundaries
   |-- Scrum-first  : scrum-playbook (scenario_match.py + Scrum Guide grounding + playbook.yaml)   runs BEFORE any data tool
   |-- Data Layer   : MCP Connector (Jira / ClickUp / Calendar / Slack)
   |-- Work agents  : Sprint-Planning Signal | Refinement Signal | Flow & Impediment Analyst | Research | Context | Facilitation Actions
   |-- QA-Agent     : owns the benchmark, pass/fail authority, forces rework, checks role fidelity
   |-- Meta-QA      : audits closed runs against real outcomes; resamples QA's own calls
   '-- Composer     : reply that names whose call it is, cites the Guide, and offers Scrum Master moves plus one decision for you
```

Nothing reaches the human unless QA passed it, `verify_brief.py` passed the brief, and `check_accountability.py` confirms it names the owner, cites the Guide, uses Scrum Master moves only, and didn't decide someone else's call for them. Meta-QA is the check on QA itself: it never blocks a live run, only reports on closed ones.

## Accountability map (per the Scrum Guide's three accountabilities)

| Question | Whose call | This co-agent's role |
|---|---|---|
| What do we commit to this Sprint? | **Developers** | Prepare capacity data; facilitate Sprint Planning. Never state a commitment as decided. |
| What order is the Product Backlog in? Is an item ready? | **Product Owner** (with Developers in Refinement) | Prepare readiness signals; facilitate Refinement. Never reorder or rule an item ready/not ready. |
| How do the Developers do the work? | **Developers** | Not this co-agent's business at all. |
| Why do we keep getting blocked? Is Scrum being enacted well? | **Scrum Master** | Full remit — diagnose, raise as an impediment, coach, facilitate the Retrospective. |
| Is an external party interrupting the team? | **Scrum Master** | Full remit — shield the team, escalate. |

Every reply states which row applies before recommending anything (see the four-part contract below).

## Principles

| Principle | Mechanism |
|---|---|
| Scrum first | Every run starts by matching the request to a playbook scenario and retrieving the Scrum Guide sections it rests on (`scenario_match.py`). Data tools run only if the scenario needs them. Grounding missing means the run stops; the Guide is never answered from memory. |
| Scrum Master moves | Every recommendation is a numbered set of moves that open with Facilitate, Coach, Teach, Make transparent, Remove impediment, Shield, Ask or Escalate, plus Do nothing, and ends with a **Decision for you** between moves. |
| Role fidelity | Every recommendation states whose call it is (Developers / Product Owner / Scrum Master) and, when it isn't the Scrum Master's call, only facilitation language is allowed — never a decision made on their behalf. Checked by `check_accountability.py`. |
| Human decides | Even within the Scrum Master's own remit, agents recommend; writes to trackers need `approval.json`, validated by `check_approval.py` against a facilitation allow-list |
| Fact-supported | Evidence ledger: every number in a brief carries `[E-nnn]` |
| Deterministic math | `scripts/` compute; the LLM never does arithmetic |
| One agent, one task | Each agent has one SKILL.md and one output |
| QA owns quality | QA sets the benchmark before work, loops rework up to 3 times |
| External evidence | Research agent: peer-reviewed, DOI-verified only, scoped to Scrum/agile coaching and team-effectiveness literature |
| Systems, not people | No individual performance ranking anywhere |
| Forward-looking | Every reply ends with questions that name the next concrete facilitation action, to keep momentum |
| Dashboard first, data later | Whenever spreadsheets (Excel, Google Sheets) or reports are requested, Tab 1 is always an Executive Visual Dashboard (KPI cards, embedded visual charts, scenario comparisons). Gradual subsequent tabs supply the detailed mathematical proofs, backlog sizing, execution schedules, and facilitation scripts. |
| Self-auditing | Meta-QA compares closed-run predictions to real outcomes, resamples QA's judgment calls, and resamples past briefs for role overstep; findings are reported, never auto-applied to rubrics |


## Scope

In this repo (free): the Scrum-first playbook (13 scenarios covering the five events, the three accountabilities, impediments, interference, adoption and reporting), Sprint Planning support, Refinement support, Flow & Impediment diagnosis (feeding the Retrospective), Facilitation actions, plus orchestrator, QA, Meta-QA and composer.
Not in this repo, and not this agent's job under Scrum at all: assigning work to individuals, ranking backlog priority, splitting or re-scoping tickets, deciding Sprint commitment. Enterprise-scope features out of repo scope: cross-team dependency mapping, multi-squad coordination, Jira-to-CI/CD automation, executive risk governance.

## Quickstart

```
pip install -r requirements.txt
pytest -q
# place the Scrum Guide 2020 text (CC BY-SA 4.0) in grounding/scrum-guide-2020/source.md, then:
python scripts/build_grounding_index.py build
# optional supplementary reference (technique only, never overrides the Guide), e.g. a Scrum body-of-knowledge text:
#   place it in grounding/<folder>/source.md, then: python scripts/build_grounding_index.py build <folder> SX
cp mcp/config.example.json mcp/config.json     # credentials via environment variables only
```

Scrum-first step: `python scripts/scenario_match.py "Can we commit to these tickets?"`
Read a Guide section: `python scripts/build_grounding_index.py show SG-08`
Run a tool: `python scripts/run.py capacity runs/<id>/normalized.json`
Verify a brief: `python scripts/qa/verify_brief.py runs/<id>/brief.md runs/<id>/ledger.jsonl`
Check role fidelity: `python scripts/qa/check_accountability.py runs/<id>/brief.md`
Check an approval: `python scripts/qa/check_approval.py runs/<id>/approval.json`

## Run folder

```
runs/<yyyymmdd-hhmm>/
  scenario_out.json  normalized.json  normalized.adjusted.json (only if human context applied)
  contract-<agent>.json  <tool>_out.json  ledger.jsonl
  qa/verdicts.jsonl  brief.md  approval.json (only for facilitation actions)
```

## Token minimization

Script library instead of generated code; math in code; compact normalized JSON between agents; grounding retrieved by section; progressive skill loading; cache by content hash (`.cache/`); QA returns defect lists, not rewrites; context changes re-run only affected tools.
