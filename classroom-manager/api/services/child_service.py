"""아이(학생) 서비스."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from api.entities import Child
from api.repository import (
    ChildAccessDeniedError,
    create_child,
    delete_child,
    get_child_for_teacher,
    get_children_by_class,
    update_child,
)
from api.services.supabase_storage import upload_child_photo_bytes
from config.settings import ALLOWED_IMAGE_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR, UPLOAD_URL_PREFIX

__all__ = [
    "ChildAccessDeniedError",
    "create_child",
    "delete_child",
    "get_child_for_teacher",
    "get_children_by_class",
    "update_child",
    "save_photo_upload",
    "resolve_photo_display",
]

_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


async def save_photo_upload(file: UploadFile | None) -> tuple[str | None, str | None]:
    if file is None or not file.filename:
        return None, None

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("jpg, jpeg, png, webp 파일만 업로드할 수 있습니다.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("파일 크기는 5MB 이하여야 합니다.")

    filename = f"{uuid.uuid4()}{suffix}"
    content_type = _CONTENT_TYPES.get(suffix, "application/octet-stream")

    public_url = upload_child_photo_bytes(content, filename, content_type)
    if public_url:
        return None, public_url

    dest = UPLOAD_DIR / filename
    dest.write_bytes(content)
    return f"{UPLOAD_URL_PREFIX}/{filename}", None


def resolve_photo_display(child: Child) -> str:
    if child.photo_path:
        return child.photo_path
    if child.photo_url:
        return child.photo_url
    return "/static/images/default-profile.svg"
