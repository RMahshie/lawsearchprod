/**
 * TypeScript interfaces matching the backend Pydantic models.
 * These should stay in sync with app/models/query.py
 */

export interface QueryRequest {
  question: string;
  max_results?: number;
  include_sources?: boolean;
  divisions_filter?: string[];
  thinking_speed?: 'quick' | 'normal' | 'long';
}

export interface SourceDocument {
  division: string;
  division_acronym: string;
  chunk_id: string;
  content_snippet: string;
  chunk_summary?: string;
  chunk_snapshot?: string;
  confidence_score?: number;
  metadata?: Record<string, unknown>;
}

export interface NumberAnnotationTarget {
  scope: 'answer' | 'division';
  division?: string;
}

export interface SourceNumberReference {
  chunk_id: string;
}

export interface DerivedNumberReference {
  equation: string;
  rationale?: string;
  input_ids: string[];
  source_input_ids: string[];
}

export type NumberAnnotation = {
  id: string;
  figure: string;
  value: number;
  label: string;
  targets: NumberAnnotationTarget[];
} & (
  | {
      kind: 'source';
      source: SourceNumberReference;
      derived?: never;
    }
  | {
      kind: 'derived';
      source?: never;
      derived: DerivedNumberReference;
    }
);

export interface DebugDivisionQuery {
  division: string;
  division_acronym: string;
  query: string;
}

export interface DivisionResult {
  division: string;
  division_acronym: string;
  chunks_retrieved: number;
  answer: string;
  source_chunk_ids: string[];
}

export interface QueryResponse {
  answer: string;
  processing_time: number;
  selected_divisions: string[];
  division_results: DivisionResult[];
  sources?: SourceDocument[];
  number_annotations: NumberAnnotation[];
  debug_division_queries?: DebugDivisionQuery[];
  timestamp: string;
  query_id?: string;
  thinking_speed?: 'quick' | 'normal' | 'long';
  model_used?: string;
}

export interface QueryProgressEvent {
  query_id: string;
  stage: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  database_status?: string;
}

export interface StatusResponse {
  service: string;
  version: string;
  status: string;
  timestamp: string;
  database_status: string;
  history_available?: boolean;
  available_divisions: string;
  current_embedding_model: string;
  endpoints: Record<string, string>;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface VectorStoreInfo {
  id: string;
  name: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  status: string;
  is_active: boolean;
  created_at: string;
  last_ingested_at?: string;
  last_used_at?: string;
  chunk_count: number;
  query_count: number;
  error_message?: string;
}

export interface EmbeddingModelInfo {
  id: string;
  name: string;
  provider: string;
  dimensions?: number;
  is_enabled: boolean;
  is_available: boolean;
}

export interface CreateVectorStoreRequest {
  name: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  activate?: boolean;
}

export interface ConversationSummary {
  id: string;
  question: string;
  answer_preview: string;
  created_at: string;
  processing_time: number;
  status: string;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
}

export interface ConversationDetail {
  response: QueryResponse;
}

// Available divisions (matching backend)
export const AVAILABLE_DIVISIONS = [
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
  "CONTINUING APPROPRIATIONS, EXTENDERS, HOMELAND SECURITY, AND OTHER MATTERS"
] as const;

export type DivisionName = typeof AVAILABLE_DIVISIONS[number];
