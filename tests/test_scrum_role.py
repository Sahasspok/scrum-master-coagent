"""Scrum Master role-fidelity tests: scenario router, accountability gate, approval allow-list."""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

MINI_GUIDE = """# The Scrum Guide

## Scrum Theory
Empiricism and lean thinking.

## The Scrum Team
One Scrum Master, one Product Owner, and Developers.

### Developers
Developers create the plan for the Sprint.

### Product Owner
The Product Owner is accountable for maximizing value and for the Product Backlog.

### Scrum Master
The Scrum Master is accountable for the Scrum Team's effectiveness and removes impediments.

## Scrum Events

### The Sprint
Nothing is done that would endanger the Sprint Goal.

### Sprint Planning
Developers select items and plan the work for the Sprint.

### Daily Scrum
A 15-minute event for the Developers.

### Sprint Review
A working session with stakeholders.

### Sprint Retrospective
The Scrum Team plans ways to increase quality and effectiveness.

## Scrum Artifacts

### Product Backlog
An ordered list of what is needed to improve the product.

### Sprint Backlog
The Sprint Goal, the selected items, and the plan.

### Increment
A concrete step toward the Product Goal.

### Commitment: Definition of Done
A formal description of the state of the Increment.
"""


def sh(*args, env=None):
    e = {**os.environ, **(env or {})}
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, env=e)


def grounded(tmp_path):
    """Build a tiny Scrum Guide index plus the real playbook under a temp grounding root."""
    g = tmp_path / "grounding"
    (g / "scrum-guide-2020").mkdir(parents=True)
    (g / "scrum-guide-2020" / "source.md").write_text(MINI_GUIDE)
    (g / "playbook.yaml").write_text((ROOT / "grounding" / "playbook.yaml").read_text())
    env = {"GROUNDING_ROOT": str(g)}
    assert sh(ROOT / "scripts" / "build_grounding_index.py", "build", env=env).returncode == 0
    return env


def match(req, env):
    return sh(ROOT / "scripts" / "scenario_match.py", req, env=env)


def test_commitment_question_routes_to_developers(tmp_path):
    env = grounded(tmp_path)
    r = match("Can we commit to these tickets for Sprint 15?", env)
    assert r.returncode == 0, r.stdout + r.stderr
    o = json.loads(r.stdout)
    assert o["scenario"]["id"] == "S01" and o["scenario"]["owner"] == "Developers"
    assert {c["title"] for c in o["guide_chunks"]} >= {"Sprint Planning", "Sprint Backlog", "Developers"}
    keys = {row["key"] for row in o["ledger_rows"]}
    assert "scenario.match" in keys and any(k.startswith("guide.SG-") for k in keys)
    assert set(o["data_tools"]) == {"capacity", "readiness"}


def test_assignment_and_individual_requests_route_away_from_pm_work(tmp_path):
    env = grounded(tmp_path)
    assert json.loads(match("Assign #104 to dev2 please", env).stdout)["scenario"]["id"] == "S10"
    o = json.loads(match("Who is the slowest developer on the team?", env).stdout)
    assert o["scenario"]["id"] == "S09" and o["data_tools"] == []


def test_dates_go_to_forecasting_and_per_person_questions_go_to_team_level(tmp_path):
    env = grounded(tmp_path)
    assert json.loads(match("When will feature X ship? My manager wants a date", env).stdout)["scenario"]["id"] == "S12"
    assert json.loads(match("Who is blocked the most?", env).stdout)["scenario"]["id"] == "S09"
    assert json.loads(match("A stakeholder wants me to add a feature mid-sprint", env).stdout)["scenario"]["id"] == "S05"


def test_impediment_is_the_scrum_masters_own_remit(tmp_path):
    env = grounded(tmp_path)
    o = json.loads(match("We keep getting blocked, what is the bottleneck?", env).stdout)
    assert o["scenario"]["id"] == "S04" and o["scenario"]["owner"] == "Scrum Master"


