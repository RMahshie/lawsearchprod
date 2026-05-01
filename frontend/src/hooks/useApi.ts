import { useQuery } from '@tanstack/react-query';
import {
  checkHealth,
  getStatus,
  queryKeys,
  queryOptions,
  listVectorStores,
  listEmbeddingModels,
  listConversations,
} from '../services/api';
import type { HealthResponse, StatusResponse } from '../types/api';

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
