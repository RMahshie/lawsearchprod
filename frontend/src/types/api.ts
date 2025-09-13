/**
 * TypeScript interfaces matching the backend Pydantic models.
 * These should stay in sync with app/models/query.py
 */

export interface QueryRequest {
  question: string;
  max_results?: number;
  include_sources?: boolean;
  divisions_filter?: string[];
}

export interface SourceDocument {
  division: string;
  content_snippet: string;
  confidence_score?: number;
}

export interface QueryResponse {
  answer: string;
  processing_time: number;
  selected_divisions: string[];
  sources?: SourceDocument[];
  timestamp: string;
  query_id?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  database_status?: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// API response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: ErrorResponse;
}

// Form state interfaces
export interface QueryFormData {
  question: string;
  maxResults: number;
  includeSources: boolean;
  selectedDivisions: string[];
}

// Available divisions (matching backend)
export const AVAILABLE_DIVISIONS = [
  "MILITARY CONSTRUCTION, VETERANS AFFAIRS, AND RELATED AGENCIES",
  "AGRICULTURE, RURAL DEVELOPMENT, FOOD AND DRUG ADMINISTRATION, AND RELATED AGENCIES", 
  "COMMERCE, JUSTICE, SCIENCE, AND RELATED AGENCIES",
  "ENERGY AND WATER DEVELOPMENT AND RELATED AGENCIES",
  "DEPARTMENT OF THE INTERIOR, ENVIRONMENT, AND RELATED AGENCIES",
  "TRANSPORTATION, HOUSING AND URBAN DEVELOPMENT, AND RELATED AGENCIES",
  "OTHER MATTERS",
  "DEPARTMENT OF DEFENSE", 
  "FINANCIAL SERVICES AND GENERAL GOVERNMENT",
  "DEPARTMENT OF HOMELAND SECURITY",
  "DEPARTMENTS OF LABOR, HEALTH AND HUMAN SERVICES, AND EDUCATION, AND RELATED AGENCIES",
  "LEGISLATIVE BRANCH",
  "DEPARTMENT OF STATE, FOREIGN OPERATIONS, AND RELATED PROGRAMS",
  "OTHER MATTERS (FURTHER)"
] as const;

export type DivisionName = typeof AVAILABLE_DIVISIONS[number];