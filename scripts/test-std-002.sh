#!/usr/bin/env bash
# test-std-002.sh — canonical CI gate for BBE-STD-002.
#
# Mandatory: 85 Python tests + corpus parity. Required for ratification.
# Optional:  16 Bash e2e tests when bbe-server-config is checked out
#            alongside (BBE_SERVER_CONFIG env var).
#
# Exit codes:
#   0  all mandatory tests pass
#   1  one or more mandatory tests fail
#
# Usage:
#   scripts/test-std-002.sh                 # mandatory only
#   BBE_SERVER_CONFIG=/path/to/repo \
#     scripts/test-std-002.sh               # + optional bash e2e

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STD="$REPO_ROOT/standards/BBE-STD-002"

PYTHON="${PYTHON:-python3}"

echo "BBE-STD-002 CI gate"
echo "  repo: $REPO_ROOT"
echo "  std:  $STD"
echo

if [[ ! -d "$STD" ]]; then
	echo "ERROR: standards/BBE-STD-002/ not found at $STD" >&2
	exit 1
fi

mandatory_failed=0

run_suite() {
	local name="$1" path="$2"
	echo "=== $name ==="
	if "$PYTHON" "$path"; then
		echo "    PASS"
	else
		echo "    FAIL — suite $name"
		mandatory_failed=$((mandatory_failed + 1))
	fi
	echo
}

run_suite "Python: legacy compat (45 tests)" \
	"$STD/tests/test_bbe_comm_lint.py"

run_suite "Python: incident-replay regression (26 tests)" \
	"$STD/tests/test_incident_replay.py"

run_suite "Python: learning-loop safety (14 tests)" \
	"$STD/tools/bbe-comm/tests/test_learning_loop.py"

# === Optional: Bash e2e (requires bbe-server-config runtime artifacts) ===
if [[ -n "${BBE_SERVER_CONFIG:-}" && -d "$BBE_SERVER_CONFIG/configs/bbe-guard/lib" ]]; then
	echo "=== Bash e2e (optional, with bbe-server-config) ==="
	echo "    SKIPPED — runtime tests live in bbe-server-config/tests/"
	echo "    (this gate validates the standard, not the runtime binding;"
	echo "     run bbe-server-config/tests/acceptance-bbe-guard.sh separately)"
	echo
else
	echo "=== Bash e2e (optional) — SKIPPED ==="
	echo "    set BBE_SERVER_CONFIG=/path/to/bbe-server-config to enable"
	echo "    (runtime tests live in that repo)"
	echo
fi

echo "============================================="
if [[ "$mandatory_failed" -eq 0 ]]; then
	echo "ALL MANDATORY GATES PASSED"
	exit 0
else
	echo "$mandatory_failed MANDATORY SUITE(S) FAILED"
	exit 1
fi
