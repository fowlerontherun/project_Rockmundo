# File: backend/tests/services/test_discord_service.py

import pytest
from core.config import settings
from services import discord_service


def test_send_message_posts_content(monkeypatch):
    sent = {}

    class DummyRequests:
        RequestException = Exception

        def post(self, url, json, timeout):
            sent["url"] = url
            sent["json"] = json

            class Resp:
                def raise_for_status(self):
                    return None

            return Resp()

    monkeypatch.setattr(settings.auth, "discord_webhook_url", "https://example.com/webhook")
    monkeypatch.setattr(discord_service, "requests", DummyRequests())

    discord_service.send_message("hello world")

    assert sent["url"] == "https://example.com/webhook"
    assert sent["json"] == {"content": "hello world"}


def test_send_message_raises_on_error(monkeypatch):
    class DummyRequestsError(Exception):
        pass

    def fake_post(*args, **kwargs):
        raise DummyRequestsError("boom")

    class DummyRequests:
        RequestException = DummyRequestsError

        def post(self, *args, **kwargs):
            return fake_post(*args, **kwargs)

    monkeypatch.setattr(settings.auth, "discord_webhook_url", "https://example.com/webhook")
    monkeypatch.setattr(discord_service, "requests", DummyRequests())

    with pytest.raises(discord_service.DiscordServiceError):
        discord_service.send_message("fail")


def test_send_message_requires_url(monkeypatch):
    monkeypatch.setattr(settings.auth, "discord_webhook_url", "")
    with pytest.raises(discord_service.DiscordServiceError):
        discord_service.send_message("oops")
