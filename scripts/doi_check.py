#!/usr/bin/env python3
"""doi_check.py v1.0.0 - verify a DOI via Crossref. Usage: doi_check.py <doi>
Confirms resolution, work type and retraction status. It does not prove peer review:
QA must still confirm the venue is peer-reviewed."""
import json
import sys
import urllib.parse
import urllib.request

ALLOWED = {"journal-article", "proceedings-article"}

if __name__ == "__main__":
    doi = sys.argv[1]
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        m = json.load(urllib.request.urlopen(url, timeout=20))["message"]
    except Exception as e:  # network or 404
        print(json.dumps({"doi": doi, "resolves": False, "error": str(e)}))
        sys.exit(1)
    retracted = any(u.get("type") == "retraction" for u in m.get("updated-by", []))
    ok = m.get("type") in ALLOWED and not retracted
    print(json.dumps({
        "doi": doi, "resolves": True, "type": m.get("type"),
        "venue": (m.get("container-title") or [""])[0],
        "year": ((m.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0],
        "title": (m.get("title") or [""])[0],
        "retracted": retracted, "peer_reviewed_type": ok}))
    sys.exit(0 if ok else 1)
