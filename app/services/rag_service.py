"""
RAG Service for LawSearch AI

Contains the core RAG logic transplanted from src/query.py into a proper service class.
Handles LangGraph workflow, ChromaDB interactions, and response formatting.
"""

import logging

# MUST be at the very top before any other imports
import sys
import os

# Handle SQLite compatibility for different environments
# In Docker, use system sqlite3. In local development, try pysqlite3-binary if available
if os.getenv('ENVIRONMENT') != 'production' and not os.path.exists('/.dockerenv'):
    # Only try to use pysqlite3 in local development
    try:
        import pysqlite3
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass  # Will use system sqlite if pysqlite3 not available
# In Docker/production, always use system sqlite3

import time
import ast
import uuid
from typing import List, Dict, Optional, Any
from functools import lru_cache
from datetime import datetime

# Import LangChain components
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

# Import from new config system
from app.core.config import get_settings

# Import our new models
from app.models.query import QueryRequest, QueryResponse, SourceDocument, IngestResponse

logger = logging.getLogger(__name__)


def create_llm_for_speed(speed: str, task: str) -> ChatOpenAI:
    """Create LLM instance with correct parameters for thinking speed and task."""
    logger.info(f"Creating LLM for speed='{speed}', task='{task}'")

    # Routing is always gpt-4o-mini regardless of speed
    if task == "routing":
        logger.info("Selected routing LLM: gpt-4o-mini")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

    if speed == "quick":
        # All tasks use gpt-4o-mini for maximum speed
        logger.info("Selected quick LLM: gpt-4o-mini")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

    elif speed == "normal":
        if task == "generation":
            logger.info("Selected normal generation LLM: gpt-4o")
            return ChatOpenAI(model="gpt-4o", temperature=0)
        elif task == "summarization":
            logger.info("Selected normal summarization LLM: o4-mini")
            return ChatOpenAI(model="o4-mini")  # O4-mini for summarization

    elif speed == "long":
        if task == "generation":
            logger.info("Selected long generation LLM: gpt-5 with model_kwargs")
            return ChatOpenAI(
                model="gpt-5",
                reasoning_effort="medium",
                model_kwargs={
                    "verbosity": "high"
                }
                
            )
        elif task == "summarization":
            logger.info("Selected long summarization LLM: gpt-5 with high reasoning")
            return ChatOpenAI(
                model="gpt-5",
                reasoning_effort="high",
                model_kwargs={
                    "verbosity": "medium"
                },
                
            )

    # Default fallback
    logger.warning(f"No specific LLM configuration found for speed='{speed}', task='{task}', using default: gpt-4o")
    return ChatOpenAI(model="gpt-4o", temperature=0)


def get_retrieval_k_for_speed(speed: str) -> int:
    """Get the number of chunks to retrieve based on thinking speed."""
    k_values = {
        "quick": 6,
        "normal": 9,
        "long": 15
    }
    k = k_values.get(speed, 9)  # Default to normal (9)
    logger.info(f"Selected retrieval k-value for speed '{speed}': {k}")
    return k

class RAGState(TypedDict):
    """State structure that flows through the LangGraph workflow."""
    question: Annotated[str, "input"]
    thinking_speed: Annotated[str, "thinking speed mode"]
    selected_subcommittees: List[str]
    subcommittee_answers: Annotated[List[str], add_messages]
    final_answer: str

