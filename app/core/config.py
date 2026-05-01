"""
Configuration management for LawSearch AI.

Uses Pydantic BaseSettings for environment-based configuration with .env file support.
Centralizes all configuration constants from the original src/config.py plus new API settings.
"""

from typing import List, Dict, Optional
from pathlib import Path
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


FY2026_INCOMPATIBLE_QUESTION_ANSWER = "This question is incompatible with the FY2026 appropriations text available in LawSearch."

FY2026_DIVISIONS = [
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES",
    "LEGISLATIVE BRANCH",
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
    "DEPARTMENT OF DEFENSE",
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT",
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS",
    "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS",
]

FY2026_SUBCOMMITTEE_STORES = {
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS_Division_B_AGRICULTURE_RURAL_DEVELOPMENT_FOOD_AND_DRUG_ADMINISTRATION_AND_RELATED_AGENCIES",
    "LEGISLATIVE BRANCH": "FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS_Division_C_LEGISLATIVE_BRANCH",
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS_Division_D_MILITARY_CONSTRUCTION_VETERANS_AFFAIRS_AND_RELATED_AGENCIES",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "FY2026_COMMERCEJUSTICESCIENCE_ENERGYWATERDEV_INTERIORENVIRONMENTAL_Division_A_COMMERCE_JUSTICE_SCIENCE_AND_RELATED_AGENCIES",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "FY2026_COMMERCEJUSTICESCIENCE_ENERGYWATERDEV_INTERIORENVIRONMENTAL_Division_B_ENERGY_AND_WATER_DEVELOPMENT_AND_RELATED_AGENCIES",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "FY2026_COMMERCEJUSTICESCIENCE_ENERGYWATERDEV_INTERIORENVIRONMENTAL_Division_C_DEPARTMENT_OF_THE_INTERIOR_ENVIRONMENT_AND_RELATED_AGENCIES",
    "DEPARTMENT OF DEFENSE": "FY2026_CONSOLIDATED_Division_A_DEPARTMENT_OF_DEFENSE",
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": "FY2026_CONSOLIDATED_Division_B_DEPARTMENTS_OF_LABOR_HEALTH_AND_HUMAN_SERVICES_AND_EDUCATION_AND_RELATED_AGENCIES",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "FY2026_CONSOLIDATED_Division_D_TRANSPORTATION_HOUSING_AND_URBAN_DEVELOPMENT_AND_RELATED_AGENCIES",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "FY2026_CONSOLIDATED_Division_E_FINANCIAL_SERVICES_AND_GENERAL_GOVERNMENT",
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": "FY2026_CONSOLIDATED_Division_F_DEPARTMENT_OF_STATE_FOREIGN_OPERATIONS_AND_RELATED_PROGRAMS",
    "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS": "FY2026_OTHER_CONTINUING_APPROPRIATIONS_EXTENDERS_HOMELAND_SECURITY_OTHER_MATTERS",
}

FY2026_DIVISION_ACRONYMS = {
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "AG",
    "LEGISLATIVE BRANCH": "LEG",
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "MCVA",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "CJS",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "EWD",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "INT",
    "DEPARTMENT OF DEFENSE": "DOD",
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": "LHHS",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "THUD",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "FSGG",
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": "SFOPS",
    "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS": "CRX",
}

FY2026_ROUTING_ALIASES = {
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "agriculture, USDA, rural development, FDA, food and drug, food safety, farm programs, nutrition programs, WIC, SNAP references when tied to agriculture appropriations.",
    "LEGISLATIVE BRANCH": "Congress, House, Senate, Capitol Police, Architect of the Capitol, Library of Congress, Government Accountability Office, GAO, Congressional Budget Office, CBO.",
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "military construction, MILCON, veterans affairs, VA, veterans health, veterans benefits, cemeteries, American Battle Monuments Commission.",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "CJS, Commerce, DOJ, Justice, FBI, DEA, ATF, prisons, NASA, NSF, NOAA, Census, NIST, science agencies.",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "Energy and Water, Department of Energy, DOE, Corps of Engineers, Bureau of Reclamation, water projects, nuclear security, NNSA.",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "Interior, DOI, EPA, environment, public lands, National Park Service, Bureau of Land Management, Fish and Wildlife, Indian Affairs, Forest Service, Smithsonian.",
    "DEPARTMENT OF DEFENSE": "Defense, DOD, military personnel, operation and maintenance, procurement, research and development, RDT&E, Army, Navy, Marine Corps, Air Force, Space Force.",
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": "Labor, DOL, HHS, Education, ED, NIH, CDC, CMS, public health, schools, Pell, student aid, workforce, OSHA.",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "THUD, Transportation, DOT, FAA, highways, transit, rail, maritime, HUD, housing, rental assistance, community development.",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "FSGG, Treasury, IRS, Executive Office of the President, judiciary, District of Columbia, GSA, OPM, SEC, FCC, FTC, SBA.",
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": "State, foreign operations, SFOPS, diplomacy, embassy, USAID, foreign assistance, international security assistance, export/import, Peace Corps.",
    "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS": "CR, continuing resolution, continuing appropriations, extensions, extenders, technical corrections, Homeland Security, DHS, FEMA, cybersecurity, E-Verify, H-2B, National Flood Insurance Program, NFIP, health care extenders, Medicare extenders, Medicaid extenders, VA extenders, other matters.",
}

