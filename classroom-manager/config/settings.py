"""classroom-manager 설정 — storycore-web과 동일 (URL + anon key)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
IS_VERCEL = os.getenv("VERCEL") == "1"

load_dotenv(BASE_DIR / ".env")
load_dotenv(REPO_ROOT / "storycore-web" / ".env", override=False)

# storycore-web과 동일한 환경변수 이름
SUPABASE_URL = (
    os.getenv("SUPABASE_URL")
    or os.getenv("VITE_SUPABASE_URL")
    or ""
).strip().rstrip("/")

SUPABASE_ANON_KEY = (
    os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("VITE_SUPABASE_ANON_KEY")
    or ""
).strip()

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def _project_ref_from_url(url: str) -> str:
    if not url:
        return ""
    match = re.search(r"https?://([^.]+)\.supabase\.co", url)
    return match.group(1) if match else ""


SUPABASE_PROJECT_REF = (
    os.getenv("SUPABASE_PROJECT_REF", "").strip()
    or _project_ref_from_url(SUPABASE_URL)
)

# 테스트 시 SQLite 강제
if os.getenv("CLASSROOM_TEST_SQLITE") == "1":
    SUPABASE_URL = ""
    SUPABASE_ANON_KEY = ""

# URL + anon key 가 있으면 Supabase API 사용 (storycore-web 방식)
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# SQLite fallback (Supabase 미설정 시)
SQLITE_DATABASE_URL = f"sqlite:///{BASE_DIR / 'data' / 'classroom.db'}"

SESSION_SECRET_KEY = os.getenv(
    "SESSION_SECRET_KEY",
    "classroom-mvp-session-secret-change-in-production",
)

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_URL_PREFIX = "/uploads"
CHILD_PHOTOS_BUCKET = os.getenv("CHILD_PHOTOS_BUCKET", "child-photos")

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
