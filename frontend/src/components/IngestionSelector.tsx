import { useState } from 'react';
import type { IngestRequest, IngestResponse } from '../types/api';
import { AVAILABLE_EMBEDDING_MODELS } from '../types/api';
import { useApiStatus } from '../hooks/useApi';

interface IngestionSelectorProps {
  onIngest?: (request: IngestRequest) => Promise<IngestResponse>;
}

export default function IngestionSelector({ onIngest }: IngestionSelectorProps) {
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState<string>(AVAILABLE_EMBEDDING_MODELS[0].value);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const { data: statusData, isLoading: statusLoading, error: statusError } = useApiStatus();

  const handleIngest = async () => {
    if (!onIngest) return;

    setIsIngesting(true);
    setIngestError(null);
    setIngestResult(null);

    try {
      const request: IngestRequest = {
        embedding_model: selectedEmbeddingModel,
        clear_existing: true
      };

      const result = await onIngest(request);
      setIngestResult(result);
    } catch (error) {
      setIngestError(error instanceof Error ? error.message : 'Ingestion failed');
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
      <div className="p-4 border-b border-gray-200 bg-gray-100 rounded-t-lg">
        <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
          <span className="text-blue-600">🔧</span>
          Data Management
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Current Embedding Model Display */}
        <div>
          <h4 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wider">Current Model</h4>
          <div className="bg-blue-50 border border-blue-200 rounded-md p-2">
            {statusLoading ? (
              <div className="flex items-center text-gray-500 text-xs">
                <div className="animate-spin w-3 h-3 mr-2 border border-gray-400 border-t-transparent rounded-full"></div>
                Loading...
              </div>
            ) : statusError ? (
              <div className="text-red-600 text-xs">
                Unable to load
              </div>
            ) : statusData ? (
              <div className="text-xs">
                <div className="font-medium text-blue-900">
                  {AVAILABLE_EMBEDDING_MODELS.find(m => m.value === statusData.current_embedding_model)?.label ||
                   statusData.current_embedding_model}
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-xs">Unknown</div>
            )}
          </div>
        </div>

        {/* Ingestion Controls */}
        <div className="space-y-3">
          <div>
            <label htmlFor="embeddingModel" className="block text-xs font-medium text-gray-700 mb-1">
              Switch Model
            </label>
            <select
              id="embeddingModel"
              value={selectedEmbeddingModel}
              onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isIngesting}
            >
              {AVAILABLE_EMBEDDING_MODELS.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleIngest}
            disabled={isIngesting}
            className={`w-full px-3 py-2 text-xs font-medium rounded-md transition-colors ${
              isIngesting 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-2 focus:ring-blue-500 focus:ring-offset-1'
            }`}
          >
            {isIngesting ? (
              <div className="flex items-center justify-center gap-2">
                <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full"></div>
                <span>Processing...</span>
              </div>
            ) : (
              'Run Ingestion'
            )}
          </button>

          <p className="text-xs text-gray-500 leading-relaxed">
            Re-ingest documents with selected model. Takes 30-60 seconds.
          </p>
        </div>

        {/* Ingestion Results */}
        {ingestResult && (
          <div className="bg-green-50 border border-green-200 rounded-md p-3">
            <h4 className="text-xs font-medium text-green-800 mb-1">✅ Completed</h4>
            <div className="text-xs text-green-700 space-y-0.5">
              <p>{ingestResult.divisions_processed} divisions processed</p>
              <p>{ingestResult.processing_time.toFixed(1)}s elapsed</p>
            </div>
          </div>
        )}

        {ingestError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <h4 className="text-xs font-medium text-red-800 mb-1">❌ Failed</h4>
            <p className="text-xs text-red-700">{ingestError}</p>
          </div>
        )}
      </div>
    </div>
  );
}
