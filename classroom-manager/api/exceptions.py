"""로그인 필수 예외 — 예외 핸들러에서 로그인 페이지로 리다이렉트."""

from __future__ import annotations


class LoginRequired(Exception):
    pass
