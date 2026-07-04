"""Supabase 클라이언트 — storycore-web과 동일 URL + anon key."""

from __future__ import annotations

from functools import lru_cache

from config.settings import SUPABASE_ANON_KEY, SUPABASE_URL, USE_SUPABASE


@lru_cache
def get_supabase_client():
    if not USE_SUPABASE:
        raise RuntimeError("Supabase가 설정되지 않았습니다.")

    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
