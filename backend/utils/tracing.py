"""Minimal tracing utilities.

Tries to use OpenTelemetry if available; otherwise provides a stub tracer
that records spans as no-ops. This keeps the application code agnostic to
whether the optional dependency is installed.
"""

from __future__ import annotations

try:  # pragma: no cover - exercised indirectly
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    def setup_tracing() -> None:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)

    def get_tracer(name: str):
        return trace.get_tracer(name)
except Exception:  # pragma: no cover - fallback for missing package
    class _Span:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Tracer:
        def start_as_current_span(self, name: str) -> _Span:
            return _Span()

    def setup_tracing() -> None:  # pragma: no cover - trivial
        pass

    def get_tracer(name: str) -> _Tracer:  # pragma: no cover - trivial
        return _Tracer()
