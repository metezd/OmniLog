from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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

    @field_validator("password")
    @classmethod
    def password_is_valid(cls, value: str) -> str:
        _reject_nul(value)
        # bcrypt only looks at the first 72 bytes and rejects longer input
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes long")
        return value


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    # No NUL check on the password: a password with NUL can never match, so the
    # service answers 401 instead of a validation error
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        # Same rule as registration, so the lookup matches the stored value
        return canonical_username(value) if isinstance(value, str) else value

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
