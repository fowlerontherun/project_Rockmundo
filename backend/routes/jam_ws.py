"""Expose WebSocket endpoints for jam sessions.

This module simply re-exports the realtime jam gateway router so it can be
mounted alongside other route modules.
"""
from backend.realtime.jam_gateway import router

__all__ = ["router"]
