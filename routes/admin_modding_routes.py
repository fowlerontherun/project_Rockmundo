from __future__ import annotations

from fastapi import APIRouter, HTTPException

from modding.loader import PluginLoader

router = APIRouter(prefix="/modding", tags=["AdminModding"])

# In-memory loader instance for managing plugins
plugin_loader = PluginLoader()


@router.get("/plugins")
def list_plugins() -> list[dict[str, str | bool | None]]:
    """Return metadata for all registered plugins."""

    return plugin_loader.list_plugins()


@router.post("/plugins/{name}/enable")
def enable_plugin(name: str) -> dict[str, str]:
    """Enable a plugin by name."""

    try:
        plugin_loader.enable(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "enabled"}


@router.post("/plugins/{name}/disable")
def disable_plugin(name: str) -> dict[str, str]:
    """Disable a plugin by name."""

    try:
        plugin_loader.disable(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "disabled"}
