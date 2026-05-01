// Prometheus metrics — wiring stub.
//
// This file is **inert by default**: app.ts does not register it. To
// enable, uncomment the `registerMetrics(app)` line in app.ts. The
// dependency `prom-client` is already pinned in package.json.
//
// Once registered:
//   * GET /metrics returns the default node + process metrics (CPU,
//     event loop, GC, file descriptors) in Prometheus exposition format.
//   * Service-specific metrics go below — counter/histogram/gauge
//     factories named by feature (e.g. authVerifyDurationMs).
//
// Convention:
//   * metric names: snake_case, prefixed with the **db-schema name**
//     (NOT the kebab-case service name — Prometheus metric names match
//     `[a-zA-Z_:][a-zA-Z0-9_:]*` and reject hyphens). For "ip-pool-api"
//     the schema is `ip_pool` → metric prefix is `ip_pool_*`.
//   * histogram buckets: tuned per metric — never the prom-client default.
//   * NO PII in label values. Cardinality cap: < 100 unique labels per
//     metric (prom-client raises a warning past that).

import type { FastifyInstance } from 'fastify';
import { Registry, collectDefaultMetrics, Histogram, Counter } from 'prom-client';

export const registry = new Registry();
collectDefaultMetrics({ register: registry });

// ----------------------------------------------------------------------
// Service-specific metrics — replace examples with real ones.
// Keep them grouped by feature; one block per route family.
// ----------------------------------------------------------------------

export const httpRequestDurationMs = new Histogram({
  name: '__DB_SCHEMA___http_request_duration_ms',
  help: 'HTTP request duration in milliseconds, by route + status_code.',
  labelNames: ['method', 'route', 'status_code'] as const,
  // 0.5..2000 ms in ~roughly-log buckets — most requests fall under 50 ms.
  buckets: [0.5, 1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2000],
  registers: [registry],
});

export const httpRequestErrorsTotal = new Counter({
  name: '__DB_SCHEMA___http_request_errors_total',
  help: 'Count of 4xx/5xx responses, by error code.',
  labelNames: ['code'] as const,
  registers: [registry],
});

// ----------------------------------------------------------------------
// Plugin entry — call from app.ts buildApp().
// ----------------------------------------------------------------------

export async function registerMetrics(app: FastifyInstance): Promise<void> {
  // Per-request observation. Fastify guarantees onResponse runs even on
  // throw paths after preHandler.
  app.addHook('onResponse', async (req, reply) => {
    const route = req.routeOptions?.url ?? req.url;
    const labels = {
      method: req.method,
      route,
      status_code: String(reply.statusCode),
    };
    httpRequestDurationMs.observe(labels, reply.elapsedTime);
    if (reply.statusCode >= 400) {
      const code = (reply as unknown as { _appErrorCode?: string })._appErrorCode ?? 'unknown';
      httpRequestErrorsTotal.inc({ code });
    }
  });

  app.get('/metrics', async (_req, reply) => {
    reply.header('content-type', registry.contentType);
    return registry.metrics();
  });
}
