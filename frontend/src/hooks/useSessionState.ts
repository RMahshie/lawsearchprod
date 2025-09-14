import { useState, useEffect } from 'react';

interface SessionState {
  query: string;
}

const SESSION_STORAGE_KEY = 'lawsearch_session';

export function useSessionState() {
  const [query, setQuery] = useState<string>('');

  // Load session state from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY);
      if (stored) {
        const sessionState: SessionState = JSON.parse(stored);
        setQuery(sessionState.query || '');
      }
    } catch (error) {
      console.warn('Failed to load session state:', error);
    }
  }, []);

  // Save session state to localStorage whenever query changes
  useEffect(() => {
    try {
      const sessionState: SessionState = { query };
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessionState));
    } catch (error) {
      console.warn('Failed to save session state:', error);
    }
  }, [query]);

  const updateQuery = (newQuery: string) => {
    setQuery(newQuery);
  };

  const clearQuery = () => {
    setQuery('');
  };

  return {
    query,
    updateQuery,
    clearQuery,
  };
}
