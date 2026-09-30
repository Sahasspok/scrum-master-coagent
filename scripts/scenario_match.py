#!/usr/bin/env python3
"""scenario_match.py v1.0.0 - Scrum-first router. Runs BEFORE any data tool.
Usage: scenario_match.py "<request text>"
Maps the request to a scenario in grounding/playbook.yaml, resolves that scenario's Scrum Guide anchors to
grounding chunks (and optional supplementary chunks), and emits ledger rows.
Exit codes: 0 ok | 2 nothing matched at all | 3 grounding index missing or anchors unresolvable
(exit 3 means: stop and tell the human to build the index; never answer the Guide from memory).
Env: GROUNDING_ROOT overrides the grounding directory (used by tests)."""
import json
import os
import pathlib
import re
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger  # noqa: E402

G = pathlib.Path(os.environ.get("GROUNDING_ROOT") or HERE.parent / "grounding")
TIER1 = "scrum-guide-2020"
VERSION = "1.0.0"

DEFAULT_MOVES = [
    {"verb": "Ask", "where": "the requester",
     "move": "Ask which outcome the requester wants and which Scrum accountability it touches"},
    {"verb": "Coach", "where": "the Scrum Team",
     "move": "Coach the Scrum Team to bring the matter to the event where it belongs"},
]


def load_index(folder):
    p = G / folder / "index.json"
    return json.loads(p.read_text()) if p.exists() else None


def resolve(anchor, idx):
    a = anchor.lower()
    for c in idx:
        if c["title"].lower() == a:
            return c
    for c in idx:
        if a in c["title"].lower():
            return c
    return None


def chunk_ref(c, folder):
    return {"id": c["id"], "title": c["title"], "path": f"grounding/{folder}/chunks/{c['id']}.md"}


def score_scenarios(text, scenarios):
    scored = []
    for s in scenarios:
        pts = 0
        for t in s["triggers"]:
            if re.search(r"\b" + re.escape(t.lower()), text):
                pts += len(t.split())
        scored.append((pts, s["id"], s))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored


def keyword_fallback(text, idx, n=2):
    q = {w for w in re.findall(r"[a-z]{4,}", text)}

    def score(c):
        title_words = set(re.findall(r"[a-z]{4,}", c["title"].lower()))
        return 5 * len(q & title_words) + len(q & set(c["keywords"]))

    ranked = sorted(idx, key=score, reverse=True)
    return [c for c in ranked[:n] if score(c) > 0]


def main(request):
    text = request.lower()
    idx1 = load_index(TIER1)
    if idx1 is None:
        print(json.dumps({"tool": "scenario_match", "error": "grounding index missing",
                          "fix": "place the Scrum Guide 2020 in grounding/scrum-guide-2020/source.md "
                                 "and run: python scripts/build_grounding_index.py build"}))
        return 3

    pb = yaml.safe_load((G / "playbook.yaml").read_text())
    scored = score_scenarios(text, pb["scenarios"])
    top_pts, _, top = scored[0]
    second_pts = scored[1][0]

    supp_folders = sorted(d.name for d in G.iterdir()
                          if d.is_dir() and d.name != TIER1 and (d / "index.json").exists())
    supp_idx = {f: load_index(f) for f in supp_folders}

    if top_pts == 0:
        hits = keyword_fallback(text, idx1)
        if not hits:
            print(json.dumps({"tool": "scenario_match", "error": "no scenario and no Guide section matched",
                              "next": "ask the human one clarifying question"}))
            return 2
        scenario = {"id": "S00", "name": "Unclassified: Scrum Guide keyword retrieval",
                    "owner": "Scrum Team", "events": []}
        guide = [chunk_ref(c, TIER1) for c in hits]
        unresolved, supp = [], []
        moves, questions, traps, tools = DEFAULT_MOVES, [], [], []
        stance = ("No playbook scenario matched. Use the retrieved Guide sections and the accountability map; "
                  "keep every recommendation to facilitation and coaching.")
        conf, reason = "low", "no playbook scenario matched; Guide keyword retrieval only"
        alternatives = []
    else:
        scenario = {k: top[k] for k in ("id", "name", "owner", "events")}
        guide, unresolved = [], []
        for a in top["guide_anchors"]:
            c = resolve(a, idx1)
            (guide.append(chunk_ref(c, TIER1)) if c else unresolved.append(a))
        if not guide:
            print(json.dumps({"tool": "scenario_match", "error": "no Guide anchor resolved",
                              "scenario": top["id"], "anchors": top["guide_anchors"],
                              "fix": "rebuild the grounding index or check the Guide headings"}))
            return 3
        supp = []
        for topic in top.get("supplementary_topics", []):
            for f, idx in supp_idx.items():
                c = resolve(topic, idx) if idx else None
                if c:
                    supp.append(chunk_ref(c, f))
        moves, questions = top["sm_moves"], top["coaching_questions"]
        traps, tools, stance = top["pm_traps"], top["data_tools"], top["scrum_stance"].strip()
        alternatives = [{"id": s["id"], "name": s["name"], "owner": s["owner"], "points": p}
                        for p, _, s in scored[1:3] if p > 0 and p >= top_pts - 1]
        if second_pts and top_pts < 2 * second_pts:
            conf, reason = "medium", f"close runner-up scenario {scored[1][1]}; confirm with the human"
        else:
            conf, reason = "high", ""

    rows = [ledger.make_row(
        "scenario.match",
        f"Request matched playbook scenario {scenario['id']} ({scenario['name']}); owner: {scenario['owner']}",
        "grounding", f"playbook:{scenario['id']}@v{pb.get('version', 1)}",
        f"scenario_match.py@{VERSION}", conf, reason)]
    for c in guide:
        rows.append(ledger.make_row(
            f"guide.{c['id']}", f"Scrum Guide 2020 section '{c['title']}' retrieved as grounding",
            "grounding", c["id"], "build_grounding_index.py", "high"))
    for c in supp:
        rows.append(ledger.make_row(
            f"supplementary.{c['id']}",
            f"Supplementary reference section '{c['title']}' retrieved; the Scrum Guide prevails on conflict",
            "grounding", c["id"], "build_grounding_index.py", "medium",
            "supplementary source, not the Scrum Guide"))

    print(json.dumps({
        "tool": "scenario_match", "version": VERSION, "playbook_version": pb.get("version", 1),
        "scenario": scenario, "confidence": conf, "alternatives": alternatives,
        "guide_chunks": guide, "supplementary_chunks": supp, "unresolved_anchors": unresolved,
        "scrum_stance": stance, "sm_moves": moves, "coaching_questions": questions,
        "pm_traps": traps, "data_tools": tools, "ledger_rows": rows}, indent=1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: scenario_match.py \"<request text>\"")
    sys.exit(main(" ".join(sys.argv[1:])))
