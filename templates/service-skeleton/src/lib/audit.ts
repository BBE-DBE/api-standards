// Audit-event writer. Schema: api-standards/protocols/audit-event-schema.yaml.
// Every state mutation MUST go through writeAudit (or writeAuditTx).
import type { PoolClient } from '../db.js';
import { pool } from '../db.js';
import { newUuid7 } from './uuid7.js';
import { buildVersion } from './build-version.js';

export interface AuditActor {
  kind: 'agent' | 'user' | 'system';
  id: string;        // UUIDv7 of the api-key row, never the raw token
  run_id?: string;
}

export interface AuditEntry {
  subject_id: number | null;     // primary-key of the mutated row, or null
  subject_ref: string;           // human-meaningful reference (e.g. address, slug)
  actor: AuditActor;
  action: string;                 // e.g. 'created', 'reserved', 'released'
  from_state: string | null;
  to_state: string | null;
  meta?: Record<string, unknown>;
}

export async function writeAudit(c: PoolClient, e: AuditEntry): Promise<string> {
  const eventUuid = newUuid7();
  const meta = { ...(e.meta ?? {}), build_version: buildVersion };
  await c.query(
    `INSERT INTO __DB_SCHEMA__.events
       (event_uuid, subject_id, subject_ref, actor_kind, actor_id, run_id,
        action, from_state, to_state, meta)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,
    [eventUuid, e.subject_id, e.subject_ref,
     e.actor.kind, e.actor.id, e.actor.run_id ?? null,
     e.action, e.from_state, e.to_state, meta],
  );
  return eventUuid;
}

export async function writeAuditTx(e: AuditEntry): Promise<string> {
  const c = await pool.connect();
  try {
    await c.query('BEGIN');
    const id = await writeAudit(c, e);
    await c.query('COMMIT');
    return id;
  } catch (err) {
    await c.query('ROLLBACK').catch(() => {});
    throw err;
  } finally {
    c.release();
  }
}
