import axios from 'axios';
import type { AxiosResponse } from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  HealthResponse,
  StatusResponse,
  IngestRequest,
  IngestResponse
} from '../types/api';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds for ingestion operations (queries still use 30s)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate instance for ingestion with longer timeout
const ingestionClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for ingestion operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Apply same interceptors to ingestion client
ingestionClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.data) {
      // Backend returned an error response
      throw new Error(error.response.data.message || error.response.data.error || 'API Error');
    } else if (error.request) {
      // Network error
      throw new Error('Unable to connect to the server. Please check your connection.');
    } else {
      // Something else went wrong
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

// Response interceptor to handle errors consistently
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.data) {
      // Backend returned an error response
      throw new Error(error.response.data.message || error.response.data.error || 'API Error');
    } else if (error.request) {
      // Network error
      throw new Error('Unable to connect to the server. Please check your connection.');
    } else {
      // Something else went wrong
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

/**
 * Submit a query to the RAG system
 */
export const submitQuery = async (queryRequest: QueryRequest): Promise<QueryResponse> => {
  try {
    const response = await apiClient.post<QueryResponse>('/api/query', queryRequest);
    return response.data;
  } catch (error) {
    console.error('Query submission failed:', error);
    throw error;
  }
};

/**
 * Trigger data ingestion with a specific embedding model
 */
export const submitIngest = async (ingestRequest: IngestRequest): Promise<IngestResponse> => {
  try {
    const response = await ingestionClient.post<IngestResponse>('/api/ingest', ingestRequest);
    return response.data;
  } catch (error) {
    console.error('Ingestion failed:', error);
    throw error;
  }
};

/**
 * Check API health status
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  try {
    const response = await apiClient.get<HealthResponse>('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

/**
 * Get API status (alternative endpoint)
 */
export const getStatus = async (): Promise<StatusResponse> => {
  try {
    const response = await apiClient.get<StatusResponse>('/api/status');
    return response.data;
  } catch (error) {
    console.error('Status check failed:', error);
    throw error;
  }
};

/**
 * React Query hook keys for consistent caching
 */
export const queryKeys = {
  health: ['health'] as const,
  status: ['status'] as const,
  query: (request: QueryRequest) => ['query', request] as const,
};

/**
 * React Query options for different query types
 */
export const queryOptions = {
  health: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  },
  query: {
    staleTime: 10 * 60 * 1000, // 10 minutes (RAG responses don't change quickly)
    retry: 1, // Only retry once for failed queries
  },
};