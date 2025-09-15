import os, tempfile
from storage.local import LocalStorage

def test_local_roundtrip(tmp_path):
    root = tmp_path / "store"
    store = LocalStorage(root=str(root), public_base_url="http://localhost/static")
    # upload bytes
    obj = store.upload_bytes(b"hello world", "a/b/hello.txt", content_type="text/plain")
    assert obj.key == "a/b/hello.txt"
    assert obj.size == 11
    assert store.exists("a/b/hello.txt")
    assert obj.url.endswith("/a/b/hello.txt")

    # stream open
    with store.open_stream("a/b/hello.txt") as f:
        assert f.read() == b"hello world"

    # download
    dest = tmp_path / "dl.txt"
    store.download_to_file("a/b/hello.txt", str(dest))
    assert dest.read_text() == "hello world"

    # delete
    store.delete("a/b/hello.txt")
    assert not store.exists("a/b/hello.txt")
