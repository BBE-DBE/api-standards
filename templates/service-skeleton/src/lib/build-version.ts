// Build-version stamp for /health and audit events.
import { existsSync, readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

function findRepoRoot(start: string): string {
  let dir = start;
  for (let i = 0; i < 6; i++) {
    if (existsSync(join(dir, 'package.json'))) return dir;
    const up = dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return start;
}
const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = findRepoRoot(here);

function readSemver(): string {
  try { return JSON.parse(readFileSync(join(repoRoot, 'package.json'), 'utf8')).version ?? '0.0.0'; }
  catch { return '0.0.0'; }
}

async function readGitSha(): Promise<string> {
  try {
    const mod = await import('./git-sha.js');
    if (typeof mod.GIT_SHA === 'string' && mod.GIT_SHA.length >= 7) return mod.GIT_SHA;
  } catch { /* fall through */ }
  if (process.env.GIT_SHA && process.env.GIT_SHA.length >= 7) return process.env.GIT_SHA.slice(0, 14);
  try {
    return execSync('git rev-parse --short=12 HEAD', { cwd: repoRoot, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
  } catch { return 'unknown'; }
}

export const buildSemver = readSemver();
export const buildSha = await readGitSha();
export const buildVersion = `${buildSemver}+${buildSha}`;
