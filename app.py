
# Legacy Streamlit app - Moved to app/main.py for FastAPI
# This file is kept for reference but should not be used in production
# To run the FastAPI version: uvicorn app.main:app --reload
# To run this legacy version: streamlit run app.py

import os

from dotenv import load_dotenv

import streamlit as st
import time

# Note: These imports will fail if src/ directory doesn't exist
# The new FastAPI version is in app/ directory
try:
    from src.ingest import ingest_all as ingest_main
    from src.query import build_graph
except ImportError:
    st.error("Legacy source files not found. Please use the FastAPI version: uvicorn app.main:app --reload")
    st.stop()

# ─── Load environment ───────────────────────────────────────────────────────────────
load_dotenv()  # so OPENAI_API_KEY is available to src.query

# ─── Page config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LawSearch AI",
    page_icon="⚖️",
    layout="wide",
)

st.title("LawSearch AI")
st.markdown(
    "Ask natural-language questions about the 2024-2025 U.S. federal appropriations bills "
    "and get precise, cited answers with budget allocations and legislative details."
)

# ─── Sidebar: Sample Questions ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("Sample Questions")
    st.markdown("Click any question below to run it automatically:")
    
    if st.button("How much funding did FEMA receive?"):
        st.session_state.query = "What was FEMA's Funding?"
        st.rerun()
        
    if st.button("How much is allocated for defense spending?"):
        st.session_state.query = "How much is defense spending?"
        st.rerun()
        
    if st.button("Summarize environmental spending"):
        st.session_state.query = "Summarize all environmental spending in these bills."
        st.rerun()

# ─── Build/cache the RAG graph ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_rag_pipeline():
    """Compile your LangGraph RAG pipeline once (and recompile on clear)."""
    return build_graph()

# ─── Main query interface ───────────────────────────────────────────────────────────
# Use session state to maintain the query between reruns
if "query" not in st.session_state:
    st.session_state.query = ""

query = st.text_input(
    "Enter your question:",
    value=st.session_state.query,
    placeholder="e.g. How much funding did FEMA receive?",
)
# Keep session state in sync with input field
st.session_state.query = query

if query:
    graph = get_rag_pipeline()
    with st.spinner("Running RAG pipeline…"):
        start = time.time()
        try:
            init_state = {
                "question": query,
                "selected_subcommittees": [],
                "subcommittee_answers": [],
                "final_answer": "",
            }
            result = graph.invoke(init_state, config={"recursion_limit": 25})
            elapsed = time.time() - start

            st.subheader("Answer")
            st.write(result.get("final_answer", "No answer returned."))

            # show per-division details, if any
            if result.get("subcommittee_answers"):
                with st.expander("🔍 View details by subcommittee"):
                    for ans in result["subcommittee_answers"]:
                        st.code(ans, language="")

            st.caption(f"⏱️ Completed in {elapsed:.2f}s")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.caption("Make sure you've ingested bills and set OPENAI_API_KEY in `.env`.")