#!/usr/bin/env python3
"""run.py - cached tool runner. Usage: run.py <capacity|readiness|flow> <normalized.json>
Cache key = sha256(script bytes + input bytes). Unchanged data means no recompute."""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CACHE = ROOT.parent / ".cache"
TOOLS = {"capacity": "capacity.py", "readiness": "readiness.py", "flow": "flow.py"}

if __name__ == "__main__":
    tool, path = sys.argv[1], pathlib.Path(sys.argv[2])
    script = ROOT / TOOLS[tool]
    key = hashlib.sha256(script.read_bytes() + path.read_bytes()).hexdigest()[:16]
    CACHE.mkdir(exist_ok=True)
    out = CACHE / f"{tool}-{key}.json"
    hit = out.exists()
    if not hit:
        r = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True)
        if r.returncode:
            sys.stderr.write(r.stdout + r.stderr)
            sys.exit(r.returncode)
        out.write_text(r.stdout)
    sys.stderr.write(f"cache {'hit' if hit else 'miss'}: {out.name}\n")
    print(out.read_text())
