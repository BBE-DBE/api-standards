// Library entrypoint. server.ts is the actual process entrypoint.
import Fastify, { type FastifyBaseLogger } from 'fastify';
import helmet from '@fastify/helmet';

import { config } from './config.js';
import { logger } from './lib/logger.js';
import { newUuid7 } from './lib/uuid7.js';
import { closeDb } from './db.js';
import { AppError } from './lib/errors.js';
import { registerHealth } from './routes/health.js';

const startedAt = Date.now();

export async function buildApp() {
  const app = Fastify({
    loggerInstance: logger as unknown as FastifyBaseLogger,
    genReqId: (req) => {
      const incoming = req.headers['x-request-id'];
      if (typeof incoming === 'string' && /^[0-9a-fA-F-]{8,}$/.test(incoming)) return incoming;
      return newUuid7();
    },
    requestIdHeader: 'x-request-id',
    requestIdLogLabel: 'request_id',
    bodyLimit: 2 * 1024 * 1024,
    keepAliveTimeout: 5_000,
  });

  app.addHook('onSend', async (req, reply) => { reply.header('x-request-id', req.id); });

  app.setErrorHandler((err, req, reply) => {
    if (err instanceof AppError) {
      reply.code(err.status);
      return err.toJSON();
    }
    if ((err as { statusCode?: number }).statusCode === 400) {
      reply.code(400);
      const e = err as { message?: string; validation?: unknown };
      return { error: { code: 'invalid_input', message: e.message ?? 'invalid input', details: e.validation ?? null } };
    }
    const stack = err instanceof Error ? err.stack : undefined;
    req.log.error({ err: String(err), stack }, 'unhandled error');
    reply.code(500);
    return { error: { code: 'internal', message: 'internal error' } };
  });

  await app.register(helmet, { global: true, contentSecurityPolicy: false });

  await registerHealth(app, { startedAt });

  return { app };
}

export async function startServer(): Promise<void> {
  const { app } = await buildApp();
  await app.listen({ host: config.HOST, port: config.PORT });
  logger.info({ host: config.HOST, port: config.PORT }, '__SERVICE_NAME__ listening');

  const shutdown = async (sig: string) => {
    logger.info({ sig }, 'shutting down');
    try { await app.close(); } catch (err) { logger.warn({ err: String(err) }, 'app.close failed'); }
    try { await closeDb(); }   catch (err) { logger.warn({ err: String(err) }, 'closeDb failed'); }
    process.exit(0);
  };
  process.on('SIGINT',  () => void shutdown('SIGINT'));
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
}