def test_every_playbook_move_uses_the_scrum_master_vocabulary():
    import yaml
    allowed = {"Facilitate", "Coach", "Teach", "Make transparent", "Remove impediment", "Shield", "Ask", "Escalate"}
    pb = yaml.safe_load((ROOT / "grounding" / "playbook.yaml").read_text())
    for s in pb["scenarios"]:
        assert s["owner"] in {"Developers", "Product Owner", "Scrum Team", "Scrum Master"}, s["id"]
        assert len(s["sm_moves"]) >= 2, s["id"]
        assert s["pm_traps"], s["id"]
        for m in s["sm_moves"]:
            assert m["verb"] in allowed, (s["id"], m["verb"])


def test_no_grounding_stops_the_run(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "playbook.yaml").write_text((ROOT / "grounding" / "playbook.yaml").read_text())
    r = match("Can we commit to these tickets?", {"GROUNDING_ROOT": str(empty)})
    assert r.returncode == 3


def test_unmatched_request_falls_back_or_asks(tmp_path):
    env = grounded(tmp_path)
    o = json.loads(match("Is the Increment always shippable?", env).stdout)
    assert o["scenario"]["id"] in {"S11", "S00"}
    assert match("zzzz qqqq", env).returncode == 2


GOOD = """# Sprint 15 planning
**Prepared for:** SM | **Data as of:** 2026-10-01 | **Scrum situation:** S01

## Answer
That is the Developers' forecast to make; the capacity signal is 34 SP [E-001].

## Data supporting this
| ID | Fact |
|---|---|
| [E-001] | 34 SP |

## Recommendation
**Whose call:** Developers. The Sprint Backlog is theirs to forecast.
**What Scrum says:** Developers select the items and plan the work for the Sprint [E-002] (SG-08).
**Scrum Master moves:**
1. **Make transparent** in Sprint Planning: show the 34 SP signal and the size of the candidate set [E-001].
2. **Coach** the Developers to treat the forecast as a hypothesis they inspect daily.
3. **Do nothing:** the Developers plan without the signal.
**Decision for you:** choose move 1 or move 2; I recommend move 1 because the signal is high confidence [E-001].
**Insight:** the buffer is the binding constraint this sprint [E-001].
**What I'd look into next:** whether the rate holds next sprint too [E-001].
**Questions to put to the team:** Which items best serve a Sprint Goal?

## Questions to keep moving
1. Confirm move 1 and I'll draft the Sprint Planning agenda with the capacity slide.
---
**Provenance:** fixture
"""

BAD = """# Sprint 15 planning

## Answer
Commit to 34 SP and split #112 first.

## Recommendation
**What Scrum says:** Commit to 34 SP.
**Scrum Master moves:**
1. Assign #104 to dev2.
2. Reorder the backlog so #112 is on top.

## Questions to keep moving
1. Confirm and I'll draft the sub-tickets and I'll assign #104.
"""


def gate(tmp_path, body, name="brief.md"):
    p = tmp_path / name
    p.write_text(body)
    return sh(ROOT / "scripts" / "qa" / "check_accountability.py", p)


def test_accountability_passes_a_facilitation_brief(tmp_path):
    r = gate(tmp_path, GOOD)
    assert r.returncode == 0, r.stdout


def test_accountability_rejects_a_project_manager_brief(tmp_path):
    r = gate(tmp_path, BAD)
    assert r.returncode == 1
    out = json.loads(r.stdout)["defects"]
    joined = " | ".join(out)
    for expected in ("missing **Whose call:**", "SG-nn", "Scrum Master verb", "Decision for you",
                     "states a Sprint commitment", "directs a ticket split", "assigns work",
                     "changes backlog or Sprint scope", "offers to do another role's work"):
        assert expected in joined, expected


def test_accountability_allows_naming_the_owners_call(tmp_path):
    body = GOOD.replace("Coach** the Developers to treat", "Coach** the Developers (commit to 34 SP is their call) to treat")
    assert gate(tmp_path, body).returncode == 0


def test_non_sm_owner_requires_questions_for_the_team(tmp_path):
    body = GOOD.replace("**Questions to put to the team:** Which items best serve a Sprint Goal?\n", "")
    r = gate(tmp_path, body)
    assert r.returncode == 1 and "Questions to put to the team" in r.stdout


