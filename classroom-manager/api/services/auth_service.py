"""인증 서비스 — MVP용 이름 기반 간편 로그인 (비밀번호 없음)."""

from api.repository import find_or_create_user_by_name

__all__ = ["find_or_create_user_by_name"]
