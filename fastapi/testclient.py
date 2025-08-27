class Response:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class TestClient:
    def __init__(self, app):
        self.app = app

    def _handle(self, method, path, json=None):
        for router, prefix, _ in getattr(self.app, "routers", []):
            for m, rpath, func in getattr(router, "routes", []):
                if m == method and path == prefix + rpath:
                    import inspect
                    from pydantic import BaseModel

                    kwargs = {}
                    params = inspect.signature(func).parameters
                    if json is not None and params:
                        name, param = next(iter(params.items()))
                        model = param.annotation
                        if isinstance(model, type) and issubclass(model, BaseModel):
                            kwargs[name] = model(**json)
                        else:
                            kwargs[name] = json
                    result = func(**kwargs)
                    return Response(200, result)
        raise NotImplementedError("Route not found")

    def post(self, path, json=None):
        return self._handle("POST", path, json=json)

    def get(self, path, json=None):
        return self._handle("GET", path, json=json)
