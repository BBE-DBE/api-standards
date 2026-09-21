# BBE-STD-004 quickstart

Everything below runs offline, from a checkout, with the standard library
only. No API key is needed to see the gate work.

```sh
STD=standards/BBE-STD-004
PORT=$STD/tools/bbe-port/bbe-port
```

## 1. Lint the manifests

```sh
$PORT validate $STD/examples/manifests/*.json
```

Then watch it fail closed on a manifest that carries a key:

```sh
$PORT validate $STD/examples/manifests/invalid/001-inline-secret.json   # exit 1
```

## 2. Lint the corpus

```sh
$PORT corpus $STD/examples/tasks
```

The example corpus has 8 tasks and says so: below the 20-task floor for
conformance level P3. It is a demonstration, not a claim.

## 3. Ask what a switch would cost

```sh
$PORT swap --from $STD/examples/manifests/primary-saas.json \
           --to   $STD/examples/manifests/offline-selfhosted.json \
           --corpus $STD/examples/tasks
```

```
  capability lost:   tools, vision, prompt_cache
  context:           200000 -> 32768 (-167232)
  sovereignty.weights_portable: False -> True
  corpus impact:     2/8 tasks blocked (weight 5/20)
  VERDICT: incompatible        # exit 1
```

That is the whole point of the swap check: the move to own hardware buys
`weights_portable: true` — weights nobody can revoke — and costs tool use and
167k of context. Both halves are on the screen before anyone commits to it.

## 4. Run the gate

```sh
$PORT eval --manifest $STD/examples/manifests/offline-selfhosted.json \
           --corpus $STD/examples/tasks \
           --transport mock --fixture $STD/examples/fixtures/demo-responses.json \
           --policy $STD/examples/policy.json \
           --out /tmp/report.json
```

```
  results: 5 passed / 1 failed / 2 blocked
  score:   80.00% (floor 80%)
  VERDICT: QUALIFIED_DEGRADED  # exit 0
```

Blocked tasks are excluded from the denominator (§7.1) — a provider cannot
improve its score by being incapable. They are reported separately so the gap
stays visible.

## 5. Point it at a real endpoint

Any OpenAI-compatible server, hosted or self-hosted:

```sh
export LOCAL_LLM_BASE_URL=http://127.0.0.1:8000/v1
export LOCAL_LLM_TOKEN=dummy            # vLLM/llama.cpp accept any bearer
$PORT eval --manifest $STD/examples/manifests/offline-selfhosted.json \
           --corpus $STD/examples/tasks --transport openai_chat \
           --policy $STD/examples/policy.json
```

The env var names come from the manifest (`endpoint_env`, `credential_ref`);
the tool never holds a URL or a secret of its own.

## 6. CI

```sh
scripts/test-std-004.sh
```
