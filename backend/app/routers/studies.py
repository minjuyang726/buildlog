from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.common import utcnow
from app.models.study import Study
from app.models.user import User
from app.schemas.study import StudyIn, StudyList, StudyListItem, StudyOut
from app.services.auth import get_current_user
from app.services.permissions import escape_like, get_owned, get_visible

router = APIRouter(prefix="/api/studies", tags=["studies"])

PREVIEW_LENGTH = 100


def to_out(study: Study, db: Session, user: User) -> StudyOut:
    author = user if study.user_id == user.id else db.get(User, study.user_id)
    return StudyOut(
        id=study.id,
        title=study.title,
        content=study.content,
        is_public=study.is_public,
        created_at=study.created_at,
        updated_at=study.updated_at,
        author_nickname=author.nickname,
        is_mine=study.user_id == user.id,
    )


@router.post("", response_model=StudyOut, status_code=status.HTTP_201_CREATED)
def create_study(data: StudyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    study = Study(user_id=user.id, title=data.title, content=data.content, is_public=data.is_public)
    db.add(study)
    db.commit()
    return to_out(study, db, user)


@router.get("", response_model=StudyList)
def list_my_studies(
    q: str = Query(default="", max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내 공부 기록 목록. 최근에 작성한 기록부터 보여주고, 검색어가 있으면 제목·내용에서 찾는다."""
    query = select(Study).where(Study.user_id == user.id)
    keyword = q.strip()
    if keyword:
        pattern = f"%{escape_like(keyword)}%"
        query = query.where(or_(Study.title.ilike(pattern, escape="\\"), Study.content.ilike(pattern, escape="\\")))
    studies = db.scalars(query.order_by(Study.created_at.desc(), Study.id.desc())).all()
    return StudyList(
        items=[
            StudyListItem(
                id=s.id,
                title=s.title,
                preview=s.content[:PREVIEW_LENGTH],
                is_public=s.is_public,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in studies
        ]
    )


@router.get("/{study_id}", response_model=StudyOut)
def read_study(study_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_out(get_visible(db, Study, study_id, user), db, user)


@router.put("/{study_id}", response_model=StudyOut)
def update_study(
    study_id: int,
    data: StudyIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    study = get_owned(db, Study, study_id, user)
    study.title = data.title
    study.content = data.content
    study.is_public = data.is_public
    study.updated_at = utcnow()
    db.commit()
    return to_out(study, db, user)


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study(study_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    study = get_owned(db, Study, study_id, user)
    db.delete(study)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
