class TestClient:
    def __init__(self, app):
        self.app = app

    # Minimal stub that raises if used. Our tests do not rely on it.
    def get(self, *args, **kwargs):
        raise NotImplementedError("TestClient stub does not support HTTP requests")

    def post(self, *args, **kwargs):
        raise NotImplementedError("TestClient stub does not support HTTP requests")
