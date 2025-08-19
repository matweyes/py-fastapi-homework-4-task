from datetime import date

from fastapi import UploadFile, Form, File, HTTPException
from pydantic import BaseModel, HttpUrl, Field, field_validator

from src.validation import (
    validate_name,
    validate_image,
    validate_gender,
    validate_birth_date
)


class ProfileResponseSchema(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: str

    class Config:
        orm_mode = True


class ProfileCreateData(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    gender: str
    date_of_birth: date
    info: str = Field(..., min_length=1)

    @field_validator("first_name")
    @classmethod
    def _validate_first_name(cls, v) -> None:
        return validate_name(v)

    @field_validator("last_name")
    @classmethod
    def _validate_last_name(cls, v: str) -> None:
        return validate_name(v)

    @field_validator("gender")
    @classmethod
    def _validate_gender(cls, v: str) -> None:
        return validate_gender(v)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_birth_date(cls, v: date) -> None:
        return validate_birth_date(v)

    @field_validator("info")
    @classmethod
    def _validate_info(cls, v: str) -> None:
        if not v or not v.strip():
            raise ValueError("Info cannot be empty.")

