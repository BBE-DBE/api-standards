"""Live transport for any OpenAI-compatible /chat/completions endpoint.

Covers hosted vendors and self-hosted servers (vLLM, llama.cpp, Ollama's
compat layer) without a branch: the difference is a base URL.

Standard library only — urllib, not requests. Retries follow
protocols/provider-adapter-interface.md (250 ms base, x2, max 4 attempts).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from ..manifest import Manifest
from . import Completion, TransportError

RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4
BASE_BACKOFF_S = 0.25


class OpenAIChatTransport:
    name = "openai_chat"

    def __init__(self, timeout_s: float = 120.0, max_output_tokens: int | None = None):
        self._timeout_s = timeout_s
        self._max_output_tokens = max_output_tokens

    def _credentials(self, manifest: Manifest) -> str:
        ref = manifest.credential_ref
        if ref.startswith("env:"):
            var = ref[4:]
            value = os.environ.get(var)
            if not value:
                raise TransportError(f"credential env var {var} is unset (manifest {manifest.id})")
            return value
        # vault:// needs the secrets-vault client; out of scope for v0.1.0.
        raise TransportError(
            f"credential_ref {ref!r} not resolvable by this transport — "
            "v0.1.0 supports env: only (see protocols/secrets-vault.md)"
        )

    def _base_url(self, manifest: Manifest) -> str:
        var = manifest.endpoint_env
        if not var:
            raise TransportError(f"manifest {manifest.id} has no endpoint_env; cannot reach a live endpoint")
        value = os.environ.get(var)
        if not value:
            raise TransportError(f"endpoint env var {var} is unset (manifest {manifest.id})")
        return value.rstrip("/")

    def complete(self, manifest: Manifest, system: str | None, prompt: str, task_id: str) -> Completion:
        url = f"{self._base_url(manifest)}/chat/completions"
        token = self._credentials(manifest)

        messages = []
        if system and manifest.capability("system_prompt"):
            messages.append({"role": "system", "content": system})
        elif system:
            # Provider has no system role: fold it into the user turn rather
            # than dropping it, so the task still measures the same work.
            prompt = f"{system}\n\n{prompt}"
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": manifest.raw["model"],
            "messages": messages,
            "max_tokens": self._max_output_tokens or manifest.max_output_tokens,
            "temperature": 0,
        }
        body = json.dumps(payload).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            request = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )
            started = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                    decoded = json.loads(response.read().decode("utf-8"))
                latency_ms = int((time.monotonic() - started) * 1000)
                return self._parse(decoded, latency_ms)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in RETRY_STATUS or attempt == MAX_ATTEMPTS:
                    raise TransportError(f"{manifest.id} task {task_id}: HTTP {exc.code}") from exc
                self._sleep(exc, attempt)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == MAX_ATTEMPTS:
                    raise TransportError(f"{manifest.id} task {task_id}: {exc}") from exc
                time.sleep(BASE_BACKOFF_S * (2 ** (attempt - 1)))

        raise TransportError(f"{manifest.id} task {task_id}: exhausted retries ({last_error})")

    @staticmethod
    def _sleep(exc: urllib.error.HTTPError, attempt: int) -> None:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            try:
                time.sleep(min(float(retry_after), 30.0))
                return
            except ValueError:
                pass
        time.sleep(BASE_BACKOFF_S * (2 ** (attempt - 1)))

    @staticmethod
    def _parse(decoded: dict, latency_ms: int) -> Completion:
        try:
            text = decoded["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise TransportError(f"unexpected response shape: {exc}") from exc
        usage = decoded.get("usage") or {}
        return Completion(
            text=text,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
        )
