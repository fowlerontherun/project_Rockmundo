from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.locale import LocaleMiddleware
from utils.i18n import _, ngettext_, pgettext_, SUPPORTED_LOCALES, DEFAULT_LOCALE
from routes.auth_routes import router as auth_router
from routes.locale_routes import router as locale_router


app = FastAPI()
app.add_middleware(LocaleMiddleware)


@app.get("/")
def root():
    return {"message": _("Welcome to RockMundo API")}


@app.get("/plural/{count}")
def plural(count: int):
    msg = ngettext_("%(num)d file", "%(num)d files", count) % {"num": count}
    return {"message": msg}


@app.get("/context/{kind}")
def ctx(kind: str):
    return {"message": pgettext_(kind, "Open")}


app.include_router(auth_router)
app.include_router(locale_router, prefix="/api")

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


def test_plural_and_context_translation():
    resp = client.get("/plural/2", headers={"Accept-Language": "es"})
    assert resp.json()["message"] == "2 archivos"
    resp = client.get("/context/status", headers={"Accept-Language": "es"})
    assert resp.json()["message"] == "Abierto"


def test_accept_language_fallback_order():
    resp = client.get("/", headers={"Accept-Language": "fr, es"})
    assert resp.json()["message"] == "Bienvenido a RockMundo API"


def test_supported_locales_endpoint():
    resp = client.get("/api/locales")
    assert resp.status_code == 200
    body = resp.json()
    assert DEFAULT_LOCALE == body["default"]
    assert set(SUPPORTED_LOCALES).issubset(set(body["locales"]))
