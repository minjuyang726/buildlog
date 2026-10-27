from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.common import utcnow
from app.models.todo import Todo
from app.models.user import User
from app.schemas.todo import TodoDoneIn, TodoFilter, TodoIn, TodoList, TodoOut
from app.services.auth import get_current_user
from app.services.permissions import get_owned, get_visible

router = APIRouter(prefix="/api/todos", tags=["todos"])


def to_out(todo: Todo, db: Session, user: User) -> TodoOut:
    author = user if todo.user_id == user.id else db.get(User, todo.user_id)
    return TodoOut(
        id=todo.id,
        title=todo.title,
        is_done=todo.is_done,
        is_public=todo.is_public,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        completed_at=todo.completed_at,
        author_nickname=author.nickname,
        is_mine=todo.user_id == user.id,
    )


@router.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(data: TodoIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = Todo(user_id=user.id, title=data.title, is_public=data.is_public)
    db.add(todo)
    db.commit()
    return to_out(todo, db, user)


@router.get("", response_model=TodoList)
def list_my_todos(
    filter: TodoFilter = Query(default="all"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내 할 일 목록. 완료하지 않은 일을 먼저, 같은 상태에서는 최근에 작성한 일부터 보여준다."""
    query = select(Todo).where(Todo.user_id == user.id)
    if filter == "open":
        query = query.where(Todo.is_done.is_(False))
    elif filter == "done":
        query = query.where(Todo.is_done.is_(True))
    todos = db.scalars(query.order_by(Todo.is_done.asc(), Todo.created_at.desc(), Todo.id.desc())).all()
    return TodoList(items=[to_out(t, db, user) for t in todos])


@router.get("/{todo_id}", response_model=TodoOut)
def read_todo(todo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_out(get_visible(db, Todo, todo_id, user), db, user)


@router.put("/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, data: TodoIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = get_owned(db, Todo, todo_id, user)
    todo.title = data.title
    todo.is_public = data.is_public
    todo.updated_at = utcnow()
    db.commit()
    return to_out(todo, db, user)


@router.put("/{todo_id}/done", response_model=TodoOut)
def set_done(todo_id: int, data: TodoDoneIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """완료로 체크하거나 완료를 취소한다. 완료 날짜·시간은 자동으로 저장되고, 취소하면 지워진다."""
    todo = get_owned(db, Todo, todo_id, user)
    if data.is_done:
        todo.mark_done()
    else:
        todo.mark_undone()
    db.commit()
    return to_out(todo, db, user)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    todo = get_owned(db, Todo, todo_id, user)
    db.delete(todo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
