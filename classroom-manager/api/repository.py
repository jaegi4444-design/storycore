"""데이터 접근 — Supabase (URL+anon) 또는 SQLite."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.database import SessionLocal, engine
from api.entities import Child, CodeTable, SchoolClass, User
from api.models import Child as ChildModel
from api.models import CodeTable as CodeTableModel
from api.models import SchoolClass as SchoolClassModel
from api.models import User as UserModel
from api.supabase_client import get_supabase_client
from config.settings import USE_SUPABASE


class ClassAlreadyExistsError(Exception):
    pass


class InvalidCurrencyError(Exception):
    pass


class ChildAccessDeniedError(Exception):
    pass


logger = logging.getLogger(__name__)


def _is_missing_table_error(exc: Exception) -> bool:
    return "PGRST205" in str(exc) or "Could not find the table" in str(exc)


# --- row mappers ---


def _user_from_row(row: dict[str, Any]) -> User:
    return User(id=row["id"], name=row["name"])


def _code_from_row(row: dict[str, Any]) -> CodeTable:
    return CodeTable(
        id=row["id"],
        group_code=row["group_code"],
        code=row["code"],
        code_name=row["code_name"],
        sort_order=row.get("sort_order", 0),
        use_yn=row.get("use_yn", "Y"),
    )


def _class_from_row(row: dict[str, Any]) -> SchoolClass:
    currency_code = row.get("currency_code", "BEAN")
    currency_name = row.get("currency_name")
    if not currency_name:
        currency_name = get_currency_name(currency_code)
    return SchoolClass(
        id=row["id"],
        teacher_user_id=row["teacher_user_id"],
        class_name=row["class_name"],
        currency_code=currency_code,
        currency_name=currency_name,
    )


def _child_from_row(row: dict[str, Any]) -> Child:
    return Child(
        id=row["id"],
        class_id=row["class_id"],
        child_name=row["child_name"],
        company_name=row.get("company_name"),
        photo_path=row.get("photo_path"),
        photo_url=row.get("photo_url"),
        deleted_yn=row.get("deleted_yn", "N"),
    )


def _user_from_orm(obj: UserModel) -> User:
    return User(id=obj.id, name=obj.name)


def _code_from_orm(obj: CodeTableModel) -> CodeTable:
    return CodeTable(
        id=obj.id,
        group_code=obj.group_code,
        code=obj.code,
        code_name=obj.code_name,
        sort_order=obj.sort_order,
        use_yn=obj.use_yn,
    )


def _class_from_orm(obj: SchoolClassModel) -> SchoolClass:
    return SchoolClass(
        id=obj.id,
        teacher_user_id=obj.teacher_user_id,
        class_name=obj.class_name,
        currency_code=obj.currency_code,
        currency_name=obj.currency_name,
    )


def _child_from_orm(obj: ChildModel) -> Child:
    return Child(
        id=obj.id,
        class_id=obj.class_id,
        child_name=obj.child_name,
        company_name=obj.company_name,
        photo_path=obj.photo_path,
        photo_url=obj.photo_url,
        deleted_yn=obj.deleted_yn,
    )


# --- public API ---


def init_database() -> None:
    if USE_SUPABASE:
        try:
            seed_currency_codes()
            from api.wallet_repository import backfill_wallets_for_active_children

            backfill_wallets_for_active_children()
        except Exception as exc:
            if _is_missing_table_error(exc):
                logger.warning(
                    "Supabase 테이블이 없습니다. "
                    "storycore-web/supabase/migrations/003_classroom_manager.sql 을 실행하세요."
                )
            else:
                raise
        return

    from api.database import Base

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_schema()
    seed_currency_codes()
    from api.wallet_repository import backfill_wallets_for_active_children

    backfill_wallets_for_active_children()


def _migrate_sqlite_schema() -> None:
    if USE_SUPABASE or engine is None:
        return

    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "children" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("children")}
    if "company_name" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE children ADD COLUMN company_name VARCHAR(100)"))
    if "deleted_yn" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE children ADD COLUMN deleted_yn VARCHAR(1) NOT NULL DEFAULT 'N'")
            )

    if "classes" not in inspector.get_table_names():
        return

    class_columns = {col["name"] for col in inspector.get_columns("classes")}
    if "currency_name" not in class_columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE classes ADD COLUMN currency_name VARCHAR(100) NOT NULL DEFAULT '콩'")
            )


def seed_currency_codes() -> None:
    if USE_SUPABASE:
        client = get_supabase_client()
        try:
            existing = (
                client.table("code_table")
                .select("id")
                .eq("group_code", "CURRENCY")
                .eq("code", "BEAN")
                .limit(1)
                .execute()
            )
        except Exception as exc:
            if _is_missing_table_error(exc):
                raise
            raise
        if existing.data:
            return
        client.table("code_table").insert(
            {
                "group_code": "CURRENCY",
                "code": "BEAN",
                "code_name": "콩",
                "sort_order": 1,
                "use_yn": "Y",
            }
        ).execute()
        return

    db = SessionLocal()
    try:
        exists = db.scalar(
            select(CodeTableModel.id).where(
                CodeTableModel.group_code == "CURRENCY",
                CodeTableModel.code == "BEAN",
            )
        )
        if exists:
            return
        db.add(
            CodeTableModel(
                group_code="CURRENCY",
                code="BEAN",
                code_name="콩",
                sort_order=1,
                use_yn="Y",
            )
        )
        db.commit()
    finally:
        db.close()


def find_or_create_user_by_name(name: str) -> User:
    trimmed = name.strip()
    if not trimmed:
        raise ValueError("이름을 입력해 주세요.")

    if USE_SUPABASE:
        client = get_supabase_client()
        found = client.table("users").select("*").eq("name", trimmed).limit(1).execute()
        if found.data:
            return _user_from_row(found.data[0])
        created = client.table("users").insert({"name": trimmed}).execute()
        return _user_from_row(created.data[0])

    db = SessionLocal()
    try:
        user = db.scalar(select(UserModel).where(UserModel.name == trimmed))
        if user:
            return _user_from_orm(user)
        user = UserModel(name=trimmed)
        db.add(user)
        db.commit()
        db.refresh(user)
        return _user_from_orm(user)
    finally:
        db.close()


def get_user_by_id(user_id: int) -> User | None:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = client.table("users").select("*").eq("id", user_id).limit(1).execute()
        return _user_from_row(result.data[0]) if result.data else None

    db = SessionLocal()
    try:
        user = db.get(UserModel, user_id)
        return _user_from_orm(user) if user else None
    finally:
        db.close()


def get_class_by_teacher(teacher_user_id: int) -> SchoolClass | None:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("classes")
            .select("*")
            .eq("teacher_user_id", teacher_user_id)
            .limit(1)
            .execute()
        )
        return _class_from_row(result.data[0]) if result.data else None

    db = SessionLocal()
    try:
        obj = db.scalar(
            select(SchoolClassModel).where(
                SchoolClassModel.teacher_user_id == teacher_user_id
            )
        )
        return _class_from_orm(obj) if obj else None
    finally:
        db.close()


def _normalize_currency_name(value: str) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        raise ValueError("화폐 단위를 입력해 주세요.")
    if len(trimmed) > 20:
        raise ValueError("화폐 단위는 20자 이내로 입력해 주세요.")
    return trimmed


def _is_missing_currency_name_column(exc: Exception) -> bool:
    text = str(exc)
    return "currency_name" in text or "42703" in text


def _class_currency_code(class_id: int) -> str:
    return f"CLS_{class_id}"


def _upsert_class_currency_label(class_id: int, currency_name: str) -> str:
    class_code = _class_currency_code(class_id)
    client = get_supabase_client()
    client.table("code_table").upsert(
        {
            "group_code": "CURRENCY",
            "code": class_code,
            "code_name": currency_name,
            "sort_order": class_id,
            "use_yn": "Y",
        },
        on_conflict="group_code,code",
    ).execute()
    return class_code


def _migrate_wallets_currency(class_id: int, old_code: str, new_code: str) -> None:
    if old_code == new_code:
        return

    client = get_supabase_client()
    children = (
        client.table("children").select("id").eq("class_id", class_id).execute()
    )
    for child in children.data or []:
        client.table("student_wallets").update({"currency_code": new_code}).eq(
            "child_id", child["id"]
        ).eq("currency_code", old_code).execute()


def _apply_class_currency_fallback(
    school_class: SchoolClass, currency_name: str
) -> SchoolClass:
    client = get_supabase_client()
    class_code = _upsert_class_currency_label(school_class.id, currency_name)
    old_code = school_class.currency_code

    if old_code != class_code:
        result = (
            client.table("classes")
            .update({"currency_code": class_code})
            .eq("id", school_class.id)
            .select()
            .execute()
        )
        if not result.data:
            raise ValueError("화폐 단위를 저장하지 못했습니다.")
        _migrate_wallets_currency(school_class.id, old_code, class_code)
        updated = _class_from_row(result.data[0])
        updated.currency_name = currency_name
        return updated

    return SchoolClass(
        id=school_class.id,
        teacher_user_id=school_class.teacher_user_id,
        class_name=school_class.class_name,
        currency_code=class_code,
        currency_name=currency_name,
    )


def create_class(teacher: User, class_name: str, currency_name: str = "콩") -> SchoolClass:
    if get_class_by_teacher(teacher.id):
        raise ClassAlreadyExistsError("이미 반이 존재합니다.")

    trimmed_name = class_name.strip()
    if not trimmed_name:
        raise ValueError("반 이름을 입력해 주세요.")
    normalized_currency = _normalize_currency_name(currency_name)

    if USE_SUPABASE:
        client = get_supabase_client()
        try:
            result = (
                client.table("classes")
                .insert(
                    {
                        "teacher_user_id": teacher.id,
                        "class_name": trimmed_name,
                        "currency_code": "CUSTOM",
                        "currency_name": normalized_currency,
                    }
                )
                .select()
                .execute()
            )
        except Exception as exc:
            if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
                raise ClassAlreadyExistsError("이미 반이 존재합니다.") from exc
            if _is_missing_currency_name_column(exc):
                result = (
                    client.table("classes")
                    .insert(
                        {
                            "teacher_user_id": teacher.id,
                            "class_name": trimmed_name,
                            "currency_code": "BEAN",
                        }
                    )
                    .select()
                    .execute()
                )
                school_class = _class_from_row(result.data[0])
                return _apply_class_currency_fallback(school_class, normalized_currency)
            raise
        return _class_from_row(result.data[0])

    db = SessionLocal()
    try:
        obj = SchoolClassModel(
            teacher_user_id=teacher.id,
            class_name=trimmed_name,
            currency_code="CUSTOM",
            currency_name=normalized_currency,
        )
        db.add(obj)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ClassAlreadyExistsError("이미 반이 존재합니다.") from None
        db.refresh(obj)
        return _class_from_orm(obj)
    finally:
        db.close()


def update_class_name(school_class: SchoolClass, class_name: str) -> SchoolClass:
    trimmed_name = class_name.strip()
    if not trimmed_name:
        raise ValueError("반 이름을 입력해 주세요.")

    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("classes")
            .update({"class_name": trimmed_name})
            .eq("id", school_class.id)
            .execute()
        )
        return _class_from_row(result.data[0])

    db = SessionLocal()
    try:
        obj = db.get(SchoolClassModel, school_class.id)
        if obj is None:
            raise ValueError("반을 찾을 수 없습니다.")
        obj.class_name = trimmed_name
        db.commit()
        db.refresh(obj)
        return _class_from_orm(obj)
    finally:
        db.close()


def update_class_currency_name(school_class: SchoolClass, currency_name: str) -> SchoolClass:
    normalized_currency = _normalize_currency_name(currency_name)

    if USE_SUPABASE:
        client = get_supabase_client()
        try:
            result = (
                client.table("classes")
                .update({"currency_name": normalized_currency})
                .eq("id", school_class.id)
                .select()
                .execute()
            )
            if not result.data:
                raise ValueError("화폐 단위를 저장하지 못했습니다.")
            return _class_from_row(result.data[0])
        except ValueError:
            raise
        except Exception as exc:
            if _is_missing_currency_name_column(exc):
                return _apply_class_currency_fallback(school_class, normalized_currency)
            raise ValueError("화폐 단위 저장 중 오류가 발생했습니다.") from exc

    db = SessionLocal()
    try:
        obj = db.get(SchoolClassModel, school_class.id)
        if obj is None:
            raise ValueError("반을 찾을 수 없습니다.")
        obj.currency_name = normalized_currency
        db.commit()
        db.refresh(obj)
        return _class_from_orm(obj)
    finally:
        db.close()


def verify_class_owner(school_class: SchoolClass, user: User) -> bool:
    return school_class.teacher_user_id == user.id


def get_active_currencies() -> list[CodeTable]:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("code_table")
            .select("*")
            .eq("group_code", "CURRENCY")
            .eq("use_yn", "Y")
            .order("sort_order")
            .order("id")
            .execute()
        )
        return [_code_from_row(row) for row in result.data]

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(CodeTableModel)
            .where(CodeTableModel.group_code == "CURRENCY", CodeTableModel.use_yn == "Y")
            .order_by(CodeTableModel.sort_order, CodeTableModel.id)
        ).all()
        return [_code_from_orm(row) for row in rows]
    finally:
        db.close()


def get_currency_name(code: str) -> str:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("code_table")
            .select("code_name")
            .eq("group_code", "CURRENCY")
            .eq("code", code)
            .limit(1)
            .execute()
        )
        return result.data[0]["code_name"] if result.data else code

    db = SessionLocal()
    try:
        row = db.scalar(
            select(CodeTableModel).where(
                CodeTableModel.group_code == "CURRENCY",
                CodeTableModel.code == code,
            )
        )
        return row.code_name if row else code
    finally:
        db.close()


def is_valid_currency_code(code: str) -> bool:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("code_table")
            .select("id")
            .eq("group_code", "CURRENCY")
            .eq("code", code)
            .eq("use_yn", "Y")
            .limit(1)
            .execute()
        )
        return bool(result.data)

    db = SessionLocal()
    try:
        row = db.scalar(
            select(CodeTableModel).where(
                CodeTableModel.group_code == "CURRENCY",
                CodeTableModel.code == code,
                CodeTableModel.use_yn == "Y",
            )
        )
        return row is not None
    finally:
        db.close()


def get_children_by_class(class_id: int) -> list[Child]:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("children")
            .select("*")
            .eq("class_id", class_id)
            .eq("deleted_yn", "N")
            .order("id")
            .execute()
        )
        return [_child_from_row(row) for row in result.data]

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(ChildModel)
            .where(ChildModel.class_id == class_id, ChildModel.deleted_yn == "N")
            .order_by(ChildModel.id)
        ).all()
        return [_child_from_orm(row) for row in rows]
    finally:
        db.close()


def get_child_by_id(child_id: int) -> Child | None:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("children")
            .select("*")
            .eq("id", child_id)
            .eq("deleted_yn", "N")
            .limit(1)
            .execute()
        )
        return _child_from_row(result.data[0]) if result.data else None

    db = SessionLocal()
    try:
        obj = db.get(ChildModel, child_id)
        if obj is None or obj.deleted_yn != "N":
            return None
        return _child_from_orm(obj)
    finally:
        db.close()


def verify_child_belongs_to_teacher(child: Child, teacher: User) -> bool:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("classes")
            .select("teacher_user_id")
            .eq("id", child.class_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return False
        return result.data[0]["teacher_user_id"] == teacher.id

    db = SessionLocal()
    try:
        school_class = db.get(SchoolClassModel, child.class_id)
        if school_class is None:
            return False
        return school_class.teacher_user_id == teacher.id
    finally:
        db.close()


def get_child_for_teacher(child_id: int, teacher: User) -> Child:
    child = get_child_by_id(child_id)
    if child is None or not verify_child_belongs_to_teacher(child, teacher):
        raise ChildAccessDeniedError("접근 권한이 없습니다.")
    return child


def _normalize_company_name(company_name: str | None) -> str | None:
    if company_name is None:
        return None
    trimmed = company_name.strip()
    return trimmed if trimmed else None


def create_child(
    school_class: SchoolClass,
    child_name: str,
    photo_path: str | None = None,
    photo_url: str | None = None,
    company_name: str | None = None,
) -> Child:
    trimmed_name = child_name.strip()
    if not trimmed_name:
        raise ValueError("아이 이름을 입력해 주세요.")

    url_trimmed = photo_url.strip() if photo_url else None
    if url_trimmed == "":
        url_trimmed = None

    payload = {
        "class_id": school_class.id,
        "child_name": trimmed_name,
        "company_name": _normalize_company_name(company_name),
        "photo_path": photo_path,
        "photo_url": url_trimmed,
        "deleted_yn": "N",
    }

    if USE_SUPABASE:
        client = get_supabase_client()
        result = client.table("children").insert(payload).execute()
        child = _child_from_row(result.data[0])
        from api.wallet_repository import ensure_wallet

        ensure_wallet(child.id, school_class.currency_code)
        return child

    db = SessionLocal()
    try:
        obj = ChildModel(**{k: v for k, v in payload.items() if k != "deleted_yn"})
        obj.deleted_yn = "N"
        db.add(obj)
        db.commit()
        db.refresh(obj)
        child = _child_from_orm(obj)
        from api.wallet_repository import ensure_wallet

        ensure_wallet(child.id, school_class.currency_code)
        return child
    finally:
        db.close()


def update_child(
    child: Child,
    child_name: str,
    photo_path: str | None = None,
    photo_url: str | None = None,
    company_name: str | None = None,
    clear_upload: bool = False,
    clear_url: bool = False,
) -> Child:
    trimmed_name = child_name.strip()
    if not trimmed_name:
        raise ValueError("아이 이름을 입력해 주세요.")

    updates: dict[str, Any] = {
        "child_name": trimmed_name,
        "company_name": _normalize_company_name(company_name),
    }

    if clear_upload:
        updates["photo_path"] = None
    elif photo_path:
        updates["photo_path"] = photo_path

    if clear_url:
        updates["photo_url"] = None
    elif photo_url is not None:
        url_trimmed = photo_url.strip()
        updates["photo_url"] = url_trimmed if url_trimmed else None

    if USE_SUPABASE:
        client = get_supabase_client()
        result = client.table("children").update(updates).eq("id", child.id).execute()
        return _child_from_row(result.data[0])

    db = SessionLocal()
    try:
        obj = db.get(ChildModel, child.id)
        if obj is None:
            raise ValueError("아이를 찾을 수 없습니다.")
        for key, value in updates.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return _child_from_orm(obj)
    finally:
        db.close()


def delete_child(child: Child) -> None:
    """soft delete — 목록에서 숨김, 거래내역 유지."""
    if USE_SUPABASE:
        client = get_supabase_client()
        client.table("children").update({"deleted_yn": "Y"}).eq("id", child.id).execute()
        return

    db = SessionLocal()
    try:
        obj = db.get(ChildModel, child.id)
        if obj:
            obj.deleted_yn = "Y"
            db.commit()
    finally:
        db.close()
