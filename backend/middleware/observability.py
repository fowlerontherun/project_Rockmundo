"""Request observability middleware.

This middleware records simple request metrics and tracing spans.  Metrics are
exported via the lightweight helpers in :mod:`backend.utils.metrics` and spans
are emitted through :mod:`backend.utils.tracing`.
"""

from __future__ import annotations

import time
from typing import Any

from backend.utils.metrics import Counter
from backend.utils.tracing import get_tracer


# Metrics ---------------------------------------------------------------------

# Total number of processed HTTP requests.
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ("method", "path", "status")
)

# Cumulative request latency in milliseconds.
REQUEST_LATENCY_MS = Counter(
    "http_request_duration_ms_total",
    "Total request latency in milliseconds",
    ("method", "path", "status"),
)


# Tracer instance reused for all requests.
_tracer = get_tracer(__name__)


class ObservabilityMiddleware:
    """Emit tracing spans and update request metrics."""

    async def dispatch(self, request: Any, call_next):  # pragma: no cover - thin wrapper
        method = getattr(request, "method", "GET")
        url = getattr(request, "url", None)
        path = getattr(url, "path", None) if url else getattr(request, "path", "")
        span_name = f"{method} {path}"

        start = time.perf_counter()
        with _tracer.start_as_current_span(span_name):
            try:
                response = await call_next(request)
                status = getattr(response, "status_code", 500)
            except Exception:
                # Record failures as 500 responses and re-raise.
                status = 500
                raise
            finally:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                labels = (method, path, str(status))
                REQUEST_COUNT.labels(*labels).inc()
                REQUEST_LATENCY_MS.labels(*labels).inc(elapsed_ms)

        return response


__all__ = ["ObservabilityMiddleware"]

