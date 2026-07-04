"""Jinja2 템플릿 필터."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from markupsafe import Markup

try:
    KST = ZoneInfo("Asia/Seoul")
except Exception:
    KST = timezone(timedelta(hours=9))
WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


def _parse_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def _korean_ampm(hour: int) -> tuple[str, int]:
    if hour < 12:
        return "오전", 12 if hour == 0 else hour
    if hour == 12:
        return "오후", 12
    return "오후", hour - 12


def format_tx_datetime(value: datetime | str | None) -> str | Markup:
    """거래일시 — 오늘/어제 + 한국어 날짜·시간."""
    dt = _parse_datetime(value)
    if dt is None:
        return "-"

    today = datetime.now(KST).date()
    tx_date = dt.date()
    ampm, hour12 = _korean_ampm(dt.hour)
    time_part = f"{ampm} {hour12}:{dt.minute:02d}"

    if tx_date == today:
        date_part = "오늘"
    elif tx_date == today - timedelta(days=1):
        date_part = "어제"
    else:
        weekday = WEEKDAYS[dt.weekday()]
        date_part = f"{dt.year}. {dt.month:02d}. {dt.day:02d} ({weekday})"

    return Markup(
        f'<span class="txn-datetime">'
        f'<span class="txn-datetime__date">{date_part}</span>'
        f'<span class="txn-datetime__time">{time_part}</span>'
        f"</span>"
    )
