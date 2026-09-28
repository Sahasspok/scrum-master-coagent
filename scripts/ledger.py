#!/usr/bin/env python3
"""ledger.py v1.0.0 - evidence ledger helpers.
CLI: ledger.py append <tool_output.json> <ledger.jsonl>   -> prints appended rows
     ledger.py show <ledger.jsonl>                        -> compact listing"""
import hashlib
import json
import pathlib
import sys

SOURCE_TYPES = {"mcp", "script", "grounding", "peer_reviewed", "human_context"}
CONFIDENCE = {"high", "medium", "low"}
REQUIRED = ("key", "claim", "source_type", "source_ref", "method", "confidence")


def make_row(key, claim, source_type, source_ref, method, confidence, reason="", value=None):
    row = {"key": key, "claim": claim, "value": value, "source_type": source_type,
           "source_ref": source_ref, "method": method,
           "confidence": confidence, "confidence_reason": reason}
    validate(row)
    return row


def validate(row):
    missing = [k for k in REQUIRED if row.get(k) in (None, "")]
    if missing:
        raise ValueError(f"ledger row {row.get('key')} missing {missing}")
    if row["source_type"] not in SOURCE_TYPES:
        raise ValueError(f"bad source_type {row['source_type']}")
    if row["confidence"] not in CONFIDENCE:
        raise ValueError(f"bad confidence {row['confidence']}")
    if row["confidence"] != "high" and not row.get("confidence_reason"):
        raise ValueError(f"{row['key']}: non-high confidence needs a reason")


def load(path):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def append(rows, path):
    existing = load(path)
    latest = {r["key"]: r for r in existing}
    n = len(existing)
    out = []
    with open(path, "a") as f:
        for r in rows:
            validate(r)
            h = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()[:12]
            prev = latest.get(r["key"])
            if prev and prev["hash"] == h:
                out.append(prev)
                continue
            n += 1
            row = {"id": f"E-{n:03d}", **r, "hash": h}
            f.write(json.dumps(row) + "\n")
            out.append(row)
            latest[r["key"]] = row
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "append":
        rows = json.load(open(sys.argv[2]))["ledger_rows"]
        print(json.dumps(append(rows, sys.argv[3]), indent=1))
    elif cmd == "show":
        for r in load(sys.argv[2]):
            print(f'{r["id"]} | {r["claim"]} | {r["source_type"]} | {r["confidence"]}')
    else:
        sys.exit("usage: ledger.py append|show ...")
