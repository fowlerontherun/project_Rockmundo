"""Simple plugin loader for game mods."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import ModuleType
from typing import Dict, Iterable

from .interfaces import ModPlugin, PluginMeta


@dataclass
class PluginEntry:
    """Record stored in the loader's registry."""

    plugin: ModPlugin
    enabled: bool = False


class PluginLoader:
    """Loads and registers mod plugins.

    Plugins are expected to expose a module-level ``plugin`` object that
    implements :class:`ModPlugin`.
    """

    def __init__(self) -> None:
        # registry keyed by plugin name
        self.registry: Dict[str, PluginEntry] = {}

    # -----------------------------------------------------
    @property
    def plugins(self) -> Dict[str, ModPlugin]:
        """Compatibility mapping of names to plugin instances."""

        return {name: entry.plugin for name, entry in self.registry.items()}

    # -----------------------------------------------------
    def register(self, plugin: ModPlugin) -> None:
        """Register a plugin instance without activating it."""

        self.registry[plugin.meta.name] = PluginEntry(plugin=plugin, enabled=False)

    # -----------------------------------------------------
    def enable(self, name: str) -> None:
        """Activate a previously registered plugin."""

        entry = self.registry[name]
        if not entry.enabled:
            entry.plugin.activate()
            entry.enabled = True

    # -----------------------------------------------------
    def disable(self, name: str) -> None:
        """Deactivate a plugin if it provides a ``deactivate`` hook."""

        entry = self.registry[name]
        if entry.enabled:
            deactivate = getattr(entry.plugin, "deactivate", None)
            if callable(deactivate):
                deactivate()
            entry.enabled = False

    # -----------------------------------------------------
    def list_plugins(self) -> list[dict[str, str | bool | None]]:
        """Return metadata and state for all registered plugins."""

        plugins: list[dict[str, str | bool | None]] = []
        for entry in self.registry.values():
            meta: PluginMeta = entry.plugin.meta
            plugins.append(
                {
                    "name": meta.name,
                    "version": meta.version,
                    "author": meta.author,
                    "enabled": entry.enabled,
                }
            )
        return plugins

    # -----------------------------------------------------
    def load_from_module(self, module: ModuleType) -> None:
        """Load a plugin from a Python module."""

        plugin = getattr(module, "plugin", None)
        if plugin is None:  # pragma: no cover - defensive branch
            raise ValueError("Module does not define a 'plugin' attribute")
        self.register(plugin)

    # -----------------------------------------------------
    def load_from_modules(self, module_names: Iterable[str]) -> None:
        """Import modules by name and register contained plugins."""

        for name in module_names:
            mod = importlib.import_module(name)
            self.load_from_module(mod)
