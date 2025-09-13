import os
from dotenv import load_dotenv
load_dotenv()

# Vectorstore persistence
BASE_DIR       = os.path.dirname(os.path.dirname(__file__))
DATA_DIR       = os.path.join(BASE_DIR, "data", "bills")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "db", "chroma")

# API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding & LLM config
EMBEDDING_MODEL = "text-embedding-ada-002"
LLM_INGEST      = "gpt-4o-mini"
LLM_SUMMARY     = "o4-mini"
LLM_ROUTING = "gpt-4o"

# Chunking parameters
CHUNK_SIZE      = 1500
CHUNK_OVERLAP   = 200


# Mapping of division names to their respective database names
subcommittee_stores = division_to_db = {
    "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_A_MILITARY_CONSTRUCTION_VETERANS_AFFAIRS_AND_RELATED_AGENCIES",
    "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_B_AGRICULTURE_RURAL_DEVELOPMENT_FOOD_AND_DRUG_ADMINISTRATION_AND_RELATED_AGENCIES",
    "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_C_COMMERCE_JUSTICE_SCIENCE_AND_RELATED_AGENCIES",
    "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_D_ENERGY_AND_WATER_DEVELOPMENT_AND_RELATED_AGENCIES",
    "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_E_DEPARTMENT_OF_THE_INTERIOR_ENVIRONMENT_AND_RELATED_AGENCIES",
    "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_F_TRANSPORTATION_HOUSING_AND_URBAN_DEVELOPMENT_AND_RELATED_AGENCIES",
    "OTHER MATTERS": "Consolidated_Appropriations_Act_2024_Public_Law_html_Division_G_OTHER_MATTERS",
    
    # Further Consolidated
    "DEPARTMENT OF DEFENSE": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_A_DEPARTMENT_OF_DEFENSE",
    "FINANCIAL SERVICES AND GENERAL GOVERNMENT": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_B_FINANCIAL_SERVICES_AND_GENERAL_GOVERNMENT",
    "DEPARTMENT OF HOMELAND SECURITY": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_C_DEPARTMENT_OF_HOMELAND_SECURITY",
    "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_D_DEPARTMENTS_OF_LABOR_HEALTH_AND_HUMAN_SERVICES_AND_EDUCATION_AND_RELATED_AGENCIES",
    "LEGISLATIVE BRANCH": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_E_LEGISLATIVE_BRANCH",
    "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_F_DEPARTMENT_OF_STATE_FOREIGN_OPERATIONS_AND_RELATED_PROGRAMS",
    "OTHER MATTERS (FURTHER)": "Further_Consolidated_Appropriations_Act_2024_Public_Law_html_Division_G_OTHER_MATTERS"
}

# Prompt for routing questions to the appropriate subcommittees
routing_prompt = """
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
    """





