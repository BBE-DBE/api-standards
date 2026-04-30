#!/bin/bash
# Skeleton smoke-test. Replace with service-specific assertions.
set -uo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then echo "[smoke] .env missing" >&2; exit 1; fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

BASE="http://${HOST:-127.0.0.1}:${PORT}"
ok=0; fail=0
pass() { ok=$((ok+1));   echo "  ✓ $*"; }
miss() { fail=$((fail+1)); echo "  ✗ $*"; }

echo "[smoke] step 1 — health"
curl -sf "${BASE}/health/live"  >/dev/null && pass "/health/live"  || miss "/health/live"
curl -sf "${BASE}/health/ready" >/dev/null && pass "/health/ready" || miss "/health/ready"
curl -sf "${BASE}/health"       >/dev/null && pass "/health"       || miss "/health"

# TODO: add service-specific assertions here.

echo
echo "[smoke] ok=${ok} fail=${fail}"
[[ $fail -eq 0 ]]
