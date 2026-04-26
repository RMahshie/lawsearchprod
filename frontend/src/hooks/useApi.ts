import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  submitQuery,
  checkHealth,
  getStatus,
  queryKeys,
  queryOptions,
  listVectorStores,
  listEmbeddingModels,
  listConversations,
} from '../services/api';
import type { QueryRequest, QueryResponse, HealthResponse, StatusResponse } from '../types/api';

/**
 * Hook for submitting queries to the RAG system
 */
export const useSubmitQuery = () => {
  const queryClient = useQueryClient();

  return useMutation<QueryResponse, Error, QueryRequest>({
    mutationFn: submitQuery,
    onSuccess: (data, variables) => {
      // Cache the successful query result
      queryClient.setQueryData(queryKeys.query(variables), data);
    },
    onError: (error) => {
      console.error('Query failed:', error);
    },
  });
};

/**
 * Hook for checking API health status
 */
export const useHealthCheck = (enabled: boolean = true) => {
  return useQuery<HealthResponse, Error>({
    queryKey: queryKeys.health,
    queryFn: checkHealth,
    enabled,
    ...queryOptions.health,
  });
};

/**
 * Hook for getting API status
 */
export const useApiStatus = (enabled: boolean = true) => {
  return useQuery<StatusResponse, Error>({
    queryKey: queryKeys.status,
    queryFn: getStatus,
    enabled,
    ...queryOptions.health, // Reuse the same options as health
  });
};

export const useVectorStores = (enabled: boolean = true) => {
  return useQuery({
    queryKey: queryKeys.vectorStores,
    queryFn: listVectorStores,
    enabled,
  });
};

export const useEmbeddingModels = (enabled: boolean = true) => {
  return useQuery({
    queryKey: queryKeys.embeddingModels,
    queryFn: listEmbeddingModels,
    enabled,
  });
};

export const useConversations = (enabled: boolean = true) => {
  return useQuery({
    queryKey: queryKeys.conversations,
    queryFn: listConversations,
    enabled,
  });
};

/**
 * Hook to get a cached query result if it exists
 */
export const useCachedQuery = (queryRequest: QueryRequest) => {
  const queryClient = useQueryClient();
  
  return queryClient.getQueryData<QueryResponse>(queryKeys.query(queryRequest));
};