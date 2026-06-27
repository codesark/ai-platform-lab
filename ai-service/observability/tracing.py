"""Optional Langfuse tracing.

`observe` is a decorator that records a function as a Langfuse span when Langfuse
is configured (both keys set), and is a transparent pass-through otherwise — so
the service and tests run unchanged without any tracing backend or keys.

Credentials are taken from our settings (which load from .env) and passed to the
Langfuse client explicitly, rather than relying on the SDK to read process env
vars — so tracing works the same whether config came from .env or real env vars.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from config import get_settings

_settings = get_settings()
_enabled = bool(_settings.langfuse_public_key and _settings.langfuse_secret_key)

if _enabled:
    try:
        from langfuse import Langfuse

        # Configures the default client that @observe uses.
        Langfuse(
            public_key=_settings.langfuse_public_key,
            secret_key=_settings.langfuse_secret_key,
            host=_settings.langfuse_host,
        )
    except Exception:
        _enabled = False


def observe(*, name: str | None = None) -> Callable[[Any], Any]:
    if not _enabled:
        return lambda fn: fn
    from langfuse import observe as _lf_observe

    return _lf_observe(name=name)
