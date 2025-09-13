import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { submitQuery, checkHealth, getStatus, queryKeys, queryOptions } from '../services/api';
import type { QueryRequest, QueryResponse, HealthResponse } from '../types/api';

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
  return useQuery<HealthResponse, Error>({
    queryKey: queryKeys.status,
    queryFn: getStatus,
    enabled,
    ...queryOptions.health, // Reuse the same options as health
  });
};

/**
 * Hook to get a cached query result if it exists
 */
export const useCachedQuery = (queryRequest: QueryRequest) => {
  const queryClient = useQueryClient();
  
  return queryClient.getQueryData<QueryResponse>(queryKeys.query(queryRequest));
};