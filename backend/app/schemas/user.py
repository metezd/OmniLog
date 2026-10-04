from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Registiration request. The password sent in plain text; Hashing is performed in the CRUD/service layer"""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(max_length=100)
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """The user returns to the client. The hashed_password is DELIBERATELY missing"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr = Field(max_length=100)
    username: str
    created_at: datetime