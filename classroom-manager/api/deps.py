"""인증 의존성 및 세션 헬퍼."""

from __future__ import annotations

from fastapi import Request

from api.entities import User
from api.exceptions import LoginRequired
from api.repository import get_user_by_id

SESSION_USER_ID_KEY = "user_id"


def get_session_user_id(request: Request) -> int | None:
    user_id = request.session.get(SESSION_USER_ID_KEY)
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def login_user(request: Request, user: User) -> None:
    request.session[SESSION_USER_ID_KEY] = user.id


def logout_user(request: Request) -> None:
    request.session.pop(SESSION_USER_ID_KEY, None)


def get_current_user(request: Request) -> User:
    user_id = get_session_user_id(request)
    if user_id is None:
        raise LoginRequired()

    user = get_user_by_id(user_id)
    if user is None:
        logout_user(request)
        raise LoginRequired()
    return user


def get_current_user_optional(request: Request) -> User | None:
    user_id = get_session_user_id(request)
    if user_id is None:
        return None
    return get_user_by_id(user_id)


def flash(request: Request, message: str, category: str = "info") -> None:
    request.session.setdefault("flash_messages", []).append(
        {"message": message, "category": category}
    )


def pop_flashes(request: Request) -> list[dict[str, str]]:
    return request.session.pop("flash_messages", [])
