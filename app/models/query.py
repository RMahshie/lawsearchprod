"""
Pydantic models for query API endpoints.

Defines request and response models with proper validation,
documentation, and examples for the LawSearch AI API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


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
        example="How much funding did FEMA receive in 2024?"
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
        example=["DEPARTMENT OF HOMELAND SECURITY", "DEPARTMENT OF DEFENSE"]
    )
    
    debug_chunks: Optional[bool] = Field(
        default=False,
        description="If True, include retrieved document chunks in response for debugging",
        example=False
    )

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        """Validate that question contains meaningful content."""
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
        """Validate that division names are from the allowed list."""
        if v is None:
            return v
            
        # Valid division names from your config
        valid_divisions = {
            "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES",
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
            "OTHER MATTERS",
            "DEPARTMENT OF DEFENSE",
            "FINANCIAL SERVICES AND GENERAL GOVERNMENT",
            "DEPARTMENT OF HOMELAND SECURITY",
            "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES",
            "LEGISLATIVE BRANCH",
            "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS",
            "OTHER MATTERS (FURTHER)"
        }
        
        invalid_divisions = [div for div in v if div not in valid_divisions]
        if invalid_divisions:
            raise ValueError(f'Invalid division names: {invalid_divisions}')
            
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How much funding was allocated to cybersecurity initiatives?",
                "max_results": 8,
                "include_sources": True,
                "divisions_filter": None
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
        example="DEPARTMENT OF HOMELAND SECURITY"
    )
    
    content_snippet: str = Field(
        ...,
        max_length=500,
        description="Relevant snippet from the source document",
        example="For cybersecurity and infrastructure security activities, $2,847,000,000..."
    )
    
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for this source (0-1)",
        example=0.95
    )


class QueryResponse(BaseModel):
    """
    Response model for query results.
    
    Contains the comprehensive answer along with metadata
    about the query processing and sources.
    """
    answer: str = Field(
        ...,
        description="The comprehensive answer synthesized from multiple divisions",
        example="Based on the 2024 appropriations, FEMA received $19.4 billion for disaster relief operations..."
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
        example=["DEPARTMENT OF HOMELAND SECURITY", "OTHER MATTERS"]
    )
    
    sources: Optional[List[SourceDocument]] = Field(
        default=None,
        description="Source documents used to generate the answer",
        example=None
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
    
    debug_chunks: Optional[List[Dict]] = Field(
        default=None,
        description="Retrieved document chunks for debugging (only if requested)",
        example=None
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Based on the 2024 Consolidated Appropriations Act, FEMA received $19.4 billion for disaster relief operations, including $10.2 billion for the Disaster Relief Fund and $9.2 billion for emergency preparedness activities.",
                "processing_time": 3.45,
                "selected_divisions": ["DEPARTMENT OF HOMELAND SECURITY"],
                "sources": [
                    {
                        "division": "DEPARTMENT OF HOMELAND SECURITY",
                        "content_snippet": "For the Disaster Relief Fund, $10,200,000,000 to remain available until expended...",
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
        default="1.0.0",
        description="API version",
        example="1.0.0"
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


class IngestRequest(BaseModel):
    """
    Request model for data ingestion.

    Used for POST /api/ingest endpoint to re-ingest vector databases
    with different embedding models.
    """
    embedding_model: str = Field(
        ...,
        description="OpenAI embedding model to use for vectorizing documents",
        example="text-embedding-ada-002"
    )

    clear_existing: Optional[bool] = Field(
        default=True,
        description="Whether to clear existing vector databases before ingestion",
        example=True
    )

    @field_validator('embedding_model')
    @classmethod
    def validate_embedding_model(cls, v):
        """Validate that embedding model is a supported OpenAI model."""
        valid_models = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large"
        ]

        if v not in valid_models:
            raise ValueError(f'Unsupported embedding model: {v}. Valid options: {valid_models}')

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "embedding_model": "text-embedding-ada-002",
                "clear_existing": True
            }
        }
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