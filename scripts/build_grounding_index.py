#!/usr/bin/env python3
"""build_grounding_index.py v2.0.0 - chunk a grounding source by heading and retrieve sections,
so agents never load a full document.
Usage: build_grounding_index.py build [folder [prefix]]    default: scrum-guide-2020 SG
       build_grounding_index.py get "<topic>" [folder]     keyword retrieval, best single chunk
       build_grounding_index.py show <chunk-id>            print one chunk by id (searches every folder)
Each folder holds source.md (Scrum Guide 2020 is CC BY-SA 4.0). Supplementary references
(e.g. a Scrum body-of-knowledge text) live in their own folder with their own prefix, for example:
  build_grounding_index.py build scrum-sbok SX
Env: GROUNDING_ROOT overrides the grounding directory (used by tests)."""
import collections
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(os.environ.get("GROUNDING_ROOT") or
                    pathlib.Path(__file__).resolve().parent.parent / "grounding")
DEFAULT = "scrum-guide-2020"
STOP = {"which", "their", "there", "these", "those", "would", "should", "about", "other", "where", "while"}


def terms(text):
    words = [w for w in re.findall(r"[a-z]{5,}", text.lower()) if w not in STOP]
    return [w for w, _ in collections.Counter(words).most_common(15)]


def build(folder=DEFAULT, prefix="SG"):
    g = ROOT / folder
    parts = re.split(r"(?m)^(#{1,3} .+)$", (g / "source.md").read_text())
    (g / "chunks").mkdir(exist_ok=True)
    idx = []
    for i in range(1, len(parts), 2):
        title, body = parts[i].lstrip("# ").strip(), parts[i + 1].strip()
        cid = f"{prefix}-{len(idx) + 1:02d}"
        (g / "chunks" / f"{cid}.md").write_text(f"# {title}\n\n{body}\n")
        idx.append({"id": cid, "title": title, "keywords": terms(body), "chars": len(body)})
    (g / "index.json").write_text(json.dumps(idx, indent=1))
    print(f"indexed {len(idx)} chunks in {folder}")


def get(query, folder=DEFAULT):
    g = ROOT / folder
    q = set(re.findall(r"[a-z]+", query.lower()))
    idx = json.loads((g / "index.json").read_text())

    def score(c):
        return 5 * len(q & set(re.findall(r"[a-z]+", c["title"].lower()))) + len(q & set(c["keywords"]))

    best = max(idx, key=score)
    if score(best) == 0:
        sys.exit("no matching section")
    print(f"[{best['id']}] {best['title']}\n")
    print((g / "chunks" / f"{best['id']}.md").read_text())


def show(cid):
    for p in sorted(ROOT.glob(f"*/chunks/{cid}.md")):
        print(p.read_text())
        return
    sys.exit(f"no such chunk: {cid}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(*sys.argv[2:4])
    elif cmd == "show":
        show(sys.argv[2])
    else:
        rest = sys.argv[2:]
        folder = DEFAULT
        if len(rest) > 1 and (ROOT / rest[-1] / "index.json").exists():
            folder = rest.pop()
        get(" ".join(rest), folder)
