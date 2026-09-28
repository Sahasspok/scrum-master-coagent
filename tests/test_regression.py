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
    secs = "\n".join(f"## {s}\nText only." for s in
                     ["Options and trade-offs", "Evidence", "Context and assumptions", "Risks",
                      "Open questions for you", "Provenance"])
    good, bad = tmp_path / "good.md", tmp_path / "bad.md"
    good.write_text(f"# Brief\n## Recommendation\nCommit to 34 SP [{cid}].\n{secs}\n")
    bad.write_text(f"# Brief\n## Recommendation\nCommit to 34 SP.\n{secs}\n")
    v = ROOT / "scripts" / "qa" / "verify_brief.py"
    assert sh(v, good, lp).returncode == 0
    assert sh(v, bad, lp).returncode == 1


def test_cache_runner(fix):
    r = sh(ROOT / "scripts" / "run.py", "capacity", fix)
    assert r.returncode == 0 and json.loads(r.stdout)["predicted_points"] == 34
