"""API models for storage manager and saved conversations."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from app.models.query import QueryResponse


class VectorStoreInfo(BaseModel):
    id: str
    name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    status: str
    is_active: bool
    created_at: datetime
    last_ingested_at: datetime | None = None
    last_used_at: datetime | None = None
    chunk_count: int
    query_count: int = 0
    error_message: str | None = None


class EmbeddingModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    dimensions: int | None = None
    is_enabled: bool


class CreateVectorStoreRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    embedding_model: str
    chunk_size: int = Field(default=1500, ge=600, le=3000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    activate: bool = True

    @model_validator(mode="after")
    def validate_overlap(self) -> "CreateVectorStoreRequest":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


class ConversationSummary(BaseModel):
    id: str
    question: str
    answer_preview: str
    created_at: datetime
    processing_time: float
    status: str


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]


class ConversationDetail(BaseModel):
    response: QueryResponse
