from __future__ import annotations
import os
from typing import Optional
from backend.storage.local import LocalStorage
try:
    # boto3 is optional unless using S3
    from backend.storage.s3 import S3Storage  # type: ignore
except Exception:  # pragma: no cover
    S3Storage = None  # type: ignore

_backend = None

def get_storage_backend():
    global _backend
    if _backend is not None:
        return _backend

    backend_name = os.getenv("STORAGE_BACKEND", "local").lower()

    if backend_name == "local":
        root = os.getenv("STORAGE_LOCAL_ROOT", "./var/storage")
        public = os.getenv("STORAGE_PUBLIC_BASE_URL", "")
        _backend = LocalStorage(root=root, public_base_url=public or None)
    elif backend_name == "s3":
        if S3Storage is None:
            raise RuntimeError("S3 backend selected but boto3 is not available.")
        bucket = os.getenv("S3_BUCKET")
        region = os.getenv("S3_REGION", "eu-west-2")
        endpoint = os.getenv("S3_ENDPOINT_URL", "") or None
        force_path = os.getenv("S3_FORCE_PATH_STYLE", "true").lower() in ("1", "true", "yes")
        if not bucket:
            raise RuntimeError("S3_BUCKET must be set when STORAGE_BACKEND=s3")
        _backend = S3Storage(bucket=bucket, region=region, endpoint_url=endpoint, force_path_style=force_path)
    else:
        raise RuntimeError(f"Unknown STORAGE_BACKEND: {backend_name}")

    return _backend
