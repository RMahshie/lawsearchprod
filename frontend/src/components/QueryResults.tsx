import type { QueryResponse } from '../types/api';
import ReactMarkdown from 'react-markdown';

interface QueryResultsProps {
  result: QueryResponse;
  question: string;
}

export default function QueryResults({ result, question }: QueryResultsProps) {
  const formatProcessingTime = (seconds: number) => {
    if (seconds < 1) {
      return `${Math.round(seconds * 1000)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const getDivisionDisplayName = (division: string) => {
    // Convert from technical name to display name
    return division
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .trim()
      .replace(/\s+/g, ' ')
      .toUpperCase(); // Keep original formatting for government divisions
  };

  return (
    <div className="w-full max-w-4xl mx-auto mt-6">
      <div className="card overflow-hidden">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-500">
          <h3 className="text-lg font-semibold text-gray-800">Search Results</h3>
          <p className="text-sm text-gray-600 mt-1">
            Question: <span className="font-medium">"{question}"</span>
          </p>
        </div>

        {/* Answer Section */}
        <div className="p-6">
          <div className="mb-6">
            <h4 className="text-md font-semibold text-gray-800 mb-3">Answer</h4>
            <div className="prose prose-sm max-w-none prose-invert prose-headings:text-gray-300 prose-p:text-gray-300 prose-strong:text-gray-200 prose-ul:text-gray-300 prose-ol:text-gray-300">
              <ReactMarkdown className="text-gray-300 leading-relaxed">
                {result.answer}
              </ReactMarkdown>
            </div>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-6">
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Processing time: {formatProcessingTime(result.processing_time)}
            </div>
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Sources: {result.sources?.length || 0} documents
            </div>
          </div>

          {/* Selected Divisions */}
          {result.selected_divisions && result.selected_divisions.length > 0 && (
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-800 mb-3">
                Searched Divisions
              </h4>
              <div className="flex flex-wrap gap-1">
                {result.selected_divisions.map((division, index) => (
                  <span
                    key={index}
                    className="division-badge"
                  >
                    {getDivisionDisplayName(division)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source Documents */}
          {result.sources && result.sources.length > 0 && (
            <div>
              <h4 className="text-md font-semibold text-gray-800 mb-3">
                Source Documents
              </h4>
              <div className="space-y-3">
                {result.sources.map((source, index) => (
                  <div
                    key={index}
                    className="border border-gray-500 rounded-lg p-4 hover:border-gray-400 transition-colors bg-gray-50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h5 className="font-medium text-gray-800 text-sm">
                        {getDivisionDisplayName(source.division)}
                      </h5>
                      {source.confidence_score && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          {Math.round(source.confidence_score * 100)}% relevance
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 leading-relaxed mb-2">
                      {source.content_snippet}
                    </p>
                    
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">Division: </span>
                      {getDivisionDisplayName(source.division)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}