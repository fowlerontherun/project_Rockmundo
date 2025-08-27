class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def Depends(dep):  # pragma: no cover - testing stub
    return dep


class Request:  # minimal request used in tests
    def __init__(self, headers: dict | None = None):
        self.headers = headers or {}


class status:  # pragma: no cover - constants for tests
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403


class APIRouter:
    def __init__(self, prefix: str = "", *args, **kwargs):
        self.routes = []
        self.prefix = prefix

    def post(self, path: str):
        def decorator(func):
            self.routes.append(("POST", self.prefix + path, func))
            return func
        return decorator

    def get(self, path: str):
        def decorator(func):
            self.routes.append(("GET", self.prefix + path, func))
            return func
        return decorator

    def delete(self, path: str):
        def decorator(func):
            self.routes.append(("DELETE", self.prefix + path, func))
            return func
        return decorator

    def put(self, path: str):
        def decorator(func):
            self.routes.append(("PUT", self.prefix + path, func))
            return func
        return decorator


class FastAPI:
    def __init__(self, *args, **kwargs):
        self.routers = []

    def add_middleware(self, *args, **kwargs):
        pass

    def on_event(self, event: str):
        def decorator(func):
            return func
        return decorator

    def include_router(self, router, prefix: str = "", tags: list | None = None):
        self.routers.append((router, prefix, tags))

    def get(self, path: str):
        def decorator(func):
            return func
        return decorator
