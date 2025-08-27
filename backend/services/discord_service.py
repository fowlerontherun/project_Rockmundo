# File: backend/services/discord_service.py

from core.config import settings

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore[assignment]


class DiscordServiceError(Exception):
    pass


def send_message(content: str) -> None:
    """Send a message to a Discord webhook."""
    url = getattr(settings, "DISCORD_WEBHOOK_URL", "")
    if not url:
        raise DiscordServiceError("DISCORD_WEBHOOK_URL is not configured")
    if requests is None:
        raise DiscordServiceError("requests library is not installed")
    try:
        resp = requests.post(url, json={"content": content}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors handled
        raise DiscordServiceError("Failed to send message to Discord") from exc
