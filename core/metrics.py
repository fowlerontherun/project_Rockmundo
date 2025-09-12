"""Tiny in-memory metrics helpers.

This module provides a very small subset of the Prometheus client API.  It is
used to track metrics without requiring an additional dependency.  Only what
is needed by the application is implemented.
"""

from __future__ import annotations

import threading
from typing import Dict, Iterable, Tuple

_REGISTRY: Dict[str, "Counter" | "Histogram"] = {}


class Counter:
    """A minimal counter implementation."""

    def __init__(self, name: str, description: str, labelnames: Iterable[str] = ()):  # pragma: no cover - simple container
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames)
        self._values: Dict[Tuple[str, ...], int] = {}
        self._lock = threading.Lock()
        _REGISTRY[self.name] = self

    class _LabelCounter:
        def __init__(self, parent: "Counter", key: Tuple[str, ...]):
            self._parent = parent
            self._key = key

        def inc(self, amount: int = 1) -> None:
            with self._parent._lock:
                self._parent._values[self._key] = self._parent._values.get(self._key, 0) + amount

    def labels(self, *labelvalues: str) -> "Counter._LabelCounter":
        if len(labelvalues) != len(self.labelnames):
            raise ValueError("Incorrect label count")
        key = tuple(labelvalues)
        with self._lock:
            self._values.setdefault(key, 0)
        return Counter._LabelCounter(self, key)

    def collect(self):  # pragma: no cover - trivial iteration
        for labels, value in self._values.items():
            yield labels, value

class Histogram:
    """A minimal histogram implementation."""

    def __init__(self, name: str, description: str, buckets: Iterable[float] = (), labelnames: Iterable[str] = ()):  # pragma: no cover - simple container
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames)
        self.buckets = sorted(buckets)
        self._values: Dict[Tuple[str, ...], Tuple[int, float]] = {}
        self._lock = threading.Lock()
        _REGISTRY[self.name] = self

    class _LabelHistogram:
        def __init__(self, parent: "Histogram", key: Tuple[str, ...]):
            self._parent = parent
            self._key = key

        def observe(self, amount: float) -> None:
            with self._parent._lock:
                count, total = self._parent._values.get(self._key, (0, 0.0))
                self._parent._values[self._key] = (count + 1, total + amount)

    def labels(self, *labelvalues: str) -> "Histogram._LabelHistogram":
        if len(labelvalues) != len(self.labelnames):
            raise ValueError("Incorrect label count")
        key = tuple(labelvalues)
        with self._lock:
            self._values.setdefault(key, (0, 0.0))
        return Histogram._LabelHistogram(self, key)

    def collect(self):  # pragma: no cover - trivial iteration
        for labels, (count, total) in self._values.items():
            yield labels, count, total

def generate_latest() -> bytes:
    """Render the current metrics in Prometheus text format."""

    lines = []
    for metric in _REGISTRY.values():
        if isinstance(metric, Counter):
            lines.append(f"# HELP {metric.name} {metric.description}")
            lines.append(f"# TYPE {metric.name} counter")
            for labels, value in metric.collect():
                if metric.labelnames:
                    label_str = ",".join(f'{n}="{v}"' for n, v in zip(metric.labelnames, labels))
                    lines.append(f"{metric.name}{{{label_str}}} {value}")
                else:
                    lines.append(f"{metric.name} {value}")
        elif isinstance(metric, Histogram):
            lines.append(f"# HELP {metric.name} {metric.description}")
            lines.append(f"# TYPE {metric.name} histogram")
            for labels, (count, total) in metric.collect():
                if metric.labelnames:
                    label_str = ",".join(f'{n}="{v}"' for n, v in zip(metric.labelnames, labels))
                    lines.append(f"{metric.name}_count{{{label_str}}} {count}")
                    lines.append(f"{metric.name}_sum{{{label_str}}} {total}")
                else:
                    lines.append(f"{metric.name}_count {count}")
                    lines.append(f"{metric.name}_sum {total}")
    return "\n".join(lines).encode("utf-8")


CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

__all__ = ["Counter", "Histogram", "generate_latest", "CONTENT_TYPE_LATEST"]
