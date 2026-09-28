#!/usr/bin/env python3
"""Chunk the Scrum Guide by heading and retrieve sections, so agents never load the full guide.
Usage: build_grounding_index.py build | get "<topic>"
Place the Scrum Guide 2020 markdown at grounding/scrum-guide-2020/source.md (CC BY-SA 4.0)."""
import collections
import json
import pathlib
import re
import sys

G = pathlib.Path(__file__).resolve().parent.parent / "grounding" / "scrum-guide-2020"
STOP = {"which", "their", "there", "these", "those", "would", "should", "about", "other", "where", "while"}


def terms(text):
    words = [w for w in re.findall(r"[a-z]{5,}", text.lower()) if w not in STOP]
    return [w for w, _ in collections.Counter(words).most_common(15)]


def build():
    parts = re.split(r"(?m)^(#{1,3} .+)$", (G / "source.md").read_text())
    (G / "chunks").mkdir(exist_ok=True)
    idx = []
    for i in range(1, len(parts), 2):
        title, body = parts[i].lstrip("# ").strip(), parts[i + 1].strip()
        cid = f"SG-{len(idx) + 1:02d}"
        (G / "chunks" / f"{cid}.md").write_text(f"# {title}\n\n{body}\n")
        idx.append({"id": cid, "title": title, "keywords": terms(body), "chars": len(body)})
    (G / "index.json").write_text(json.dumps(idx, indent=1))
    print(f"indexed {len(idx)} chunks")


def get(query):
    q = set(re.findall(r"[a-z]+", query.lower()))
    idx = json.loads((G / "index.json").read_text())
    def score(c):
        return 5 * len(q & set(re.findall(r"[a-z]+", c["title"].lower()))) + len(q & set(c["keywords"]))
    best = max(idx, key=score)
    if score(best) == 0:
        sys.exit("no matching section")
    print(f"[{best['id']}] {best['title']}\n")
    print((G / "chunks" / f"{best['id']}.md").read_text())


if __name__ == "__main__":
    build() if sys.argv[1] == "build" else get(" ".join(sys.argv[2:]))
