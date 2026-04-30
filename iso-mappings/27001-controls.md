# ISO/IEC 27001:2022 — Controls used by BBE-DBE services

Stripped to the controls we actually implement. Each row points at where the
evidence sits inside a service repo. Keep this in sync with the
`STANDARDS.md` of each service.

| Control | Title                          | Evidence (per service)                                |
|---------|--------------------------------|--------------------------------------------------------|
| A.5.15  | Access control                 | scopes in `api_keys.scopes`, `requireAuth(scopes)`     |
| A.5.18  | Access rights                  | revoke / expire on `api_keys`                          |
| A.5.21  | ICT supply-chain security      | `pnpm build:sbom` (CycloneDX), digest-pinned images    |
| A.5.30  | ICT readiness for continuity   | `scripts/backup.sh` + `restore.sh` + DR runbook        |
| A.8.4   | Access to source code          | private repos under `BBE-DBE/`                         |
| A.8.5   | Secure authentication          | argon2id + verify-cache + brute-force counter          |
| A.8.13  | Information backup             | retention policy in `backup.sh`, weekly restore drill  |
| A.8.15  | Logging                        | pino structured logs, request_id, redacted auth        |
| A.8.16  | Monitoring activities          | `/health`, `/health/live`, `/health/ready`, `/metrics` |
| A.8.20  | Network controls               | services bind 127.0.0.1, Caddy fronts TLS              |
| A.8.25  | Secure development life cycle  | TS strict, vitest unit + integration, smoke gate       |
| A.8.27  | Secure system architecture     | transactional outbox, state-machine trigger, idem keys |

## Out of scope (intentional)

- A.8.24 (cryptography): operator-decision (disk-level / TDE), see each
  service's `docs/data-processing.md` for the open question.
- A.5.7 (threat intelligence): external function, not in service code.
