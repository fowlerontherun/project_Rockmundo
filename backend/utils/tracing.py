"""
Minimal tracing utilities.

Tries to use OpenTelemetry if available; otherwise provides a stub tracer
that records spans as no-ops. This keeps the application code agnostic to
whether the optional dependency is installed.
"""

from __future__ import annotations

import os

try:  # pragma: no cover - exercised indirectly
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )

    def setup_tracing(exporter: str = "console") -> None:
        provider = TracerProvider()

        chosen = exporter.lower()
        processor: SimpleSpanProcessor | BatchSpanProcessor

        if chosen == "otlp":  # pragma: no cover - optional dependency
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter,
                )

                processor = BatchSpanProcessor(OTLPSpanExporter())
            except Exception:  # pragma: no cover - fallback
                processor = SimpleSpanProcessor(ConsoleSpanExporter())
        elif chosen == "jaeger":  # pragma: no cover - optional dependency
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter

                jaeger_host = os.getenv("JAEGER_HOST", "localhost")
                jaeger_port = int(os.getenv("JAEGER_PORT", "6831"))
                exporter = JaegerExporter(
                    agent_host_name=jaeger_host, agent_port=jaeger_port
                )
                processor = BatchSpanProcessor(exporter)
            except Exception:  # pragma: no cover - fallback
                processor = SimpleSpanProcessor(ConsoleSpanExporter())
        else:
            processor = SimpleSpanProcessor(ConsoleSpanExporter())

        provider.add_span_processor(processor)
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

    def setup_tracing(exporter: str = "console") -> None:  # pragma: no cover - trivial
        pass

    def get_tracer(name: str) -> _Tracer:  # pragma: no cover - trivial
        return _Tracer()
