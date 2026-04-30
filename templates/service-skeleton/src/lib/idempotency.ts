// Idempotency-Key store. Backed by __DB_SCHEMA__.idempotency_keys.
// Contract: api-standards/protocols/idempotency-contract.md (when added).
import { createHash } from 'node:crypto';
import { pool } from '../db.js';
import { IdempotencyMismatch } from './errors.js';

export function hashRequest(body: unknown): string {
  return createHash('sha256').update(canonicalJson(body)).digest('hex');
}

function canonicalJson(v: unknown): string {
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) return '[' + v.map(canonicalJson).join(',') + ']';
  const keys = Object.keys(v as Record<string, unknown>).sort();
  return '{' + keys.map((k) => JSON.stringify(k) + ':' + canonicalJson((v as Record<string, unknown>)[k])).join(',') + '}';
}

export interface CachedResponse { status_code: number; response: unknown }

export async function lookup(key: string, requestHash: string): Promise<CachedResponse | null> {
  const r = await pool.query<{ request_hash: string; status_code: number; response: unknown }>(
    'SELECT request_hash, status_code, response FROM __DB_SCHEMA__.idempotency_keys WHERE key = $1',
    [key],
  );
  if (r.rowCount === 0) return null;
  const row = r.rows[0]!;
  if (row.request_hash !== requestHash) throw IdempotencyMismatch();
  return { status_code: row.status_code, response: row.response };
}

export async function store(key: string, requestHash: string, statusCode: number, response: unknown): Promise<void> {
  await pool.query(
    `INSERT INTO __DB_SCHEMA__.idempotency_keys(key, request_hash, status_code, response)
     VALUES ($1, $2, $3, $4) ON CONFLICT (key) DO NOTHING`,
    [key, requestHash, statusCode, response],
  );
}

export async function purge(ttlHours: number): Promise<number> {
  const r = await pool.query(
    `DELETE FROM __DB_SCHEMA__.idempotency_keys WHERE created_at < now() - ($1 || ' hours')::interval`,
    [String(ttlHours)],
  );
  return r.rowCount ?? 0;
}
