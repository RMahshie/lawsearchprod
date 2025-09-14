import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import QueryForm from './components/QueryForm';
import QueryResults from './components/QueryResults';
import IngestionSelector from './components/IngestionSelector';
import ThinkingSpeedSelector from './components/ThinkingSpeedSelector';
import { useSubmitQuery, useHealthCheck } from './hooks/useApi';
import { useSessionState } from './hooks/useSessionState';
import { submitIngest } from './services/api';
import type { QueryRequest, QueryResponse, IngestRequest, IngestResponse } from './types/api';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string>('');
  const [thinkingSpeed, setThinkingSpeed] = useState<'quick' | 'normal' | 'long'>('normal');

  const { query, updateQuery } = useSessionState();
  const submitQueryMutation = useSubmitQuery();
  const { data: healthData, isError: healthError } = useHealthCheck();

  const handleQuery = async (queryRequest: QueryRequest) => {
    setLastQuestion(queryRequest.question);

    try {
      const response = await submitQueryMutation.mutateAsync(queryRequest);
      setResult(response);
    } catch (error) {
      console.error('Query failed:', error);
      // Error handling is done by the mutation
    }
  };

  const handleIngest = async (ingestRequest: IngestRequest): Promise<IngestResponse> => {
    return await submitIngest(ingestRequest);
  };

  const handleThinkingSpeedChange = (speed: 'quick' | 'normal' | 'long') => {
    setThinkingSpeed(speed);
  };

  return (
    <div className="app-container">
      {/* Fixed Sidebar */}
      <aside className="fixed-sidebar">
        <div className="p-4 space-y-4">
          <IngestionSelector onIngest={handleIngest} />
          <ThinkingSpeedSelector
            onSpeedChange={handleThinkingSpeedChange}
            currentSpeed={thinkingSpeed}
          />
        </div>
      </aside>

      {/* Scrollable Main Content */}
      <main className="main-content">
        <div className="content-wrapper">
          {/* API Status Indicator - Top Right Corner */}
          <div className="fixed top-4 right-6 z-50">
            {healthError ? (
              <div className="inline-flex items-center text-xs text-red-400 bg-gray-800 px-2 py-1 rounded">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                API Offline
              </div>
            ) : healthData ? (
              <div className="inline-flex items-center text-xs text-green-400 bg-gray-800 px-2 py-1 rounded">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                API Online
              </div>
            ) : (
              <div className="inline-flex items-center text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
                <svg className="animate-spin w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Checking...
              </div>
            )}
          </div>

          {/* Header - Now in scrollable area */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-100 mb-2">
              LawSearch AI
            </h1>
            <p className="text-lg text-gray-300 mb-4">
              Ask natural-language questions about the 2024-2025 U.S. federal appropriations bills
              and get precise, cited answers with budget allocations and legislative details.
            </p>
          </div>

          {/* Search Section - Near Top */}
          <div className="search-section">
            <QueryForm
              onSubmit={handleQuery}
              isLoading={submitQueryMutation.isPending}
              query={query}
              onQueryChange={updateQuery}
              thinkingSpeed={thinkingSpeed}
            />

            {/* Loading State */}
            {submitQueryMutation.isPending && (
              <div className="flex items-center justify-center py-4 mt-4">
                <div className="animate-spin w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full"></div>
                <span className="text-gray-300" style={{ marginLeft: '16px' }}>Running RAG pipeline...</span>
              </div>
            )}

            {/* Error Display */}
            {submitQueryMutation.isError && (
              <div className="bg-red-900 border border-red-700 rounded-lg p-4 mt-4">
                <div className="flex">
                  <svg className="w-5 h-5 text-red-400 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="text-sm font-medium text-red-300">
                      Error processing your request
                    </h3>
                    <p className="text-sm text-red-200 mt-1">
                      {submitQueryMutation.error?.message || 'An unknown error occurred'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results Section - Below Search */}
          <div className="results-section">
            {result && (
              <QueryResults result={result} question={lastQuestion} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
