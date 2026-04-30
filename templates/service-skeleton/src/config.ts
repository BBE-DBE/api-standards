import 'dotenv/config';
import { z } from 'zod';

const Schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('production'),
  PORT: z.coerce.number().int().positive().default(__DEFAULT_PORT__),
  HOST: z.string().min(1).default('127.0.0.1'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace']).default('info'),

  PGHOST: z.string().min(1).default('127.0.0.1'),
  PGPORT: z.coerce.number().int().positive().default(5432),
  PGUSER: z.string().min(1),
  PGPASSWORD: z.string().min(1),
  PGDATABASE: z.string().min(1),
  PG_SCHEMA: z.string().min(1).default('__DB_SCHEMA__'),
  PG_POOL_MAX: z.coerce.number().int().positive().default(20),
  PG_POOL_MIN: z.coerce.number().int().nonnegative().default(2),
  PG_IDLE_TIMEOUT_MS: z.coerce.number().int().nonnegative().default(30_000),
  PG_CONN_TIMEOUT_MS: z.coerce.number().int().positive().default(5_000),
  PG_STATEMENT_TIMEOUT_MS: z.coerce.number().int().nonnegative().default(10_000),
});

const parsed = Schema.safeParse(process.env);
if (!parsed.success) {
  // eslint-disable-next-line no-console
  console.error('[config] invalid environment:', parsed.error.flatten().fieldErrors);
  process.exit(1);
}
export const config = parsed.data;
export type AppConfig = typeof config;
