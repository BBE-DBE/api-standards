# Changelog — BBE-STD-004

## [0.1.0] - 2026-09-21 — DRAFT

Initial draft of **Model Provider Portability**. Answers one operational
question with a measured number instead of a belief: if the current model
provider disappears, how fast are we running again and how much quality do we
lose?

### Added
- `BBE-STD-004.md` — spec (§1–§10): purpose, conformance levels P0–P4, the
  `ModelProviderAdapter` surface, golden-corpus format, swap check, scoring and
  verdict rules, RTO-model / QLO reporting obligation.
- `schema/model-provider-manifest.schema.json` — capability descriptor per
  provider/model pair. Carries credential *references*, never credentials.
- `schema/eval-task.schema.json`, `schema/portability-report.schema.json`.
- `tools/bbe-port/` — reference CLI (`validate`, `corpus`, `swap`, `eval`,
  `report`). Python 3.11+, standard library only: the api-standards CI
  environment has no third-party packages, and a gate that cannot run is
  worthless.
- Transports: `mock` (deterministic replay, what CI uses) and `openai_chat`
  (any OpenAI-compatible endpoint — hosted vendors and self-hosted
  vLLM/llama.cpp alike).
- `examples/` — 3 valid manifests, 5 invalid ones, an 8-task golden corpus,
  a response fixture and a `policy.json` carrying the agreed score floor.
- `tests/` — 50 tests across 3 suites, all offline.
- `docs/adr/0001-sibling-surface-not-extension.md`, `docs/quickstart.md`.

### Design decisions worth restating
- **Blocked ≠ failed.** A task whose `requires` capability the provider lacks
  is excluded from the score denominator. A provider must not be able to raise
  its score by being less capable.
- **Transport errors are exit code 2, never a quality result.** A broken
  fixture or an unreachable endpoint means the measurement did not happen.
- **No model-as-judge on the blocking path.** Checks are mechanical or the task
  does not belong in the gate.
- **Manifests fail closed on anything resembling a key** (BBE-PORT-004).

### Not done (see §10)
- Streaming is in the surface but not exercised by the gate (D1).
- Cost is recorded, deliberately not part of the verdict (D2).
- Audit-store binding waits on BBE-STD-003 (D4).
- Ratification needs a service at P3 with a stored report and an operator
  mandate.
