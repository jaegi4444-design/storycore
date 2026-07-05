"""공통 코드 테이블 서비스."""

from api.entities import SchoolClass
from api.repository import get_active_currencies, get_currency_name, is_valid_currency_code

__all__ = [
    "get_active_currencies",
    "get_currency_name",
    "is_valid_currency_code",
    "resolve_class_currency_name",
]


def resolve_class_currency_name(school_class: SchoolClass | None) -> str:
    if school_class is None:
        return "콩"
    if school_class.currency_name:
        return school_class.currency_name
    return get_currency_name(school_class.currency_code)
