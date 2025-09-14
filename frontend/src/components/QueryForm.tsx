import { useState } from 'react';
import type { QueryRequest } from '../types/api';

interface QueryFormProps {
  onSubmit: (query: QueryRequest) => void;
  isLoading: boolean;
  query: string;
  onQueryChange: (query: string) => void;
  thinkingSpeed: 'quick' | 'normal' | 'long';
}

export default function QueryForm({ onSubmit, isLoading, query, onQueryChange, thinkingSpeed }: QueryFormProps) {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    if (query.length < 10) {
      setError('Question must be at least 10 characters long');
      return;
    }

    onSubmit({ question: query.trim(), thinking_speed: thinkingSpeed });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full max-w-none">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-200 mb-2">
            Enter your question:
          </label>
          <div className="relative">
            <input
              type="text"
              id="question"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g. How much funding did FEMA receive?"
              className="form-input w-full px-3 py-2 text-base rounded-md border focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              style={{ paddingLeft: '16px' }}
              disabled={isLoading}
            />
            {query.trim() && !isLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
                Press Enter to apply
              </div>
            )}
          </div>
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>
      </form>
    </div>
  );
}