import { useState } from 'react';
import type { QueryRequest } from '../types/api';

interface QueryFormProps {
  onSubmit: (query: QueryRequest) => void;
  isLoading: boolean;
}

export default function QueryForm({ onSubmit, isLoading }: QueryFormProps) {
  const [question, setQuestion] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    if (question.length < 10) {
      setError('Question must be at least 10 characters long');
      return;
    }

    onSubmit({ question: question.trim() });
  };


  return (
    <div className="w-full max-w-none">
      <div className="card p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Ask a Question About Federal Appropriations
        </h2>
        <p className="text-gray-600 mb-6">
          Search through the 2024 Consolidated Appropriations Acts to find specific funding information,
          program details, and legislative provisions.
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., How much funding was allocated for NASA in 2024?"
              className="form-input w-full px-3 py-3 rounded-md resize-vertical min-h-[120px]"
              disabled={isLoading}
            />
            {error && (
              <p className="mt-1 text-sm text-red-600">{error}</p>
            )}
          </div>

          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              {question.length}/1000 characters
            </div>
            
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className={`btn-primary ${isLoading ? 'btn-loading' : ''}`}
            >
              {isLoading ? (
                <>
                  <div className="loading-spinner"></div>
                  <span className="btn-text">Searching...</span>
                </>
              ) : (
                'Ask Question'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}