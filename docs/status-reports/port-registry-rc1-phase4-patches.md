# port-registry rc1 — Phase 4 Plan-Patches

> Phase-4 (watermark-engine + health-sweeper) addressed three deliverables;
> two were implemented exactly per brief, one was scope-trimmed for rc1
> with explicit rc2 follow-up. The advisory-lock-key choice is recorded
> here so future BBE-DBE services don't collide.

Erfasst: 2026-05-01 · Service: port-registry · Phase: 4 · Validator: Claude Opus 4.7 (1M)

---

## P5 — Conflict-Detection scope-trimmed (rc2 follow-up)

**Brief (Phase 4.3):**
> Wenn 2 Services auf gleichem (port, host) → status='conflict'.
> Audit "PORT.CONFLICT_DETECTED". Manual Resolution erforderlich.

**Patch:** Phase-4 implements only the database-layer half:

- `UNIQUE (port, host_id)` on `port_registry.ports` (003_port_registry.sql)
  rejects any second `INSERT` with `port_unique_violation` (23505) at the
  reserve route. That covers the *registry* side: nobody can have two
  reservations on the same (port, host).

The application-layer half — detecting a *running* process on a
released-or-foreign port via the sweeper — is **deferred to rc2**.
Rationale:

1. The reliable signal would be `/health` returning a `service.name`
   that does not match the port-registry reservation. Today we only
   probe `/health/live` (just `{ status: 'ok' }`), because `/health`
   carries DB connectivity and varies in shape across BBE-DBE services.
2. A `404 /health` from a port whose reservation says `running` could
   mean (a) orphan process, (b) service was just restarted, (c) network
   blip — collapsing all three into `status='conflict'` would generate
   false positives that operators have to triage.
3. Phase-4 already emits `health_fail_streak` audit + `port_history`
   `health_fail` after 3 consecutive failures. That covers the
   actionable case: sweeper says fail, operator investigates.

**rc2 plan:**

- Sweeper probes `/health` (full) instead of `/health/live`.
- Compares `service.name` from response with `port.service_name`.
- On mismatch: mark `port.status='conflict'`, emit
  `port_history` action `conflict_detected`, audit
  `PORT.CONFLICT_DETECTED`. Operator resolves via
  `POST /v1/ports/:port/release`.
- Requires every BBE-DBE service to expose `/health` with
  `{ service: { name, version } }` — needs an api-standards
  protocol commit and a one-time PR sweep across services.

**Entscheid-Pfad:** Korrektheit (false-positive-free) > Brief-Wortlaut.
Trimming the unreliable half now keeps the audit log meaningful;
adding it half-baked would teach operators to ignore the alerts.

---

## Lock-Registry — `pg_advisory_lock` keys (port-registry)

The health-sweeper claims a Postgres advisory lock at the start of
every sweep tick so two pod replicas don't run the sweep concurrently.
Recorded here so future services pick a non-colliding key.

| Key  | Service        | Subsystem       | Mode   | Status   |
|------|----------------|-----------------|--------|----------|
| 7099 | port-registry  | health-sweeper  | shared | active   |

**Convention** (proposed; please codify in api-standards rc2):

- 4-digit numeric.
- The first two digits encode the **service-port-prefix** (so
  port-registry's 70xx slot maps to its 50xx port range halved
  to a 4-digit key). Saves us from a global allocation table.
- The last two digits identify the subsystem:
  - `xx99` = sweeper / cron-style background job
  - `xx01..xx98` = service-internal locks (per-aggregate, per-tenant, …)

For port-registry: 7099 = port-registry health-sweeper. Subsequent
internal locks would be 7001, 7002, …

**Action (api-standards rc2):** add an `advisory-lock-registry.md`
analogous to `PREFIX-REGISTRY.md` so the convention is enforceable
during code review.

---

## Phase-4 Smoke-Validation Snapshot (2026-05-01)

```
LISTEN/NOTIFY end-to-end:
  UPDATE port_registry.ports … → trigger trg_ports_notify →
  pg_notify('port_registry_ports_changed', payload) →
  watermark.ts listenClient.notification → invalidate() + log

  payload: {"action":"UPDATE","status_new":"running","status_old":"running",
            "range_class_new":"meta","range_class_old":"meta"}

Health-sweeper:
  sweep_id=3, total=2, ok=1 (port-registry@5099), fail=1 (ip-pool-api@5107),
  unknown=0, latency_ok=28ms, latency_fail=4ms (no listener)

  advisory_lock_key=7099 acquired + released cleanly per tick.
```
