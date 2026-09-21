#!/usr/bin/env bash
# test-std-004.sh — canonical CI gate for BBE-STD-004 (Model Provider Portability).
#
# Mandatory: 3 Python suites (manifest validation, corpus + checks, offline
#            gate semantics) plus a golden-corpus round trip through the CLI.
#            All of it runs offline: no credentials, no network, no
#            third-party packages. A portability gate that needs a live vendor
#            to be tested is a gate that stops being run.
#
# Optional:  live-transport conformance against a real endpoint, enabled by
#            BBE_PORT_LIVE_MANIFEST. Never part of the mandatory set — see
#            BBE-STD-004 §10 D5.
#
# Exit codes:
#   0  all mandatory gates pass
#   1  one or more mandatory gates fail
#
# Usage:
#   scripts/test-std-004.sh
#   BBE_PORT_LIVE_MANIFEST=/path/to/manifest.json scripts/test-std-004.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STD="$REPO_ROOT/standards/BBE-STD-004"
TOOL="$STD/tools/bbe-port"

PYTHON="${PYTHON:-python3}"

echo "BBE-STD-004 CI gate"
echo "  repo: $REPO_ROOT"
echo "  std:  $STD"
echo

if [[ ! -d "$STD" ]]; then
	echo "ERROR: standards/BBE-STD-004/ not found at $STD" >&2
	exit 1
fi

mandatory_failed=0

run_suite() {
	local name="$1" path="$2"
	echo "=== $name ==="
	if (cd "$STD/tests" && "$PYTHON" "$path"); then
		echo "    PASS"
	else
		echo "    FAIL — suite $name"
		mandatory_failed=$((mandatory_failed + 1))
	fi
	echo
}

run_step() {
	local name="$1"
	shift
	echo "=== $name ==="
	if "$@" >/dev/null; then
		echo "    PASS"
	else
		echo "    FAIL — $name"
		mandatory_failed=$((mandatory_failed + 1))
	fi
	echo
}

run_step_expect() {
	# Some gate outcomes are failures by design (an incompatible swap must
	# exit 1). Asserting the code keeps the contract honest in both directions.
	local name="$1" expected="$2"
	shift 2
	echo "=== $name (expect exit $expected) ==="
	set +e
	"$@" >/dev/null 2>&1
	local actual=$?
	set -e
	if [[ "$actual" -eq "$expected" ]]; then
		echo "    PASS"
	else
		echo "    FAIL — $name exited $actual, expected $expected"
		mandatory_failed=$((mandatory_failed + 1))
	fi
	echo
}

run_suite "Python: manifest validation (13 tests)"   "test_manifest.py"
run_suite "Python: corpus + checks (16 tests)"       "test_corpus.py"
run_suite "Python: offline gate semantics (21 tests)" "test_gate_offline.py"

run_step "CLI: golden manifests validate" \
	"$PYTHON" "$TOOL/bbe-port" validate "$STD"/examples/manifests/*.json

run_step "CLI: golden corpus lints" \
	"$PYTHON" "$TOOL/bbe-port" corpus "$STD/examples/tasks"

run_step_expect "CLI: invalid manifest corpus is rejected" 1 \
	"$PYTHON" "$TOOL/bbe-port" validate "$STD"/examples/manifests/invalid/001-inline-secret.json

run_step "CLI: gate run against the primary manifest" \
	"$PYTHON" "$TOOL/bbe-port" eval \
	--manifest "$STD/examples/manifests/primary-saas.json" \
	--corpus "$STD/examples/tasks" \
	--transport mock --fixture "$STD/examples/fixtures/demo-responses.json" \
	--policy "$STD/examples/policy.json"

run_step_expect "CLI: capability-losing swap is blocked" 1 \
	"$PYTHON" "$TOOL/bbe-port" swap \
	--from "$STD/examples/manifests/primary-saas.json" \
	--to "$STD/examples/manifests/offline-selfhosted.json" \
	--corpus "$STD/examples/tasks"

# === Optional: live transport (requires credentials + network) ===
if [[ -n "${BBE_PORT_LIVE_MANIFEST:-}" ]]; then
	echo "=== Live transport (optional) ==="
	if "$PYTHON" "$TOOL/bbe-port" eval \
		--manifest "$BBE_PORT_LIVE_MANIFEST" \
		--corpus "${BBE_PORT_LIVE_CORPUS:-$STD/examples/tasks}" \
		--transport openai_chat \
		--policy "$STD/examples/policy.json"; then
		echo "    PASS (advisory — not counted toward the mandatory gate)"
	else
		echo "    FAIL (advisory — not counted toward the mandatory gate)"
	fi
	echo
else
	echo "=== Live transport (optional) — SKIPPED ==="
	echo "    set BBE_PORT_LIVE_MANIFEST=/path/to/manifest.json to enable"
	echo "    (needs the endpoint + credential env vars named in that manifest)"
	echo
fi

echo "============================================="
if [[ "$mandatory_failed" -eq 0 ]]; then
	echo "ALL MANDATORY GATES PASSED"
	exit 0
else
	echo "$mandatory_failed MANDATORY GATE(S) FAILED"
	exit 1
fi
