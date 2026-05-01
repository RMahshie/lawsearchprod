import { useEffect, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Database, History, Search } from 'lucide-react';
import QueryResults from '@/components/QueryResults';
import { useApiStatus, useConversations, useEmbeddingModels, useHealthCheck, useVectorStores } from './hooks/useApi';
import { useSessionState } from './hooks/useSessionState';
import {
  activateVectorStore,
  createVectorStore,
  deleteVectorStore,
  getConversation,
  queryKeys,
  submitQueryStream,
} from './services/api';
import {
  AVAILABLE_DIVISIONS,
  type ConversationSummary,
  type DivisionName,
  type QueryProgressEvent,
  type QueryRequest,
  type QueryResponse,
  type VectorStoreInfo,
} from './types/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const AVAILABLE_CHUNK_SIZES = [
  '800',
  '1000',
  '1250',
  '1500',
  '2000',
  '2500',
] as const;

const AVAILABLE_CHUNK_OVERLAPS = [
  '100',
  '200',
  '350',
  '500',
  '700',
] as const;

function AppContent() {
  const queryClient = useQueryClient();
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [lastQuestion, setLastQuestion] = useState('');
  const [historyMode, setHistoryMode] = useState(false);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [storageOpen, setStorageOpen] = useState(false);
  const [newIngestionOpen, setNewIngestionOpen] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [thinkingSpeed, setThinkingSpeed] = useState<'quick' | 'normal' | 'long'>('normal');
  const [maxResults, setMaxResults] = useState('8');
  const [autoRoute, setAutoRoute] = useState(true);
  const [selectedDivisions, setSelectedDivisions] = useState<DivisionName[]>([]);
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [ingestChunkSize, setIngestChunkSize] = useState('1500');
  const [ingestChunkOverlap, setIngestChunkOverlap] = useState('200');
  const [ingestionName, setIngestionName] = useState('');
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);
  const [ingestPending, setIngestPending] = useState(false);
  const [queryPending, setQueryPending] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryProgress, setQueryProgress] = useState<QueryProgressEvent | null>(null);

  const { query, updateQuery } = useSessionState();
  const { data: healthData, isError: healthError } = useHealthCheck();
  const { data: statusData, refetch: refetchStatus } = useApiStatus();
  const historyAvailable = Boolean(statusData?.history_available);
  const { data: vectorStores = [] } = useVectorStores();
  const { data: embeddingModels = [] } = useEmbeddingModels();
  const { data: conversationsData } = useConversations(historyMode);
  const conversations = conversationsData?.conversations ?? [];
  const currentEmbeddingModel = statusData?.current_embedding_model;
  const availableEmbeddingModels = useMemo(
    () => embeddingModels.filter((model) => model.is_enabled),
    [embeddingModels],
  );

  useEffect(() => {
    if (currentEmbeddingModel && availableEmbeddingModels.some((model) => model.id === currentEmbeddingModel)) {
      setEmbeddingModel(currentEmbeddingModel);
    } else if (
      availableEmbeddingModels.length > 0
      && !availableEmbeddingModels.some((model) => model.id === embeddingModel)
    ) {
      setEmbeddingModel(availableEmbeddingModels[0].id);
    }
  }, [availableEmbeddingModels, currentEmbeddingModel, embeddingModel]);

  const handleQuery = async (queryRequest: QueryRequest) => {
    setLastQuestion(queryRequest.question);
    setQueryPending(true);
    setQueryError(null);
    setQueryProgress(null);

    try {
      const response = await submitQueryStream(queryRequest, setQueryProgress);
      setResult(response);
    } catch (error) {
      setQueryError(error instanceof Error ? error.message : 'Query failed');
    } finally {
      setQueryPending(false);
    }
  };

  const runIngestion = async () => {
    setIngestPending(true);
    setIngestStatus(null);
    try {
      const response = await createVectorStore({
        name: ingestionName || `${embeddingModel} ${ingestChunkSize}/${ingestChunkOverlap}`,
        embedding_model: embeddingModel,
        chunk_size: Number(ingestChunkSize),
        chunk_overlap: Number(ingestChunkOverlap),
        activate: true,
      });
      void refetchStatus();
      await queryClient.invalidateQueries({ queryKey: queryKeys.vectorStores });
      setIngestStatus(
        `${response.name} is ready with ${response.chunk_count.toLocaleString()} chunks`
      );
      setNewIngestionOpen(false);
    } catch (error) {
      setIngestStatus(error instanceof Error ? error.message : 'Ingestion failed');
    } finally {
      setIngestPending(false);
    }
  };

  const handleLoadConversation = async (conversation: ConversationSummary) => {
    setHistoryLoading(true);
    setSelectedConversationId(conversation.id);
    try {
      const detail = await getConversation(conversation.id);
      setResult(detail.response);
      setLastQuestion(conversation.question);
    } catch (error) {
      setQueryError(error instanceof Error ? error.message : 'Could not load saved question');
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleActivateStore = async (store: VectorStoreInfo) => {
    await activateVectorStore(store.id);
    await queryClient.invalidateQueries({ queryKey: queryKeys.vectorStores });
    void refetchStatus();
  };

  const handleDeleteStore = async (store: VectorStoreInfo) => {
    await deleteVectorStore(store.id);
    await queryClient.invalidateQueries({ queryKey: queryKeys.vectorStores });
  };

  const submitCurrentQuery = () => {
    const trimmed = query.trim();
    if (!trimmed || queryPending) return;

    void handleQuery({
      question: trimmed,
      thinking_speed: thinkingSpeed,
      max_results: Number(maxResults),
      include_sources: true,
      divisions_filter: autoRoute ? undefined : selectedDivisions,
    });
  };

  const toggleDivision = (division: DivisionName) => {
    const isRemoving = selectedDivisions.includes(division);
    if (autoRoute && !isRemoving) {
      setAutoRoute(false);
    }
    setSelectedDivisions(
      isRemoving
        ? selectedDivisions.filter((item) => item !== division)
        : [...selectedDivisions, division]
    );
  };

  const handleAutoRouteChange = (checked: boolean) => {
    if (checked) {
      setSelectedDivisions([]);
    }
    setAutoRoute(checked);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid min-h-screen grid-cols-[400px_1fr]">
        <aside className="border-r bg-sidebar text-sidebar-foreground">
          <div className="flex flex-col gap-3 p-3">
            <div className="px-1 py-2">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">LawSearch</div>
              <div className="mt-1 text-xl font-semibold tracking-tight">Control Panel</div>
            </div>

            <Button
              className="h-12 w-full rounded-sm text-base font-semibold shadow-sm"
              onClick={() => setStorageOpen(true)}
            >
              <Database className="mr-2 size-5" />
              Storage Manager
            </Button>
            <Button
              className="h-12 w-full rounded-sm text-base font-semibold shadow-sm"
              disabled={!historyAvailable && !historyMode}
              onClick={() => setHistoryMode((value) => !value)}
            >
              {historyMode ? <Search className="mr-2 size-5" /> : <History className="mr-2 size-5" />}
              {historyMode ? 'Ask a Question' : 'Question History'}
            </Button>
            {!historyAvailable && (
              <p className="px-1 text-xs text-muted-foreground">Question history unavailable.</p>
            )}

            {historyMode ? (
              <ControlCard title="History" description={`${conversations.length} saved questions`}>
                <div className="flex max-h-[calc(100vh-190px)] flex-col gap-2 overflow-y-auto">
                  {conversations.length === 0 && (
                    <p className="text-sm text-muted-foreground">Saved questions will appear here after you run queries.</p>
                  )}
                  {conversations.map((conversation) => (
                    <button
                      key={conversation.id}
                      className={`border bg-background p-3 text-left text-xs hover:bg-muted ${
                        selectedConversationId === conversation.id ? 'border-primary' : 'border-border'
                      }`}
                      onClick={() => void handleLoadConversation(conversation)}
                    >
                      <div className="font-medium text-foreground">{conversation.question}</div>
                      <div className="mt-1 text-muted-foreground">
                        {new Date(conversation.created_at).toLocaleString()}
                      </div>
                      <div className="mt-2 line-clamp-2 text-muted-foreground">{conversation.answer_preview}</div>
                    </button>
                  ))}
                </div>
              </ControlCard>
            ) : (
              <>
                <ControlCard title="Query Settings" description="Speed, retrieval">
                  <div className="flex flex-col gap-2">
                    <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">Thinking speed</div>
                    <ToggleGroup
                      type="single"
                      value={thinkingSpeed}
                      onValueChange={(value) => value && setThinkingSpeed(value as 'quick' | 'normal' | 'long')}
                      className="grid grid-cols-3 gap-1"
                    >
                      <ToggleGroupItem value="quick" className="rounded-sm">Quick</ToggleGroupItem>
                      <ToggleGroupItem value="normal" className="rounded-sm">Normal</ToggleGroupItem>
                      <ToggleGroupItem value="long" className="rounded-sm">Long</ToggleGroupItem>
                    </ToggleGroup>
                  </div>

                  <ControlRow label="Chunks per division">
                    <Select value={maxResults} onValueChange={setMaxResults}>
                      <SelectTrigger className="w-24 rounded-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {['4', '6', '8', '10', '12', '15', '20'].map((value) => (
                            <SelectItem key={value} value={value}>{value}</SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </ControlRow>
                </ControlCard>

                <ControlCard title="Divisions" description="Auto route or target manually">
                  <ControlRow label="Auto route">
                    <Switch checked={autoRoute} onCheckedChange={handleAutoRouteChange} />
                  </ControlRow>
                  <div className="flex max-h-64 flex-col gap-1 overflow-y-auto border bg-background p-2">
                    {AVAILABLE_DIVISIONS.map((division) => (
                      <label
                        key={division}
                        className="flex cursor-pointer items-start gap-2 rounded-sm px-2 py-1 text-xs leading-snug hover:bg-muted"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDivisions.includes(division)}
                          onChange={() => toggleDivision(division)}
                          className="mt-0.5"
                        />
                        <span>{division}</span>
                      </label>
                    ))}
                  </div>
                </ControlCard>
              </>
            )}

          </div>
        </aside>

        <main className="flex min-w-0 flex-col">
          <div className="flex items-center justify-between border-b px-8 py-4">
            <div>
              <div className="text-xs uppercase tracking-[0.28em] text-muted-foreground">Federal Appropriations Search Tool</div>
              <h1 className="text-3xl font-semibold tracking-tight">LawSearch AI</h1>
            </div>
            <Badge variant={healthError ? 'destructive' : healthData ? 'secondary' : 'outline'} className="rounded-sm">
              {healthError ? 'API Offline' : healthData ? 'API Online' : 'Checking'}
            </Badge>
          </div>

          <div className="flex flex-1 flex-col gap-5 p-8">
            <Card className="rounded-sm border-border/80">
              <CardHeader>
                <CardTitle>{historyMode ? 'Saved Question' : 'Query Workspace'}</CardTitle>
                <CardDescription>
                  {historyMode
                    ? 'This is a read-only saved result. Return to search to ask a new question.'
                    : 'Ask a natural-language question. Settings are controlled from the left rail.'}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <Textarea
                  value={historyMode ? lastQuestion : query}
                  onChange={(event) => updateQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (!historyMode && event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                      submitCurrentQuery();
                    }
                  }}
                  disabled={historyMode}
                  placeholder="How much money was appropriated for FEMA disaster relief?"
                  className={`min-h-36 resize-y rounded-sm text-base ${historyMode ? 'bg-muted text-muted-foreground' : ''}`}
                />
                <div className="flex items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {historyMode ? (
                      <Badge variant="outline" className="rounded-sm">
                        {historyLoading ? 'loading history' : 'saved result'}
                      </Badge>
                    ) : (
                      <>
                        <Badge variant="outline" className="rounded-sm">{thinkingSpeed}</Badge>
                        <Badge variant="outline" className="rounded-sm">{maxResults} chunks/division</Badge>
                        <Badge variant="outline" className="rounded-sm">{autoRoute ? 'auto route' : `${selectedDivisions.length} divisions`}</Badge>
                      </>
                    )}
                  </div>
                  {!historyMode && (
                    <Button className="rounded-sm" onClick={submitCurrentQuery} disabled={!query.trim() || queryPending}>
                      {queryPending ? 'Running...' : 'Run Query'}
                    </Button>
                  )}
                </div>
                {queryError && (
                  <div className="border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                    {queryError}
                  </div>
                )}
              </CardContent>
            </Card>

            {queryPending && (
              <Card className="rounded-sm">
                <CardContent className="flex items-center justify-between py-5 text-sm text-muted-foreground">
                  <div className="flex flex-col gap-1">
                    <span className="font-medium text-foreground">{queryProgress?.message ?? 'Starting query'}</span>
                    <span className="text-xs">
                      {queryProgress?.stage ?? 'queued'}
                      {typeof queryProgress?.details?.model === 'string' ? ` · ${queryProgress.details.model}` : ''}
                      {formatProgressDivisions(queryProgress)}
                    </span>
                  </div>
                  <span className="h-2 w-28 overflow-hidden bg-muted">
                    <span className="block h-full w-1/2 animate-pulse bg-primary" />
                  </span>
                </CardContent>
              </Card>
            )}

            {result && <QueryResults result={result} question={lastQuestion} />}
          </div>
        </main>
      </div>

      {storageOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-8">
          <div className="max-h-[88vh] w-full max-w-6xl overflow-hidden border bg-background shadow-xl">
            <div className="flex items-start justify-between border-b p-5">
              <div>
                <h2 className="text-xl font-semibold">Storage Manager</h2>
                <p className="text-sm text-muted-foreground">Manage versioned vector stores for the appropriations bills.</p>
              </div>
              <div className="flex gap-2">
                <Button className="rounded-sm" onClick={() => setNewIngestionOpen(true)}>New Ingestion</Button>
                <Button variant="outline" className="rounded-sm" onClick={() => setStorageOpen(false)}>Close</Button>
              </div>
            </div>

            <div className="overflow-auto p-5">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-muted text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                  <tr>
                    <th className="border p-3">Name</th>
                    <th className="border p-3">Model</th>
                    <th className="border p-3">Chunk / Overlap</th>
                    <th className="border p-3">Chunks</th>
                    <th className="border p-3">Created</th>
                    <th className="border p-3">Last Used</th>
                    <th className="border p-3">Status</th>
                    <th className="border p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {vectorStores.map((store) => (
                    <tr key={store.id}>
                      <td className="border p-3">
                        <div className="font-medium">{store.name}</div>
                        {store.is_active && <div className="text-xs text-muted-foreground">Active store</div>}
                      </td>
                      <td className="border p-3">{store.embedding_model}</td>
                      <td className="border p-3">{store.chunk_size} / {store.chunk_overlap}</td>
                      <td className="border p-3">{store.chunk_count.toLocaleString()}</td>
                      <td className="border p-3">{new Date(store.created_at).toLocaleDateString()}</td>
                      <td className="border p-3">{store.last_used_at ? new Date(store.last_used_at).toLocaleString() : 'Never'}</td>
                      <td className="border p-3">
                        <Badge variant={store.status === 'ready' ? 'secondary' : 'outline'} className="rounded-sm">
                          {store.status}
                        </Badge>
                      </td>
                      <td className="border p-3">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="rounded-sm"
                            disabled={store.is_active || store.status !== 'ready'}
                            onClick={() => void handleActivateStore(store)}
                          >
                            Activate
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="rounded-sm"
                            disabled={store.is_active}
                            onClick={() => void handleDeleteStore(store)}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {ingestStatus && <p className="mt-3 text-sm text-muted-foreground">{ingestStatus}</p>}
            </div>
          </div>

          {newIngestionOpen && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 p-8">
              <div className="w-full max-w-2xl border bg-background p-6 shadow-xl">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">New Ingestion</h3>
                    <p className="text-sm text-muted-foreground">Create a new vector store from the same two bills.</p>
                  </div>
                  <Button variant="outline" className="rounded-sm" onClick={() => setNewIngestionOpen(false)}>Close</Button>
                </div>

                <div className="mt-5 flex flex-col gap-4">
                  <label className="flex flex-col gap-2 text-sm">
                    Ingestion name
                    <input
                      value={ingestionName}
                      onChange={(event) => setIngestionName(event.target.value)}
                      placeholder="e.g. FY2026 Large Chunks"
                      className="border bg-background px-3 py-2"
                    />
                  </label>

                  <div className="flex flex-col gap-4 md:flex-row md:flex-wrap md:items-end">
                    <label className="flex min-w-0 flex-col gap-2 text-sm">
                      Embedding model
                      <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
                        <SelectTrigger className="rounded-sm">
                          <SelectValue placeholder="Embedding model" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectGroup>
                            {availableEmbeddingModels.map((model) => (
                              <SelectItem key={model.id} value={model.id}>
                                {model.name}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                    </label>
                    <label className="flex min-w-0 flex-col gap-2 text-sm">
                      Chunk size
                      <Select value={ingestChunkSize} onValueChange={setIngestChunkSize}>
                        <SelectTrigger className="rounded-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectGroup>
                            {AVAILABLE_CHUNK_SIZES.map((size) => (
                              <SelectItem key={size} value={size}>
                                {size}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                    </label>
                    <label className="flex min-w-0 flex-col gap-2 text-sm">
                      Overlap
                      <Select value={ingestChunkOverlap} onValueChange={setIngestChunkOverlap}>
                        <SelectTrigger className="rounded-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectGroup>
                            {AVAILABLE_CHUNK_OVERLAPS.map((overlap) => (
                              <SelectItem key={overlap} value={overlap}>
                                {overlap}
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                    </label>
                  </div>

                  <Button className="self-end rounded-sm" onClick={runIngestion} disabled={ingestPending || !embeddingModel}>
                    {ingestPending ? 'Creating Store...' : 'Create and Activate'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ControlCard({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <Card className="overflow-visible rounded-sm border-border/80 bg-card/80" size="sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">{children}</CardContent>
    </Card>
  );
}

function ControlRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="min-w-0 text-sm text-muted-foreground">{label}</span>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function formatProgressDivisions(progress: QueryProgressEvent | null) {
  const details = progress?.details;
  if (!details) return '';

  if (Array.isArray(details.divisions) && details.divisions.length > 0) {
    return ` · ${details.divisions.join(', ')}`;
  }

  return typeof details.division === 'string' ? ` · ${details.division}` : '';
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
