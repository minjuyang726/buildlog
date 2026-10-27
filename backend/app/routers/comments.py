from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.comment import Comment
from app.models.common import utcnow
from app.models.error_record import ErrorRecord
from app.models.study import Study
from app.models.user import User
from app.schemas.comment import CommentIn, CommentList, CommentOut
from app.services.auth import get_current_user
from app.services.permissions import NOT_FOUND

# 댓글은 공부 기록과 오류 기록에만 달 수 있다. 할 일에는 댓글 경로 자체가 없다.
router = APIRouter(tags=["comments"])

COMMENT_NOT_FOUND = "댓글을 찾을 수 없습니다."
NOT_YOUR_COMMENT = "내 댓글만 수정할 수 있습니다."
NOT_ALLOWED_TO_DELETE = "내 댓글이거나 내 기록에 달린 댓글만 삭제할 수 있습니다."


def get_public_parent(db: Session, model, record_id: int):
    """댓글을 볼 수 있는 기록. 공개된 기록만 가능하다.

    비공개가 된 기록의 댓글은 지워지지 않고 숨겨지며, 다시 공개하면 그대로 돌아온다.
    """
    record = db.get(model, record_id)
    if record is None or not record.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return record


def parent_column(model):
    return Comment.study_id if model is Study else Comment.error_id


def to_out(comment: Comment, parent, db: Session, user: User) -> CommentOut:
    author = user if comment.user_id == user.id else db.get(User, comment.user_id)
    mine = comment.user_id == user.id
    return CommentOut(
        id=comment.id,
        content=comment.content,
        author_nickname=author.nickname,
        is_mine=mine,
        can_delete=mine or parent.user_id == user.id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def parent_of(db: Session, comment: Comment):
    model, record_id = (Study, comment.study_id) if comment.study_id is not None else (ErrorRecord, comment.error_id)
    return get_public_parent(db, model, record_id)


def load_comment(db: Session, comment_id: int) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=COMMENT_NOT_FOUND)
    return comment


def _register_parent_routes(prefix: str, model) -> None:
    @router.get(f"/api/{prefix}/{{record_id}}/comments", response_model=CommentList, name=f"list_{prefix}_comments")
    def list_comments(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """오래된 댓글부터 보여준다."""
        parent = get_public_parent(db, model, record_id)
        comments = db.scalars(
            select(Comment).where(parent_column(model) == record_id).order_by(Comment.created_at.asc(), Comment.id.asc())
        ).all()
        return CommentList(items=[to_out(c, parent, db, user) for c in comments])

    @router.post(
        f"/api/{prefix}/{{record_id}}/comments",
        response_model=CommentOut,
        status_code=status.HTTP_201_CREATED,
        name=f"create_{prefix}_comment",
    )
    def create_comment(
        record_id: int, data: CommentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ):
        parent = get_public_parent(db, model, record_id)
        comment = Comment(user_id=user.id, content=data.content)
        setattr(comment, "study_id" if model is Study else "error_id", record_id)
        db.add(comment)
        db.commit()
        return to_out(comment, parent, db, user)


_register_parent_routes("studies", Study)
_register_parent_routes("errors", ErrorRecord)


@router.put("/api/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int, data: CommentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    comment = load_comment(db, comment_id)
    parent = parent_of(db, comment)  # 숨겨진(비공개) 기록의 댓글은 없는 것처럼 응답한다.
    if comment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NOT_YOUR_COMMENT)
    comment.content = data.content
    comment.updated_at = utcnow()
    db.commit()
    return to_out(comment, parent, db, user)


@router.delete("/api/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    comment = load_comment(db, comment_id)
    parent = parent_of(db, comment)
    # 댓글 작성자와 그 기록의 작성자만 삭제할 수 있다.
    if comment.user_id != user.id and parent.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NOT_ALLOWED_TO_DELETE)
    db.delete(comment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
