// /health, /health/live, /health/ready. Schema:
// api-standards/protocols/health-response-schema.yaml.
import type { FastifyInstance } from 'fastify';
import { pingDb } from '../db.js';
import { buildVersion } from '../lib/build-version.js';

export async function registerHealth(app: FastifyInstance, deps: { startedAt: number }): Promise<void> {
  app.get('/health/live', async () => ({ status: 'ok' as const }));

  app.get('/health/ready', async (_req, reply) => {
    const db = await pingDb();
    if (!db.up) {
      reply.code(503);
      return { error: { code: 'not_ready', message: 'subsystem not ready', details: { db } } };
    }
    return { status: 'ok' as const };
  });

  app.get('/health', async () => {
    const db = await pingDb();
    return {
      status: db.up ? ('ok' as const) : ('down' as const),
      version: buildVersion,
      uptime_s: Math.floor((Date.now() - deps.startedAt) / 1000),
      db,
    };
  });
}
