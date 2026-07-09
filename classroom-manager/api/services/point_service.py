"""포인트(콩) 입금·출금 서비스."""

from __future__ import annotations

from api.entities import PointTransaction, User
from api.repository import (
    ChildAccessDeniedError,
    get_child_for_teacher,
    get_class_by_teacher,
)
from api.wallet_repository import (
    AccessDeniedError,
    ChildNotFoundError,
    InsufficientBalanceError,
    InvalidAmountError,
    WalletNotFoundError,
    deposit_atomic,
    get_child_transactions,
    get_class_transactions,
    get_wallet,
    withdraw_atomic,
)


def _parse_amount(amount: int | str) -> int:
    if isinstance(amount, str):
        trimmed = amount.strip()
        if not trimmed.isdigit():
            raise InvalidAmountError("수량은 1 이상의 숫자만 입력할 수 있습니다.")
        amount = int(trimmed)
    if not isinstance(amount, int) or amount < 1:
        raise InvalidAmountError("수량은 1 이상이어야 합니다.")
    return amount


def _normalize_memo(memo: str | None) -> str | None:
    if memo is None:
        return None
    trimmed = memo.strip()
    return trimmed if trimmed else None


def deposit(child_id: int, amount: int | str, memo: str | None, teacher: User) -> dict[str, int]:
    child = get_child_for_teacher(child_id, teacher)
    if child.deleted_yn == "Y":
        raise ChildAccessDeniedError("접근 권한이 없습니다.")

    parsed_amount = _parse_amount(amount)
    school_class = get_class_by_teacher(teacher.id)
    if school_class is None:
        raise ChildAccessDeniedError("접근 권한이 없습니다.")

    wallet = get_wallet(child.id, school_class.currency_code)
    if wallet is None:
        raise WalletNotFoundError()

    try:
        return deposit_atomic(child.id, parsed_amount, _normalize_memo(memo), teacher.id)
    except (AccessDeniedError, ChildNotFoundError):
        raise ChildAccessDeniedError("접근 권한이 없습니다.") from None
    except InvalidAmountError:
        raise
    except Exception as exc:
        if "INVALID_AMOUNT" in str(exc):
            raise InvalidAmountError("수량은 1 이상이어야 합니다.") from exc
        if "ACCESS_DENIED" in str(exc):
            raise ChildAccessDeniedError("접근 권한이 없습니다.") from exc
        raise


def withdraw(child_id: int, amount: int | str, memo: str | None, teacher: User) -> dict[str, int]:
    child = get_child_for_teacher(child_id, teacher)
    if child.deleted_yn == "Y":
        raise ChildAccessDeniedError("접근 권한이 없습니다.")

    parsed_amount = _parse_amount(amount)
    school_class = get_class_by_teacher(teacher.id)
    if school_class is None:
        raise ChildAccessDeniedError("접근 권한이 없습니다.")

    wallet = get_wallet(child.id, school_class.currency_code)
    if wallet is None:
        raise WalletNotFoundError()
    if wallet.balance < parsed_amount:
        raise InsufficientBalanceError("현재 잔액보다 큰 금액은 출금할 수 없습니다.")

    try:
        return withdraw_atomic(child.id, parsed_amount, _normalize_memo(memo), teacher.id)
    except InsufficientBalanceError:
        raise
    except (AccessDeniedError, ChildNotFoundError):
        raise ChildAccessDeniedError("접근 권한이 없습니다.") from None
    except InvalidAmountError:
        raise
    except Exception as exc:
        if "INSUFFICIENT_BALANCE" in str(exc):
            raise InsufficientBalanceError("현재 잔액보다 큰 금액은 출금할 수 없습니다.") from exc
        if "INVALID_AMOUNT" in str(exc):
            raise InvalidAmountError("수량은 1 이상이어야 합니다.") from exc
        if "ACCESS_DENIED" in str(exc):
            raise ChildAccessDeniedError("접근 권한이 없습니다.") from exc
        raise


def get_child_transactions_for_teacher(child_id: int, teacher: User) -> list[PointTransaction]:
    get_child_for_teacher(child_id, teacher)
    return get_child_transactions(child_id)


def get_class_transactions_for_teacher(teacher: User) -> list[PointTransaction]:
    school_class = get_class_by_teacher(teacher.id)
    if school_class is None:
        raise ChildAccessDeniedError("접근 권한이 없습니다.")
    return get_class_transactions(school_class.id)


def get_child_balance(child_id: int, teacher: User) -> int:
    child = get_child_for_teacher(child_id, teacher)
    school_class = get_class_by_teacher(teacher.id)
    if school_class is None:
        return 0
    wallet = get_wallet(child.id, school_class.currency_code)
    return wallet.balance if wallet else 0
