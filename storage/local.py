from __future__ import annotations
import os, io, shutil
from typing import Optional, BinaryIO
from .base import StorageBackend, StorageObject

class LocalStorage(StorageBackend):
    def __init__(self, root: str, public_base_url: Optional[str] = None) -> None:
        self.root = os.path.abspath(root)
        self.public_base_url = public_base_url.rstrip('/') if public_base_url else None
        os.makedirs(self.root, exist_ok=True)

    def _full_path(self, key: str) -> str:
        safe_key = key.lstrip('/')
        return os.path.join(self.root, safe_key)

    def upload_file(self, src_path: str, dest_key: str, content_type: Optional[str] = None) -> StorageObject:
        dest_path = self._full_path(dest_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copyfile(src_path, dest_path)
        size = os.path.getsize(dest_path)
        return StorageObject(key=dest_key, url=self.url_for(dest_key), size=size, content_type=content_type)

    def upload_bytes(self, data: bytes, dest_key: str, content_type: Optional[str] = None) -> StorageObject:
        dest_path = self._full_path(dest_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        size = os.path.getsize(dest_path)
        return StorageObject(key=dest_key, url=self.url_for(dest_key), size=size, content_type=content_type)

    def open_stream(self, key: str) -> BinaryIO:
        return open(self._full_path(key), "rb")

    def download_to_file(self, key: str, dest_path: str) -> None:
        src_path = self._full_path(key)
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        shutil.copyfile(src_path, dest_path)

    def delete(self, key: str) -> None:
        path = self._full_path(key)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))

    def url_for(self, key: str) -> str:
        if self.public_base_url:
            return f"{self.public_base_url}/{key.lstrip('/')}"
        return f"file://{self._full_path(key)}"
