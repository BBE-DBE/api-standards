// Process entrypoint. PM2 fork-mode passes argv[1]=ProcessContainerFork.js,
// so we always call startServer() unconditionally.
import { writeSync } from 'node:fs';

process.on('uncaughtException', (err) => {
  writeSync(2, `[fatal:uncaught] ${err instanceof Error ? err.stack ?? err.message : String(err)}\n`);
  process.exit(1);
});
process.on('unhandledRejection', (reason) => {
  writeSync(2, `[fatal:unhandled-rejection] ${reason instanceof Error ? reason.stack ?? reason.message : String(reason)}\n`);
  process.exit(1);
});

import { startServer } from './app.js';

startServer().catch((err) => {
  writeSync(2, `[server] fatal: ${err instanceof Error ? err.stack ?? err.message : String(err)}\n`);
  process.exit(1);
});
