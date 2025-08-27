"""Lightweight metrics helpers with Prometheus-style exposition."""

from __future__ import annotations

import threading
from typing import Dict, Iterable, Tuple

_REGISTRY: Dict[str, "Counter"] = {}


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


def generate_latest() -> bytes:
    lines = []
    for c in _REGISTRY.values():
        lines.append(f"# HELP {c.name} {c.description}")
        lines.append(f"# TYPE {c.name} counter")
        for labels, value in c.collect():
            if c.labelnames:
                label_str = ",".join(f'{n}="{v}"' for n, v in zip(c.labelnames, labels))
                lines.append(f"{c.name}{{{label_str}}} {value}")
            else:
                lines.append(f"{c.name} {value}")
    return "\n".join(lines).encode("utf-8")


CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
