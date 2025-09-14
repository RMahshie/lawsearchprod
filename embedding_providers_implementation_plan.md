# Multi-Provider Embedding Implementation Plan

## 🎯 **Overview**
Add support for `gemini-embedding-001` (Google) and `voyage-law-2` (VoyageAI) alongside existing OpenAI embeddings. Leverage existing dimension-handling infrastructure for seamless provider switching.

## 📋 **Supported Embedding Models**

| Provider | Model | Dimensions | Max Tokens | Description |
|----------|-------|------------|------------|-------------|
| OpenAI | `text-embedding-3-large` | 3072 | 8191 | High-quality embeddings (default) |
| OpenAI | `text-embedding-3-small` | 1536 | 8191 | Faster, cost-effective |
| Google | `gemini-embedding-001` | up to 3072 | 2048 | State-of-the-art performance across English, multilingual and code tasks |
| VoyageAI | `voyage-law-2` | 16,000 | 1024 | Optimized for legal retrieval and RAG |

## 🔄 **Phase-by-Phase Implementation**

### **Phase 1: Dependencies & Configuration**

#### **1.1 Update `requirements.txt`**
```txt
# Add these lines to requirements.txt
langchain-google-genai>=1.0.0
langchain-voyageai>=0.1.0
```

#### **1.2 Update `app/core/config.py`**
```python
# Add after OpenAI Configuration section:
# === Google Gemini Configuration ===
google_api_key: Optional[str] = Field(default=None, description="Google API key for Gemini")

# === VoyageAI Configuration ===
voyage_api_key: Optional[str] = Field(default=None, description="VoyageAI API key")

# Update embedding configuration:
embedding_provider: str = Field(default="openai", description="Embedding provider: openai, gemini, voyageai")
embedding_model: str = Field(default="text-embedding-3-large", description="Model name (varies by provider)")
```

### **Phase 2: Embedding Factory Pattern**

#### **2.1 Create Embedding Factory in `app/services/rag_service.py`**

Add after the imports:
```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_voyageai import VoyageAIEmbeddings

def create_embedding_provider(provider: str, model: str, api_key: str = None) -> Embeddings:
    """Factory function to create embedding providers."""
    if provider == "openai":
        return OpenAIEmbeddings(model=model, api_key=api_key)
    elif provider == "gemini":
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        return GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)
    elif provider == "voyageai":
        if not api_key:
            api_key = os.getenv("VOYAGE_API_KEY")
        return VoyageAIEmbeddings(model=model, voyage_api_key=api_key)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
```

#### **2.2 Update RAG Service Initialization**

Replace line 143 in `rag_service.py`:
```python
# OLD:
self.embedder = OpenAIEmbeddings(model=self.settings.embedding_model)

# NEW:
self.embedder = create_embedding_provider(
    provider=self.settings.embedding_provider,
    model=self.settings.embedding_model
)
```

Update the log message:
```python
logger.info(f"RAG service initialized with {self.settings.embedding_provider} embedding model: {self.settings.embedding_model}")
```

### **Phase 3: Dynamic Switching Support**

#### **3.1 Update `reingest_data` Method**

Replace lines 476-477 in `reingest_data`:
```python
# OLD:
self.embedder = OpenAIEmbeddings(model=embedding_model)

# NEW:
# Note: embedding_model here is just the model name, we need provider too
# For now, assume provider stays the same, just model changes
self.embedder = create_embedding_provider(
    provider=self.settings.embedding_provider,
    model=embedding_model
)
```

#### **3.2 Enhanced Reingest with Provider Switching**

Add new method for full provider switching:
```python
def reingest_with_provider(self, embedding_provider: str, embedding_model: str, clear_existing: bool = True) -> tuple[IngestResponse, str]:
    """Re-ingest with a completely different embedding provider."""

    # Validate provider
    supported_providers = ["openai", "gemini", "voyageai"]
    if embedding_provider not in supported_providers:
        raise ValueError(f"Unsupported provider: {embedding_provider}")

    # Clear existing data (dimensions will definitely change)
    if clear_existing:
        import shutil
        import os
        chroma_dir = str(self.settings.vectorstore_dir)
        if os.path.exists(chroma_dir):
            shutil.rmtree(chroma_dir)
            os.makedirs(chroma_dir, exist_ok=True)
            logger.info(f"Cleared existing ChromaDB directory: {chroma_dir}")

    # Update settings temporarily for this operation
    original_provider = self.settings.embedding_provider
    original_model = self.settings.embedding_model

    try:
        # Create new embedder
        self.embedder = create_embedding_provider(embedding_provider, embedding_model)

        # Update cached settings for this operation
        self.settings.embedding_provider = embedding_provider
        self.settings.embedding_model = embedding_model

        # Clear caches and proceed with ingestion
        self.get_store.cache_clear()
        logger.info("Cleared LLM and store caches")

        # Run ingestion script
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "src.ingest", "--embedding-model", embedding_model]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.settings.base_dir)

        if result.returncode == 0:
            logger.info("Ingestion completed successfully")
            response = IngestResponse(
                success=True,
                message=f"Successfully ingested data using {embedding_provider}/{embedding_model}",
                divisions_processed=0,  # Would need to parse from output
                total_chunks=0,
                embedding_model=f"{embedding_provider}/{embedding_model}",
                ingestion_id=None
            )
            return response, f"{embedding_provider}/{embedding_model}"
        else:
            error_msg = f"Ingestion failed: {result.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)

    finally:
        # Restore original settings
        self.settings.embedding_provider = original_provider
        self.settings.embedding_model = original_model
```

### **Phase 4: Environment Setup**

