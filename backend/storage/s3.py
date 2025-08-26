from __future__ import annotations
import os, io
from typing import Optional, BinaryIO
import boto3
from botocore.client import Config
from .base import StorageBackend, StorageObject

class S3Storage(StorageBackend):
    def __init__(self, bucket: str, region: str, endpoint_url: Optional[str] = None, force_path_style: bool = True):
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url or None
        s3_cfg = Config(signature_version="s3v4", s3={"addressing_style": "path" if force_path_style else "auto"})
        self.client = boto3.client("s3", region_name=region, endpoint_url=self.endpoint_url, config=s3_cfg)

    def upload_file(self, src_path: str, dest_key: str, content_type: Optional[str] = None) -> StorageObject:
        extra = {"ContentType": content_type} if content_type else None
        self.client.upload_file(src_path, self.bucket, dest_key, ExtraArgs=extra)
        head = self.client.head_object(Bucket=self.bucket, Key=dest_key)
        return StorageObject(key=dest_key, url=self.url_for(dest_key), size=head["ContentLength"], etag=head["ETag"].strip('"'), content_type=head.get("ContentType"))

    def upload_bytes(self, data: bytes, dest_key: str, content_type: Optional[str] = None) -> StorageObject:
        extra = {"ContentType": content_type} if content_type else None
        resp = self.client.put_object(Bucket=self.bucket, Key=dest_key, Body=data, **(extra or {}))
        head = self.client.head_object(Bucket=self.bucket, Key=dest_key)
        return StorageObject(key=dest_key, url=self.url_for(dest_key), size=head["ContentLength"], etag=head["ETag"].strip('"'), content_type=head.get("ContentType"))

    def open_stream(self, key: str) -> BinaryIO:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return io.BytesIO(obj["Body"].read())

    def download_to_file(self, key: str, dest_path: str) -> None:
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        with open(dest_path, "wb") as f:
            self.client.download_fileobj(self.bucket, key, f)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.NoSuchKey:
            return False
        except Exception:
            return False

    def url_for(self, key: str) -> str:
        if self.endpoint_url:
            # For custom endpoints (e.g., MinIO), synthesize a URL
            base = self.endpoint_url.rstrip('/')
            return f"{base}/{self.bucket}/{key.lstrip('/')}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key.lstrip('/')}"
