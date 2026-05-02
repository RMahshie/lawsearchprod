import axios from 'axios';
import type { AxiosResponse } from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  QueryProgressEvent,
  HealthResponse,
  StatusResponse,
  VectorStoreInfo,
  EmbeddingModelInfo,
  CreateVectorStoreRequest,
  ConversationListResponse,
  ConversationDetail
} from '../types/api';

// API configuration
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
if (import.meta.env.PROD && !configuredApiBaseUrl) {
  throw new Error('VITE_API_BASE_URL is required for production builds');
}
const API_BASE_URL = configuredApiBaseUrl || 'http://localhost:8000';

const normalizeApiError = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (error.response?.data) {
      const data = error.response.data as {
        detail?: string | { error?: string; message?: string };
        message?: string;
        error?: string;
      };
      const detail = data.detail;
      if (detail && typeof detail === 'object') {
        throw new Error(detail.message || detail.error || 'API Error');
      }
      throw new Error(
        (typeof detail === 'string' ? detail : undefined) ||
          data.message ||
          data.error ||
          'API Error',
      );
    }
    if (error.request) {
      throw new Error('Unable to connect to the server. Please check your connection.');
    }
  }
  throw new Error(error instanceof Error ? error.message : 'An unexpected error occurred');
};

const createApiClient = (timeout: number) => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  });
  client.interceptors.response.use((response: AxiosResponse) => response, normalizeApiError);
  return client;
};

const apiClient = createApiClient(120000);
const ingestionClient = createApiClient(300000);

/**
 * Submit a query and receive live Server-Sent Events progress updates.
 */
export const submitQueryStream = async (
  queryRequest: QueryRequest,
  onProgress: (progress: QueryProgressEvent) => void
): Promise<QueryResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/query/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(queryRequest),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Query stream failed');
  }

  if (!response.body) {
    throw new Error('Query stream did not return a response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result: QueryResponse | null = null;

  const handleEvent = (rawEvent: string) => {
    const lines = rawEvent.split('\n');
    let eventName = 'message';
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName = line.slice('event:'.length).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice('data:'.length).trimStart());
      }
    }

    if (dataLines.length === 0) return;

    const payload = JSON.parse(dataLines.join('\n'));
    if (eventName === 'progress') {
      onProgress(payload as QueryProgressEvent);
    } else if (eventName === 'result') {
      result = payload as QueryResponse;
    } else if (eventName === 'error') {
      throw new Error(payload.message || 'Query stream failed');
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';
    for (const event of events) {
      if (event.trim()) handleEvent(event);
    }

    if (done) break;
  }

  if (buffer.trim()) handleEvent(buffer);
  if (!result) throw new Error('Query stream ended without a result');

  return result;
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

export const listVectorStores = async (): Promise<VectorStoreInfo[]> => {
  const response = await apiClient.get<VectorStoreInfo[]>('/api/storage/vector-stores');
  return response.data;
};

export const createVectorStore = async (request: CreateVectorStoreRequest): Promise<VectorStoreInfo> => {
  const response = await ingestionClient.post<VectorStoreInfo>('/api/storage/vector-stores', request);
  return response.data;
};

export const activateVectorStore = async (id: string): Promise<VectorStoreInfo> => {
  const response = await apiClient.post<VectorStoreInfo>(`/api/storage/vector-stores/${id}/activate`);
  return response.data;
};

export const deleteVectorStore = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/storage/vector-stores/${id}`);
};

export const listEmbeddingModels = async (): Promise<EmbeddingModelInfo[]> => {
  const response = await apiClient.get<EmbeddingModelInfo[]>('/api/storage/embedding-models');
  return response.data;
};

export const listConversations = async (): Promise<ConversationListResponse> => {
  const response = await apiClient.get<ConversationListResponse>('/api/conversations');
  return response.data;
};

export const getConversation = async (id: string): Promise<ConversationDetail> => {
  const response = await apiClient.get<ConversationDetail>(`/api/conversations/${id}`);
  return response.data;
};

/**
 * React Query hook keys for consistent caching
 */
export const queryKeys = {
  health: ['health'] as const,
  status: ['status'] as const,
  vectorStores: ['vector-stores'] as const,
  embeddingModels: ['embedding-models'] as const,
  conversations: ['conversations'] as const,
};

/**
 * React Query options for different query types
 */
export const queryOptions = {
  health: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  },
};