def approval(tmp_path, actions, expires="2999-01-01T00:00:00Z", extra=None):
    p = tmp_path / "approval.json"
    p.write_text(json.dumps({"run": "r1", "approved_by": "human", "approved_at": "2026-10-01T00:00:00Z",
                             "expires_at": expires, "actions": actions, **(extra or {})}))
    return sh(ROOT / "scripts" / "qa" / "check_approval.py", p)


def test_approval_allows_facilitation_actions(tmp_path):
    ok = approval(tmp_path, [
        {"id": "A1", "tool": "jira", "op": "log_impediment", "target": "IMP", "payload": {"summary": "API mockup wait"}},
        {"id": "A2", "tool": "slack", "op": "post_message", "target": "#team", "payload": {"text": "Retro agenda"}}])
    assert ok.returncode == 0, ok.stdout


def test_approval_blocks_backlog_and_assignment_writes(tmp_path):
    r = approval(tmp_path, [
        {"id": "A1", "tool": "jira", "op": "create_subtasks", "target": "112", "payload": {}},
        {"id": "A2", "tool": "jira", "op": "comment", "target": "104", "payload": {"assignee": "dev2"}}])
    assert r.returncode == 1
    assert "outside the Scrum Master facilitation allow-list" in r.stdout and "payload field" in r.stdout


def test_approval_expiry_and_second_approval(tmp_path):
    a = [{"id": f"A{i}", "tool": "slack", "op": "post_message", "target": "#t", "payload": {}} for i in range(11)]
    assert approval(tmp_path, a).returncode == 1
    assert approval(tmp_path, a, extra={"second_approval": True}).returncode == 0
    assert approval(tmp_path, a[:1], expires="2020-01-01T00:00:00Z").returncode == 1


def test_composer_example_passes_both_gates(tmp_path):
    """The worked example in the composer skill must satisfy the same gates it teaches."""
    import re
    sys.path.insert(0, str(ROOT / "scripts"))
    import ledger
    skill = (ROOT / "skills" / "composer" / "SKILL.md").read_text()
    example = re.search(r"# Example \(illustrative ids\)\n```\n(.*?)\n```", skill, re.S).group(1)
    brief = tmp_path / "example.md"
    brief.write_text(example + "\n")
    lp = tmp_path / "ledger.jsonl"
    ledger.append([ledger.make_row(f"k{n}", f"claim {n}", "script", f"s{n}", "test", "high") for n in range(1, 19)], lp)
    v = sh(ROOT / "scripts" / "qa" / "verify_brief.py", brief, lp)
    assert v.returncode == 0, v.stdout
    a = sh(ROOT / "scripts" / "qa" / "check_accountability.py", brief)
    assert a.returncode == 0, a.stdout


def test_playbook_and_brief_template_agree_on_vocabulary():
    """Template must offer the same verbs the gate enforces."""
    tpl = (ROOT / "skills" / "composer" / "templates" / "scrum-brief.md").read_text()
    for verb in ("Facilitate", "Coach", "Teach", "Make transparent", "Remove impediment", "Shield", "Ask", "Escalate"):
        assert verb in tpl, verb
    for label in ("Whose call", "What Scrum says", "Scrum Master moves", "Decision for you", "Questions to put to the team"):
        assert f"**{label}:**" in tpl, label


def test_accountability_blocks_drafting_ac_or_organizing_backlog_and_allows_po_memos(tmp_path):
    bad_ac = GOOD.replace("Confirm move 1 and I'll draft the Sprint Planning agenda with the capacity slide.",
                          "Confirm move 1 and I'll draft the acceptance criteria for candidate tickets.")
    assert gate(tmp_path, bad_ac).returncode == 1

    bad_org = GOOD.replace("Confirm move 1 and I'll draft the Sprint Planning agenda with the capacity slide.",
                           "Confirm move 1 and I'll organize the backlog priorities for the sprint.")
    assert gate(tmp_path, bad_org).returncode == 1

    good_po_memo = GOOD.replace("Confirm move 1 and I'll draft the Sprint Planning agenda with the capacity slide.",
                                "Confirm move 1 and I'll draft the email to the Product Owner requesting backlog prioritization.")
    assert gate(tmp_path, good_po_memo).returncode == 0
