import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import QueryForm from './components/QueryForm';
import QueryResults from './components/QueryResults';
import IngestionSelector from './components/IngestionSelector';
import { useSubmitQuery, useHealthCheck } from './hooks/useApi';
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

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-none">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            LawSearch AI
          </h1>
          <p className="text-xl text-gray-600">
            Search Federal Appropriations Acts with AI
          </p>

          {/* API Status Indicator */}
          <div className="mt-4 flex justify-center">
            {healthError ? (
              <div className="status-indicator status-offline">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                API Offline
              </div>
            ) : healthData ? (
              <div className="status-indicator status-online">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                API Online - {healthData.status}
              </div>
            ) : (
              <div className="status-indicator status-loading">
                <svg className="animate-spin w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Checking API Status...
              </div>
            )}
          </div>
        </div>

        {/* Main Content Layout */}
        <div className="main-layout flex gap-12 w-full">
          {/* Left Sidebar - Ingestion Selector */}
          <aside className="sidebar w-80 flex-shrink-0">
            <IngestionSelector onIngest={handleIngest} />
          </aside>

          {/* Right Content Area */}
          <main className="flex-1 min-w-0 space-y-6">
            {/* Query Form */}
            <QueryForm
              onSubmit={handleQuery}
              isLoading={submitQueryMutation.isPending}
            />

            {/* Error Display */}
            {submitQueryMutation.isError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <svg className="w-5 h-5 text-red-400 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="text-sm font-medium text-red-800">
                      Error processing your request
                    </h3>
                    <p className="text-sm text-red-700 mt-1">
                      {submitQueryMutation.error?.message || 'An unknown error occurred'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>

        {/* Full-width Results Section */}
        {result && (
          <div className="full-width-results mt-8">
            <QueryResults result={result} question={lastQuestion} />
          </div>
        )}
      </div>
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
