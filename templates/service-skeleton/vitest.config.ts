import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['tests/unit/**/*.test.ts', 'tests/integration/**/*.test.ts'],
    environment: 'node',
    coverage: {
      provider: 'v8',
      include: [
        'src/lib/audit.ts',
        'src/lib/idempotency.ts',
        'src/lib/errors.ts',
      ],
      thresholds: { lines: 80, branches: 70, functions: 70, statements: 80 },
      reporter: ['text', 'json-summary'],
    },
    setupFiles: ['tests/setup.ts'],
  },
});
