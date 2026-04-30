"""SQLAlchemy models for storage registry and query history."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def new_id() -> str:
    """Generate a random string identifier for database rows.

    Args:
        None.

    Returns:
        UUID4 string suitable for primary key values.
    """
    return str(uuid4())


class EmbeddingModel(Base):
    __tablename__ = "embedding_models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), default="openai", nullable=False)
    dimensions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class VectorStore(Base):
    __tablename__ = "vector_stores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    embedding_model_id: Mapped[str] = mapped_column(ForeignKey("embedding_models.id"), nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False)
    relative_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="building", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_ingested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    embedding_model: Mapped[EmbeddingModel] = relationship()
    partitions: Mapped[list["VectorStorePartition"]] = relationship(
        back_populates="vector_store",
        cascade="all, delete-orphan",
    )


class VectorStorePartition(Base):
    __tablename__ = "vector_store_partitions"
    __table_args__ = (UniqueConstraint("vector_store_id", "division_key"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    vector_store_id: Mapped[str] = mapped_column(ForeignKey("vector_stores.id"), nullable=False)
    division_key: Mapped[str] = mapped_column(String(300), nullable=False)
    store_name: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ready", nullable=False)

    vector_store: Mapped[VectorStore] = relationship(back_populates="partitions")


class QueryRun(Base):
    __tablename__ = "query_runs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    vector_store_id: Mapped[str | None] = mapped_column(ForeignKey("vector_stores.id"), nullable=True)
    processing_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    number_annotations: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    answer_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_mode_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    answer_mode_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    vector_store: Mapped[VectorStore | None] = relationship()
    division_results: Mapped[list["QueryDivisionResult"]] = relationship(
        back_populates="query_run",
        cascade="all, delete-orphan",
        order_by="QueryDivisionResult.sort_order",
    )


class QueryDivisionResult(Base):
    __tablename__ = "query_division_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    query_run_id: Mapped[str] = mapped_column(ForeignKey("query_runs.id"), nullable=False)
    division_key: Mapped[str] = mapped_column(String(300), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    chunks_retrieved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    query_run: Mapped[QueryRun] = relationship(back_populates="division_results")
    sources: Mapped[list["QuerySource"]] = relationship(
        back_populates="division_result",
        cascade="all, delete-orphan",
        order_by="QuerySource.rank",
    )


class QuerySource(Base):
    __tablename__ = "query_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    query_run_id: Mapped[str] = mapped_column(ForeignKey("query_runs.id"), nullable=False)
    query_division_result_id: Mapped[str] = mapped_column(ForeignKey("query_division_results.id"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(128), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    division_result: Mapped[QueryDivisionResult] = relationship(back_populates="sources")
