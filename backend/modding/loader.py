"""Simple plugin loader for game mods."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Dict, Iterable

from .interfaces import ModPlugin


class PluginLoader:
    """Loads and registers mod plugins.

    Plugins are expected to expose a module-level ``plugin`` object that
    implements :class:`ModPlugin`.
    """

    def __init__(self) -> None:
        self.plugins: Dict[str, ModPlugin] = {}

    # -----------------------------------------------------
    def register(self, plugin: ModPlugin) -> None:
        """Register a plugin instance and invoke its activate hook."""

        self.plugins[plugin.meta.name] = plugin
        # allow plugin to perform any setup
        plugin.activate()

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
