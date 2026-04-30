import pg from 'pg';
import { config } from './config.js';

// BIGINT (oid 20) → number (safe for ids up to 2^53).
pg.types.setTypeParser(20, (v) => (v === null ? null : Number(v)));

const connectionOptions = [
  `-c search_path=${config.PG_SCHEMA},public`,
  config.PG_STATEMENT_TIMEOUT_MS > 0
    ? `-c statement_timeout=${config.PG_STATEMENT_TIMEOUT_MS}`
    : '',
].filter(Boolean).join(' ');

export const pool = new pg.Pool({
  host: config.PGHOST,
  port: config.PGPORT,
  user: config.PGUSER,
  password: config.PGPASSWORD,
  database: config.PGDATABASE,
  max: config.PG_POOL_MAX,
  min: config.PG_POOL_MIN,
  idleTimeoutMillis: config.PG_IDLE_TIMEOUT_MS,
  connectionTimeoutMillis: config.PG_CONN_TIMEOUT_MS,
  application_name: '__SERVICE_NAME__',
  options: connectionOptions,
});

export type PoolClient = pg.PoolClient;

export async function pingDb(): Promise<{ up: boolean; latency_ms: number }> {
  const start = process.hrtime.bigint();
  try {
    await pool.query('SELECT 1');
    return { up: true, latency_ms: Math.round(Number(process.hrtime.bigint() - start) / 1e6) };
  } catch {
    return { up: false, latency_ms: -1 };
  }
}

export async function closeDb(): Promise<void> { await pool.end(); }
