# 마이그레이션이 모든 테이블을 알 수 있도록 모델을 여기서 모두 불러온다.
from app.models.error_record import ErrorRecord  # noqa: F401
from app.models.study import Study  # noqa: F401
from app.models.todo import Todo  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.like import Like  # noqa: F401
