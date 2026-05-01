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

## If this service authenticates callers (i.e. has its own bearer tokens)

Before minting any new key or writing `auth.ts`:

1. Read
   [`api-standards/templates/service-skeleton/_optional/auth/PREFIX-REGISTRY.md`](https://github.com/BBE-DBE/api-standards/blob/main/templates/service-skeleton/_optional/auth/PREFIX-REGISTRY.md)
   end-to-end. Prefixes are global, not per-service.
2. If the prefix this service plans to use is not in the registry,
   add a row in the **same change** that introduces the auth code.
3. If a prefix conflict is found, stop and ask the operator.
