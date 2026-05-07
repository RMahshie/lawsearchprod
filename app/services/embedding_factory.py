"""Embedding provider registry and LangChain-compatible factories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings

VOYAGE_BATCH_SIZE = 64


class EmbeddingModelUnavailableError(ValueError):
    """Raised when an embedding model is supported but unusable in this runtime."""


@dataclass(frozen=True)
class EmbeddingModelConfig:
    """LawSearch embedding configuration persisted by id on Vector Stores."""

    id: str
    name: str
    provider: str
    dimensions: int | None = None
    output_dimension: int | None = None


SUPPORTED_EMBEDDING_MODELS: tuple[EmbeddingModelConfig, ...] = (
    EmbeddingModelConfig(
        id="text-embedding-ada-002",
        name="text-embedding-ada-002",
        provider="openai",
        dimensions=None,
    ),
    EmbeddingModelConfig(
        id="text-embedding-3-small",
        name="text-embedding-3-small",
        provider="openai",
        dimensions=1536,
    ),
    EmbeddingModelConfig(
        id="text-embedding-3-large",
        name="text-embedding-3-large",
        provider="openai",
        dimensions=3072,
    ),
    EmbeddingModelConfig(
        id="voyage-law-2",
        name="voyage-law-2",
        provider="voyage",
        dimensions=1024,
    ),
    EmbeddingModelConfig(
        id="voyage-4-large-2048",
        name="voyage-4-large",
        provider="voyage",
        dimensions=2048,
        output_dimension=2048,
    ),
)

SUPPORTED_EMBEDDING_MODEL_BY_ID = {
    config.id: config
    for config in SUPPORTED_EMBEDDING_MODELS
}


def embedding_config_for(model_id: str) -> EmbeddingModelConfig:
    """Return an embedding config, preserving historical OpenAI custom ids."""
    config = SUPPORTED_EMBEDDING_MODEL_BY_ID.get(model_id)
    if config:
        return config
    if model_id.startswith("text-embedding-"):
        return EmbeddingModelConfig(
            id=model_id,
            name=model_id,
            provider="openai",
            dimensions=None,
        )
    raise ValueError(f"Unsupported embedding model: {model_id}")


def is_embedding_model_available(model_id: str, settings: Settings) -> bool:
    """Return whether a supported embedding model can be used right now."""
    try:
        ensure_embedding_model_available(model_id, settings)
    except (EmbeddingModelUnavailableError, ValueError):
        return False
    return True


def ensure_embedding_model_available(model_id: str, settings: Settings) -> None:
    """Fail loudly when provider credentials required by a model are missing."""
    config = embedding_config_for(model_id)
    if config.provider == "voyage" and not settings.voyage_api_key:
        raise EmbeddingModelUnavailableError(
            f"Embedding model {model_id} is unavailable because VOYAGE_API_KEY is not configured."
        )


def create_embeddings(model_id: str, settings: Settings) -> Embeddings:
    """Create a LangChain-compatible embedding implementation for a config id."""
    config = embedding_config_for(model_id)
    ensure_embedding_model_available(model_id, settings)
    if config.provider == "openai":
        return OpenAIEmbeddings(model=config.name)
    if config.provider == "voyage":
        return VoyageEmbeddings(
            model=config.name,
            api_key=settings.voyage_api_key or "",
            output_dimension=config.output_dimension,
        )
    raise ValueError(f"Unsupported embedding provider for {model_id}: {config.provider}")


class VoyageEmbeddings(Embeddings):
    """Small Voyage wrapper that preserves document/query input types."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        output_dimension: int | None = None,
        batch_size: int = VOYAGE_BATCH_SIZE,
        client: Any | None = None,
    ):
        self.model = model
        self.output_dimension = output_dimension
        self.batch_size = batch_size
        if client is not None:
            self.client = client
            return
        try:
            import voyageai
        except ImportError as exc:
            raise EmbeddingModelUnavailableError(
                "The voyageai package is required to use Voyage embedding models."
            ) from exc
        self.client = voyageai.Client(api_key=api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed stored source chunks using Voyage's document input type."""
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            embeddings.extend(self._embed(texts[start : start + self.batch_size], input_type="document"))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed user retrieval text using Voyage's query input type."""
        return self._embed([text], input_type="query")[0]

    def _embed(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input_type": input_type,
            "truncation": True,
            "output_dtype": "float",
        }
        if self.output_dimension is not None:
            kwargs["output_dimension"] = self.output_dimension
        result = self.client.embed(texts, **kwargs)
        return result.embeddings
