# hetzner-api — Compliance Gaps (snapshot 2026-05-02)

**Repo state at snapshot:** branch `release/v1.0.0` (local-only, not
pushed), tip `adab95d fix: dual-base Hetzner architecture, api.hetzner.com
for storage (ADR 0013)`, **12 untracked files** (6 migrations 003–008,
6 ADRs 0014–0019).

**Why this report exists:** so that the architecture compliance posture
is documented in `api-standards` even while hetzner-api itself remains
under active development. **No code changes have been made to hetzner-api
as part of this snapshot.** The gaps below are markers for the operator
to close inside hetzner-api on its own schedule.

## Gap inventory vs. PRINCIPLES.md and 14-dimensions

| Dim | Item | Status | Note |
|---|---|---|---|
| §2 API-First | OpenAPI 3.1 spec | ❌ missing | ADR 0019 (untracked) plans Zod→OpenAPI generator. Until then `openapi.yaml` is absent. Blocks `service-manifest.openapi_url`. |
| §6 Kompatibilität | OpenAPI as SoT | ❌ | follows from above |
| §8 Observability | Health-Split (`/live`, `/ready`, `/health`) | 🟡 partial | only `src/routes/health.routes.ts` (single endpoint). Three-way split per netcup-api / ip-pool-api pattern not yet ported. |
| §8 Observability | Prometheus `/metrics` | ❌ missing | no `src/metrics.ts` and no `/metrics` route handler. |
| §2 Agent-First / §13 | Idempotency replay store | 🟡 partial | error codes (`idempotency_mismatch`, `missing_idempotency_key`) are defined in `src/lib/errors.ts` but the DB-backed store (`src/lib/idempotency.ts`) and the `hetzner.idempotency_keys` table from migration `006_idempotency.sql` are **untracked** — work-in-progress. |
| §13 Agent-Tauglichkeit | Idempotency dual-header (`Idempotency-Key` + `X-Idempotency-Key`) | ❌ | new rule, see `protocols/idempotency-header-compat.md`. To implement once §13 idempotency lib lands. |
| §5 Modularität | Provider-Adapter via interface | 🟡 | `src/client/client.ts` exists; not yet wrapped in `ProviderAdapter` shape from `protocols/provider-adapter-interface.md`. ADR 0013 (dual-base) already aligns with the protocol's `bases[]` model. |
| §13 Agent-Tauglichkeit | `/service-manifest` endpoint | ❌ missing | new requirement; not yet a route. |
| PRINCIPLES §9 | Self-Registration to port-registry | 🟡 config-only | `.env.example` already declares `PORT_REGISTRY_URL=http://127.0.0.1:5099` (impl-side wiring TBD). |
| §9 Code-Qualität | CLI | ❌ missing | ADR 0017 `cli-shape` (untracked) plans this; no `bin` in `package.json`. |
| §10 Compliance | sbom.json | ❌ missing | netcup-api and ip-pool-api ship one; hetzner-api does not yet. |
| §12 Dokumentation | CHANGELOG.md | ❌ missing | toplevel listing shows no `CHANGELOG.md`. |
| Git workflow | release/v1.0.0 pushed to origin | ❌ | local-only branch; first push needs operator decision (PRINCIPLES.md branch conventions: feat/release/fix). |
| Working tree | 12 untracked files | 🟡 | active work-in-progress; NOT for this report to commit. |

## Closing the gaps (operator-side, not for this PR)

When hetzner-api day-1-closure resumes, the recommended order is:

1. Commit the 6 migrations + 6 ADRs in 2–3 logical batches (operator
   judgement which ADRs go together).
2. Push `release/v1.0.0` to origin so the work is visible to CI.
3. Implement OpenAPI generator (ADR 0019) — copy the working pattern
   from `BBE-DBE/ip-pool-api` (Zod schemas → `openapi:dump` script).
4. Port health-split + `/metrics` from ip-pool-api / netcup-api
   (≈ 60 lines, mostly route wiring).
5. Implement the DB-backed idempotency lib using `006_idempotency.sql`
   and ip-pool-api's `src/lib/idempotency.ts` as the reference (literal
   copy with `hetzner.` schema-prefix substitution).
6. Add dual-header idempotency middleware per the new
   `protocols/idempotency-header-compat.md`.
7. Add `/service-manifest` route per `protocols/service-manifest.md`.
8. Wire self-registration to port-registry per
   `protocols/service-self-registration.md` (the env var is already
   there).
9. Wrap `src/client/client.ts` in the `ProviderAdapter` shape from
   `protocols/provider-adapter-interface.md`. Multi-base is already
   designed (ADR 0013) — the protocol just formalises it.
10. Implement CLI per ADR 0017.
11. Generate sbom.json (`pnpm build:sbom`).
12. Add CHANGELOG.md and tag `v0.1.0-rc1`.

This is the recipe; none of it is executed in this PR.

## Re-snapshot trigger

Re-run this gap report whenever hetzner-api's tip moves past
`adab95d` or once `release/v1.0.0` reaches origin.
