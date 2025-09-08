"""WebSocket connection metrics and helpers."""
from __future__ import annotations

import asyncio
from typing import Dict

from backend.utils.metrics import Counter, Gauge

TOPIC = "metrics"

CONNECTIONS_TOTAL = Counter(
    "websocket_connections_total", "Total WebSocket connections established"
)
CONNECTIONS_ACTIVE = Gauge(
    "websocket_connections_active", "Current active WebSocket connections"
)
MESSAGES_TOTAL = Counter(
    "websocket_messages_total", "Total WebSocket messages received"
)

def _snapshot() -> Dict[str, int]:
    return {
        "connections": int(CONNECTIONS_ACTIVE._values.get((), 0)),
        "messages": int(MESSAGES_TOTAL._values.get((), 0)),
    }

async def _broadcast() -> None:
    try:
        from backend.realtime.gateway import hub
    except Exception:  # pragma: no cover - hub not available
        return
    await hub.publish(TOPIC, _snapshot())

async def track_connect() -> None:
    CONNECTIONS_TOTAL.labels().inc()
    CONNECTIONS_ACTIVE.labels().inc()
    await _broadcast()

async def track_disconnect() -> None:
    CONNECTIONS_ACTIVE.labels().dec()
    await _broadcast()

async def track_message() -> None:
    MESSAGES_TOTAL.labels().inc()
    await _broadcast()
