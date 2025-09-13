#!/usr/bin/env python3
"""
Debug script to see what documents are actually being passed to the LLM.
"""

import os
import sys

# Add current directory to path
sys.path.append('.')

# Load environment variables properly
from dotenv import load_dotenv
load_dotenv()

def test_what_llm_sees():
    """Test what documents the retriever actually returns."""

    from app.services.rag_service import RAGService

    try:
        service = RAGService()
        store = service.get_store('Consolidated_Appropriations_Act_2024_Public_Law_html_Division_C_COMMERCE_JUSTICE_SCIENCE_AND_RELATED_AGENCIES')
        
        # Test the retriever directly
        retriever = store.as_retriever(search_kwargs={"k": 20})
        
        question = "how much money is appropriated for nasa"
        print(f"Question: {question}")
        print("=" * 50)
        
        # Get documents that would be passed to the LLM
        docs = retriever.invoke(question)
        
        print(f"Retrieved {len(docs)} documents:")
        
        nasa_found = False
        funding_found = False
        
        for i, doc in enumerate(docs):
            content = doc.page_content
            content_lower = content.lower()
            
            has_nasa = any(keyword in content_lower for keyword in ['nasa', 'aeronautics', 'space administration'])
            has_funding = any(keyword in content_lower for keyword in ['$', 'million', 'billion', 'appropriated'])
            
            print(f"\n--- Document {i+1} ---")
            print(f"NASA content: {has_nasa}")
            print(f"Funding content: {has_funding}")
            print(f"Content preview: {content[:300]}...")
            
            if has_nasa:
                nasa_found = True
                print("*** THIS CONTAINS NASA! ***")
                if has_funding:
                    funding_found = True
                    print("*** AND FUNDING! ***")
        
        print(f"\nSummary:")
        print(f"NASA documents found: {nasa_found}")
        print(f"NASA + Funding documents found: {funding_found}")
        
        if not funding_found:
            print("\n!!! PROBLEM: No NASA funding documents in retrieval results !!!")
            print("The vector search is not finding the NASA funding documents!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_what_llm_sees()
