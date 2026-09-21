# ADR-0001 — A sibling adapter surface, not an extension of the infra adapter

**Status:** Accepted (v0.1.0 DRAFT)
**Context date:** 2026-09-21

## Context

`protocols/provider-adapter-interface.md` already defines a provider adapter
for infrastructure vendors (Netcup, Hetzner). PRINCIPLES.md §8 (Reuse-First /
Lookup-before-Build) requires us to consume an existing contract rather than
build an adjacent one, so the default answer was to extend it with model
providers.

## Decision

Define a **sibling** surface (`ModelProviderAdapter`) in BBE-STD-004 that
inherits the parent's cross-cutting obligations verbatim, instead of extending
the parent interface.

## Why

1. **The shapes do not match.** The parent is CRUD over resources
   (`list/get/create/update/delete` + `TResource`). A model call is a single
   non-idempotent request/response over free text with token accounting. Forcing
   `complete()` into `create()` would make every implementation lie about what
   it is doing.
2. **Idempotency semantics differ.** The parent's retry rule is built on
   idempotent methods and `Idempotency-Key`. A completion is not idempotent even
   with identical input; retrying it is safe only because the caller discards
   the earlier attempt, not because the provider deduplicates.
3. **Capability negotiation has no analogue.** Model providers differ in what
   they can do at all (tools, JSON mode, context window). The parent has no
   concept of a declared capability set, and adding one would burden two
   existing consumers with a field that means nothing to them.
4. **Reuse is preserved where it is real.** Retries, rate limits, redaction,
   error mapping and audit are the genuinely shared concerns, and BBE-STD-004 §4.1
   inherits them by reference rather than by copy. That is the part §8 was
   protecting; the method signatures were not.

## Consequences

- Two adapter documents exist. Each names the other; the model document does
  not restate the shared obligations, so they cannot drift apart by edit.
- A future third category (e.g. payment providers) should ask the same
  question rather than assume either answer.
- If the two surfaces converge later, the merge point is the cross-cutting
  section, which is already single-sourced.

## Rejected alternatives

- **Extend `ProviderAdapter<TConfig, TResource>` with optional model methods.**
  Rejected: makes `TResource` meaningless for model adapters and pushes
  `not_supported_by_provider` onto every existing consumer's surface.
- **A generic `capabilities` map on the parent interface.** Rejected for now as
  speculative generality: one consumer category needs it. Revisit at the third.
