"""
Query API endpoints for LawSearch AI.

Handles POST /api/query and GET /api/health endpoints with proper
error handling, validation, and response formatting.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.models.query import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    ErrorResponse,
    IngestRequest,
    IngestResponse
)
from app.services.rag_service import get_rag_service, RAGService

# Configure logging
logger = logging.getLogger(__name__)

# Create router for query endpoints
router = APIRouter()


async def get_rag_service_dependency() -> RAGService:
    """Dependency to get RAG service instance."""
    return get_rag_service()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a legislative query",
    description="Submit a question about U.S. federal appropriations bills and receive an AI-generated answer with sources.",
    responses={
        200: {"description": "Query processed successfully"},
        400: {"description": "Invalid request data", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def process_query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service_dependency)
) -> QueryResponse:
    """
    Process a legislative query using RAG.
    
    Args:
        request: The query request with question and optional filters
        rag_service: Injected RAG service instance
        
    Returns:
        QueryResponse: Structured response with answer, timing, and sources
        
    Raises:
        HTTPException: For various error conditions
    """
    # Generate unique query ID for tracking
    query_id = f"query_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    logger.info(f"Processing query {query_id}: {request.question[:100]}...")
    
    try:
        # Process the query through RAG service
        response = await rag_service.process_query(request, query_id)
        
        logger.info(
            f"Query {query_id} completed in {response.processing_time:.2f}s, "
            f"selected {len(response.selected_divisions)} divisions"
        )
        
        return response
        
    except ValueError as e:
        # Handle validation or input errors
        logger.warning(f"Query {query_id} validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": str(e),
                "query_id": query_id
            }
        )
        
    except FileNotFoundError as e:
        # Handle missing database/file errors
        logger.error(f"Query {query_id} database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "database_unavailable",
                "message": "Vector database not available. Please ensure data has been ingested.",
                "query_id": query_id
            }
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Query {query_id} unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred while processing your query.",
                "query_id": query_id
            }
        )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-ingest data with different embedding model",
    description="Clear existing vector databases and re-ingest all bill documents using the specified embedding model. This operation may take 30-60 seconds.",
    responses={
        200: {"description": "Ingestion completed successfully"},
        400: {"description": "Invalid request data", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def ingest_data(
    request: IngestRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> IngestResponse:
    """
    Re-ingest vector databases with a different embedding model.

    This endpoint allows dynamic switching of embedding models without
    rebuilding the container. The operation clears existing vector stores
    and re-processes all bill documents.

    Args:
        request: Ingestion parameters including embedding model
        rag_service: Injected RAG service instance

    Returns:
        IngestResponse: Results of the ingestion operation

    Raises:
        HTTPException: For various error conditions
    """
    # Generate unique ingestion ID for tracking
    ingest_id = f"ingest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    logger.info(f"Starting ingestion {ingest_id} with model: {request.embedding_model}")

    try:
        # Perform the ingestion
        response, used_model = await rag_service.ingest_data(
            embedding_model=request.embedding_model,
            clear_existing=request.clear_existing,
            ingest_id=ingest_id
        )

        logger.info(
            f"Ingestion {ingest_id} completed in {response.processing_time:.2f}s, "
            f"processed {response.divisions_processed} divisions with model {used_model}"
        )

        return response

    except ValueError as e:
        # Handle validation or input errors
        logger.warning(f"Ingestion {ingest_id} validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": str(e),
                "ingest_id": ingest_id
            }
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Ingestion {ingest_id} unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ingestion_error",
                "message": "An unexpected error occurred during data ingestion.",
                "ingest_id": ingest_id
            }
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the RAG service and its dependencies.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy", "model": ErrorResponse},
    }
)
async def health_check(
    rag_service: RAGService = Depends(get_rag_service_dependency)
) -> HealthResponse:
    """
    Check the health of the RAG service.
    
    Args:
        rag_service: Injected RAG service instance
        
    Returns:
        HealthResponse: Health status and service information
        
    Raises:
        HTTPException: If service is unhealthy
    """
    try:
        # Check RAG service health
        health_info = await rag_service.health_check()
        
        if health_info["status"] == "healthy":
            logger.debug("Health check passed")
            return HealthResponse(
                status="healthy",
                timestamp=datetime.utcnow(),
                version="1.0.0",
                database_status=health_info.get("database_status", "unknown")
            )
        else:
            # Service reports as unhealthy
            logger.warning(f"Health check failed: {health_info.get('reason', 'Unknown')}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "service_unhealthy",
                    "message": health_info.get("reason", "Service is not healthy"),
                    "details": health_info
                }
            )
            
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "health_check_failed",
                "message": "Could not determine service health",
                "details": {"exception": str(e)}
            }
        )


@router.get(
    "/status",
    summary="Service status",
    description="Get detailed service status and configuration information.",
    response_model=Dict[str, Any]
)
async def service_status(
    rag_service: RAGService = Depends(get_rag_service_dependency)
) -> Dict[str, Any]:
    """
    Get detailed service status information.
    
    Args:
        rag_service: Injected RAG service instance
        
    Returns:
        Dict with detailed status information
    """
    try:
        health_info = await rag_service.health_check()
        
        return {
            "service": "LawSearch AI",
            "version": "1.0.0",
            "status": health_info.get("status", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "database_status": health_info.get("database_status", "unknown"),
            "available_divisions": health_info.get("available_divisions", "unknown"),
            "current_embedding_model": rag_service.settings.embedding_model,
            "endpoints": {
                "query": "/api/query",
                "health": "/api/health",
                "status": "/api/status",
                "docs": "/docs"
            }
        }
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return {
            "service": "LawSearch AI",
            "version": "1.0.0", 
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }