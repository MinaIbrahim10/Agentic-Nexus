from datetime import datetime

from pydantic import BaseModel, Field


class QueryCreate(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=4000,
    )


class QueryRun(BaseModel):
    id: str
    query: str
    status: str
    created_at: datetime
