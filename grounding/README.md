# Grounding

Two tiers, one playbook.

| Item | Path | Role |
|---|---|---|
| Tier 1: Scrum Guide 2020 | `scrum-guide-2020/source.md` (CC BY-SA 4.0; you supply it) | The authority. Only this text may be cited under **What Scrum says** (ids `SG-nn`). Decides accountabilities. |
| Tier 2: supplementary reference | `<folder>/source.md`, for example a Scrum body-of-knowledge text | Technique only: how to run a session, what a format looks like (ids `SX-nn`). Never decides who owns a decision. If it conflicts with the Guide, the Guide wins and the conflict is reported. |
| Playbook | `playbook.yaml` | Our recommendation layer: scenarios, owners, Guide anchors, Scrum Master moves, coaching questions, PM traps. Human-edited. Cited as `playbook:<id>`, never as Guide text. |

Why two tiers: general project-management-flavored references describe roles and controls (plans, dates, resource allocation, sign-offs) that Scrum does not give the Scrum Master. Used as authority they pull answers back toward project management. Used for technique only, they add facilitation detail without changing who decides.

Build:
```
python scripts/build_grounding_index.py build                      # Scrum Guide, ids SG-nn
python scripts/build_grounding_index.py build <folder> SX          # supplementary reference, ids SX-nn
python scripts/build_grounding_index.py show SG-08                 # print one chunk
```
Each `guide_anchors` entry in `playbook.yaml` is a Guide heading; `scenario_match.py` resolves it to a chunk id. If your Guide copy uses different heading text, adjust the anchors (a human edit).
