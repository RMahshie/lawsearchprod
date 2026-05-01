"""Test environment setup."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
