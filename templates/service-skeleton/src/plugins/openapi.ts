// OpenAPI 3.1 — wiring stub.
//
// This file is **inert by default**: app.ts does not register it. To
// enable, uncomment the `registerOpenApi(app)` line in app.ts. The
// dependencies `@fastify/swagger`, `@fastify/swagger-ui`, and
// `fastify-type-provider-zod` are already pinned in package.json.
//
// Once registered:
//   * GET /openapi.yaml returns the spec, generated from zod schemas
//     attached to routes via fastify-type-provider-zod.
//   * GET /docs serves the swagger-ui static UI.
//
// Conventions (api-standards/templates/openapi-skeleton.yaml):
//   * Bearer token auth — bearerFormat = service token-prefix
//     (e.g. "iplk" for ip-pool-api).
//   * /v1/* paths only.
//   * Idempotency-Key header parameter on every POST/PUT/PATCH/DELETE.
//   * Errors share the schema from protocols/error-codes.yaml.

import type { FastifyInstance } from 'fastify';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import { jsonSchemaTransform, type ZodTypeProvider } from 'fastify-type-provider-zod';

export async function registerOpenApi(app: FastifyInstance): Promise<void> {
  // Cast: zod-type-provider takes over schema parsing for routes that
  // declare their schema with zod. Routes that don't are unaffected.
  app.withTypeProvider<ZodTypeProvider>();

  await app.register(swagger, {
    openapi: {
      info: {
        title: '__SERVICE_NAME__',
        description: '__SERVICE_DESC__',
        version: '0.1.0',
      },
      servers: [{ url: 'http://127.0.0.1:__DEFAULT_PORT__', description: 'loopback' }],
      components: {
        securitySchemes: {
          bearer: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'token',
          },
        },
      },
      tags: [
        { name: 'health', description: 'liveness / readiness / full report' },
      ],
    },
    transform: jsonSchemaTransform,
  });

  await app.register(swaggerUi, {
    routePrefix: '/docs',
    uiConfig: { docExpansion: 'list', deepLinking: false },
    staticCSP: true,
  });

  // Plain YAML alongside swagger-ui's JSON.
  app.get('/openapi.yaml', async (_req, reply) => {
    reply.header('content-type', 'application/yaml');
    const spec = app.swagger({ yaml: true });
    return spec;
  });
}
