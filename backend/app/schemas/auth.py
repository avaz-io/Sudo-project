from typing import Literal

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import APIModel, InputModel
from app.schemas.user import UserRead


class RegisterRequest(InputModel):
    display_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class LoginRequest(InputModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class TokenResponse(APIModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserRead
