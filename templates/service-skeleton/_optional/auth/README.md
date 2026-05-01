# Optional auth snippets

This folder holds opt-in auth scaffolding that `new-service.sh
--with-auth` copies into a freshly-bootstrapped service. The folder is
**excluded** from the default `rsync` of the skeleton (so a bare
service has no auth code by default).

## What `--with-auth` does

When invoked with `--with-auth --prefix=<2-4 lowercase letters>`,
`new-service.sh` performs these extra steps after the standard skeleton
copy:

1. Copies `_optional/auth/migration.sql` to
   `db/migrations/002_auth.sql` of the new service.
2. Substitutes `__SERVICE_NAME__`, `__DB_SCHEMA__`, `__TOKEN_PREFIX__`
   in the copied file.
3. Adds operator-TODO lines pointing at the reference TS implementation
   (`BBE-DBE/ip-pool-api/src/auth.ts`, ~325 LoC) and the registry.

## What `--with-auth` does NOT do

- Does **not** copy a TypeScript `auth.ts`. The reference
  implementation is `BBE-DBE/ip-pool-api/src/auth.ts`. Copy it
  manually and replace `iplk_` with your `__TOKEN_PREFIX___`.
- Does **not** mint a bootstrap key. Run a `scripts/bootstrap-key.sh`
  (also from ip-pool-api as reference) once `auth.ts` is in place
  **and** the migration has run.
- Does **not** wire the auth preHandler into routes. Each route
  decides whether it needs `requireAuth(['scope'])`.

## Why no full TS scaffold yet

The auth flow has enough service-specific judgment calls
(scope vocabulary, token-prefix collision avoidance, cluster-cache
strategy, audit-event verbs) that a "one-size-fits-all" `.ts.tpl`
either becomes too rigid or too generic to be useful. Once a second
service has gone through the same pattern and we see what genuinely
generalises, the snippet will move here in a later calver.

## Token-prefix collision guard

The single source of truth for prefix reservations is
**[`PREFIX-REGISTRY.md`](PREFIX-REGISTRY.md)** in this folder. Operators
**must** consult it before picking a prefix and append a row in the
same change as the new service.

`new-service.sh --with-auth` without `--prefix` does NOT pick a default
silently — it prints a hint pointing to the registry and exits non-zero.
