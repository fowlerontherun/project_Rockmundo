# File: backend/tests/test_exception_handlers.py
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from core.errors import AppError
from core.exception_handlers import register_exception_handlers

def make_app():
    app = FastAPI()
    register_exception_handlers(app)

    class ItemIn(BaseModel):
        name: str = Field(..., min_length=2)

    @app.get("/boom-app")
    def boom_app():
        raise AppError("Nope", code="APP_OOPS", http_status=418)

    @app.get("/boom-http")
    def boom_http():
        raise HTTPException(status_code=404, detail="Not here")

    @app.get("/boom-uncaught")
    def boom_uncaught():
        raise RuntimeError("hidden internals")

    @app.post("/validate")
    def validate(item: ItemIn):
        return {"ok": True, "name": item.name}

    return app

def test_app_error_payload():
    app = make_app()
    client = TestClient(app)
    r = client.get("/boom-app")
    assert r.status_code == 418
    assert r.json() == {"code": "APP_OOPS", "message": "Nope"}

def test_http_exception_normalized():
    app = make_app()
    client = TestClient(app)
    r = client.get("/boom-http")
    assert r.status_code == 404
    assert r.json()["code"] == "HTTP_ERROR"

def test_uncaught_mapped_to_500():
    app = make_app()
    client = TestClient(app)
    r = client.get("/boom-uncaught")
    assert r.status_code == 500
    assert r.json()["code"] == "INTERNAL_SERVER_ERROR"

def test_validation_error_shape():
    app = make_app()
    client = TestClient(app)
    r = client.post("/validate", json={"name": "x"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert isinstance(body["errors"], list) and body["errors"]