#### **4.1 Create/Update `.env` Template**
```bash
# Existing OpenAI
OPENAI_API_KEY=your_openai_key

# New providers
GOOGLE_API_KEY=your_google_key
VOYAGE_API_KEY=your_voyage_key

# Embedding configuration
EMBEDDING_PROVIDER=openai  # Options: openai, gemini, voyageai
EMBEDDING_MODEL=text-embedding-3-large  # Provider-specific model names
```

### **Phase 5: Testing & Validation**

#### **5.1 Provider-Specific Model Validation**
```python
def validate_embedding_config(provider: str, model: str) -> bool:
    """Validate that provider/model combination is supported."""
    valid_combinations = {
        "openai": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
        "gemini": ["gemini-embedding-001"],
        "voyageai": ["voyage-law-2", "voyage-3", "voyage-2"]
    }
    return model in valid_combinations.get(provider, [])
```

#### **5.2 Test Commands**
```bash
# Test each provider
python -c "
from app.services.rag_service import create_embedding_provider
import numpy as np

# Test embeddings
test_configs = [
    ('openai', 'text-embedding-3-small'),
    ('gemini', 'gemini-embedding-001'),
    ('voyageai', 'voyage-law-2')
]

for provider, model in test_configs:
    try:
        embedder = create_embedding_provider(provider, model)
        test_vec = embedder.embed_query('test legal document')
        print(f'✅ {provider}/{model}: {len(test_vec)} dimensions')
    except Exception as e:
        print(f'❌ {provider}/{model}: {str(e)}')
"
```

### **Phase 6: Documentation Updates**

#### **6.1 Update README.md**
```markdown
## Embedding Providers

The system supports multiple embedding providers optimized for legal document retrieval:

### Available Providers

- **OpenAI** (default)
  - `text-embedding-3-large`: 3072 dimensions, best quality
  - `text-embedding-3-small`: 1536 dimensions, faster/cost-effective

- **Google Gemini**
  - `gemini-embedding-001`: up to 3072 dimensions, multilingual support

- **VoyageAI** (Legal-Optimized)
  - `voyage-law-2`: 16,000 dimensions, specialized for legal retrieval and RAG

### Switching Providers

Update your `.env` file:
```bash
EMBEDDING_PROVIDER=voyageai
EMBEDDING_MODEL=voyage-law-2
```

**Note**: Switching providers requires re-ingesting all documents due to different vector dimensions.

### Performance Recommendations

- **Legal Documents**: Use `voyage-law-2` for best retrieval accuracy
- **General Purpose**: Use `text-embedding-3-large` (OpenAI)
- **Cost-Effective**: Use `text-embedding-3-small` (OpenAI) or `gemini-embedding-001`
```

## 🔄 **Migration Strategy**

### **Option A: Environment Variable Switching** (Recommended)
- Users can switch providers by changing `EMBEDDING_PROVIDER` in `.env`
- Automatic re-ingestion on next startup
- Simple, no code changes needed

### **Option B: Runtime API Endpoint** (Future Enhancement)
- Add `/api/admin/switch-embedding-provider` endpoint
- Allows switching without restarting the service
- More complex implementation

## ⚠️ **Important Considerations**

### **Dimension Differences**
| Provider | Model | Dimensions | Impact |
|----------|-------|------------|---------|
| OpenAI | text-embedding-3-large | 3072 | Baseline |
| OpenAI | text-embedding-3-small | 1536 | Requires re-ingestion |
| Google | gemini-embedding-001 | up to 3072 | Compatible with OpenAI large |
| VoyageAI | voyage-law-2 | 16,000 | Requires re-ingestion |

### **Token Limits**
- **OpenAI**: 8191 tokens (most flexible)
- **Gemini**: 2048 tokens (smaller chunks needed)
- **VoyageAI**: 1024 tokens (smallest chunks needed)

### **Costs & Performance**
- Different pricing models per provider
- VoyageAI `voyage-law-2`: Optimized for legal domain, potentially higher accuracy
- Cloud providers generally faster than local alternatives

### **API Limits**
- Each provider has different rate limits and quotas
- Monitor usage patterns when switching providers

## 🎯 **Success Criteria**

- ✅ All three providers work for embedding queries
- ✅ Switching providers triggers automatic re-ingestion
- ✅ No breaking changes to existing API
- ✅ Clear error messages for invalid configurations
- ✅ Performance benchmarks show voyage-law-2 improves legal retrieval
- ✅ Documentation covers all provider options

## 📊 **Testing Checklist**

### **Unit Tests**
- [ ] Factory function creates correct embedder types
- [ ] Provider/model validation works
- [ ] Dimension compatibility checks
- [ ] Error handling for invalid configurations

### **Integration Tests**
- [ ] Full ingestion pipeline works with each provider
- [ ] Query retrieval accuracy maintained across providers
- [ ] Performance benchmarks for each provider
- [ ] Memory usage within acceptable limits

### **End-to-End Tests**
- [ ] Provider switching via environment variables
- [ ] Data persistence across restarts
- [ ] Error recovery and fallback mechanisms

## 🚀 **Quick Start**

1. **Install Dependencies**
   ```bash
   pip install langchain-google-genai langchain-voyageai
   ```

2. **Configure Environment**
   ```bash
   echo "GOOGLE_API_KEY=your_key" >> .env
   echo "VOYAGE_API_KEY=your_key" >> .env
   ```

3. **Switch to Legal-Optimized Embeddings**
   ```bash
   echo "EMBEDDING_PROVIDER=voyageai" >> .env
   echo "EMBEDDING_MODEL=voyage-law-2" >> .env
   ```

4. **Re-ingest Data**
   ```bash
   # Clear existing data and re-ingest
   rm -rf db/chroma/*
   python -m src.ingest
   ```

---

*This implementation leverages existing dimension-handling infrastructure, making provider switching seamless and requiring minimal changes to the core RAG pipeline.*
