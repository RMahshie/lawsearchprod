#!/usr/bin/env python3
# MUST be at the very top before any other imports
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass  # Will use system sqlite if pysqlite3 not available

import os
import time
import ast
from dotenv import load_dotenv
from functools import lru_cache  
from src.config import routing_prompt, subcommittee_stores, LLM_ROUTING

# Load environment variables from .env file to get API keys


# Import LangChain components for building the RAG pipeline
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# ChromaDB for vector storage and retrieval
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
from src.config import VECTORSTORE_DIR, EMBEDDING_MODEL, LLM_INGEST, LLM_SUMMARY

# LangGraph imports for building the agentic workflow
from typing import TypedDict, List
from typing_extensions import Annotated 

from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph
# from langgraph.constants import Fixed
from langchain_core.documents import Document

from langgraph.graph.message import add_messages

# Start timing the pipeline execution for performance monitoring
t0 = time.time()
print("[0.00] Starting RAG pipeline...")

# Initialize the different LLMs for specific tasks in our pipeline
qa_llm      = ChatOpenAI(model_name=LLM_INGEST, temperature=0)    # For extracting information from documents
summary_llm = ChatOpenAI(model_name=LLM_SUMMARY)                 # For summarizing results
routing_llm = ChatOpenAI(model_name=LLM_ROUTING , temperature=0) # For deciding which databases to query

# Set up the embedding model for converting text to vectors
embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

# Cache vectorstore instances to avoid reloading them repeatedly
@lru_cache(maxsize=None)
def get_store(label: str) -> Chroma:
    """Lazily load a vectorstore only when needed"""
    path = os.path.join(VECTORSTORE_DIR, label)
    
    # Configure ChromaDB with the correct settings for persistence
    from chromadb.config import Settings
    
    # Create client settings for persistent storage
    client_settings = Settings(
        persist_directory=path,
        is_persistent=True
    )
    
    return Chroma(
        persist_directory=path,
        embedding_function=embedder,
        client_settings=client_settings
    )

# Cache the list of available databases to avoid repeated filesystem calls
@lru_cache(maxsize=1)
def get_division_names():
    """Get all division names from the vectorstore directory"""
    return [
        name for name in os.listdir(VECTORSTORE_DIR)
        if os.path.isdir(os.path.join(VECTORSTORE_DIR, name))
    ]

# Prompt template for extracting key information from document chunks
map_prompt = PromptTemplate(
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

# Prompt template for combining extracted information into a final answer
combine_prompt = PromptTemplate(
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

# Define the state structure that flows through our agentic workflow
class RAGState(TypedDict):
    question: Annotated[str, "input"]                              # The user's original question
    selected_subcommittees: List[str]                              # Which databases the router selected
    subcommittee_answers: Annotated[List[str], add_messages]       # Answers from each database query
    final_answer: str                                              # The merged final response

def route_subcommittees(state: RAGState) -> dict:
    """Route the question to the appropriate subcommittees based on the question."""
    
    # Get the user's question from the current state
    question = state["question"]
    # Insert the question into our routing prompt template
    formatted_prompt = routing_prompt.format(question=question)
    
    # Ask the routing LLM which databases are relevant for this question
    response = routing_llm.invoke(formatted_prompt)
    content = response.content.strip()
    
    # Handle cases where the LLM returns code in markdown format
    if content.startswith("```"):
        # Extract the actual Python list from markdown code blocks
        lines = content.split("\n")
        # Remove the first line (```python) and last line (```)
        code_lines = [line for line in lines[1:-1] if line.strip()]
        if code_lines:
            content = "\n".join(code_lines)
    
    # Safely parse the LLM response as a Python list
    try:
        subcommittees = ast.literal_eval(content)
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing routing response: {e}")
        subcommittees = []
    
    print(f"\n[{time.time() - t0:.2f}] Routing response to databases: {subcommittees}")

    return {"selected_subcommittees": subcommittees}

def make_map_reduce_node(name: str, path: str) -> RunnableLambda:
    # Set up a retriever that will find the most relevant documents for our question
    retriever = get_store(path).as_retriever(search_kwargs={"k": 8})
    
    def node_fn(state: RAGState) -> RAGState:
        # Create a map-reduce chain that processes documents in parallel then combines results
        chain = RetrievalQA.from_chain_type(
            llm=qa_llm,
            retriever=retriever,
            chain_type="map_reduce",
            chain_type_kwargs={
                "question_prompt": map_prompt,      # How to extract info from each document
                "combine_prompt": combine_prompt,   # How to merge all extractions
            },
            return_source_documents=False,
        )
        
        print(f"[{time.time() - t0:.2f}] Querying {name} database...")
        
        # Run the retrieval and QA process for this specific database
        result = chain.invoke(state["question"])
        
        # Extract the text result from the chain response
        if isinstance(result, dict) and "result" in result:
            result_text = result["result"]
        else:
            result_text = str(result)

        # Return the answer with the database name for identification
        return {"subcommittee_answers": [f"{name}:\n{result_text}"]}
    
    return RunnableLambda(node_fn)

def merge_node(state: RAGState) -> dict:
    """Merge all subcommittee answers into a final answer."""
    
    print(f"[{time.time() - t0:.2f}] Merging subcommittee answers...")
    # Combine all the individual database responses into one comprehensive answer
    merged = "\n\n".join(msg.content for msg in state["subcommittee_answers"])

    print(f"[{time.time() - t0:.2f}] Finished merging subcommittee answers.")
    return { "final_answer": merged}

def build_graph(): 
    # Create the main workflow graph that orchestrates our RAG pipeline
    graph = StateGraph(RAGState)

    # Add the routing node that decides which databases to query
    graph.add_node("router", RunnableLambda(route_subcommittees))
    # Add the merge node that combines all database responses
    graph.add_node("merge", RunnableLambda(merge_node))

    # Create a query node for each available subcommittee database
    subcommittee_nodes = {}
    for label, path in subcommittee_stores.items():
        node_id = f"query_{label}"
        # Each node runs a map-reduce process on its specific database
        graph.add_node(node_id, make_map_reduce_node(label, path))
        # All query nodes flow their results to the merge node
        graph.add_edge(node_id, "merge")
        subcommittee_nodes[label] = node_id

    # Set up conditional routing: the router decides which query nodes to activate
    graph.add_conditional_edges(
        "router",
        lambda state: state["selected_subcommittees"],  # Use the router's selections
        subcommittee_nodes,                            # Map to actual node IDs
    )

    # Define the workflow: start with routing, end with merging
    graph.set_entry_point("router")
    graph.set_finish_point("merge")
    return graph.compile()

def main():
    # Get the user's question and build our RAG workflow
    question = input(f"[{time.time() - t0:.2f}] Your question: ")
    app = build_graph()
    
    # Initialize the state that will flow through our workflow
    initial_state = {
        "question": question,
        "selected_subcommittees": [],
        "subcommittee_answers": [],
        "final_answer": "",
    }

    # Execute the entire RAG workflow with the user's question
    result = app.invoke(initial_state, config={"recursion_limit": 25})

    # Display the final synthesized answer
    print("\n=== FINAL ANSWER ===")
    print(result["final_answer"])
    print(f"\n[{time.time() - t0:.2f}] Total time: {time.time() - t0:.2f} seconds")
    
if __name__ == '__main__':
    main()
