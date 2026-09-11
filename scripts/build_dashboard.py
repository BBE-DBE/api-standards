#!/usr/bin/env python3
"""
build_dashboard.py — inject registry.json into docs/dashboard.template.html.

The dashboard is the filter surface over the same register the YAML carries:
same numbers, same verdicts, no second source of truth. Regenerate after every
build_registry.py run.

Usage: python3 scripts/build_dashboard.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "registry", "registry.json")
TPL = os.path.join(ROOT, "docs", "dashboard.template.html")
OUT = os.path.join(ROOT, "docs", "dashboard.html")

# Only the fields the page actually renders — keeps the inlined payload small.
KEEP = ("full_name", "org", "name", "description", "language", "default_branch",
        "domain", "cluster", "tier", "action", "score",
        "lifespan_d", "dormant_d", "unmerged_trunk", "undocumented")

reg = json.load(open(SRC, encoding="utf-8"))
payload = {
    "generated_at": reg["generated_at"],
    "clusters": {k: {"canonical": v["canonical"], "members": v["members"]}
                 for k, v in reg["clusters"].items()},
    "repos": [{k: r[k] for k in KEEP} for r in reg["repos"]],
}
blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
# </script> inside a JSON string would close the host <script> tag early.
blob = blob.replace("</", "<\\/")

tpl = open(TPL, encoding="utf-8").read()
assert "/*__REGISTRY_DATA__*/" in tpl, "template placeholder missing"
open(OUT, "w", encoding="utf-8").write(tpl.replace("/*__REGISTRY_DATA__*/", blob))
print(f"{len(payload['repos'])} repos, {len(payload['clusters'])} clusters -> "
      f"docs/dashboard.html ({os.path.getsize(OUT)//1024} KB)")
