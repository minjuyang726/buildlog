from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def clean_required(value: str, field: str, max_length: int) -> str:
    """앞뒤 공백을 지우고 1~max_length자인지 확인한다. 중간 띄어쓰기는 유지한다."""
    value = value.strip()
    if not 1 <= len(value) <= max_length:
        raise ValueError(f"{field}은(는) 1~{max_length:,}자로 입력해 주세요.")
    return value


def clean_optional(value: str | None, field: str, max_length: int) -> str | None:
    """비워 둘 수 있는 항목. 공백만 입력하면 비운 것으로 본다."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return clean_required(value, field, max_length)
