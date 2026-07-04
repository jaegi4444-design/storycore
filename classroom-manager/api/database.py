"""SQLAlchemy 엔진 — SQLite fallback 전용."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import BASE_DIR, IS_VERCEL, SQLITE_DATABASE_URL, USE_SUPABASE

DATA_DIR = BASE_DIR / "data"
_use_sqlite = not USE_SUPABASE and not IS_VERCEL
if _use_sqlite:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

_engine_kwargs: dict = {"pool_pre_ping": True}
if _use_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLITE_DATABASE_URL, **_engine_kwargs) if _use_sqlite else None
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False) if engine else None


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """SQLite fallback용 (레거시). Supabase 모드에서는 사용하지 않음."""
    if SessionLocal is None:
        raise RuntimeError("Supabase 모드에서는 get_db()를 사용하지 않습니다.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
