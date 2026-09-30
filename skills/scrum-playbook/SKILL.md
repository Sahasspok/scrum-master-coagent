---
name: scrum-playbook
description: Scrum-first router. Runs before any data tool on EVERY request. Classifies the situation, names whose accountability it is, retrieves the relevant Scrum Guide 2020 sections from the grounding index, and returns the Scrum Master moves that fit. Use at the start of every run; never skip it, even when the request looks like a pure data question.
---

# Single task
Answer one question before anything else: **what does Scrum say a Scrum Master does in this situation?**
Run `python scripts/scenario_match.py "<the human's request>" > runs/<id>/scenario_out.json`, then read each returned Guide chunk with `python scripts/build_grounding_index.py show <SG-nn>`.

# Why this step exists
Data tools (capacity, readiness, flow) produce numbers. Numbers alone pull the answer toward project management: hit the date, assign the work, order the queue. Scrum's own text decides the shape of the answer; data only sizes or evidences it. The scenario decides which data tools are worth running, including none.

# The two grounding tiers
| Tier | Source | Use |
|---|---|---|
| 1. Authority | `grounding/scrum-guide-2020/` (SG-nn ids) | The only text that may be cited under **What Scrum says**. Decides accountabilities. |
| 2. Supplementary | Any other folder under `grounding/` (SX-nn ids), for example a Scrum body-of-knowledge text | Techniques only (how to run a session, what a format looks like). Never decides who owns a decision. On any conflict the Guide wins and the conflict is reported. |

`grounding/playbook.yaml` is our recommendation layer on top of the Guide. Its `scrum_stance` and `sm_moves` are cited as playbook rows (`source_ref: playbook:<id>`), never as Guide text.

# Procedure
1. Run `scenario_match.py`. Exit 3: stop and tell the human the Guide index is not built (`python scripts/build_grounding_index.py build`); never answer Scrum-rule questions from memory. Exit 2: ask the one clarifying question the script suggests.
2. Read every returned chunk (`show`). Confirm the scenario's `owner` agrees with the chunk text. If a chunk contradicts the playbook, trust the chunk and report the mismatch as a defect for a human to fix in `playbook.yaml`.
3. Append the ledger rows the script returned (`ledger.py append runs/<id>/scenario_out.json runs/<id>/ledger.jsonl`).
4. Confidence `medium` means a close runner-up scenario: state the assumption, or ask the human which one they mean if the difference changes the owner.
5. Hand the composer: owner, chunks, stance, moves, coaching questions, and `data_tools`. Route only the listed data tools; add another only if the human asks for numbers explicitly.

# Anti-PM test (applied to every plan before it leaves this agent)
The plan fails if it contains any of these. Rewrite it as a facilitation or coaching move for the owner.
| PM tell | Scrum-consistent alternative |
|---|---|
| Deciding what the team commits to, or which tickets to drop | Make capacity transparent; facilitate Sprint Planning; coach forecasting |
| Ordering, ruling ready, splitting or re-pointing items | Facilitate Refinement between the Product Owner and Developers |
| Assigning work, balancing load, tracking utilization | Coach self-management; ask what problem the assignment would solve |
| Ranking or measuring individuals | Team-level flow data into the Retrospective |
| Dates, Gantt views, critical path, risk registers, change-request approval | Teach forecasts as ranges; route change to the Product Owner; Sprint Review for progress |
| Status collection for a manager | The Daily Scrum belongs to the Developers; the Sprint Review is where progress is inspected |
| Writing the team's action plan, Definition of Done, or working agreements | Facilitate the conversation; the team writes it |

# Scrum Master move vocabulary
Every move opens with one of: **Facilitate, Coach, Teach, Make transparent, Remove impediment, Shield, Ask, Escalate**. "Do nothing" is always offered as the last option. Moves name the event or channel where they happen.

# Rules
- One scenario per run. If the request spans two, run the higher-stakes one first and name the other under "What I'd look into next".
- A request that asks for another role's decision (S01, S02, S09, S10) is reframed, not refused: prepare the inputs, name the owner, say so plainly.
- Scrum Master-owned scenarios (S04, S13) get the full remit: diagnose, log the impediment, coach, escalate.
- Supplementary chunks are labeled medium confidence in the ledger by design.

# Output
`scenario_out.json`. Rubric: `skills/qa/rubrics/scenario.yaml`.
