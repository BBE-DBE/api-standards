// PM2 process descriptor. Loads .env into the env: block so PM2 itself
// sees the variables (visible via `pm2 env <id>`).
const path = require('node:path');
const fs   = require('node:fs');

function readEnvFile(p) {
  if (!fs.existsSync(p)) return {};
  const out = {};
  for (const raw of fs.readFileSync(p, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq < 1) continue;
    let v = line.slice(eq + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    out[line.slice(0, eq).trim()] = v;
  }
  return out;
}

const envFromFile = readEnvFile(path.join(__dirname, '.env'));

module.exports = {
  apps: [{
    name: '__SERVICE_NAME__',
    cwd: __dirname,
    script: 'dist/src/server.js',
    exec_mode: 'fork',
    autorestart: true,
    max_memory_restart: '512M',
    kill_timeout: 5000,
    instances: 1,
    out_file:   './logs/pm2-out.log',
    error_file: './logs/pm2-err.log',
    merge_logs: true,
    time: false,
    env: {
      ...envFromFile,
      NODE_ENV: envFromFile.NODE_ENV ?? 'production',
      GIT_SHA: process.env.GIT_SHA ?? '',
    },
  }],
};
