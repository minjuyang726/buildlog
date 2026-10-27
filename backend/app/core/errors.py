from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# 입력값이 규칙에 맞지 않을 때 항목별로 보여줄 안내 문구.
FIELD_MESSAGES = {
    "email": "올바른 이메일 주소를 입력해 주세요.",
    "password": "비밀번호는 8자 이상 64자 이하로 입력해 주세요.",
    "nickname": "닉네임은 2~20자의 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다.",
}
DEFAULT_MESSAGE = "입력한 내용을 다시 확인해 주세요."


class FieldErrors(Exception):
    """항목별 안내 문구와 함께 요청을 거절할 때 쓴다. (예: 이미 사용 중인 닉네임)"""

    def __init__(self, status_code: int, errors: dict[str, str]):
        self.status_code = status_code
        self.errors = errors


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(FieldErrors)
    async def field_errors_handler(_request: Request, exc: FieldErrors):
        return JSONResponse(status_code=exc.status_code, content={"errors": exc.errors})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        """검사에 실패한 항목마다 사람이 읽을 수 있는 문구를 돌려준다."""
        errors: dict[str, str] = {}
        for error in exc.errors():
            location = error.get("loc", ())
            field = str(location[-1]) if len(location) > 1 else "body"
            errors.setdefault(field, FIELD_MESSAGES.get(field, DEFAULT_MESSAGE))
        return JSONResponse(status_code=422, content={"errors": errors})
