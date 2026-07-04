"""DB 초기화."""

from __future__ import annotations

from pathlib import Path

from api.repository import init_database as _init_database
from config.settings import BASE_DIR, IS_VERCEL, UPLOAD_DIR, USE_SUPABASE


def init_database() -> None:
    if IS_VERCEL and not USE_SUPABASE:
        import logging

        logging.getLogger(__name__).warning(
            "Vercel: Supabase 환경 변수가 없습니다. "
            "VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, SESSION_SECRET_KEY 를 설정하세요."
        )
        return
    if not IS_VERCEL:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not USE_SUPABASE:
        (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
    _init_database()
