from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.locale import LocaleMiddleware
from utils.i18n import _
from routes.auth_routes import router as auth_router


app = FastAPI()
app.add_middleware(LocaleMiddleware)

@app.get("/")
def root():
    return {"message": _("Welcome to RockMundo API")}

app.include_router(auth_router)

client = TestClient(app)


def test_default_locale_fallback():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Welcome to RockMundo API"


def test_spanish_locale_selection():
    resp = client.get("/", headers={"Accept-Language": "es"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Bienvenido a RockMundo API"


def test_error_translation():
    resp = client.post(
        "/auth/login", data={"username": "bad", "password": "bad"}, headers={"Accept-Language": "es"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciales inválidas"
