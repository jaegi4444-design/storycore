"""Supabase Storage — anon key (storycore-web과 동일)."""

from __future__ import annotations

from api.supabase_client import get_supabase_client
from config.settings import CHILD_PHOTOS_BUCKET, USE_SUPABASE


def upload_child_photo_bytes(content: bytes, filename: str, content_type: str) -> str | None:
    if not USE_SUPABASE:
        return None

    client = get_supabase_client()
    path = f"uploads/{filename}"

    client.storage.from_(CHILD_PHOTOS_BUCKET).upload(
        path,
        content,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    return client.storage.from_(CHILD_PHOTOS_BUCKET).get_public_url(path)
