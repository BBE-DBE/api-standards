# api-standards

Cross-service standards for the **BBE-DBE** ecosystem. Used by humans and
agents when building or modifying any service under `BBE-DBE/`.

The point of this repo is **token efficiency** for agentic code work:
instead of pasting a 500-line workflow into every prompt, a service's
`AGENTS.md` points at one file here. The agent loads only what the
current task needs.

## Layout

```
workflows/
  agent-prompt-prefix.md    # the 3-part workflow (vorher/nachher/optimierung)
checklists/
  14-dimensions.md          # post-build self-check
  new-service-bootstrap.md  # what every new service must ship with
iso-mappings/
  27001-controls.md         # the controls we actually implement
templates/
  status-report.md          # final-status format
registry/
  repos.snapshot.tsv        # raw GitHub facts (input, refreshed by a script)
  REGISTRY.yaml             # GENERATED asset register — 145 repos, scored
  registry.json             # GENERATED flat form for dashboards
scripts/
  fetch_repos.sh            # GitHub API  -> repos.snapshot.tsv
  build_registry.py         # snapshot    -> REGISTRY.yaml + docs/ASSET-REPORT.md
  build_dashboard.py        # registry.json -> docs/dashboard.html
docs/
  ASSET-REPORT.md           # GENERATED human view of the register
  dashboard.template.html   # filter-surface template (source)
  dashboard.html            # GENERATED filterable dashboard
```

## The asset register

`registry/REGISTRY.yaml` is the machine-readable answer to PRINCIPLES.md 8
(*Lookup-before-Build*). It carries every repo in `BBE-DBE/` and `SSR-SFS/`
with:

- `domain:` — the capability axis to search on before building anything new
- `cluster:` + `canonical:` — which repos overlap, and which one wins
- `tier:` — `CORE` / `ACTIVE` / `ASSET` / `SEED` / `DUMP`
- `score:` — 0-100 reuse value (35 iteration + 30 freshness + 15 docs
  + 10 clean trunk + 10 ratified)
- `action:` — the single open decision: `KEEP` / `SHIP` / `REVIVE` /
  `MERGE` / `ARCHIVE`

**Never hand-edit the generated files.** Refresh instead:

```bash
GITHUB_TOKEN=... ./scripts/fetch_repos.sh BBE-DBE SSR-SFS   # facts
python3 scripts/build_registry.py                            # verdicts
```

Every verdict is reproducible from the snapshot; the rules live in
`scripts/build_registry.py` so they can be argued with and changed, rather
than negotiated per repo.

`docs/dashboard.html` is the filter surface over the same data — search,
filter by tier / domain / action, sort by reuse score. It carries no numbers
of its own; `scripts/build_dashboard.py` inlines `registry/registry.json`
into `docs/dashboard.template.html`, so there is no second source of truth:

```bash
python3 scripts/build_dashboard.py    # registry.json -> docs/dashboard.html
```

## How a service references this

Each service repo has a top-level `AGENTS.md` with ~10 lines:

```markdown
# AGENTS.md

When you (an agent) take an instruction in this repo:
1. Read `~/projects/api-standards/workflows/agent-prompt-prefix.md`
   (or clone `BBE-DBE/api-standards` to `~/projects/api-standards/` if missing).
2. Load only the checklist that matches the task.
3. Status report follows `templates/status-report.md`.

Service-specific exceptions live in this repo's PRINCIPLES.md / STANDARDS.md.
```

This way the workflow is one source of truth, services reference it, and the
agent's context window stays small.

## Versioning

The standards repo uses calendar-versioning (`2026.04`). Services pin a
version they were last validated against in their own `STANDARDS.md`. New
controls land here first, then propagate to services in their next release.
