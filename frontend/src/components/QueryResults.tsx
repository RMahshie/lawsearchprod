import { useState } from 'react';
import type { QueryResponse } from '../types/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface QueryResultsProps {
  result: QueryResponse;
  question: string;
}

export default function QueryResults({ result, question }: QueryResultsProps) {
  const [showDetails, setShowDetails] = useState(false);

  const formatProcessingTime = (seconds: number) => {
    if (seconds < 1) {
      return `${Math.round(seconds * 1000)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const getDivisionDisplayName = (division: string) => {
    // Division names are already properly formatted, just return as-is
    return division;
  };

  return (
    <div className="w-full max-w-none">
      <div className="card overflow-hidden">
        {/* Header */}
        <div className="bg-gray-800 px-6 py-4 border-b border-gray-600">
          <h3 className="text-lg font-semibold text-gray-100">Search Results</h3>
          <p className="text-sm text-gray-300 mt-1">
            Question: <span className="font-medium">"{question}"</span>
          </p>
        </div>

        {/* Answer Section */}
        <div className="p-6">
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-100 mb-4">Answer</h4>

            {/* Department Tags */}
            {result.selected_divisions && result.selected_divisions.length > 0 && (
              <div className="mb-4">
                {result.selected_divisions.map((division, index) => (
                  <div key={index} className="text-sm font-bold text-gray-200 uppercase tracking-wide mb-2">
                    {getDivisionDisplayName(division)}
                  </div>
                ))}
              </div>
            )}

            {/* Formatted Answer Content */}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
            >
              {result.answer}
            </ReactMarkdown>
          </div>

          {/* Processing Time */}
          <div className="mb-6 text-sm text-gray-400">
            ⏱️ Completed in {formatProcessingTime(result.processing_time)}
          </div>

          {/* Expandable Details Section */}
          {result.sources && result.sources.length > 0 && (
            <div className="mb-6">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="expandable-button text-sm font-medium"
              >
                <span className="mr-2">{showDetails ? '▼' : '▶'}</span>
                🔍 View details by subcommittee
              </button>

              {showDetails && (
                <div className="expandable-content">
                  <div className="space-y-3">
                    {result.sources.map((source, index) => (
                      <div
                        key={index}
                        className="border border-gray-600 rounded-lg p-4 bg-gray-800"
                      >
                        <div className="text-xs text-gray-300 mb-2 font-mono leading-relaxed">
                          {source.content_snippet}
                        </div>
                        <div className="text-xs text-gray-400">
                          Division: {getDivisionDisplayName(source.division)}
                          {source.confidence_score && (
                            <span className="ml-2">
                              • {Math.round(source.confidence_score * 100)}% relevance
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Searched Divisions */}
          {result.selected_divisions && result.selected_divisions.length > 0 && (
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-100 mb-3">
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
        </div>
      </div>
    </div>
  );
}