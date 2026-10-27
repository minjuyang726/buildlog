from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.user import NICKNAME_PATTERN, normalize_email

PASSWORD_MIN = 8
PASSWORD_MAX = 64
PASSWORD_MESSAGE = "비밀번호는 8자 이상 64자 이하로 입력해 주세요."
NICKNAME_MESSAGE = "닉네임은 2~20자의 한글, 영문, 숫자, 밑줄만 사용할 수 있습니다."


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def _check_nickname(value: str) -> str:
    value = value.strip()
    if not NICKNAME_PATTERN.match(value):
        raise ValueError(NICKNAME_MESSAGE)
    return value


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str

    @field_validator("email", mode="before")
    @classmethod
    def _trim_email(cls, value):
        return _strip(value)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        # 비밀번호는 입력한 그대로 확인한다. 공백을 지우지 않는다.
        if not PASSWORD_MIN <= len(value) <= PASSWORD_MAX:
            raise ValueError(PASSWORD_MESSAGE)
        return value

    @field_validator("nickname")
    @classmethod
    def _valid_nickname(cls, value: str) -> str:
        return _check_nickname(value)


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return normalize_email(value)


class NicknameUpdateRequest(BaseModel):
    nickname: str

    @field_validator("nickname")
    @classmethod
    def _valid_nickname(cls, value: str) -> str:
        return _check_nickname(value)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
