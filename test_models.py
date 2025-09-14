#!/usr/bin/env python3
"""
Simple test to verify model creation logic for different thinking speeds.
"""

# Mock ChatOpenAI class for testing
class MockChatOpenAI:
    def __init__(self, model=None, temperature=None, model_kwargs=None, **kwargs):
        self.model_name = model
        self.temperature = temperature
        self.model_kwargs = model_kwargs or {}

def create_llm_for_speed(speed: str, task: str) -> MockChatOpenAI:
    """Create LLM instance with correct parameters for thinking speed and task."""

    # Routing is always gpt-4o-mini regardless of speed
    if task == "routing":
        return MockChatOpenAI(model="gpt-4o-mini", temperature=0)

    if speed == "quick":
        # All tasks use gpt-4o-mini for maximum speed
        return MockChatOpenAI(model="gpt-4o-mini", temperature=0)

    elif speed == "normal":
        if task == "generation":
            return MockChatOpenAI(model="gpt-4o", temperature=0)
        elif task == "summarization":
            return MockChatOpenAI(model="o4-mini")  # O4-mini for summarization

    elif speed == "long":
        if task == "generation":
            return MockChatOpenAI(
                model="gpt-5",
                temperature=0,  # Lower temperature for generation
                model_kwargs={
                    "verbosity": "high",
                    "reasoning_effort": "medium"
                }
            )
        elif task == "summarization":
            return MockChatOpenAI(
                model="gpt-5",
                model_kwargs={
                    "verbosity": "medium",
                    "reasoning_effort": "high"  # Higher reasoning for summarization
                }
            )

    # Default fallback
    return MockChatOpenAI(model="gpt-4o", temperature=0)


def get_retrieval_k_for_speed(speed: str) -> int:
    """Get the number of chunks to retrieve based on thinking speed."""
    k_values = {
        "quick": 6,
        "normal": 9,
        "long": 15
    }
    return k_values.get(speed, 9)  # Default to normal (9)


def test_model_creation():
    """Test function to verify model creation works correctly."""
    print("🧪 Testing model creation for different thinking speeds:")
    print("=" * 60)

    test_cases = [
        ("quick", "routing"),
        ("quick", "generation"),
        ("normal", "routing"),
        ("normal", "generation"),
        ("normal", "summarization"),
        ("long", "routing"),
        ("long", "generation"),
        ("long", "summarization"),
    ]

    for speed, task in test_cases:
        try:
            llm = create_llm_for_speed(speed, task)
            params = []
            if hasattr(llm, 'temperature') and llm.temperature is not None:
                params.append(f"temp={llm.temperature}")
            if hasattr(llm, 'model_kwargs') and llm.model_kwargs:
                params.append(f"kwargs={llm.model_kwargs}")

            param_str = f" ({', '.join(params)})" if params else ""
            print(f"✅ {speed:6} + {task:12}: {llm.model_name}{param_str}")
        except Exception as e:
            print(f"❌ {speed:6} + {task:12}: {str(e)}")

    print("\n📊 Testing k-values:")
    print("=" * 30)
    for speed in ["quick", "normal", "long"]:
        k = get_retrieval_k_for_speed(speed)
        print(f"✅ {speed:6}: k={k} chunks")

    print("\n🎯 Summary:")
    print("- Routing: Always gpt-4o-mini (consistent)")
    print("- Quick: All tasks use gpt-4o-mini (fast)")
    print("- Normal: Generation=gpt-4o, Summarization=o4-mini (balanced)")
    print("- Long: Both tasks use gpt-5 with different parameters (quality)")
    print("- K-values: 6/9/15 chunks respectively")


if __name__ == "__main__":
    test_model_creation()
