"""도메인 엔티티 (Supabase / SQLite 공통)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CodeTable:
    id: int
    group_code: str
    code: str
    code_name: str
    sort_order: int = 0
    use_yn: str = "Y"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class SchoolClass:
    id: int
    teacher_user_id: int
    class_name: str
    currency_code: str = "BEAN"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Child:
    id: int
    class_id: int
    child_name: str
    company_name: str | None = None
    photo_path: str | None = None
    photo_url: str | None = None
    deleted_yn: str = "N"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class StudentWallet:
    id: int
    child_id: int
    currency_code: str
    balance: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PointTransaction:
    id: int
    class_id: int
    child_id: int
    wallet_id: int
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    currency_code: str
    memo: str | None
    created_by_user_id: int
    created_at: datetime | None = None
    child_name: str | None = None
    teacher_name: str | None = None
