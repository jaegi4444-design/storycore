"""아이별 QR 토큰 생성·검증."""

from __future__ import annotations

from itsdangerous import BadSignature, URLSafeSerializer

from config.settings import SESSION_SECRET_KEY

_serializer = URLSafeSerializer(SESSION_SECRET_KEY, salt="classroom-child-qr")


def make_child_qr_token(child_id: int) -> str:
    return _serializer.dumps({"child_id": child_id})


def verify_child_qr_token(token: str) -> int | None:
    try:
        data = _serializer.loads(token)
        return int(data["child_id"])
    except (BadSignature, KeyError, TypeError, ValueError):
        return None
