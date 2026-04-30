# AGENTS.md

When you (an agent) take an instruction in this repo:

1. Read `~/projects/api-standards/workflows/agent-prompt-prefix.md`. If
   missing, `gh repo clone BBE-DBE/api-standards ~/projects/api-standards`.
2. Pinned standards version: **>= 2026.04.30** (or whatever the
   current calver is on the day this skeleton was generated).
3. Load only the checklist that matches the task — usually
   `checklists/14-dimensions.md` for the post-build self-check.
4. The final status report follows `templates/status-report.md`.

Service-specific exceptions live in [`PRINCIPLES.md`](PRINCIPLES.md) and
[`STANDARDS.md`](STANDARDS.md).
