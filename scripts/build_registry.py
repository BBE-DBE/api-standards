#!/usr/bin/env python3
"""
build_registry.py — turn a repo snapshot into a scored, machine-readable asset register.

Input :  registry/repos.snapshot.tsv   (see scripts/fetch_repos.sh for how to refresh)
Output:  registry/REGISTRY.yaml        (canonical, machine-readable — agents read this)
         docs/ASSET-REPORT.md          (human view)
         registry/registry.json        (flat, for dashboards)

No hand-editing of the outputs. Change the inputs or the rules, then re-run.
Rules live in this file so that every verdict is reproducible and arguable.

Usage: python3 scripts/build_registry.py [--ref-date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(ROOT, "registry", "repos.snapshot.tsv")
OUT_YAML = os.path.join(ROOT, "registry", "REGISTRY.yaml")
OUT_JSON = os.path.join(ROOT, "registry", "registry.json")
OUT_MD = os.path.join(ROOT, "docs", "ASSET-REPORT.md")

# ── Tier thresholds ────────────────────────────────────────────────────────
# lifespan = pushed_at - created_at. It is the cheapest honest proof that a repo
# was iterated on rather than dumped once. A repo whose entire history fits in
# one hour is a backup snapshot, not a project.
DUMP_LIFESPAN_H = 1.0      # < 1h of history  -> DUMP
SEED_LIFESPAN_D = 7.0      # < 7d of history  -> SEED
ACTIVE_DORMANT_D = 45.0    # pushed within 45d -> ACTIVE

# ── Ratified foundation (SERVICES.yaml, reuse_priority 0-1) ───────────────
# These are the entries the catalog already declares canonical. They outrank
# every heuristic below: a foundation service is CORE even when it sits quiet.
CORE = {
    "BBE-DBE/api-standards": 0,
    "BBE-DBE/infra-postgres": 0,
    "BBE-DBE/port-registry": 0,
    "BBE-DBE/ip-pool-api": 1,
    "BBE-DBE/netcup-api": 1,
    "BBE-DBE/hetzner-api": 1,
    "BBE-DBE/server-bootstrap": 1,
}

# ── Capability domains ─────────────────────────────────────────────────────
# Ordered: first match wins. This is the axis an agent searches on when asking
# "does something that does X already exist?" (PRINCIPLES.md 8, Lookup-before-Build).
DOMAIN_RULES = [
    ("standards-governance", r"api-standards|principles|iso-mapping|compliance"),
    ("identity-auth",        r"\bauth\b|auth0|oidc|oauth|identity|\blogin\b|signup|keychain|vault|secret|signtrust|signit"),
    ("infra-provisioning",   r"hetzner|netcup|upcloud|bootstrap|server-config|infra-|postgres|port-registry|ip-pool|base-stack|emergency|design-stack"),
    ("agent-orchestration",  r"\bagent|aatp|oktogen-os|coord|sentinel|multiagenten|\bmaof\b|pm-runner|event-router|brydge|\bcawf\b|neuraisphere|skills"),
    ("ai-routing",           r"ai-gateway|owl-router|ai-connect|global-rank|xbrain|\bapex\b|llm-router"),
    ("comms-messaging",      r"\bmail\b|\bchat\b(?!gpt)|chat-|wa-gateway|whatsapp|\bvoice\b|bitchat|mattermost"),
    ("lead-gen",             r"\blead\b|lead-gen|question-engine|nutrio|viral|immowert|graydion|\bbkw\b|automotive|questionaire|luescher"),
    ("construction-ssr",     r"^ssr|\bssr\b|\bsms\b|sanier|fassaden|maschine|wiebusch|lohn|banking|angebot|prozesse|projekt-studio|drone|verwaltung|partner-backend|neubau|copy-service|showcase"),
    ("commerce",             r"marketplace|mercur|commerce|shopify|supplier|preowned|storefront|dropset|verified-purchase|litecard|liteprofil"),
    ("analytics-tracking",   r"track|analytics|visibility|geo-obs|geo-cities|harvester|resonance|10bx|\b11x\b|design-value|marketing"),
    ("content-cms",          r"\bcms\b|notes-hub|wiki|magazine|ideas-hub|imgmf|watermark|logo-db|\bqr\b|canva|directus"),
    ("hub-dashboard",        r"\bhubs?\b|devhub|fork-control|launchpad|cost-wallet|presentation|feeder|frontend|\bshell\b|dashboard"),
    ("security-tooling",     r"security-scanner|worktree|sprint-machine|guard"),
    ("brand-site",           r"zaba|zingo|off---set|offset|taxonair|airscope|parkpeak|kuberg|maxxipower|gotteswasser|earth-moon|pyka|gp-pm|trainingbox|cloud-adam-eve|website|landing"),
]


# ── Duplicate / overlap clusters ───────────────────────────────────────────
# Curated, not inferred: naming is too inconsistent for a regex to be trusted.
# Each cluster names ONE canonical repo. Everything else in it is a merge or
# archive candidate. This is the part of the register that actually kills the
# graveyard.
CLUSTERS = {
    "zabazingo": {
        "canonical": "BBE-DBE/zabazingo-platform",
        "members": ["BBE-DBE/zabazingo-platform", "BBE-DBE/zabazingo-website", "BBE-DBE/zabazingo-hub",
                    "BBE-DBE/zabazingo-domains", "BBE-DBE/zaba-zingo", "BBE-DBE/zaba-zingo-yt",
                    "BBE-DBE/preowned-zabazingo", "BBE-DBE/zz-keychain", "BBE-DBE/zz-logo-db"],
    },
    "taxonair": {
        "canonical": "BBE-DBE/taxonair",
        "members": ["BBE-DBE/taxonair", "BBE-DBE/taxonair-hub", "BBE-DBE/airscope-taxonair"],
    },
    "parkpeak": {
        "canonical": "BBE-DBE/parkpeak-v2",
        "members": ["BBE-DBE/parkpeak", "BBE-DBE/parkpeak-v2"],
    },
    "off---set": {
        "canonical": "BBE-DBE/offset-site",
        "members": ["BBE-DBE/off---set", "BBE-DBE/off---set-ideas", "BBE-DBE/offset-site", "BBE-DBE/offset-studio"],
    },
    "resonance": {
        "canonical": "BBE-DBE/resonance-lab",
        "members": ["BBE-DBE/resonance-lab", "BBE-DBE/resonance-sector"],
    },
    "launchpad": {
        "canonical": "BBE-DBE/launchpad-modules",
        "members": ["BBE-DBE/LaunchPad", "BBE-DBE/launchpad-modules"],
    },
    "qr": {
        "canonical": "BBE-DBE/oktogen-qr",
        "members": ["BBE-DBE/qr", "BBE-DBE/oktogen-qr"],
    },
    "estate-hubs": {
        "canonical": "BBE-DBE/bestbrands-hub",
        "members": ["BBE-DBE/bestbrands-hub", "BBE-DBE/company-hubs", "BBE-DBE/dbl9-hub",
                    "BBE-DBE/devhub", "BBE-DBE/ideas-hub"],
    },
    "tracking": {
        "canonical": "BBE-DBE/bbe-track-analytics",
        "members": ["BBE-DBE/bbe-track", "BBE-DBE/bbe-track-analytics"],
    },
    "signit": {
        "canonical": "BBE-DBE/signit-selfdemo",
        "members": ["BBE-DBE/signit-selfdemo", "BBE-DBE/signit-admin-demo"],
    },
    "identity": {
        "canonical": "BBE-DBE/bbe-auth",
        "members": ["BBE-DBE/bbe-auth", "BBE-DBE/auth00-agent"],
    },
    "agent-os": {
        "canonical": "BBE-DBE/oktogen-os",
        "members": ["BBE-DBE/oktogen-os", "BBE-DBE/AATP-OS", "BBE-DBE/oktogen-aatp",
                    "BBE-DBE/Multiagentensysteme", "BBE-DBE/sentinel", "BBE-DBE/bbe-coord",
                    "BBE-DBE/oktogen-agents", "BBE-DBE/CAWF", "BBE-DBE/Neuraisphere"],
    },
    "geo": {
        "canonical": "BBE-DBE/geo-visibility",
        "members": ["BBE-DBE/geo-visibility", "BBE-DBE/geo-obs", "BBE-DBE/bbe-geo-cities"],
    },
}

# Curated domain overrides. A repo whose description leads with a word from
# another domain ("agent-first mail platform") lands wrong on pure regex.
DOMAIN_OVERRIDES = {
    "BBE-DBE/bbe-mail": "comms-messaging",
    "BBE-DBE/oktogen-chat": "comms-messaging",
    "BBE-DBE/bbe-voice": "comms-messaging",
    "BBE-DBE/base-stack": "comms-messaging",
    "BBE-DBE/cloud-adam-eve": "content-cms",
    "BBE-DBE/viral-workspace": "content-cms",
    "BBE-DBE/oktogen-vault": "identity-auth",
    "BBE-DBE/bbe-secrets-vault": "identity-auth",
    "BBE-DBE/apex": "analytics-tracking",
    "BBE-DBE/10BX": "analytics-tracking",
    "BBE-DBE/LEAD-GEN-SSR": "lead-gen",
    "BBE-DBE/bbe-leads": "lead-gen",
    "BBE-DBE/offset-site": "brand-site",
    "BBE-DBE/global-rank": "analytics-tracking",
    "BBE-DBE/Health-Magazine-1000": "content-cms",
    "BBE-DBE/agentpedia-wiki": "content-cms",
}

MEMBER_TO_CLUSTER = {m: c for c, v in CLUSTERS.items() for m in v["members"]}


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def classify_domain(full_name: str, desc: str) -> str:
    hay = f"{full_name.split('/')[-1]} {desc}".lower()
    if full_name in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[full_name]
    for domain, pattern in DOMAIN_RULES:
        if re.search(pattern, hay):
            return domain
    return "unclassified"


def tier_of(row: dict) -> str:
    if row["full_name"] in CORE:
        return "CORE"
    if row["lifespan_h"] < DUMP_LIFESPAN_H:
        return "DUMP"
    if row["dormant_d"] <= ACTIVE_DORMANT_D:
        return "ACTIVE"
    if row["lifespan_d"] >= SEED_LIFESPAN_D:
        return "ASSET"
    return "SEED"


def score_of(row: dict) -> int:
    """Reuse value 0-100. Every input is verifiable from the snapshot."""
    iteration = min(row["lifespan_d"] / 30.0, 1.0)              # 30d of history = full marks
    freshness = max(0.0, 1.0 - row["dormant_d"] / 120.0)        # linear decay over 4 months
    documented = 1.0 if row["description"] else 0.0
    trunk_clean = 1.0 if row["default_branch"] in ("main", "master") else 0.0
    ratified = 1.0 if row["full_name"] in CORE else 0.0
    return round(35 * iteration + 30 * freshness + 15 * documented
                 + 10 * trunk_clean + 10 * ratified)


def action_of(row: dict) -> str:
    """The one decision this repo is waiting on."""
    fn, tier = row["full_name"], row["tier"]
    cluster = row.get("cluster")
    if tier == "CORE":
        return "KEEP"
    if cluster and CLUSTERS[cluster]["canonical"] != fn:
        return "MERGE"          # fold into the cluster's canonical repo
    if tier == "DUMP":
        return "ARCHIVE"        # one-shot snapshot, no iteration ever happened
    if tier == "ACTIVE":
        return "SHIP" if row["unmerged_trunk"] else "KEEP"
    if tier == "ASSET":
        return "REVIVE"         # real work sits here, dormant — decide explicitly
    return "ARCHIVE"


def load_rows(ref: datetime) -> list[dict]:
    rows = []
    with open(SNAPSHOT, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            parts += [""] * (len(header) - len(parts))
            rec = dict(zip(header, parts))
            created, pushed = parse_ts(rec["created_at"]), parse_ts(rec["pushed_at"])
            lifespan_s = (pushed - created).total_seconds()
            row = {
                "full_name": rec["full_name"].strip(),
                "org": rec["full_name"].split("/")[0],
                "name": rec["full_name"].split("/")[1],
                "description": rec["description"].strip(),
                "language": rec["language"].strip() or None,
                "private": rec["private"].strip() == "true",
                "default_branch": rec["default_branch"].strip(),
                "open_issues": int(rec["open_issues"] or 0),
                "created_at": rec["created_at"].strip(),
                "pushed_at": rec["pushed_at"].strip(),
                "lifespan_d": round(lifespan_s / 86400.0, 2),
                "lifespan_h": round(lifespan_s / 3600.0, 2),
                "dormant_d": round((ref - pushed).total_seconds() / 86400.0, 1),
            }
            row["unmerged_trunk"] = row["default_branch"] not in ("main", "master")
            row["undocumented"] = not row["description"]
            row["domain"] = classify_domain(row["full_name"], row["description"])
            row["cluster"] = MEMBER_TO_CLUSTER.get(row["full_name"])
            row["reuse_priority"] = CORE.get(row["full_name"])
            row["tier"] = tier_of(row)
            row["score"] = score_of(row)
            row["action"] = action_of(row)
            rows.append(row)
    return rows


def y(s) -> str:
    """Minimal YAML scalar quoting — no external deps in the standards repo."""
    if s is None:
        return "null"
    if isinstance(s, bool):
        return "true" if s else "false"
    if isinstance(s, (int, float)):
        return str(s)
    s = str(s)
    if s == "" or re.search(r'[:#\-\[\]{}&*!|>%@`"\']|^\s|\s$', s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def emit_yaml(rows: list[dict], ref: datetime) -> str:
    tiers = {}
    for r in rows:
        tiers.setdefault(r["tier"], []).append(r)
    out = [
        "# REGISTRY.yaml — BBE-DBE / SSR-SFS asset register",
        "#",
        "# GENERATED by scripts/build_registry.py — DO NOT HAND-EDIT.",
        "# Refresh the snapshot (scripts/fetch_repos.sh), then re-run the builder.",
        "#",
        "# This is the machine-readable answer to PRINCIPLES.md 8 (Lookup-before-Build):",
        "# before proposing ANY new capability, search `domain:` and `cluster:` here first.",
        "#",
        "# tier    CORE   ratified foundation (SERVICES.yaml, reuse_priority 0-1)",
        "#         ACTIVE pushed within 45d — someone is working on it now",
        "#         ASSET  >=7d of real history, dormant — reusable, needs a revive/kill call",
        "#         SEED   started but <7d of history — thin",
        "#         DUMP   entire history inside 1h — a backup snapshot, not a project",
        "# action  KEEP | SHIP | REVIVE | MERGE | ARCHIVE  — the one open decision",
        "# score   0-100 reuse value: 35 iteration + 30 freshness + 15 docs",
        "#         + 10 clean trunk + 10 ratified",
        "",
        "version: 1",
        f'generated_at: "{ref.strftime("%Y-%m-%d")}"',
        f"repo_count: {len(rows)}",
        "",
        "totals:",
    ]
    for t in ("CORE", "ACTIVE", "ASSET", "SEED", "DUMP"):
        out.append(f"  {t.lower()}: {len(tiers.get(t, []))}")
    out += ["", "clusters:"]
    for cname, c in sorted(CLUSTERS.items()):
        out.append(f"  {y(cname)}:")
        out.append(f"    canonical: {y(c['canonical'])}")
        out.append(f"    members: {len(c['members'])}")
        out.append("    fold_in:")
        for m in c["members"]:
            if m != c["canonical"]:
                out.append(f"      - {y(m)}")
    out += ["", "repos:"]
    for r in sorted(rows, key=lambda x: (-x["score"], x["full_name"])):
        out.append(f"  {y(r['full_name'])}:")
        for k in ("tier", "action", "score", "domain", "cluster", "reuse_priority",
                  "language", "private", "default_branch", "open_issues",
                  "created_at", "pushed_at", "lifespan_d", "dormant_d",
                  "unmerged_trunk", "undocumented", "description"):
            out.append(f"    {k}: {y(r[k])}")
    return "\n".join(out) + "\n"


def emit_md(rows: list[dict], ref: datetime) -> str:
    by_tier = {}
    for r in rows:
        by_tier.setdefault(r["tier"], []).append(r)
    for v in by_tier.values():
        v.sort(key=lambda x: -x["score"])

    n = len(rows)
    L = [
        "# Asset Report — BBE-DBE / SSR-SFS",
        "",
        f"**Stand:** {ref:%Y-%m-%d} · **{n} Repos** · generiert aus `registry/REGISTRY.yaml`",
        "",
        "> Generiert von `scripts/build_registry.py`. Nicht von Hand editieren.",
        "> Jede Bewertung unten ist aus dem Snapshot reproduzierbar — Regeln stehen im Skript.",
        "",
        "## Wie gelesen wird",
        "",
        "| Tier | Bedeutung | Was zu tun ist |",
        "|---|---|---|",
        "| `CORE` | Ratifizierte Foundation (SERVICES.yaml) | Halten, Version pinnen |",
        "| `ACTIVE` | Push in den letzten 45 Tagen | Zu Ende bringen |",
        "| `ASSET` | ≥7 Tage echte Historie, aber ruhend | **Bewusst entscheiden:** wiederbeleben oder stilllegen |",
        "| `SEED` | Angefangen, <7 Tage Historie | Meist stilllegen |",
        "| `DUMP` | Gesamte Historie <1 Stunde | Backup-Snapshot, kein Projekt — stilllegen |",
        "",
        "`score` = Wiederverwendungswert 0–100: 35 Iterationstiefe + 30 Aktualität + 15 Doku "
        "+ 10 sauberer Trunk + 10 ratifiziert.",
        "",
        "---",
        "",
        "## Bestand",
        "",
        "| Tier | Repos | Anteil |",
        "|---|---:|---:|",
    ]
    for t in ("CORE", "ACTIVE", "ASSET", "SEED", "DUMP"):
        c = len(by_tier.get(t, []))
        L.append(f"| `{t}` | {c} | {100*c//n}% |")
    L += ["", "### Nach Domäne", "", "| Domäne | Repos | davon CORE+ACTIVE | Top-Asset |", "|---|---:|---:|---|"]
    doms = {}
    for r in rows:
        doms.setdefault(r["domain"], []).append(r)
    for d, rs in sorted(doms.items(), key=lambda kv: -len(kv[1])):
        live = sum(1 for r in rs if r["tier"] in ("CORE", "ACTIVE"))
        top = max(rs, key=lambda x: x["score"])
        L.append(f"| `{d}` | {len(rs)} | {live} | `{top['name']}` ({top['score']}) |")

    L += ["", "---", "", "## Konsolidierung — was zusammengehört", "",
          "Kuratiert, nicht geraten. Pro Cluster **ein** kanonisches Repo; der Rest ist Merge-Kandidat.",
          "", "| Cluster | Kanonisch | Einfalten | Betroffene Repos |", "|---|---|---:|---|"]
    saved = 0
    for cname, c in sorted(CLUSTERS.items(), key=lambda kv: -len(kv[1]["members"])):
        fold = [m for m in c["members"] if m != c["canonical"]]
        saved += len(fold)
        L.append(f"| `{cname}` | `{c['canonical'].split('/')[1]}` | {len(fold)} | "
                 + ", ".join(f"`{m.split('/')[1]}`" for m in fold) + " |")
    L.append("")
    L.append(f"**{saved} Repos** lassen sich in **{len(CLUSTERS)} kanonische** zusammenführen.")

    L += ["", "---", "", "## Die Assets", ""]
    titles = {
        "CORE": "CORE — ratifizierte Foundation",
        "ACTIVE": "ACTIVE — läuft gerade",
        "ASSET": "ASSET — echte Substanz, ruhend (hier liegt das ungenutzte Kapital)",
        "SEED": "SEED — angefangen, dünn",
        "DUMP": "DUMP — Backup-Snapshots, keine Projekte",
    }
    for t in ("CORE", "ACTIVE", "ASSET", "SEED", "DUMP"):
        rs = by_tier.get(t, [])
        if not rs:
            continue
        L += ["", f"### {titles[t]} ({len(rs)})", "",
              "| Score | Repo | Domäne | Sprache | Historie | Ruht seit | Aktion | Was es ist |",
              "|---:|---|---|---|---:|---:|---|---|"]
        for r in rs:
            flags = ""
            if r["unmerged_trunk"]:
                flags += " ⚠"
            desc = (r["description"] or "—")
            desc = desc[:88] + "…" if len(desc) > 88 else desc
            L.append(
                f"| {r['score']} | `{r['name']}`{flags} | {r['domain']} | {r['language'] or '—'} | "
                f"{r['lifespan_d']:.0f}d | {r['dormant_d']:.0f}d | **{r['action']}** | {desc} |"
            )

    unmerged = [r for r in rows if r["unmerged_trunk"]]
    L += ["", "---", "", f"## ⚠ Offene Trunks ({len(unmerged)})", "",
          "Der Default-Branch ist ein Feature-Branch. Die Hauptarbeit wurde nie auf `main` gebracht —",
          "jeder Klon landet auf halbfertigem Stand, und CI/Releases greifen ins Leere.", "",
          "| Repo | Default-Branch | Tier |", "|---|---|---|"]
    for r in sorted(unmerged, key=lambda x: -x["score"]):
        L.append(f"| `{r['name']}` | `{r['default_branch']}` | {r['tier']} |")

    undoc = [r for r in rows if r["undocumented"]]
    L += ["", "---", "", f"## Ohne Beschreibung ({len(undoc)})", "",
          "Kein `description`-Feld. Für einen Agenten (und für dich in 3 Monaten) unsichtbar —",
          "`Lookup-before-Build` kann darauf nicht greifen. Billigster Fix im ganzen Bestand.", "",
          "| Repo | Tier | Score |", "|---|---|---:|"]
    for r in sorted(undoc, key=lambda x: -x["score"]):
        L.append(f"| `{r['name']}` | {r['tier']} | {r['score']} |")

    L += ["", "---", "",
          "## Nächste Aktion", "",
          "| Aktion | Repos | Bedeutung |", "|---|---:|---|"]
    acts = {}
    for r in rows:
        acts.setdefault(r["action"], []).append(r)
    meaning = {
        "KEEP": "Bestand, nichts zu tun",
        "SHIP": "Aktiv, aber Trunk offen — Branch nach main mergen",
        "REVIVE": "Substanz vorhanden, ruhend — bewusst entscheiden",
        "MERGE": "In das kanonische Repo des Clusters einfalten",
        "ARCHIVE": "Stilllegen (GitHub-Archive, nicht löschen)",
    }
    for a in ("KEEP", "SHIP", "REVIVE", "MERGE", "ARCHIVE"):
        if a in acts:
            L.append(f"| **{a}** | {len(acts[a])} | {meaning[a]} |")
    L += ["", "---", "",
          "_Regenerieren:_ `python3 scripts/build_registry.py`", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-date", default=None, help="YYYY-MM-DD (default: today, UTC)")
    args = ap.parse_args()
    ref = (datetime.strptime(args.ref_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
           if args.ref_date else datetime.now(timezone.utc))

    rows = load_rows(ref)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_YAML, "w", encoding="utf-8") as fh:
        fh.write(emit_yaml(rows, ref))
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"generated_at": ref.strftime("%Y-%m-%d"),
                   "clusters": CLUSTERS, "repos": rows}, fh, indent=1, ensure_ascii=False)
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write(emit_md(rows, ref))

    t = {}
    for r in rows:
        t[r["tier"]] = t.get(r["tier"], 0) + 1
    print(f"{len(rows)} repos -> " + "  ".join(f"{k}:{v}" for k, v in sorted(t.items())))
    print(f"wrote {os.path.relpath(OUT_YAML, ROOT)}, {os.path.relpath(OUT_JSON, ROOT)}, "
          f"{os.path.relpath(OUT_MD, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
