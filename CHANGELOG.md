# Changelog

Calendar versioning: **YYYY.MM.DD**. Tags are immutable; new policies
land as a new tag, services pin a minimum version they were last
validated against.

## [2026.04.30] - 2026-04-30

### Added
- `workflows/agent-prompt-prefix.md` — three-part workflow (Trade-off →
  14-Dimension-Selbstcheck → Optimierungs-Schleife).
- `checklists/14-dimensions.md` — full checklist used by the post-build
  self-check.
- `checklists/new-service-bootstrap.md` — what every new BBE-DBE
  service must ship with on day one.
- `iso-mappings/27001-controls.md` — ISO 27001 controls actually
  implemented across the ecosystem (with per-service evidence pointers).
- `templates/status-report.md` — final-status-report layout used at the
  end of every agent task.

### Pinned by

- BBE-DBE/ip-pool-api ≥ 2026.04.30 (since v0.3.0)
- BBE-DBE/infra-postgres ≥ 2026.04.30 (since v0.1.1)
