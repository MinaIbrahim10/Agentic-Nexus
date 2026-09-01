from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QueryCreate(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=4000,
    )


class QueryRun(BaseModel):
    id: str
    user_id: str
    query: str
    status: str
    created_at: datetime


class IngestRequest(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=200,
    )
    content: str = Field(
        min_length=10,
        max_length=50_000,
    )


class BackgroundJobResponse(BaseModel):
    id: str
    user_id: str
    kind: str
    status: str
    attempts: int
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    word_count: int
    created_at: datetime
