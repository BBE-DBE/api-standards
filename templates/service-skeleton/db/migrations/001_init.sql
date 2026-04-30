-- Author: <fill at first run>
-- Date:   <fill at first run>
-- Commit: bootstrap from api-standards/templates/service-skeleton
-- ============================================================
-- __SERVICE_NAME__ — initial schema. Schema __DB_SCHEMA__ must already
-- exist in infra-postgres (operator-provisioned per service).
-- ============================================================

-- ---- schema_migrations marker -------------------------------
CREATE TABLE IF NOT EXISTS __DB_SCHEMA__.schema_migrations (
  filename     TEXT PRIMARY KEY,
  checksum     TEXT,
  author       TEXT,
  authored_at  TIMESTAMPTZ,
  git_commit   TEXT,
  executed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  applied_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---- events: append-only audit log --------------------------
CREATE TABLE IF NOT EXISTS __DB_SCHEMA__.events (
  id                BIGSERIAL PRIMARY KEY,
  event_uuid        UUID NOT NULL UNIQUE,
  subject_id        BIGINT,
  subject_ref       TEXT NOT NULL,
  actor_kind        TEXT NOT NULL,
  actor_id          TEXT NOT NULL,
  run_id            TEXT,
  action            TEXT NOT NULL,
  from_state        TEXT,
  to_state          TEXT,
  meta              JSONB NOT NULL DEFAULT '{}'::jsonb,
  at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE __DB_SCHEMA__.events IS 'Append-only audit log; UPDATE/DELETE rejected by trigger.';

CREATE INDEX IF NOT EXISTS events_subject_id_at
  ON __DB_SCHEMA__.events (subject_id, at DESC);
CREATE INDEX IF NOT EXISTS events_run_id_at
  ON __DB_SCHEMA__.events (run_id, at DESC) WHERE run_id IS NOT NULL;

-- ---- events immutability ------------------------------------
CREATE OR REPLACE FUNCTION __DB_SCHEMA__.tg_events_immutable()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '__DB_SCHEMA__.events is append-only (op=%)', TG_OP
    USING ERRCODE = '42501';
END $$;

DROP TRIGGER IF EXISTS events_immutable ON __DB_SCHEMA__.events;
CREATE TRIGGER events_immutable
  BEFORE UPDATE OR DELETE ON __DB_SCHEMA__.events
  FOR EACH ROW EXECUTE FUNCTION __DB_SCHEMA__.tg_events_immutable();

-- ---- idempotency_keys ---------------------------------------
CREATE TABLE IF NOT EXISTS __DB_SCHEMA__.idempotency_keys (
  key          TEXT PRIMARY KEY,
  request_hash TEXT NOT NULL,
  status_code  INT  NOT NULL,
  response     JSONB NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idempotency_keys_created_at
  ON __DB_SCHEMA__.idempotency_keys (created_at);
