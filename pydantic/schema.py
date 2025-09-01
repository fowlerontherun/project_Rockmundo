"""Minimal stub of ``pydantic.schema`` for tests.

Only the callable names accessed by FastAPI in the test suite are
implemented and each returns an empty dictionary. This avoids pulling in
pydantic as a heavy dependency while satisfying imports.
"""

def schema(*args, **kwargs):
    return {}

def field_schema(*args, **kwargs):
    return {}

def get_model_name_map(*args, **kwargs):
    return {}

def model_process_schema(*args, **kwargs):
    return {}

def schema_of(*args, **kwargs):
    return {}

def get_flat_models_from_fields(*args, **kwargs):
    return set()

def get_annotation_from_field_info(*args, **kwargs):
    return None

__all__ = [
    "schema",
    "field_schema",
    "get_model_name_map",
    "model_process_schema",
    "schema_of",
    "get_flat_models_from_fields",
    "get_annotation_from_field_info",
]
