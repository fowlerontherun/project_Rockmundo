class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class APIRouter:
    def __init__(self, *args, **kwargs):
        self.routes = []

    def post(self, path: str):
        def decorator(func):
            self.routes.append(("POST", path, func))
            return func
        return decorator

    def get(self, path: str):
        def decorator(func):
            self.routes.append(("GET", path, func))
            return func
        return decorator

    def delete(self, path: str):
        def decorator(func):
            self.routes.append(("DELETE", path, func))
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
