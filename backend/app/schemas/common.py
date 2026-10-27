from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def _as_utc(value: datetime) -> datetime:
    # SQLite는 시간대 정보를 저장하지 않아서 UTC로 간주해 붙여 준다. (Supabase는 이미 시간대가 있다.)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


# 응답에 나가는 날짜·시간은 항상 UTC 표시(끝에 Z)가 붙게 한다. 화면이 사용자 시간대로 바꿔 보여준다.
UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]