class RAGService:
    """
    RAG Service for processing legislative queries.
    
    Transplants and refactors the existing query.py logic into a proper service class
    with async methods and structured responses.
    """
    
    def __init__(self):
        """Initialize the RAG service with LLMs and configuration."""
        logger.info("Initializing RAG service")
        # Get settings
        self.settings = get_settings()

        # Cache for dynamically created LLMs
        self.llm_cache = {}

        # Initialize LLMs for different tasks
        self.qa_llm = ChatOpenAI(model_name=self.settings.llm_ingest, temperature=0)
        self.summary_llm = ChatOpenAI(model_name=self.settings.llm_summary)
        self.routing_llm = ChatOpenAI(model_name=self.settings.llm_routing, temperature=0)

        # Set up embedding model
        self.embedder = OpenAIEmbeddings(model=self.settings.embedding_model)
        logger.info(f"RAG service initialized with embedding model: {self.settings.embedding_model}")
        
        # Prompt templates (transplanted from your original code)
        self.map_prompt = PromptTemplate(
            template="""
You are an expert legislative financial analyst at a premier lobbying firm. Extract key financial and legislative information from the following context to answer the question.

1. **Extract** every dollar figure, fiscal year, agency/department name, or section number from the context.
2. **Include** only information relevant to the question.
3. **Keep** each statement concise with one numeric fact per sentence when possible.

Context:
{context}

Question:
{question}

Extracted Information:
""",
            input_variables=["context", "question"],
        )
        
        self.combine_prompt = PromptTemplate(
            template="""
You are an expert legislative financial analyst at a premier lobbying firm. Synthesize the following extracted information into a comprehensive answer.

1. **Integrate** all relevant dollar figures, fiscal years, agency names, and section references.
2. **Maintain** all citations in square brackets.
3. **Present** a concise, policy-brief tone—clear, authoritative, and numerically accurate.
4. **Eliminate** redundancies while preserving all unique information.
5. **Organize** information logically by topic, agency, or fiscal year as appropriate.
6. **Use bullet points** (- ) for any lists. Use nested bullets for related details. Format like:
   - **Main Program**: $Amount
     - Related detail or sub-allocation
   - **Another Program**: $Amount

Example Format:
The National Aeronautics and Space Administration (NASA) has been allocated funding through the Commerce, Justice, Science, and Related Agencies appropriations.

**Total Allocation**: $7,666,200,000 (available until September 30, 2025)

**Program Breakdown**:
- **Science research and development**: $3,129,000,000
- **Aeronautics research and development**: $935,000,000
  - Up to $1,000,000 available for grant disbursements
- **Space technology research and development**: $1,100,000,000
- **Space operations research and development**: $4,220,000,000

**Special Provisions**:
- **Emergency requirements**: $450,000,000 under section 251(b)(2)(A)(i)
- **Working Capital Fund transfer**: Up to $32,600,000
- **Legal authority**: Sections 5901 and 5902 of title 5, U.S. Code

Question:
{question}

Extracted Information:
{summaries}

Comprehensive Answer:
""",
            input_variables=["summaries", "question"],
        )

    def get_llm_for_task(self, thinking_speed: str, task: str) -> ChatOpenAI:
        """Get or create LLM for specific thinking speed and task."""
        cache_key = f"{thinking_speed}_{task}"

        if cache_key not in self.llm_cache:
            logger.info(f"Creating new LLM for cache key: {cache_key}")
            self.llm_cache[cache_key] = create_llm_for_speed(thinking_speed, task)
        else:
            logger.debug(f"Using cached LLM for cache key: {cache_key}")

        return self.llm_cache[cache_key]

    @lru_cache(maxsize=None)
    def get_store(self, label: str) -> Chroma:
        """Lazily load a vectorstore only when needed (transplanted from original)."""
        path = os.path.join(str(self.settings.vectorstore_dir), label)
        logger.info(f"Loading vectorstore for label: {label} from path: {path}")

        from chromadb.config import Settings
        client_settings = Settings(
            persist_directory=path,
            is_persistent=True
        )

        return Chroma(
            persist_directory=path,
            embedding_function=self.embedder,
            client_settings=client_settings
        )

    def route_subcommittees(self, state: RAGState) -> dict:
        """Route the question to appropriate subcommittees (transplanted from original)."""
        question = state["question"]
        thinking_speed = state.get("thinking_speed", "normal")
        logger.info(f"Routing question with thinking speed: {thinking_speed}")
        formatted_prompt = self.settings.routing_prompt.format(question=question)

        # Get routing LLM based on thinking speed
        routing_llm = self.get_llm_for_task(thinking_speed, "routing")
        response = routing_llm.invoke(formatted_prompt)
        content = response.content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            code_lines = [line for line in lines[1:-1] if line.strip()]
            if code_lines:
                content = "\n".join(code_lines)

        # Parse LLM response
        try:
            subcommittees = ast.literal_eval(content)
            logger.info(f"Selected subcommittees: {subcommittees}")
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Error parsing routing response: {e}")
            subcommittees = []

        return {"selected_subcommittees": subcommittees}

    def make_map_reduce_node(self, name: str, path: str) -> RunnableLambda:
        """Create a map-reduce node for a specific division (transplanted from original)."""
        logger.info(f"Creating map-reduce node for: {name}")

        def node_fn(state: RAGState) -> RAGState:
            # Get thinking speed and dynamic k-value
            thinking_speed = state.get("thinking_speed", "normal")
            k_value = get_retrieval_k_for_speed(thinking_speed)

            # Create retriever with dynamic k-value
            retriever = self.get_store(path).as_retriever(search_kwargs={"k": k_value})
            logger.info(f"Created retriever with k={k_value} for subcommittee: {name}")

            # Get LLM for generation task
            generation_llm = self.get_llm_for_task(thinking_speed, "generation")

            # Test retriever to see how many docs it actually returns
            test_docs = retriever.get_relevant_documents(state["question"])
            logger.info(f"Retriever returned {len(test_docs)} documents for subcommittee: {name}")

            chain = RetrievalQA.from_chain_type(
                llm=generation_llm,
                retriever=retriever,
                chain_type="map_reduce",
                chain_type_kwargs={
                    "question_prompt": self.map_prompt,
                    "combine_prompt": self.combine_prompt,
                },
                return_source_documents=False,  # Match original implementation
            )

            logger.info(f"Starting map-reduce processing for subcommittee: {name}")
            result = chain.invoke(state["question"])
            logger.info(f"Completed map-reduce processing for subcommittee: {name}")
            
            # Extract the text result from the chain response (match original implementation)
            if isinstance(result, dict) and "result" in result:
                result_text = result["result"]
            else:
                result_text = str(result)
            
            # Return the answer without subcommittee name (shown separately in UI)
            return {"subcommittee_answers": [result_text]}
        
        return RunnableLambda(node_fn)

    def merge_node(self, state: RAGState) -> dict:
        """Merge all subcommittee answers (transplanted from original)."""
        subcommittee_answers = state["subcommittee_answers"]
        logger.info(f"Merging {len(subcommittee_answers)} subcommittee answers")

        if not subcommittee_answers:
            logger.warning("No subcommittee answers to merge")
            return {"final_answer": "No answers found."}

        # Handle both string and message object formats
        if hasattr(subcommittee_answers[0], 'content'):
            # Message objects - extract content
            merged = "\n\n".join(msg.content for msg in subcommittee_answers)
            logger.info("Merged answers from message objects")
        else:
            # String format - use directly
            merged = "\n\n".join(subcommittee_answers)
            logger.info("Merged answers from string format")

        return {"final_answer": merged}

    def build_graph(self) -> any:
        """Build the LangGraph workflow (transplanted from original)."""
        logger.info("Building LangGraph workflow")
        graph = StateGraph(RAGState)

        # Add nodes
        graph.add_node("router", RunnableLambda(self.route_subcommittees))
        graph.add_node("merge", RunnableLambda(self.merge_node))

        # Create query nodes for each subcommittee
        subcommittee_nodes = {}
        for label, path in self.settings.subcommittee_stores.items():
            node_id = f"query_{label}"
            graph.add_node(node_id, self.make_map_reduce_node(label, path))
            graph.add_edge(node_id, "merge")
            subcommittee_nodes[label] = node_id

        logger.info(f"Created {len(subcommittee_nodes)} subcommittee query nodes")

        # Set up routing with proper handling of the selection
        def route_to_nodes(state):
            selected = state["selected_subcommittees"]
            # If no subcommittees selected after routing, something went wrong
            # This should not happen with proper routing, but handle gracefully
            if not selected:
                logger.warning(f"No subcommittees selected by router for question: {state['question']}")
                return []
            return selected

        graph.add_conditional_edges(
            "router",
            route_to_nodes,
            subcommittee_nodes,
        )

        graph.set_entry_point("router")
        graph.set_finish_point("merge")
        compiled_graph = graph.compile()
        logger.info("LangGraph workflow built successfully")
        return compiled_graph

    async def process_query(
        self,
        request: QueryRequest,
        query_id: Optional[str] = None
    ) -> QueryResponse:
        """
        Process a query request and return structured response.

        Main method that handles the entire RAG workflow and returns
        data in the format expected by the API.
        """
        start_time = time.time()

        if query_id is None:
            query_id = f"query_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        logger.info(f"Processing query {query_id} with thinking speed: {request.thinking_speed or 'normal'}")
        logger.info(f"Request thinking_speed attribute: {getattr(request, 'thinking_speed', 'NOT_SET')}")

        # Build the workflow graph
        app = self.build_graph()

        # Prepare initial state to match workshop version exactly
        thinking_speed = request.thinking_speed or "normal"
        logger.info(f"Using thinking_speed: {thinking_speed} for query {query_id}")

        initial_state = {
            "question": request.question,
            "thinking_speed": thinking_speed,
            "selected_subcommittees": [],
            "subcommittee_answers": [],
            "final_answer": "",
        }

        try:
            # Execute the RAG workflow
            logger.info(f"Executing RAG workflow for query {query_id}")
            result = app.invoke(initial_state, config={"recursion_limit": 25})

            processing_time = time.time() - start_time
            logger.info(f"Query {query_id} processed successfully in {processing_time:.2f}s")

            # Return structured response (sources disabled to match original implementation)
            return QueryResponse(
                answer=result["final_answer"],
                processing_time=processing_time,
                selected_divisions=result["selected_subcommittees"],
                sources=None,  # Sources disabled per user preference
                query_id=query_id,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Query {query_id} failed after {processing_time:.2f}s: {str(e)}")
            # Return error in structured format
            raise Exception(f"RAG processing failed: {str(e)}")

    async def ingest_data(
        self,
        embedding_model: str,
        clear_existing: bool = True,
        ingest_id: Optional[str] = None
    ) -> tuple[IngestResponse, str]:
        """
        Re-ingest vector databases with a different embedding model.

        This method allows dynamic switching of embedding models at runtime
        without restarting the container.

        Args:
            embedding_model: The OpenAI embedding model to use
            clear_existing: Whether to clear existing vector stores
            ingest_id: Optional ID for tracking this ingestion

        Returns:
            IngestResponse: Results of the ingestion operation
        """
        import time
        import subprocess
        import sys

        start_time = time.time()
        logger.info(f"Starting data ingestion with embedding model: {embedding_model}, clear_existing: {clear_existing}")

        try:
            # Clear existing vector stores if requested
            if clear_existing:
                import shutil
                import os
                chroma_dir = str(self.settings.vectorstore_dir)
                if os.path.exists(chroma_dir):
                    # When switching embedding models, we need to completely clear
                    # the entire ChromaDB directory because collections are tied to
                    # specific embedding dimensions and are incompatible between models
                    shutil.rmtree(chroma_dir)
                    os.makedirs(chroma_dir, exist_ok=True)
                    logger.info(f"Cleared existing ChromaDB directory: {chroma_dir}")
                else:
                    logger.info("No existing ChromaDB directory to clear")

            # Update the embedding model for this service instance
            self.embedder = OpenAIEmbeddings(model=embedding_model)

            # Clear the cached stores so they get recreated with new embedder
            self.get_store.cache_clear()
            logger.info("Cleared LLM and store caches")

            # Run the ingestion script as a subprocess
            # We need to run it in the same Python environment
            cmd = [sys.executable, "-m", "src.ingest", "--embedding-model", embedding_model]
            env = os.environ.copy()
            env["PYTHONPATH"] = "/app"
            # Ensure the API key is available
            if "OPENAI_API_KEY" not in env and hasattr(self.settings, 'openai_api_key'):
                env["OPENAI_API_KEY"] = self.settings.openai_api_key

            logger.info(f"Running ingestion subprocess with command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd="/app",
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Ingestion subprocess failed with return code {result.returncode}: {result.stderr}")
                raise Exception(f"Ingestion failed: {result.stderr}")

            # Count how many divisions were processed
            # The ingestion script outputs "Created Chroma DB for..." messages
            output_lines = result.stdout.split('\n')
            divisions_processed = sum(1 for line in output_lines if "Created Chroma DB for" in line)
            logger.info(f"Ingestion completed, processed {divisions_processed} divisions")

            processing_time = time.time() - start_time

            response = IngestResponse(
                status="completed",
                message=f"Successfully ingested {divisions_processed} divisions using {embedding_model}",
                embedding_model=embedding_model,
                divisions_processed=divisions_processed,
                processing_time=processing_time
            )

            # Update the RAG service's embedder to match the new model
            self.embedder = OpenAIEmbeddings(model=embedding_model)
            self.get_store.cache_clear()

            logger.info(f"Data ingestion completed successfully in {processing_time:.2f}s")
            return response, embedding_model

        except subprocess.TimeoutExpired:
            processing_time = time.time() - start_time
            logger.error(f"Ingestion timed out after {processing_time:.1f}s")
            raise Exception(f"Ingestion timed out after {processing_time:.1f} seconds")

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Ingestion failed after {processing_time:.1f}s: {str(e)}")
            raise Exception(f"Ingestion failed after {processing_time:.1f} seconds: {str(e)}")

    async def health_check(self) -> Dict[str, str]:
        """Check the health of the RAG service and its dependencies."""
        logger.info("Performing health check")
        try:
            # Test database connectivity
            available_stores = [
                name for name in os.listdir(str(self.settings.vectorstore_dir))
                if os.path.isdir(os.path.join(str(self.settings.vectorstore_dir), name))
            ]

            logger.info(f"Found {len(available_stores)} available vector stores")

            if not available_stores:
                logger.warning("Health check failed: No vector databases found")
                return {"status": "unhealthy", "reason": "No vector databases found"}

            # Test one store
            test_store_name = available_stores[0]
            logger.info(f"Testing connectivity with store: {test_store_name}")
            test_store = self.get_store(test_store_name)
            # Quick test query (this might need adjustment based on your ChromaDB setup)

            logger.info("Health check passed")
            return {
                "status": "healthy",
                "database_status": "connected",
                "available_divisions": str(len(available_stores))
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "reason": f"Database connectivity issue: {str(e)}"
            }


# Global service instance (singleton pattern)
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        logger.info("Creating new RAG service instance (singleton)")
        _rag_service = RAGService()
    else:
        logger.debug("Returning existing RAG service instance")
    return _rag_service