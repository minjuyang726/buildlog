from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User

NOT_FOUND = "기록을 찾을 수 없습니다."
FORBIDDEN = "작성자만 수정하거나 삭제할 수 있습니다."


def get_visible(db: Session, model, record_id: int, user: User):
    """내가 볼 수 있는 기록만 돌려준다: 내 기록(공개·비공개 모두) 또는 다른 사람의 공개 기록.

    볼 수 없는 기록은 존재 여부도 알려주지 않도록 '없음'과 똑같이 응답한다.
    공부 기록, 할 일, 오류 기록이 모두 이 규칙을 함께 쓴다.
    """
    record = db.get(model, record_id)
    if record is None or not (record.user_id == user.id or record.is_public):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return record


def get_owned(db: Session, model, record_id: int, user: User):
    """수정·삭제처럼 작성자만 할 수 있는 작업에 쓴다.

    볼 수 없는 기록은 404, 볼 수는 있지만 내 것이 아닌 공개 기록은 403으로 거절한다.
    """
    record = get_visible(db, model, record_id, user)
    if record.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
    return record


def escape_like(text: str) -> str:
    """검색어에 들어 있는 % 와 _ 를 일반 글자로 취급하게 한다."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
