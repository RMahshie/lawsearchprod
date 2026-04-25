import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import QueryResults from '@/components/QueryResults';
import { useApiStatus, useHealthCheck, useSubmitQuery } from './hooks/useApi';
import { useSessionState } from './hooks/useSessionState';
import { submitIngest } from './services/api';
import {
  AVAILABLE_DIVISIONS,
  AVAILABLE_EMBEDDING_MODELS,
  type DivisionName,
  type IngestRequest,
  type IngestResponse,
  type QueryRequest,
  type QueryResponse,
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
  { value: '1000', label: 'Small', note: 'More precise retrieval, less context per hit.' },
  { value: '1500', label: 'Balanced', note: 'Default balance of precision and context.' },
  { value: '2200', label: 'Large', note: 'More context per chunk, less targeted retrieval.' },
] as const;

function AppContent() {
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [lastQuestion, setLastQuestion] = useState('');
  const [thinkingSpeed, setThinkingSpeed] = useState<'quick' | 'normal' | 'long'>('normal');
  const [maxResults, setMaxResults] = useState('8');
  const [includeSources, setIncludeSources] = useState(true);
  const [debugChunks, setDebugChunks] = useState(false);
  const [autoRoute, setAutoRoute] = useState(true);
  const [selectedDivisions, setSelectedDivisions] = useState<DivisionName[]>([]);
  const [modelOverride, setModelOverride] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState<string>(AVAILABLE_EMBEDDING_MODELS[0].value);
  const [ingestChunkSize, setIngestChunkSize] = useState('1500');
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);
  const [ingestPending, setIngestPending] = useState(false);

  const { query, updateQuery } = useSessionState();
  const submitQueryMutation = useSubmitQuery();
  const { data: healthData, isError: healthError } = useHealthCheck();
  const { data: statusData, refetch: refetchStatus } = useApiStatus();

  useEffect(() => {
    if (statusData?.current_embedding_model) {
      setEmbeddingModel(statusData.current_embedding_model);
    }
  }, [statusData?.current_embedding_model]);

  const handleQuery = async (queryRequest: QueryRequest) => {
    setLastQuestion(queryRequest.question);
    const response = await submitQueryMutation.mutateAsync(queryRequest);
    setResult(response);
  };

  const handleIngest = async (ingestRequest: IngestRequest): Promise<IngestResponse> => {
    return await submitIngest(ingestRequest);
  };

  const runIngestion = async () => {
    setIngestPending(true);
    setIngestStatus(null);
    try {
      const response = await handleIngest({
        embedding_model: embeddingModel,
        clear_existing: true,
        chunk_size: Number(ingestChunkSize),
      });
      void refetchStatus();
      setIngestStatus(
        `${response.divisions_processed} divisions rebuilt with ${response.chunk_size ?? ingestChunkSize}-char chunks in ${response.processing_time.toFixed(1)}s`
      );
    } catch (error) {
      setIngestStatus(error instanceof Error ? error.message : 'Ingestion failed');
    } finally {
      setIngestPending(false);
    }
  };

  const submitCurrentQuery = () => {
    const trimmed = query.trim();
    if (!trimmed || submitQueryMutation.isPending) return;

    void handleQuery({
      question: trimmed,
      thinking_speed: thinkingSpeed,
      max_results: Number(maxResults),
      include_sources: includeSources,
      debug_chunks: debugChunks,
      divisions_filter: autoRoute ? undefined : selectedDivisions,
      model_override: modelOverride.trim() || undefined,
    });
  };

  const toggleDivision = (division: DivisionName) => {
    setSelectedDivisions((current) =>
      current.includes(division)
        ? current.filter((item) => item !== division)
        : [...current, division]
    );
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid min-h-screen grid-cols-[400px_1fr]">
        <aside className="border-r bg-sidebar text-sidebar-foreground">
          <div className="flex flex-col gap-3 p-3">
            <div className="px-1 py-2">
              <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">LawSearch</div>
              <div className="mt-1 text-xl font-semibold tracking-tight">Control Rail</div>
            </div>

            <ControlCard title="Data" description="Embedding and ingestion">
              <ControlRow label="Current model">
                <Badge variant="secondary" className="max-w-52 truncate rounded-sm">
                  {statusData?.current_embedding_model ?? 'unknown'}
                </Badge>
              </ControlRow>
              <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
                <SelectTrigger className="w-full rounded-sm">
                  <SelectValue placeholder="Embedding model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    {AVAILABLE_EMBEDDING_MODELS.map((model) => (
                      <SelectItem key={model.value} value={model.value}>
                        {model.label}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
              <ControlRow label="Chunk size">
                <Select value={ingestChunkSize} onValueChange={setIngestChunkSize}>
                  <SelectTrigger className="w-32 rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {AVAILABLE_CHUNK_SIZES.map((size) => (
                        <SelectItem key={size.value} value={size.value}>
                          {size.label} ({size.value})
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </ControlRow>
              <p className="text-xs leading-relaxed text-muted-foreground">
                Chunk size controls source text length during ingestion. Smaller chunks are sharper;
                larger chunks keep more surrounding context.
              </p>
              <Button className="w-full rounded-sm" onClick={runIngestion} disabled={ingestPending}>
                {ingestPending ? 'Ingesting...' : 'Run Ingestion'}
              </Button>
              {ingestStatus && <p className="text-xs text-muted-foreground">{ingestStatus}</p>}
            </ControlCard>

            <ControlCard title="Query Settings" description="Speed, retrieval, sources">
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

              <ControlRow label="Include sources">
                <Switch checked={includeSources} onCheckedChange={setIncludeSources} />
              </ControlRow>
              <ControlRow label="Debug chunks">
                <Switch checked={debugChunks} onCheckedChange={setDebugChunks} />
              </ControlRow>
            </ControlCard>

            <ControlCard title="Model Override" description="Optional OpenAI model">
              <input
                value={modelOverride}
                onChange={(event) => setModelOverride(event.target.value)}
                placeholder="Use speed default"
                className="h-9 w-full rounded-sm border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <p className="text-xs text-muted-foreground">Leave blank to use the selected thinking speed.</p>
            </ControlCard>

            <ControlCard title="Divisions" description="Auto route or target manually">
              <ControlRow label="Auto route">
                <Switch checked={autoRoute} onCheckedChange={setAutoRoute} />
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
                      disabled={autoRoute}
                      onChange={() => toggleDivision(division)}
                      className="mt-0.5"
                    />
                    <span className={autoRoute ? 'text-muted-foreground' : ''}>{division}</span>
                  </label>
                ))}
              </div>
            </ControlCard>
          </div>
        </aside>

        <main className="flex min-w-0 flex-col">
          <div className="flex items-center justify-between border-b px-8 py-4">
            <div>
              <div className="text-xs uppercase tracking-[0.28em] text-muted-foreground">Federal Appropriations RAG</div>
              <h1 className="text-3xl font-semibold tracking-tight">LawSearch AI</h1>
            </div>
            <Badge variant={healthError ? 'destructive' : healthData ? 'secondary' : 'outline'} className="rounded-sm">
              {healthError ? 'API Offline' : healthData ? 'API Online' : 'Checking'}
            </Badge>
          </div>

          <div className="flex flex-1 flex-col gap-5 p-8">
            <Card className="rounded-sm border-border/80">
              <CardHeader>
                <CardTitle>Query Workspace</CardTitle>
                <CardDescription>
                  Ask a natural-language question. Settings are controlled from the left rail.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <Textarea
                  value={query}
                  onChange={(event) => updateQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                      submitCurrentQuery();
                    }
                  }}
                  placeholder="How much money was appropriated for FEMA disaster relief?"
                  className="min-h-36 resize-y rounded-sm text-base"
                />
                <div className="flex items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline" className="rounded-sm">{thinkingSpeed}</Badge>
                    <Badge variant="outline" className="rounded-sm">{maxResults} chunks/division</Badge>
                    <Badge variant="outline" className="rounded-sm">{autoRoute ? 'auto route' : `${selectedDivisions.length} divisions`}</Badge>
                    {modelOverride.trim() && <Badge variant="outline" className="rounded-sm">{modelOverride.trim()}</Badge>}
                  </div>
                  <Button className="rounded-sm" onClick={submitCurrentQuery} disabled={!query.trim() || submitQueryMutation.isPending}>
                    {submitQueryMutation.isPending ? 'Running...' : 'Run Query'}
                  </Button>
                </div>
                {submitQueryMutation.isError && (
                  <div className="border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                    {submitQueryMutation.error?.message || 'An unknown error occurred'}
                  </div>
                )}
              </CardContent>
            </Card>

            {submitQueryMutation.isPending && (
              <Card className="rounded-sm">
                <CardContent className="flex items-center justify-between py-5 text-sm text-muted-foreground">
                  <span>Graph is routing divisions, retrieving chunks, and reducing answers.</span>
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

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
