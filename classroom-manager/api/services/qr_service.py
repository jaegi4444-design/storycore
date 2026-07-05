"""QR 스캔 흐름 서비스."""

from __future__ import annotations

from fastapi import Request

from api.entities import Child, User
from api.qr_tokens import make_child_qr_token
from api.repository import get_child_by_id, get_class_by_id, get_user_by_id
from config.settings import CLASSROOM_PUBLIC_URL


def build_child_qr_url(request: Request | None, child_id: int) -> str:
    """아이별 고정 QR URL — child_id 토큰은 변하지 않음."""
    token = make_child_qr_token(child_id)
    if CLASSROOM_PUBLIC_URL:
        base = CLASSROOM_PUBLIC_URL
    elif request is not None:
        base = str(request.base_url).rstrip("/")
    else:
        base = ""
    return f"{base}/q/{token}"


def get_teacher_for_child(child: Child) -> User | None:
    school_class = get_class_by_id(child.class_id)
    if school_class is None:
        return None
    return get_user_by_id(school_class.teacher_user_id)


def resolve_child_from_qr_token(token: str) -> tuple[Child, User] | None:
    from api.qr_tokens import verify_child_qr_token

    child_id = verify_child_qr_token(token)
    if child_id is None:
        return None

    child = get_child_by_id(child_id)
    if child is None:
        return None

    teacher = get_teacher_for_child(child)
    if teacher is None:
        return None

    return child, teacher
