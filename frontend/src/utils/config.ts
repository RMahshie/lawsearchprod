/**
 * API configuration and base URL settings
 */

// API base URL - can be overridden by environment variable
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  query: '/api/query',
  health: '/api/health',
  status: '/api/status',
} as const;

// Build full API URLs
export const buildApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};

// Request timeout in milliseconds
export const REQUEST_TIMEOUT = 300000; // 5 minutes for long RAG queries

// Default request configuration
export const DEFAULT_REQUEST_CONFIG = {
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
};