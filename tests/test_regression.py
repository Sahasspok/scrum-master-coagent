import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))
sys.path.insert(0, str(ROOT / "scripts"))
import ledger  # noqa: E402
import make_fixtures  # noqa: E402


@pytest.fixture(scope="module")
def fix(tmp_path_factory):
    p = tmp_path_factory.mktemp("fx") / "sprint14.json"
    p.write_text(json.dumps(make_fixtures.build()))
    return p


def sh(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def tool(fix, name):
    r = sh(ROOT / "scripts" / f"{name}.py", fix)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads(r.stdout)


def test_capacity(fix):
    o = tool(fix, "capacity")
    assert o["predicted_points"] == 34
    assert o["candidate_points"] == 48
    assert o["over_commit_pct"] == 41.2
    assert o["scope_cut_pct"] == 29.2
    assert o["confidence"] == "high"
    assert any(x["type"] == "pto" and x["hours"] == 24 for x in o["deductions"])


def test_readiness(fix):
    o = tool(fix, "readiness")
    assert {(f["ticket"], f["rule"]) for f in o["flags"]} == {("104", "R1"), ("112", "R2")}
    assert o["size_threshold"] == 8


def test_flow(fix):
    o = tool(fix, "flow")
    assert round(o["mean_completion_pct"]) == 84
    top = o["bottlenecks"][0]
    assert top["state"] == "Waiting for API mockup" and top["mean_h"] == 22.0 and top["n"] == 12
    assert "assignee" not in json.dumps(o)


def test_flow_needs_three_sprints(fix, tmp_path):
    d = json.loads(fix.read_text())
    d["sprints"] = d["sprints"][:2]
    p = tmp_path / "short.json"
    p.write_text(json.dumps(d))
    assert sh(ROOT / "scripts" / "flow.py", p).returncode == 2


def test_qa_scripts_pass(fix, tmp_path):
    for name, qa in (("capacity", "recompute_capacity"), ("flow", "check_flow")):
        out = tmp_path / f"{name}.json"
        out.write_text(json.dumps(tool(fix, name)))
        r = sh(ROOT / "scripts" / "qa" / f"{qa}.py", fix, out)
        assert r.returncode == 0, r.stdout
    assert sh(ROOT / "scripts" / "qa" / "validate_normalized.py", fix, 18).returncode == 0


def test_qa_catches_tampering(fix, tmp_path):
    o = tool(fix, "capacity")
    o["predicted_points"] = 40
    out = tmp_path / "bad.json"
    out.write_text(json.dumps(o))
    assert sh(ROOT / "scripts" / "qa" / "recompute_capacity.py", fix, out).returncode == 1


def test_verify_brief(fix, tmp_path):
    lp = tmp_path / "ledger.jsonl"
    ids = {r["key"]: r["id"] for r in ledger.append(tool(fix, "capacity")["ledger_rows"], lp)}
    cid = ids["capacity.points"]
    good, bad = tmp_path / "good.md", tmp_path / "bad.md"
    good.write_text(
        "# Brief\n"
        f"## Answer\nYes, commit to 34 SP [{cid}].\n"
        f"## Data supporting this\n| ID | Fact |\n|---|---|\n| [{cid}] | 34 SP |\n"
        f"## Recommendation\nCommit to 34 SP [{cid}].\n"
        f"**Insight:** the buffer is the binding constraint this sprint [{cid}].\n"
        f"**What I'd look into next:** whether the rate holds next sprint too [{cid}].\n"
        "## Questions to keep moving\n1. Confirm the commitment and I'll notify the team now.\n"
        "---\n**Provenance:** fixture | QA: capacity-forecast PASS (1)\n"
    )
    bad.write_text(
        "# Brief\n## Recommendation\nCommit to 34 SP.\n"
        "## Questions to keep moving\n1. What should we do?\n"
    )
    v = ROOT / "scripts" / "qa" / "verify_brief.py"
    assert sh(v, good, lp).returncode == 0, sh(v, good, lp).stdout
    assert sh(v, bad, lp).returncode == 1


def test_cache_runner(fix):
    r = sh(ROOT / "scripts" / "run.py", "capacity", fix)
    assert r.returncode == 0 and json.loads(r.stdout)["predicted_points"] == 34


def test_meta_qa_calibration(tmp_path):
    runs = tmp_path / "runs"
    # Three closed runs: capacity predicted vs actual, one readiness false positive.
    cases = [(34, 33, True, False), (30, 32, True, True), (28, 28, False, True)]
    for i, (pred, actual, t104_blocked, t112_blocked) in enumerate(cases, 1):
        d = runs / f"run{i}"
        d.mkdir(parents=True)
        (d / "capacity_out.json").write_text(json.dumps({"predicted_points": pred}))
        (d / "readiness_out.json").write_text(json.dumps({"flags": [{"ticket": "104"}, {"ticket": "112"}]}))
        (d / "actuals.json").write_text(json.dumps({
            "run": f"run{i}", "closed_at": "2026-10-01T00:00:00",
            "capacity": {"actual_completed_points": actual},
            "readiness": [{"ticket": "104", "did_block": t104_blocked},
                          {"ticket": "112", "did_block": t112_blocked}],
            "flow": {"bottleneck_confirmed_next_sprint": True},
        }))

    calib = json.loads(sh(ROOT / "scripts" / "qa" / "audit_calibration.py", runs).stdout)
    assert calib["closed_runs"] == 3
    assert calib["capacity"]["n"] == 3
    # (1/34 + 2/30 + 0/28) / 3 * 100
    assert calib["capacity"]["mean_abs_pct_error"] == pytest.approx(3.2, abs=0.2)
    assert calib["readiness"]["flagged_and_checked"] == 6
    assert calib["readiness"]["true_positives"] == 4
    assert calib["readiness"]["false_positives"] == 2
    assert calib["readiness"]["precision_pct"] == pytest.approx(66.7, abs=0.1)
    assert calib["flow"]["confirmation_rate_pct"] == 100.0

    good = tmp_path / "meta_qa_out.json"
    good.write_text(json.dumps({"tool": "meta_qa", "closed_runs": 3, "calibration": calib,
                                 "bands": {"capacity": "within band", "readiness": "drifting",
                                          "flow": "within band"}}))
    v = ROOT / "scripts" / "qa" / "verify_calibration.py"
    assert sh(v, runs, good).returncode == 0, sh(v, runs, good).stdout

    tampered = tmp_path / "tampered.json"
    bad_calib = dict(calib, capacity={**calib["capacity"], "mean_abs_pct_error": 1.0})
    tampered.write_text(json.dumps({"closed_runs": 3, "calibration": bad_calib,
                                    "bands": {"capacity": "within band", "readiness": "drifting",
                                             "flow": "within band"}}))
    assert sh(v, runs, tampered).returncode == 1

    scorecard = tmp_path / "scorecard.yaml"
    scorecard.write_text(
        "capacity_mape_max_pct: 15\nreadiness_precision_min_pct: 70\n"
        "flow_confirmation_min_pct: 60\nqa_agreement_min_pct: 90\n"
        "research_integrity_min_pct: 100\nmin_closed_runs_for_trend: 3\n"
    )
    b = ROOT / "scripts" / "qa" / "check_band.py"
    assert sh(b, good, scorecard).returncode == 0, sh(b, good, scorecard).stdout

    mislabeled = tmp_path / "mislabeled.json"
    mislabeled.write_text(json.dumps({"closed_runs": 3, "calibration": calib,
                                      "bands": {"capacity": "within band", "readiness": "within band",
                                               "flow": "within band"}}))
    assert sh(b, mislabeled, scorecard).returncode == 1
