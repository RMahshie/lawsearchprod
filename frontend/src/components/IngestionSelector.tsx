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
    <div className="bg-gray-800 rounded-lg border border-gray-600 shadow-sm">
      <div className="p-4 border-b border-gray-600 bg-gray-900 rounded-t-lg">
        <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
          <span className="text-gray-600">🔧</span>
          Data Management
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Current Embedding Model Display */}
        <div>
          <h4 className="text-xs font-medium text-gray-200 mb-2 uppercase tracking-wider">Current Model</h4>
          <div className="form-input rounded-md p-2 text-center">
            {statusLoading ? (
              <div className="flex items-center text-gray-500 text-xs">
                <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full"></div>
                <span style={{ marginLeft: '8px' }}>Loading...</span>
              </div>
            ) : statusError ? (
              <div className="text-red-600 text-xs">
                Unable to load
              </div>
            ) : statusData ? (
              <div className="text-xs">
                <div className="font-medium text-gray-100">
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
        <div className="space-y-4">
          <div>
            <label htmlFor="embeddingModel" className="block text-xs font-medium text-gray-200 mb-2">
              Switch Model
            </label>
            <select
              id="embeddingModel"
              value={selectedEmbeddingModel}
              onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
              className="w-full px-3 py-2 text-sm form-input"
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
            className={`w-full px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              isIngesting
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-gray-800 hover:bg-gray-900 text-white focus:ring-2 focus:ring-gray-500 focus:ring-offset-1'
            }`}
          >
            {isIngesting ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full"></div>
                <span style={{ marginLeft: '8px' }}>Processing...</span>
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
          <div className="bg-gray-800 border border-gray-600 rounded-md p-3">
            <h4 className="text-xs font-medium text-gray-100 mb-1">✅ Completed</h4>
            <div className="text-xs text-gray-200 space-y-0.5">
              <p>{ingestResult.divisions_processed} divisions processed</p>
              <p>{ingestResult.processing_time.toFixed(1)}s elapsed</p>
            </div>
          </div>
        )}

        {ingestError && (
          <div className="bg-red-900 border border-red-700 rounded-md p-3">
            <h4 className="text-xs font-medium text-red-800 mb-1">❌ Failed</h4>
            <p className="text-xs text-red-700">{ingestError}</p>
          </div>
        )}
      </div>
    </div>
  );
}
