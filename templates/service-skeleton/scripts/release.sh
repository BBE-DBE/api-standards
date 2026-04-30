#!/bin/bash
# Reproducible-build release. Refuses unless tree is clean, on main,
# up-to-date, tag doesn't exist. Then bumps, builds, tests, commits, tags.
set -euo pipefail
cd "$(dirname "$0")/.."

VER="${1:-}"
if [[ -z "${VER}" ]]; then echo "usage: $0 <semver>" >&2; exit 2; fi
if ! [[ "${VER}" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.-]+)?$ ]]; then
  echo "[release] '${VER}' is not a valid semver" >&2; exit 2
fi

echo "[release] gate 1/4: clean tree"
if ! git diff-index --quiet HEAD -- 2>/dev/null || [[ -n "$(git ls-files -o --exclude-standard)" ]]; then
  echo "  ✗ tree dirty:"; git status --short; exit 3
fi
echo "[release] gate 2/4: on main"
[[ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]] || { echo "  ✗ not on main"; exit 3; }
echo "[release] gate 3/4: up-to-date with origin/main"
git fetch --tags --quiet origin main
[[ "$(git rev-parse @)" == "$(git rev-parse @{u})" ]] || { echo "  ✗ diverged"; exit 3; }
echo "[release] gate 4/4: tag v${VER} free"
git rev-parse "v${VER}" >/dev/null 2>&1 && { echo "  ✗ tag exists"; exit 3; } || true

echo "[release] bumping → ${VER}"
node -e "const fs=require('node:fs');const p=JSON.parse(fs.readFileSync('package.json','utf8'));p.version='${VER}';fs.writeFileSync('package.json',JSON.stringify(p,null,2)+'\n');"

echo "[release] pnpm build (GIT_SHA=$(git rev-parse --short=12 HEAD))"
GIT_SHA="$(git rev-parse --short=12 HEAD)" pnpm build
echo "[release] pnpm test"
pnpm test

if ! grep -q "^## \[${VER}\]" CHANGELOG.md; then
  echo "[release] WARNING: CHANGELOG.md missing [${VER}] section"
fi

git add package.json
git commit -m "release: v${VER}"
git tag -a "v${VER}" -m "v${VER}"

echo
echo "[release] tagged v${VER} locally. Push:"
echo "  git push --follow-tags origin main"
