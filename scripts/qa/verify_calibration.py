#!/usr/bin/env python3
"""verify_calibration.py v1.0.0 - QA check: recompute calibration independently and diff
against meta-qa's reported numbers. Usage: verify_calibration.py <runs_dir> <meta_qa_out.json>"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

recomputed = json.loads(subprocess.run(
    [sys.executable, str(HERE / "audit_calibration.py"), sys.argv[1]],
    capture_output=True, text=True, check=True).stdout)
reported = json.load(open(sys.argv[2])).get("calibration", {})

errs = []
for key in ("capacity", "readiness", "flow"):
    if recomputed.get(key) != reported.get(key):
        errs.append(f"{key}: recomputed {recomputed.get(key)} != reported {reported.get(key)}")
if recomputed.get("closed_runs") != reported.get("closed_runs", recomputed.get("closed_runs")):
    errs.append("closed_runs count mismatch")

print(json.dumps({"check": "verify_calibration", "verdict": "FAIL" if errs else "PASS", "defects": errs}))
sys.exit(1 if errs else 0)
