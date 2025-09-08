import asyncio

from fastapi import Request

from backend.routes import admin_media_moderation_routes as routes


def _setup(monkeypatch):
    """Patch authentication dependencies for isolated testing."""

    async def fake_current_user(req: Request):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(routes, "require_permission", fake_require_permission)


def test_queue_and_review(monkeypatch):
    _setup(monkeypatch)

    # ensure clean state
    routes.skin_service._submissions.clear()
    routes.skin_service._reviews.clear()

    submission = routes.skin_service.submit_skin("Test", {"mesh": "m"}, creator_id=2)

    req = Request({"type": "http"})

    queue = asyncio.run(routes.list_submission_queue(req))
    assert any(item["id"] == submission.id for item in queue)

    asyncio.run(routes.review_submission(submission.id, "approve", req))
    assert routes.skin_service.list_submission_queue() == []

