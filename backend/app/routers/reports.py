from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import FieldErrors
from app.db.session import get_db
from app.models.comment import Comment
from app.models.common import clean_required
from app.models.error_record import ErrorRecord
from app.models.report import REASON_MAX, Report
from app.models.study import Study
from app.models.todo import Todo
from app.models.user import User
from app.routers.comments import parent_of
from app.services.auth import get_current_user
from app.services.permissions import NOT_FOUND

# 신고는 접수(저장)만 한다. 신고 내용을 돌려주는 요청은 어디에도 없다.
# 운영자는 데이터베이스(Supabase) 화면에서 직접 확인한다.
router = APIRouter(prefix="/api/reports", tags=["reports"])

ALREADY_REPORTED = "이미 신고한 대상입니다."
ACCEPTED = "신고가 접수되었습니다."

TargetType = Literal["study", "todo", "error", "comment"]
MODELS = {"study": Study, "todo": Todo, "error": ErrorRecord}
COLUMNS = {"study": "study_id", "todo": "todo_id", "error": "error_id", "comment": "comment_id"}


class ReportIn(BaseModel):
    target_type: TargetType
    target_id: int
    reason: str

    @field_validator("reason")
    @classmethod
    def _reason(cls, value: str) -> str:
        return clean_required(value, "신고 이유", REASON_MAX)


class ReportAccepted(BaseModel):
    message: str


def ensure_reportable(db: Session, data: ReportIn) -> None:
    """공개된 기록이나 공개된 기록의 댓글만 신고할 수 있다. 볼 수 없는 대상은 '없음'으로 응답한다."""
    if data.target_type == "comment":
        comment = db.get(Comment, data.target_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
        parent_of(db, comment)  # 비공개 기록에 달린 댓글이면 404
        return
    record = db.get(MODELS[data.target_type], data.target_id)
    if record is None or not record.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)


@router.post("", response_model=ReportAccepted, status_code=status.HTTP_201_CREATED)
def create_report(data: ReportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportable(db, data)
    column = COLUMNS[data.target_type]
    already = db.scalar(select(Report.id).where(Report.reporter_id == user.id, getattr(Report, column) == data.target_id))
    if already is not None:
        raise FieldErrors(status.HTTP_409_CONFLICT, {"target": ALREADY_REPORTED})
    db.add(Report(reporter_id=user.id, reason=data.reason, **{column: data.target_id}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # 거의 동시에 두 번 보낸 경우
        raise FieldErrors(status.HTTP_409_CONFLICT, {"target": ALREADY_REPORTED})
    # 신고만으로 기록이나 댓글을 지우거나 숨기지 않는다.
    return ReportAccepted(message=ACCEPTED)
