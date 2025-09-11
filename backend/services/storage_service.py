from __future__ import annotations

import os
import time
import uuid
from typing import Dict, Any

from fastapi import UploadFile

from backend.core.config import settings
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

    backend_name = settings.storage.backend.lower()

    if backend_name == "local":
        root = settings.storage.local_root
        public = settings.storage.public_base_url
        _backend = LocalStorage(root=root, public_base_url=public or None)
    elif backend_name == "s3":
        if S3Storage is None:
            raise RuntimeError("S3 backend selected but boto3 is not available.")
        bucket = settings.storage.s3_bucket
        region = settings.storage.s3_region
        endpoint = settings.storage.s3_endpoint_url or None
        force_path = settings.storage.s3_force_path_style
        if not bucket:
            raise RuntimeError("S3_BUCKET must be set when STORAGE_BACKEND=s3")
        _backend = S3Storage(
            bucket=bucket,
            region=region,
            endpoint_url=endpoint,
            force_path_style=force_path,
        )
    else:
        raise RuntimeError(f"Unknown STORAGE_BACKEND: {backend_name}")

    return _backend


async def save_attachment(file: UploadFile) -> Dict[str, Any]:
    """Persist an uploaded file and return metadata.

    The file is stored using the configured storage backend under a unique key.
    Returns a dictionary with the original filename and public URL.
    """

    backend = get_storage_backend()
    data = await file.read()
    filename = os.path.basename(file.filename)
    key = f"mail/attachments/{int(time.time())}_{uuid.uuid4().hex}_{filename}"
    obj = backend.upload_bytes(data, key, content_type=file.content_type)
    return {"filename": file.filename, "url": obj.url}
