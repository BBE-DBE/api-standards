# Token-Prefix Reserve-Registry — BBE-DBE ecosystem

Single source of truth for **bearer-token prefixes**. Every service that
authenticates callers itself (via `_optional/auth/migration.sql` opt-in
in this repo) reserves a unique 2–4-letter lowercase prefix here.

Token format across the ecosystem:

```
<prefix>_<key_id>_<secret>
            └─26ch base32       └─43ch base64url
```

## Why a registry

A duplicate prefix means two services accept tokens with the same
visual layout. A token leak from service A would look "similar enough"
that an attacker might try it against service B — and if B's `key_id`
range happens to match A's, even the early lookup hits something
plausible. Independent of timing-attack concerns, the operator
confusion alone is a strong reason to keep prefixes globally unique.

## Operator-Pflicht

**Before** running `bash new-service.sh ... --with-auth --prefix=<X>`:

1. Search this table for `X`. If present and the row is not marked
   `RETIRED`, pick a different prefix.
2. Append a new row in the **same PR** that introduces the new service
   (or in the next api-standards calver bump, whichever comes first).
3. Never reuse a retired prefix without a 90-day cooldown — there may
   still be unrevoked tokens in the wild.

## Validation rules

- Prefix matches `^[a-z]{2,4}$`.
- 2-letter prefixes are reserved for **core/meta services** only
  (e.g. an `au_` for a future auth-server). Default for application
  services is 3 letters.
- The prefix is part of the bearer token's wire format. Renaming a
  prefix is **breaking** for every issued token; do not rename — retire
  the old service-prefix and mint a new one.

## Registry

| Prefix  | Service       | Repository                    | Reserved at | Status   |
|---------|---------------|-------------------------------|-------------|----------|
| `iplk_` | ip-pool-api   | `BBE-DBE/ip-pool-api` v0.3.0  | 2026-04-30  | active   |

<!-- Append rows in chronological order. Status ∈ {active, retired, RETIRED}.
     Retired = soft-retired (90-day cooldown still running).
     RETIRED = full retirement, prefix reusable. -->

## Reserved-but-not-yet-active

If a service has been **planned** but not yet bootstrapped, list the
prefix here so simultaneous service-design rounds don't collide. Move
to the main registry when the service is committed.

| Prefix  | Service       | Note                                  | Reserved at |
|---------|---------------|---------------------------------------|-------------|
| `prr_`  | port-registry | bootstrap deferred, see notes 2026-05 | 2026-05-01  |

## How an agent uses this

When an agent (Claude/Codex) is told to add a new authenticated service:

1. Read this file.
2. Pick a prefix that doesn't appear in either table.
3. Either edit this file in the same change, OR raise a flag and ask
   the operator to do it (if the agent doesn't have api-standards
   write-access).

`new-service.sh --with-auth` references this registry by path in its
hint output when no `--prefix` is given.