FY2026_SOURCE_PARTS = {
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "B", "source_division_title": "Agriculture, Rural Development, Food and Drug Administration, and Related Agencies Appropriations Act, 2026"}
    ],
    "LEGISLATIVE BRANCH": [
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "C", "source_division_title": "Legislative Branch Appropriations Act, 2026"}
    ],
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "D", "source_division_title": "Military Construction, Veterans Affairs, and Related Agencies Appropriations Act, 2026"}
    ],
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm", "source_public_law": "P.L. 119-74", "source_division_letter": "A", "source_division_title": "Commerce, Justice, Science, and Related Agencies Appropriations Act, 2026"}
    ],
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm", "source_public_law": "P.L. 119-74", "source_division_letter": "B", "source_division_title": "Energy and Water Development and Related Agencies Appropriations Act, 2026"}
    ],
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_CommerceJusticeScience_EnergyWaterDev_INTERIOREnvironmental.htm", "source_public_law": "P.L. 119-74", "source_division_letter": "C", "source_division_title": "Department of the Interior, Environment, and Related Agencies Appropriations Act, 2026"}
    ],
    "DEPARTMENT OF DEFENSE": [
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "A", "source_division_title": "Department of Defense Appropriations Act, 2026"}
    ],
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "B", "source_division_title": "Departments of Labor, Health and Human Services, and Education, and Related Agencies Appropriations Act, 2026"}
    ],
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": [
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "D", "source_division_title": "Transportation, Housing and Urban Development, and Related Agencies Appropriations Act, 2026"}
    ],
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": [
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "E", "source_division_title": "Financial Services and General Government Appropriations Act, 2026"}
    ],
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": [
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "F", "source_division_title": "National Security, Department of State, and Related Programs Appropriations Act, 2026"}
    ],
    "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS": [
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "A", "source_division_title": "Continuing Appropriations Act, 2026"},
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "E", "source_division_title": "Extension of Agricultural Programs"},
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "F", "source_division_title": "Health Extenders"},
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "G", "source_division_title": "Department of Veterans Affairs Extenders"},
        {"source_file": "2026/FY2026_AGRICULTURE_LEGBRANCH_MILITARYCONSTRUCTIONVETERANSAFFAIRS.htm", "source_public_law": "P.L. 119-37", "source_division_letter": "H", "source_division_title": "Miscellaneous"},
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "G", "source_division_title": "Other Matters"},
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "H", "source_division_title": "Further Continuing Appropriations Act, 2026"},
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "I", "source_division_title": "Authorizing Extenders and Technical Corrections"},
        {"source_file": "2026/FY2026_CONSOLIDATED.htm", "source_public_law": "P.L. 119-75", "source_division_letter": "J", "source_division_title": "Health Care Extenders"},
    ],
}


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
    database_url: Optional[str] = Field(default=None, description="Application database URL")
    
    @field_validator('data_dir', mode='before')
    @classmethod
    def set_data_dir(cls, v, info):
        """Resolve the source data directory setting.

        Args:
            v: Explicit directory value from environment or settings input.
            info: Pydantic validation context containing already parsed fields.

        Returns:
            Path to the bill data directory.
        """
        if v is None:
            return info.data['base_dir'] / "data" / "bills"
        return Path(v)
    
    @field_validator('vectorstore_dir', mode='before')
    @classmethod
    def set_vectorstore_dir(cls, v, info):
        """Resolve the vector store directory setting.

        Args:
            v: Explicit directory value from environment or settings input.
            info: Pydantic validation context containing already parsed fields.

        Returns:
            Path to the Chroma vector store directory.
        """
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
        default=FY2026_SUBCOMMITTEE_STORES,
        description="Mapping of division names to database paths"
    )

    fy2026_source_parts: Dict[str, List[Dict[str, str]]] = Field(
        default=FY2026_SOURCE_PARTS,
        description="FY2026 source-file and source-division manifest"
    )

    routing_aliases: Dict[str, str] = Field(
        default=FY2026_ROUTING_ALIASES,
        description="Routing aliases and hints keyed by canonical division"
    )
    
    # === Environment Detection ===
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=False, description="Debug mode")
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate that the configured runtime environment is supported.

        Args:
            v: Environment string supplied by settings input.

        Returns:
            Validated environment string.
        """
        if v not in ["development", "production", "testing"]:
            raise ValueError("Environment must be development, production, or testing")
        return v
    
    @field_validator('debug', mode='before')
    @classmethod
    def set_debug_from_env(cls, v, info):
        """Resolve debug mode from explicit input or environment defaults.

        Args:
            v: Explicit debug value from environment or settings input.
            info: Pydantic validation context containing the environment value.

        Returns:
            Boolean debug setting.
        """
        # Auto-set debug based on environment if not explicitly set
        if v is None:
            return info.data.get('environment', 'development') == 'development'
        return v
    
    # === Computed Properties ===
    @property
    def is_development(self) -> bool:
        """Check if running in development mode.

        Args:
            None.

        Returns:
            True when environment is development, otherwise False.
        """
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode.

        Args:
            None.

        Returns:
            True when environment is production, otherwise False.
        """
        return self.environment == "production"
    
    @property
    def server_host_port(self) -> str:
        """Get formatted host and port string.

        Args:
            None.

        Returns:
            Host and port formatted as host:port.
        """
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
    """Get or create the global settings instance.

    Args:
        None.

    Returns:
        Singleton Settings object loaded from environment and defaults.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience functions for backwards compatibility with src/config.py
def get_vectorstore_dir() -> Path:
    """Get vector store directory path.

    Args:
        None.

    Returns:
        Path to the configured Chroma vector store directory.
    """
    return get_settings().vectorstore_dir

def get_data_dir() -> Path:
    """Get bill data directory path.

    Args:
        None.

    Returns:
        Path to the configured source bill data directory.
    """
    return get_settings().data_dir

def get_subcommittee_stores() -> Dict[str, str]:
    """Get division-to-vector-store mapping.

    Args:
        None.

    Returns:
        Mapping of division names to Chroma store directory names.
    """
    return get_settings().subcommittee_stores

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
