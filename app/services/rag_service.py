"""
RAG Service for LawSearch AI

Contains the core RAG logic transplanted from src/query.py into a proper service class.
Handles LangGraph workflow, ChromaDB interactions, and response formatting.
"""

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
from typing import List, Dict, Optional
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
from app.models.query import QueryRequest, QueryResponse, SourceDocument


class RAGState(TypedDict):
    """State structure that flows through the LangGraph workflow."""
    question: Annotated[str, "input"]
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
        # Get settings
        self.settings = get_settings()
        
        # Initialize LLMs for different tasks
        self.qa_llm = ChatOpenAI(model_name=self.settings.llm_ingest, temperature=0)
        self.summary_llm = ChatOpenAI(model_name=self.settings.llm_summary)
        self.routing_llm = ChatOpenAI(model_name=self.settings.llm_routing, temperature=0)
        
        # Set up embedding model
        self.embedder = OpenAIEmbeddings(model=self.settings.embedding_model)
        
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

Question:
{question}

Extracted Information:
{summaries}

Comprehensive Answer:
""",
            input_variables=["summaries", "question"],
        )

    @lru_cache(maxsize=None)
    def get_store(self, label: str) -> Chroma:
        """Lazily load a vectorstore only when needed (transplanted from original)."""
        path = os.path.join(str(self.settings.vectorstore_dir), label)
        
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
        formatted_prompt = self.settings.routing_prompt.format(question=question)
        
        response = self.routing_llm.invoke(formatted_prompt)
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
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing routing response: {e}")
            subcommittees = []
        
        return {"selected_subcommittees": subcommittees}

    def make_map_reduce_node(self, name: str, path: str) -> RunnableLambda:
        """Create a map-reduce node for a specific division (transplanted from original)."""
        retriever = self.get_store(path).as_retriever(search_kwargs={"k": 8})
        
        def node_fn(state: RAGState) -> RAGState:
            chain = RetrievalQA.from_chain_type(
                llm=self.qa_llm,
                retriever=retriever,
                chain_type="map_reduce",
                chain_type_kwargs={
                    "question_prompt": self.map_prompt,
                    "combine_prompt": self.combine_prompt,
                },
                return_source_documents=False,  # Match original implementation
            )
            
            result = chain.invoke(state["question"])
            
            # Extract the text result from the chain response (match original implementation)
            if isinstance(result, dict) and "result" in result:
                result_text = result["result"]
            else:
                result_text = str(result)
            
            # Return the answer with the database name for identification
            return {"subcommittee_answers": [f"{name}:\n{result_text}"]}
        
        return RunnableLambda(node_fn)

    def merge_node(self, state: RAGState) -> dict:
        """Merge all subcommittee answers (transplanted from original)."""
        merged = "\n\n".join(msg.content for msg in state["subcommittee_answers"])
        
        return {"final_answer": merged}

    def build_graph(self) -> any:
        """Build the LangGraph workflow (transplanted from original)."""
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

        # Set up routing with proper handling of the selection
        def route_to_nodes(state):
            selected = state["selected_subcommittees"]
            # If no subcommittees selected after routing, something went wrong
            # This should not happen with proper routing, but handle gracefully
            if not selected:
                print(f"Warning: No subcommittees selected by router for question: {state['question']}")
                return []
            return selected

        graph.add_conditional_edges(
            "router",
            route_to_nodes,
            subcommittee_nodes,
        )

        graph.set_entry_point("router")
        graph.set_finish_point("merge")
        return graph.compile()

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
        
        # Build the workflow graph
        app = self.build_graph()
        
        # Prepare initial state to match workshop version exactly
        initial_state = {
            "question": request.question,
            "selected_subcommittees": [],
            "subcommittee_answers": [],
            "final_answer": "",
        }
        
        try:
            # Execute the RAG workflow
            result = app.invoke(initial_state, config={"recursion_limit": 25})
            
            processing_time = time.time() - start_time
            
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
            # Return error in structured format
            raise Exception(f"RAG processing failed: {str(e)}")

    async def health_check(self) -> Dict[str, str]:
        """Check the health of the RAG service and its dependencies."""
        try:
            # Test database connectivity
            available_stores = [
                name for name in os.listdir(str(self.settings.vectorstore_dir))
                if os.path.isdir(os.path.join(str(self.settings.vectorstore_dir), name))
            ]
            
            if not available_stores:
                return {"status": "unhealthy", "reason": "No vector databases found"}
            
            # Test one store
            test_store = self.get_store(available_stores[0])
            # Quick test query (this might need adjustment based on your ChromaDB setup)
            
            return {
                "status": "healthy",
                "database_status": "connected",
                "available_divisions": str(len(available_stores))
            }
            
        except Exception as e:
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
        _rag_service = RAGService()
    return _rag_service