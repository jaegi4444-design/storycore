"""아이별 QR 토큰 생성·검증.

child_id 기준 서명 토큰이라 아이마다 고유하고, SESSION_SECRET_KEY가 바뀌지 않는 한
동일 아이는 항상 같은 QR 토큰을 유지합니다.
"""

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
