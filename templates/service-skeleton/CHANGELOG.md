# Changelog

All notable changes are documented here.
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format,
[SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - <fill date>

### Added
- Initial scaffold from `BBE-DBE/api-standards/templates/service-skeleton`.
- `/health`, `/health/live`, `/health/ready`.
- Migration `001_init.sql` with append-only `events`, `idempotency_keys`,
  `schema_migrations` (sha-256 drift detection), per-service schema.
- `scripts/build.sh` (generates `src/lib/git-sha.ts`), `migrate.sh`,
  `release.sh` (clean-tree gated), `smoke-test.sh`.
- `.github/workflows/test.yml` (typecheck + build + vitest + coverage).
- `.github/workflows/gitleaks.yml`.
- `.github/dependabot.yml` (pnpm weekly).
