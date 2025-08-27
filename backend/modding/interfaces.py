from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass
class PluginMeta:
    """Basic metadata describing a plugin."""

    name: str
    version: str
    author: str | None = None


class ModPlugin(Protocol):
    """Simple protocol every mod plugin should implement."""

    meta: PluginMeta

    def activate(self) -> None:
        """Called once when the plugin is registered."""
        ...
