# mail_service.py content here
# === Storage-backed attachment functions (patched in) ===
import mimetypes, uuid, time
from backend.services.storage_service import get_storage_backend

def _guess_mime(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"

def _attachment_key(message_id: int, filename: str) -> str:
    safe = filename.replace('..','').replace('/', '_').replace('\\', '_')
    return f"mail/attachments/{message_id}/{int(time.time())}_{uuid.uuid4().hex}_{safe}"

def add_attachment_from_path(message_id: int, file_path: str, filename: str | None = None, content_type: str | None = None):
    storage = get_storage_backend()
    filename = filename or os.path.basename(file_path)
    content_type = content_type or _guess_mime(filename)
    key = _attachment_key(message_id, filename)
    obj = storage.upload_file(file_path, key, content_type=content_type)
    return {
        "message_id": message_id,
        "filename": filename,
        "mime": obj.content_type or content_type,
        "size": obj.size,
        "storage_url": obj.url,
        "storage_key": obj.key,
    }

def add_attachment_from_bytes(message_id: int, data: bytes, filename: str, content_type: str | None = None):
    storage = get_storage_backend()
    content_type = content_type or _guess_mime(filename)
    key = _attachment_key(message_id, filename)
    obj = storage.upload_bytes(data, key, content_type=content_type)
    return {
        "message_id": message_id,
        "filename": filename,
        "mime": obj.content_type or content_type,
        "size": obj.size,
        "storage_url": obj.url,
        "storage_key": obj.key,
    }

def delete_attachment(storage_key: str) -> None:
    storage = get_storage_backend()
    storage.delete(storage_key)
