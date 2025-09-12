import types
import sys


def load_character_module(monkeypatch):
    class DummyRouter:
        def __init__(self, *args, **kwargs):
            pass
        def get(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def put(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def post(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def delete(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    monkeypatch.setattr("fastapi.APIRouter", DummyRouter)

    from backend.auth import dependencies as deps

    def fake_require_permission(_roles):
        def _dep():
            return True

        return _dep

    deps.require_permission = fake_require_permission
    deps.get_current_user_id = lambda: 1

    sys.modules.pop("routes.character", None)
    import routes.character as character_routes

    return character_routes


class DummyAvatar:
    def __init__(self, networking=20):
        self.id = 1
        self.networking = networking


class DummyAvatarService:
    def __init__(self):
        self.avatar = DummyAvatar()

    def get_avatar_by_character_id(self, character_id: int):
        return self.avatar

    def update_avatar(self, avatar_id: int, data):
        if getattr(data, "networking", None) is not None:
            self.avatar.networking = data.networking
        return self.avatar


def test_networking_routes(monkeypatch):
    character_routes = load_character_module(monkeypatch)
    svc = DummyAvatarService()
    monkeypatch.setattr(character_routes, "avatar_service", svc)
    result = character_routes.get_networking(1, user_id=1)
    assert result == {"networking": 20}
    character_routes.set_networking(1, character_routes.NetworkingUpdate(networking=90), user_id=1)
    result = character_routes.get_networking(1, user_id=1)
    assert result == {"networking": 90}
