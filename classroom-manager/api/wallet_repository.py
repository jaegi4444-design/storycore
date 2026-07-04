"""지갑·거래내역 데이터 접근."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.entities import PointTransaction, StudentWallet
from api.models import Child as ChildModel
from api.models import PointTransaction as PointTransactionModel
from api.models import SchoolClass as SchoolClassModel
from api.models import StudentWallet as StudentWalletModel
from api.models import User as UserModel
from api.supabase_client import get_supabase_client
from config.settings import USE_SUPABASE

TRANSACTION_TYPE_LABELS = {
    "DEPOSIT": "이체",
    "WITHDRAW": "차감",
    "ADJUST": "조정",
    "TRANSFER_IN": "입금",
    "TRANSFER_OUT": "출금",
}


def transaction_type_label(transaction_type: str) -> str:
    return TRANSACTION_TYPE_LABELS.get(transaction_type, transaction_type)


def _wallet_from_row(row: dict[str, Any]) -> StudentWallet:
    return StudentWallet(
        id=row["id"],
        child_id=row["child_id"],
        currency_code=row["currency_code"],
        balance=row["balance"],
    )


def _wallet_from_orm(obj: StudentWalletModel) -> StudentWallet:
    return StudentWallet(
        id=obj.id,
        child_id=obj.child_id,
        currency_code=obj.currency_code,
        balance=obj.balance,
    )


def _tx_from_row(row: dict[str, Any]) -> PointTransaction:
    return PointTransaction(
        id=row["id"],
        class_id=row["class_id"],
        child_id=row["child_id"],
        wallet_id=row["wallet_id"],
        transaction_type=row["transaction_type"],
        amount=row["amount"],
        balance_before=row["balance_before"],
        balance_after=row["balance_after"],
        currency_code=row["currency_code"],
        memo=row.get("memo"),
        created_by_user_id=row["created_by_user_id"],
        created_at=row.get("created_at"),
        child_name=row.get("child_name"),
        teacher_name=row.get("teacher_name"),
    )


def _tx_from_orm(obj: PointTransactionModel, child_name: str | None = None, teacher_name: str | None = None) -> PointTransaction:
    return PointTransaction(
        id=obj.id,
        class_id=obj.class_id,
        child_id=obj.child_id,
        wallet_id=obj.wallet_id,
        transaction_type=obj.transaction_type,
        amount=obj.amount,
        balance_before=obj.balance_before,
        balance_after=obj.balance_after,
        currency_code=obj.currency_code,
        memo=obj.memo,
        created_by_user_id=obj.created_by_user_id,
        created_at=obj.created_at,
        child_name=child_name,
        teacher_name=teacher_name,
    )


def ensure_wallet(child_id: int, currency_code: str) -> StudentWallet:
    if USE_SUPABASE:
        client = get_supabase_client()
        existing = (
            client.table("student_wallets")
            .select("*")
            .eq("child_id", child_id)
            .eq("currency_code", currency_code)
            .limit(1)
            .execute()
        )
        if existing.data:
            return _wallet_from_row(existing.data[0])
        created = (
            client.table("student_wallets")
            .insert({"child_id": child_id, "currency_code": currency_code, "balance": 0})
            .execute()
        )
        return _wallet_from_row(created.data[0])

    db = SessionLocal()
    try:
        wallet = db.scalar(
            select(StudentWalletModel).where(
                StudentWalletModel.child_id == child_id,
                StudentWalletModel.currency_code == currency_code,
            )
        )
        if wallet:
            return _wallet_from_orm(wallet)
        wallet = StudentWalletModel(child_id=child_id, currency_code=currency_code, balance=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        return _wallet_from_orm(wallet)
    finally:
        db.close()


def backfill_wallets_for_active_children() -> None:
    if USE_SUPABASE:
        client = get_supabase_client()
        children = client.table("children").select("id, class_id").eq("deleted_yn", "N").execute()
        for child in children.data or []:
            cls = (
                client.table("classes")
                .select("currency_code")
                .eq("id", child["class_id"])
                .limit(1)
                .execute()
            )
            if cls.data:
                ensure_wallet(child["id"], cls.data[0]["currency_code"])
        return

    db = SessionLocal()
    try:
        rows = db.execute(
            select(ChildModel.id, SchoolClassModel.currency_code)
            .join(SchoolClassModel, SchoolClassModel.id == ChildModel.class_id)
            .where(ChildModel.deleted_yn == "N")
        ).all()
        for child_id, currency_code in rows:
            ensure_wallet(child_id, currency_code)
    finally:
        db.close()


def get_wallet(child_id: int, currency_code: str) -> StudentWallet | None:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("student_wallets")
            .select("*")
            .eq("child_id", child_id)
            .eq("currency_code", currency_code)
            .limit(1)
            .execute()
        )
        return _wallet_from_row(result.data[0]) if result.data else None

    db = SessionLocal()
    try:
        wallet = db.scalar(
            select(StudentWalletModel).where(
                StudentWalletModel.child_id == child_id,
                StudentWalletModel.currency_code == currency_code,
            )
        )
        return _wallet_from_orm(wallet) if wallet else None
    finally:
        db.close()


def get_wallets_for_children(child_ids: list[int], currency_code: str) -> dict[int, StudentWallet]:
    if not child_ids:
        return {}

    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("student_wallets")
            .select("*")
            .in_("child_id", child_ids)
            .eq("currency_code", currency_code)
            .execute()
        )
        return {row["child_id"]: _wallet_from_row(row) for row in result.data}

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(StudentWalletModel).where(
                StudentWalletModel.child_id.in_(child_ids),
                StudentWalletModel.currency_code == currency_code,
            )
        ).all()
        return {w.child_id: _wallet_from_orm(w) for w in rows}
    finally:
        db.close()


def deposit_atomic(child_id: int, amount: int, memo: str | None, user_id: int) -> dict[str, int]:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = client.rpc(
            "cm_deposit_points",
            {
                "p_child_id": child_id,
                "p_amount": amount,
                "p_memo": memo,
                "p_user_id": user_id,
            },
        ).execute()
        data = result.data
        return {
            "transaction_id": data["transaction_id"],
            "balance_before": data["balance_before"],
            "balance_after": data["balance_after"],
        }

    db = SessionLocal()
    try:
        return _sqlite_mutate_points(db, child_id, amount, memo, user_id, is_deposit=True)
    finally:
        db.close()


def withdraw_atomic(child_id: int, amount: int, memo: str | None, user_id: int) -> dict[str, int]:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = client.rpc(
            "cm_withdraw_points",
            {
                "p_child_id": child_id,
                "p_amount": amount,
                "p_memo": memo,
                "p_user_id": user_id,
            },
        ).execute()
        data = result.data
        return {
            "transaction_id": data["transaction_id"],
            "balance_before": data["balance_before"],
            "balance_after": data["balance_after"],
        }

    db = SessionLocal()
    try:
        return _sqlite_mutate_points(db, child_id, amount, memo, user_id, is_deposit=False)
    finally:
        db.close()


def _sqlite_mutate_points(
    db: Session,
    child_id: int,
    amount: int,
    memo: str | None,
    user_id: int,
    *,
    is_deposit: bool,
) -> dict[str, int]:
    with db.begin():
        child = db.get(ChildModel, child_id)
        if child is None or child.deleted_yn != "N":
            raise ChildNotFoundError()

        school_class = db.get(SchoolClassModel, child.class_id)
        if school_class is None or school_class.teacher_user_id != user_id:
            raise AccessDeniedError()

        wallet = db.scalar(
            select(StudentWalletModel)
            .where(
                StudentWalletModel.child_id == child_id,
                StudentWalletModel.currency_code == school_class.currency_code,
            )
            .with_for_update()
        )
        if wallet is None:
            raise WalletNotFoundError()

        balance_before = wallet.balance
        if is_deposit:
            balance_after = balance_before + amount
            tx_type = "DEPOSIT"
        else:
            if balance_before < amount:
                raise InsufficientBalanceError()
            balance_after = balance_before - amount
            tx_type = "WITHDRAW"

        wallet.balance = balance_after
        tx = PointTransactionModel(
            class_id=school_class.id,
            child_id=child_id,
            wallet_id=wallet.id,
            transaction_type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            currency_code=school_class.currency_code,
            memo=memo,
            created_by_user_id=user_id,
        )
        db.add(tx)
        db.flush()
        return {
            "transaction_id": tx.id,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }


def get_child_transactions(child_id: int) -> list[PointTransaction]:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("point_transactions")
            .select("*")
            .eq("child_id", child_id)
            .order("created_at", desc=True)
            .execute()
        )
        txs = []
        for row in result.data:
            tx = _tx_from_row(row)
            from api.repository import get_user_by_id

            teacher = get_user_by_id(tx.created_by_user_id)
            if teacher:
                tx.teacher_name = teacher.name
            txs.append(tx)
        return txs

    db = SessionLocal()
    try:
        rows = db.scalars(
            select(PointTransactionModel)
            .where(PointTransactionModel.child_id == child_id)
            .order_by(PointTransactionModel.created_at.desc())
        ).all()
        result = []
        for r in rows:
            teacher = db.get(UserModel, r.created_by_user_id)
            result.append(_tx_from_orm(r, teacher_name=teacher.name if teacher else None))
        return result
    finally:
        db.close()


def get_class_transactions(class_id: int) -> list[PointTransaction]:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("point_transactions")
            .select("*")
            .eq("class_id", class_id)
            .order("created_at", desc=True)
            .execute()
        )
        txs = []
        from api.repository import get_user_by_id, get_child_by_id

        for row in result.data:
            tx = _tx_from_row(row)
            child = get_child_by_id(tx.child_id)
            if child:
                tx.child_name = child.child_name
            teacher = get_user_by_id(tx.created_by_user_id)
            if teacher:
                tx.teacher_name = teacher.name
            txs.append(tx)
        return txs

    db = SessionLocal()
    try:
        rows = db.execute(
            select(PointTransactionModel, ChildModel.child_name, UserModel.name)
            .join(ChildModel, ChildModel.id == PointTransactionModel.child_id)
            .join(UserModel, UserModel.id == PointTransactionModel.created_by_user_id)
            .where(PointTransactionModel.class_id == class_id)
            .order_by(PointTransactionModel.created_at.desc())
        ).all()
        return [_tx_from_orm(tx, child_name=cn, teacher_name=tn) for tx, cn, tn in rows]
    finally:
        db.close()


def count_child_transactions(child_id: int) -> int:
    if USE_SUPABASE:
        client = get_supabase_client()
        result = (
            client.table("point_transactions")
            .select("id", count="exact")
            .eq("child_id", child_id)
            .execute()
        )
        return result.count or 0

    db = SessionLocal()
    try:
        from sqlalchemy import func

        return db.scalar(
            select(func.count()).select_from(PointTransactionModel).where(
                PointTransactionModel.child_id == child_id
            )
        ) or 0
    finally:
        db.close()


class AccessDeniedError(Exception):
    pass


class ChildNotFoundError(Exception):
    pass


class WalletNotFoundError(Exception):
    pass


class InsufficientBalanceError(Exception):
    pass


class InvalidAmountError(Exception):
    pass
