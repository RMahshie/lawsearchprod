"""
Pydantic models for query API endpoints.

Defines request and response models with proper validation,
documentation, and examples for the LawSearch AI API.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime

from app import __version__ as APP_VERSION
from app.core.config import FY2026_DIVISIONS


class QueryRequest(BaseModel):
    """
    Request model for querying appropriations bills.
    
    Used for POST /api/query endpoint to validate incoming requests.
    """
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The question to ask about federal appropriations bills",
        example="How much FEMA-related funding is continued in FY2026?"
    )
    
    max_results: Optional[int] = Field(
        default=8,
        ge=1,
        le=20,
        description="Maximum number of document chunks to retrieve per division",
        example=8
    )
    
    include_sources: Optional[bool] = Field(
        default=True,
        description="Whether to include source information in the response",
        example=True
    )
    
    divisions_filter: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific divisions to search. If None, router will select automatically.",
        example=["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS", "DEPARTMENT OF DEFENSE"]
    )
    
    thinking_speed: Optional[str] = Field(
        default="normal",
        description="Thinking speed mode affecting model selection and retrieval parameters",
        example="normal"
    )

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        """Validate that question contains meaningful content.

        Args:
            v: Raw question value supplied to the request model.

        Returns:
            Stripped question text.
        """
        if not v.strip():
            raise ValueError('Question cannot be empty or whitespace only')
        
        # Check for basic question words to ensure it's actually a question
        question_indicators = ['how', 'what', 'when', 'where', 'why', 'which', 'who', 'is', 'are', 'does', 'do', 'can', 'will', 'should']
        if not any(indicator in v.lower() for indicator in question_indicators):
            # Allow it but could warn - some statements are valid queries
            pass
            
        return v.strip()

    @field_validator('divisions_filter')
    @classmethod
    def validate_divisions(cls, v):
        """Validate that division names are from the allowed list.

        Args:
            v: Optional list of requested division names.

        Returns:
            Original list when valid, or None when no filter was supplied.
        """
        if v is None:
            return v

        valid_divisions = set(FY2026_DIVISIONS)

        invalid_divisions = [div for div in v if div not in valid_divisions]
        if invalid_divisions:
            raise ValueError(f'Invalid division names: {invalid_divisions}')

        return v

    @field_validator('thinking_speed')
    @classmethod
    def validate_thinking_speed(cls, v):
        """Validate that thinking speed is one of the allowed values.

        Args:
            v: Optional thinking speed string supplied to the request model.

        Returns:
            Validated thinking speed string.
        """
        if v is None:
            return "normal"  # Default value

        valid_speeds = {"quick", "normal", "long"}
        if v not in valid_speeds:
            raise ValueError(f'Invalid thinking speed: {v}. Valid options: {valid_speeds}')

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How much funding was allocated to cybersecurity initiatives?",
                "max_results": 8,
                "include_sources": True,
                "divisions_filter": None,
                "thinking_speed": "normal"
            }
        }
    )


class SourceDocument(BaseModel):
    """
    Model for source document information.
    """
    division: str = Field(
        ...,
        description="The legislative division this information came from",
        example="CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
    )

    division_acronym: str = Field(
        ...,
        description="Compact division/committee marker used in inline citations",
        example="CRX"
    )

    chunk_id: str = Field(
        ...,
        description="Stable chunk identifier for UI citation lookup",
        example="CRX-1-a1b2c3d4"
    )
    
    content_snippet: str = Field(
        ...,
        description="Relevant raw source chunk or source excerpt",
        example="For cybersecurity and infrastructure security activities, $2,847,000,000..."
    )

    chunk_summary: Optional[str] = Field(
        default=None,
        description="One-line LLM-generated summary for source hover UI",
        example="This chunk lists FY2026 continuing appropriations and availability."
    )

    chunk_snapshot: Optional[str] = Field(
        default=None,
        description="Short LLM-generated label for source excerpt lists",
        example="FY2026 continuing appropriations"
    )
    
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for this source (0-1)",
        example=0.95
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw metadata carried by the vector store"
    )


class NumberAnnotationTarget(BaseModel):
    """Where a number marker appears in returned markdown."""

    scope: Literal["answer", "division"] = Field(..., description="Markdown field containing the marker")
    division: Optional[str] = Field(default=None, description="Division name for division-scoped targets")


class SourceNumberReference(BaseModel):
    """Minimal reference to a source chunk backing an atomic figure."""

    chunk_id: str = Field(..., description="Stable chunk id containing the source-backed figure")


class DerivedNumberReference(BaseModel):
    """Readable calculation metadata for a derived figure."""

    equation: str = Field(..., description="Readable equation for derived figures")
    rationale: Optional[str] = Field(default=None, description="Concise non-chain-of-thought rationale")
    input_ids: List[str] = Field(default_factory=list, description="Immediate source or derived annotation inputs")
    source_input_ids: List[str] = Field(
        default_factory=list,
        description="Flattened source annotation ids used for source rows in derived hovers",
    )


class NumberAnnotation(BaseModel):
    """Structured provenance for a visible dollar figure."""

    id: str = Field(..., description="Unique hidden marker id, without the [[num:...]] wrapper")
    kind: Literal["source", "derived"] = Field(..., description="Source-backed atomic figure or validated derived figure")
    figure: str = Field(..., description="Visible figure text in the answer")
    value: float = Field(..., description="Figure value normalized to dollars")
    label: str = Field(..., description="Short human-readable description of the figure")
    targets: List[NumberAnnotationTarget] = Field(
        default_factory=list,
        description="Answer or division markdown locations containing this marker",
    )
    source: Optional[SourceNumberReference] = Field(default=None, description="Source chunk reference for source figures")
    derived: Optional[DerivedNumberReference] = Field(default=None, description="Calculation metadata for derived figures")

    @model_validator(mode="after")
    def validate_kind_payload(self):
        """Ensure annotation kind and payload stay aligned."""
        if self.kind == "source" and self.source is None:
            raise ValueError("source annotations require source.chunk_id")
        if self.kind == "derived" and self.derived is None:
            raise ValueError("derived annotations require derived metadata")
        return self


class DebugDivisionQuery(BaseModel):
    """Per-division retrieval query returned for query inspection."""
    division: str
    division_acronym: str
    query: str


class DivisionResult(BaseModel):
    """Per-division reduction output."""
    division: str
    division_acronym: str
    chunks_retrieved: int
    answer: str
    source_chunk_ids: List[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """
    Response model for query results.
    
    Contains the comprehensive answer along with metadata
    about the query processing and sources.
    """
    answer: str = Field(
        ...,
        description="The comprehensive answer synthesized from multiple divisions",
        example="Based on the FY2026 appropriations text available in LawSearch, FEMA-related continuation material appears in the CRX catch-all division..."
    )
    
    processing_time: float = Field(
        ...,
        ge=0,
        description="Time taken to process the query in seconds",
        example=3.45
    )
    
    selected_divisions: List[str] = Field(
        ...,
        description="List of divisions that were queried for this request",
        example=["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"]
    )

    division_results: List[DivisionResult] = Field(
        default_factory=list,
        description="Per-division reduced answers and supporting chunk IDs"
    )
    
    sources: Optional[List[SourceDocument]] = Field(
        default=None,
        description="Source documents used to generate the answer",
        example=None
    )

    number_annotations: List[NumberAnnotation] = Field(
        default_factory=list,
        description="Structured provenance for source-backed and validated derived dollar figures"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this query was processed",
        example="2024-03-15T14:30:00Z"
    )
    
    query_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this query (for logging/tracking)",
        example="query_20240315_143000_abc123"
    )
    
    debug_division_queries: Optional[List[DebugDivisionQuery]] = Field(
        default=None,
        description="Refined per-division retrieval questions",
        example=None
    )

    thinking_speed: Optional[str] = Field(
        default=None,
        description="Thinking speed used for this query"
    )

    model_used: Optional[str] = Field(
        default=None,
        description="Primary OpenAI chat model used for answer generation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Based on the FY2026 appropriations text available in LawSearch, FEMA-related continuation material appears in the CRX catch-all division.",
                "processing_time": 3.45,
                "selected_divisions": ["CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"],
                "sources": [
                    {
                        "division": "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
                        "content_snippet": "Appropriations are continued under the Continuing Appropriations Act, 2026...",
                        "confidence_score": 0.95
                    }
                ],
                "timestamp": "2024-03-15T14:30:00Z",
                "query_id": "query_20240315_143000_abc123"
            }
        }
    )


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(
        default="healthy",
        description="Health status of the API",
        example="healthy"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current server timestamp"
    )
    
    version: str = Field(
        default=APP_VERSION,
        description="API version",
    )
    
    database_status: Optional[str] = Field(
        default=None,
        description="Status of vector database connections",
        example="connected"
    )


class ErrorResponse(BaseModel):
    """
    Response model for error cases.
    """
    error: str = Field(
        ...,
        description="Error type or code",
        example="validation_error"
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="The question field is required and cannot be empty"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
        example={"field": "question", "constraint": "min_length"}
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )


class IngestResponse(BaseModel):
    """
    Response model for ingestion results.
    """
    status: str = Field(
        ...,
        description="Ingestion status",
        example="completed"
    )

    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Successfully ingested 14 divisions using text-embedding-ada-002"
    )

    embedding_model: str = Field(
        ...,
        description="Embedding model used for ingestion",
        example="text-embedding-ada-002"
    )

    divisions_processed: int = Field(
        ...,
        description="Number of divisions processed",
        example=14
    )

    chunk_size: Optional[int] = Field(
        default=None,
        description="Chunk size used for ingestion",
        example=1500
    )

    processing_time: float = Field(
        ...,
        ge=0,
        description="Time taken to complete ingestion in seconds",
        example=45.67
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When ingestion completed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "completed",
                "message": "Successfully ingested 14 divisions using text-embedding-ada-002",
                "embedding_model": "text-embedding-ada-002",
                "divisions_processed": 14,
                "processing_time": 45.67,
                "timestamp": "2024-03-15T14:30:00Z"
            }
        }
    )
