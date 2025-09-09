"""Lightweight metrics helpers with Prometheus-style exposition."""

from __future__ import annotations

import threading
from typing import Dict, Iterable, List, Tuple, Union

_REGISTRY: Dict[str, Union["Counter", "Gauge", "Histogram"]] = {}


class Counter:
    """A very small counter implementation compatible with Prometheus."""

    def __init__(self, name: str, description: str, labelnames: Iterable[str] = ()):  # pragma: no cover - exercised indirectly
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

    def collect(self):  # pragma: no cover - trivial
        for labels, value in self._values.items():
            yield labels, value


class Gauge:
    """A gauge metric supporting increment, decrement and set operations."""

    def __init__(self, name: str, description: str, labelnames: Iterable[str] = ()):  # pragma: no cover - exercised indirectly
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames)
        self._values: Dict[Tuple[str, ...], float] = {}
        self._lock = threading.Lock()
        _REGISTRY[self.name] = self

    class _LabelGauge:
        def __init__(self, parent: "Gauge", key: Tuple[str, ...]):
            self._parent = parent
            self._key = key

        def inc(self, amount: float = 1) -> None:
            with self._parent._lock:
                self._parent._values[self._key] = self._parent._values.get(self._key, 0.0) + amount

        def dec(self, amount: float = 1) -> None:
            self.inc(-amount)

        def set(self, value: float) -> None:
            with self._parent._lock:
                self._parent._values[self._key] = value

    def labels(self, *labelvalues: str) -> "Gauge._LabelGauge":
        if len(labelvalues) != len(self.labelnames):
            raise ValueError("Incorrect label count")
        key = tuple(labelvalues)
        with self._lock:
            self._values.setdefault(key, 0.0)
        return Gauge._LabelGauge(self, key)

    def collect(self):  # pragma: no cover - trivial
        for labels, value in self._values.items():
            yield labels, value


class Histogram:
    """A simple histogram implementation compatible with Prometheus."""

    def __init__(
        self,
        name: str,
        description: str,
        buckets: Iterable[float],
        labelnames: Iterable[str] = (),
    ):  # pragma: no cover - exercised indirectly
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames)
        self.buckets: List[float] = sorted(buckets)
        if not self.buckets or self.buckets[-1] != float("inf"):
            self.buckets.append(float("inf"))
        self._values: Dict[Tuple[str, ...], Dict[str, Union[List[int], float, int]]] = {}
        self._lock = threading.Lock()
        _REGISTRY[self.name] = self

    class _LabelHistogram:
        def __init__(self, parent: "Histogram", key: Tuple[str, ...]):
            self._parent = parent
            self._key = key

        def observe(self, amount: float) -> None:
            with self._parent._lock:
                data = self._parent._values.setdefault(
                    self._key,
                    {"buckets": [0] * len(self._parent.buckets), "sum": 0.0, "count": 0},
                )
                for i, b in enumerate(self._parent.buckets):
                    if amount <= b:
                        data["buckets"][i] += 1
                data["sum"] += amount
                data["count"] += 1

    def labels(self, *labelvalues: str) -> "Histogram._LabelHistogram":
        if len(labelvalues) != len(self.labelnames):
            raise ValueError("Incorrect label count")
        key = tuple(labelvalues)
        with self._lock:
            self._values.setdefault(
                key, {"buckets": [0] * len(self.buckets), "sum": 0.0, "count": 0}
            )
        return Histogram._LabelHistogram(self, key)

    def collect(self):  # pragma: no cover - trivial
        for labels, value in self._values.items():
            yield labels, value


def generate_latest() -> bytes:
    lines = []
    for c in _REGISTRY.values():
        lines.append(f"# HELP {c.name} {c.description}")
        if isinstance(c, Counter):
            lines.append(f"# TYPE {c.name} counter")
            for labels, value in c.collect():
                if c.labelnames:
                    label_str = ",".join(f'{n}="{v}"' for n, v in zip(c.labelnames, labels))
                    lines.append(f"{c.name}{{{label_str}}} {value}")
                else:
                    lines.append(f"{c.name} {value}")
        elif isinstance(c, Gauge):
            lines.append(f"# TYPE {c.name} gauge")
            for labels, value in c.collect():
                if c.labelnames:
                    label_str = ",".join(f'{n}="{v}"' for n, v in zip(c.labelnames, labels))
                    lines.append(f"{c.name}{{{label_str}}} {value}")
                else:
                    lines.append(f"{c.name} {value}")
        elif isinstance(c, Histogram):
            lines.append(f"# TYPE {c.name} histogram")
            for labels, data in c.collect():
                base_labels = list(zip(c.labelnames, labels))
                for b, count in zip(c.buckets, data["buckets"]):
                    lbls = base_labels + [("le", "+Inf" if b == float("inf") else str(b))]
                    label_str = ",".join(f'{n}="{v}"' for n, v in lbls)
                    lines.append(f"{c.name}_bucket{{{label_str}}} {count}")
                if base_labels:
                    label_str = ",".join(f'{n}="{v}"' for n, v in base_labels)
                    lines.append(f"{c.name}_sum{{{label_str}}} {data['sum']}")
                    lines.append(f"{c.name}_count{{{label_str}}} {data['count']}")
                else:
                    lines.append(f"{c.name}_sum {data['sum']}")
                    lines.append(f"{c.name}_count {data['count']}")
    return ("\n".join(lines) + "\n").encode("utf-8")


CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
