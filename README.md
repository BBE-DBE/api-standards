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
