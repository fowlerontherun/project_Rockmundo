import os
import boto3
import pytest
from moto import mock_aws
from backend.storage.s3 import S3Storage

@mock_aws
def test_s3_roundtrip(monkeypatch, tmp_path):
    region = "eu-west-2"
    bucket = "test-bucket"
    # set dummy creds
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "y")

    s3 = boto3.client("s3", region_name=region)
    s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region})

    store = S3Storage(bucket=bucket, region=region, endpoint_url=None, force_path_style=True)

    obj = store.upload_bytes(b"hello", "k/hello.txt", content_type="text/plain")
    assert obj.key == "k/hello.txt"
    assert obj.size == 5
    assert obj.url.endswith("/k/hello.txt")

    # open_stream
    with store.open_stream("k/hello.txt") as f:
        assert f.read() == b"hello"

    # download_to_file
    dest = tmp_path / "out.txt"
    store.download_to_file("k/hello.txt", str(dest))
    assert dest.read_text() == "hello"

    # delete & exists
    store.delete("k/hello.txt")
    assert store.exists("k/hello.txt") is False
