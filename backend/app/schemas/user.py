import unicodedata
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import BCRYPT_MAX_BYTES
from app.core.usernames import canonical_username


def _reject_nul(value: str) -> str:
    # NUL bytes cannot be stored in PostgreSQL text columns and bcrypt cannot hash them
    if "\x00" in value:
        raise ValueError("must not contain NUL characters")
    return value


class UserCreate(BaseModel):
    """Registration request. The password arrives in plain text and is hashed in the service layer."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=100)
    password: str = Field(min_length=8)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        # Normalize before the length checks: "   " is too short, and the stored value fits the column
        return canonical_username(value) if isinstance(value, str) else value

    @field_validator("username")
    @classmethod
    def username_has_no_nul(cls, value: str) -> str:
        return _reject_nul(value)

    @field_validator("username")
    @classmethod
    def username_has_no_at(cls, value: str) -> str:
        # A value with @ is read as an email at login, so a username must never have one (BR-18)
        if "@" in value:
            raise ValueError("must not contain @")
        return value

    @field_validator("password")
    @classmethod
    def password_is_valid(cls, value: str) -> str:
        _reject_nul(value)
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(f"password must be at most {BCRYPT_MAX_BYTES} bytes long")
        return value


class UserLogin(BaseModel):
    # A username or an email. The field keeps the name "username", so older clients still work.
    # 100 characters is the length of the email column.
    username: str = Field(min_length=1, max_length=100)
    # No byte-length or NUL check on the password: a password that can never match
    # (NUL bytes, or longer than bcrypt's limit) gets 401 from the service layer
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_identifier(cls, value):
        if not isinstance(value, str):
            return value
        if "@" in value:
            # An email. It is stored in plain lower case, so the Turkish letter rules of the
            # usernames must not be used here: they would turn "I" into "\u0131" (dotless i).
            return unicodedata.normalize("NFC", value.strip()).lower()
        # A username: the same rule as registration, so the lookup matches the stored value
        return canonical_username(value)

    @field_validator("username")
    @classmethod
    def username_has_no_nul(cls, value: str) -> str:
        return _reject_nul(value)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """The user returned to the client. The hashed_password is deliberately missing."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr = Field(max_length=100)
    username: str
    created_at: datetime
