"""
Configuration management for LawSearch AI.

Uses Pydantic BaseSettings for environment-based configuration with .env file support.
Centralizes all configuration constants from the original src/config.py plus new API settings.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings.
    
    Automatically loads from environment variables and .env files.
    Provides validation and type conversion.
    """
    
    # === API Configuration ===
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="Enable auto-reload in development")
    api_workers: int = Field(default=1, description="Number of worker processes")
    
    # === CORS Configuration ===
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://frontend:3000",
            "http://localhost:5173",  # Vite dev server default
        ],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    cors_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # === Directory Paths (from original src/config.py) ===
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default=None, description="Directory containing bill data")
    vectorstore_dir: Path = Field(default=None, description="Directory for vector databases")
    
    @field_validator('data_dir', mode='before')
    @classmethod
    def set_data_dir(cls, v, info):
        if v is None:
            return info.data['base_dir'] / "data" / "bills"
        return Path(v)
    
    @field_validator('vectorstore_dir', mode='before')
    @classmethod
    def set_vectorstore_dir(cls, v, info):
        if v is None:
            return info.data['base_dir'] / "db" / "chroma"
        return Path(v)
    
    # === OpenAI Configuration ===
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # === Model Configuration (from original src/config.py) ===
    embedding_model: str = Field(default="text-embedding-3-large", description="OpenAI embedding model")
    llm_ingest: str = Field(default="gpt-4o-mini", description="LLM for document processing")
    llm_summary: str = Field(default="o4-mini", description="LLM for summarization") 
    llm_routing: str = Field(default="gpt-4o", description="LLM for query routing")
    
    # === Chunking Parameters (from original src/config.py) ===
    chunk_size: int = Field(default=1500, description="Text chunk size for processing")
    chunk_overlap: int = Field(default=200, description="Overlap between text chunks")
    
    # === Logging Configuration ===
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path (optional)")
    
    # === Performance Configuration ===
    max_query_length: int = Field(default=1000, description="Maximum query length")
    max_results_per_division: int = Field(default=20, description="Max results per division")
    default_results_per_division: int = Field(default=8, description="Default results per division")
    query_timeout: int = Field(default=300, description="Query timeout in seconds")
    
    # === Division/Subcommittee Mapping (from original src/config.py) ===
    subcommittee_stores: Dict[str, str] = Field(
        default={
            "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_A_MILITARY_CONSTRUCTION_VETERANS_AFFAIRS_AND_RELATED_AGENCIES",
            "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_B_AGRICULTURE_RURAL_DEVELOPMENT_FOOD_AND_DRUG_ADMINISTRATION_AND_RELATED_AGENCIES",
            "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_C_COMMERCE_JUSTICE_SCIENCE_AND_RELATED_AGENCIES",
            "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_D_ENERGY_AND_WATER_DEVELOPMENT_AND_RELATED_AGENCIES",
            "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_E_DEPARTMENT_OF_THE_INTERIOR_ENVIRONMENT_AND_RELATED_AGENCIES",
            "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_F_TRANSPORTATION_HOUSING_AND_URBAN_DEVELOPMENT_AND_RELATED_AGENCIES",
            "OTHER MATTERS": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_G_OTHER_MATTERS",
            "DEPARTMENT OF DEFENSE": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_A_DEPARTMENT_OF_DEFENSE",
            "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_B_FINANCIAL_SERVICES_AND_GENERAL_GOVERNMENT",
            "DEPARTMENT OF HOMELAND SECURITY": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_C_DEPARTMENT_OF_HOMELAND_SECURITY",
            "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_D_DEPARTMENTS_OF_LABOR_HEALTH_AND_HUMAN_SERVICES_AND_EDUCATION_AND_RELATED_AGENCIES",
            "LEGISLATIVE BRANCH": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_E_LEGISLATIVE_BRANCH",
            "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_F_DEPARTMENT_OF_STATE_FOREIGN_OPERATIONS_AND_RELATED_PROGRAMS",
            "OTHER MATTERS (FURTHER)": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_G_OTHER_MATTERS"
        },
        description="Mapping of division names to database paths"
    )
    
    # === Routing Prompt (from original src/config.py) ===
    routing_prompt: str = Field(
        default="""
    You are an expert legislative financial analyst at a premier lobbying firm. 
    Given the question, identify the relevant subcommittees that should be queried.

    ONLY use the EXACT subcommittee names from this list:
    - MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES
    - AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES
    - COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES
    - ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES
    - DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES
    - TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES
    - OTHER MATTERS
    - DEPARTMENT OF DEFENSE
    - FINANCIAL SERVICES AND GENERAL GOVERNMENT
    - DEPARTMENT OF HOMELAND SECURITY
    - DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES
    - LEGISLATIVE BRANCH
    - DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS
    - OTHER MATTERS (FURTHER)
    
    Question: {question}

    Return ONLY a Python list of strings from the EXACT subcommittee names listed above.
    Example: ["DEPARTMENT OF HOMELAND SECURITY", "DEPARTMENT OF DEFENSE"]
    Relevant Subcommittees:
    """,
        description="Prompt template for routing queries to subcommittees"
    )
    
    # === Environment Detection ===
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=False, description="Debug mode")
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "production", "testing"]:
            raise ValueError("Environment must be development, production, or testing")
        return v
    
    @field_validator('debug', mode='before')
    @classmethod
    def set_debug_from_env(cls, v, info):
        # Auto-set debug based on environment if not explicitly set
        if v is None:
            return info.data.get('environment', 'development') == 'development'
        return v
    
    # === Computed Properties ===
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    @property
    def server_host_port(self) -> str:
        """Get formatted host:port string."""
        return f"{self.api_host}:{self.api_port}"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Allow environment variables to override settings
        env_prefix=""
    )


# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Get or create the global settings instance.
    
    This uses a singleton pattern to ensure settings are loaded once
    and reused throughout the application.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience functions for backwards compatibility with src/config.py
def get_vectorstore_dir() -> Path:
    """Get vectorstore directory path."""
    return get_settings().vectorstore_dir

def get_data_dir() -> Path:
    """Get data directory path.""" 
    return get_settings().data_dir

def get_subcommittee_stores() -> Dict[str, str]:
    """Get subcommittee to database mapping."""
    return get_settings().subcommittee_stores

def get_routing_prompt() -> str:
    """Get routing prompt template."""
    return get_settings().routing_prompt


# For backwards compatibility, expose common constants
settings = get_settings()
VECTORSTORE_DIR = str(settings.vectorstore_dir)
DATA_DIR = str(settings.data_dir)
EMBEDDING_MODEL = settings.embedding_model
LLM_INGEST = settings.llm_ingest
LLM_SUMMARY = settings.llm_summary
LLM_ROUTING = settings.llm_routing
CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
subcommittee_stores = settings.subcommittee_stores
routing_prompt = settings.routing_prompt