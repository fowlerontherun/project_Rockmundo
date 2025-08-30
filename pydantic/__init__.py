class BaseModel:
    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self):
        return self.__dict__.copy()


def Field(default=None, *, default_factory=None, **kwargs):
    """Return a default value similar to pydantic.Field."""
    if default_factory is not None:
        return default_factory()
    return default
