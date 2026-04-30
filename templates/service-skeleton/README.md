# __SERVICE_NAME__

__SERVICE_DESC__

Generated from `BBE-DBE/api-standards/templates/service-skeleton/`. Replace
this introduction with the actual service description before the first commit.

## Quickstart

```bash
cp .env.example .env       # fill PGPASSWORD with a real value
pnpm install
pnpm migrate               # apply db/migrations/
pnpm build
pnpm start
```

## Endpoints

| Method | Path           | Notes                           |
|--------|----------------|---------------------------------|
| GET    | `/health`      | full report                     |
| GET    | `/health/live` | process liveness                |
| GET    | `/health/ready`| readiness                       |

## Layout

- `src/` — TypeScript sources (ESM/NodeNext)
- `db/migrations/` — immutable SQL migrations
- `scripts/` — operator scripts (build, migrate, smoke, release)
- `tests/` — vitest unit + integration

## See also

- [`AGENTS.md`](AGENTS.md) — agent workflow + standards pinning
- [`PRINCIPLES.md`](PRINCIPLES.md) — architectural decisions
- [`STANDARDS.md`](STANDARDS.md) — compliance + ISO mapping
- [`CHANGELOG.md`](CHANGELOG.md)
