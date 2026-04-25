import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { QueryResponse, SourceDocument } from '../types/api';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';

interface QueryResultsProps {
  result: QueryResponse;
  question: string;
}

export default function QueryResults({ result, question }: QueryResultsProps) {
  const answerWithFigureLinks = linkAnswerFigures(result.answer, result.sources ?? []);
  const excerpts = uniqueSources(result.sources ?? []);

  return (
    <div className="flex flex-col gap-5">
      <Card className="rounded-sm">
        <CardHeader>
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-2xl font-bold tracking-tight">Answer</CardTitle>
              <Badge className="rounded-sm border-emerald-200 bg-emerald-50 px-1.5 py-0 text-[10px] font-medium text-emerald-700/80 hover:bg-emerald-50">
                Summary
              </Badge>
              <span className="text-xs font-normal text-muted-foreground/70">
                Response generated in {formatProcessingTime(result.processing_time)}
              </span>
            </div>
            <CardDescription className="text-sm font-medium text-foreground/90">{question}</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          <div className="rag-markdown">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ href, children }) => {
                  const match = href?.match(/^#figure-(\d+)$/);
                  if (!match) {
                    return <a href={href}>{children}</a>;
                  }

                  const citation = answerWithFigureLinks.citations[Number(match[1])];
                  if (!citation) return <>{children}</>;

                  return <FigurePopover figure={citation.figure} sources={citation.sources} />;
                },
              }}
            >
              {answerWithFigureLinks.markdown}
            </ReactMarkdown>
          </div>
        </CardContent>
      </Card>

      {result.division_results?.length > 0 && (
        <Card className="rounded-sm">
          <CardHeader>
            <CardTitle>Division Reductions</CardTitle>
            <CardDescription>Per-division answers from the reduce stage.</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" className="w-full">
              {result.division_results.map((division) => (
                <AccordionItem key={division.division} value={division.division}>
                  <AccordionTrigger>
                    <div className="flex items-center gap-2 text-left">
                      <Badge variant="secondary" className="rounded-sm">{division.division_acronym}</Badge>
                      <span>{division.division}</span>
                      <Badge variant="outline" className="rounded-sm">{division.chunks_retrieved} chunks</Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="rag-markdown border bg-muted/30 p-4">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{division.answer}</ReactMarkdown>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>
      )}

      {result.debug_division_queries && result.debug_division_queries.length > 0 && (
        <Card className="rounded-sm">
          <CardHeader>
            <CardTitle>Debug Division Queries</CardTitle>
            <CardDescription>Refined retrieval questions sent to each division.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {result.debug_division_queries.map((item) => (
                <div key={item.division} className="border bg-muted/30 p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs">
                    <Badge variant="outline" className="rounded-sm">{item.division_acronym}</Badge>
                    <span className="text-muted-foreground">{item.division}</span>
                  </div>
                  <p className="text-sm leading-relaxed">{item.query}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {excerpts.length > 0 && (
        <Card className="rounded-sm">
          <CardHeader>
            <CardTitle>Relevant Excerpts</CardTitle>
            <CardDescription>Retrieved chunks that support the answer.</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" className="w-full">
              {excerpts.map((source, index) => (
                <AccordionItem key={source.chunk_id} value={source.chunk_id}>
                  <AccordionTrigger>
                    <div className="flex min-w-0 items-center gap-3 text-left">
                      <span className="w-5 shrink-0 text-xs text-muted-foreground">{index + 1}</span>
                      <span className="min-w-0 text-sm">
                        <span className="font-medium">{source.division_acronym}</span>
                        <span className="text-muted-foreground"> - {summaryForSource(source)}</span>
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="outline" className="rounded-sm">{source.division_acronym}</Badge>
                      <span>{source.chunk_id}</span>
                    </div>
                    <pre className="max-h-80 overflow-auto whitespace-pre-wrap border bg-background p-4 text-xs leading-relaxed">
                      {source.content_snippet}
                    </pre>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function uniqueSources(sources: SourceDocument[]) {
  const seen = new Set<string>();
  return sources.filter((source) => {
    if (seen.has(source.chunk_id)) return false;
    seen.add(source.chunk_id);
    return true;
  });
}

function summaryForSource(source: SourceDocument) {
  return source.chunk_snapshot?.trim() || source.chunk_summary?.trim() || 'Retrieved source excerpt.';
}

interface FigureCitation {
  figure: string;
  sources: SourceDocument[];
}

function FigurePopover({ figure, sources }: FigureCitation) {
  const leadSummary = sources.find((source) => source.chunk_summary?.trim())?.chunk_summary?.trim();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="font-medium text-blue-700 underline decoration-blue-300 underline-offset-2 hover:bg-blue-50">
          {figure}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-[640px] rounded-sm">
        <div className="flex flex-col gap-3">
          <div>
            <div className="text-sm font-medium">{figure}</div>
            {leadSummary && <p className="mt-1 text-sm text-muted-foreground">{leadSummary}</p>}
            <p className="mt-1 text-xs text-muted-foreground">
              Found in {sources.length} retrieved {sources.length === 1 ? 'chunk' : 'chunks'}.
            </p>
          </div>
          <Separator />
          <div className="max-h-96 overflow-y-auto">
            <div className="flex flex-col gap-4 pr-2">
              {sources.map((source) => (
                <div key={source.chunk_id} className="border bg-background p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs">
                    <Badge variant="outline" className="rounded-sm">[{source.division_acronym}]</Badge>
                    <span className="text-muted-foreground">{source.chunk_id}</span>
                  </div>
                  {source.chunk_summary && (
                    <p className="mb-2 text-sm text-muted-foreground">{source.chunk_summary}</p>
                  )}
                  <pre className="whitespace-pre-wrap text-xs leading-relaxed">
                    {source.content_snippet}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

function linkAnswerFigures(answer: string, sources: SourceDocument[]) {
  const citations: FigureCitation[] = [];
  const figurePattern = /\$\d[\d,]*(?:\.\d+)?(?:\s*(?:thousand|million|billion|trillion))?/gi;

  const markdown = answer.replace(figurePattern, (figure) => {
    const matchingSources = sources.filter((source) => sourceContainsFigure(source.content_snippet, figure));
    if (matchingSources.length === 0) return figure;

    const citationIndex = citations.length;
    citations.push({ figure, sources: matchingSources });
    return `[${figure}](#figure-${citationIndex})`;
  });

  return { markdown, citations };
}

function sourceContainsFigure(content: string, figure: string) {
  const normalizedFigure = normalizeFigure(figure);
  if (!normalizedFigure) return content.includes(figure);

  const sourceFigures = content.match(/\$\d[\d,]*(?:\.\d+)?(?:\s*(?:thousand|million|billion|trillion))?/gi) ?? [];
  return sourceFigures.some((sourceFigure) => normalizeFigure(sourceFigure) === normalizedFigure);
}

function normalizeFigure(figure: string) {
  const match = figure.match(/\$([\d,]+(?:\.\d+)?)(?:\s*(thousand|million|billion|trillion))?/i);
  if (!match) return null;

  const value = Number(match[1].replace(/,/g, ''));
  if (!Number.isFinite(value)) return null;

  const multiplier = {
    thousand: 1_000,
    million: 1_000_000,
    billion: 1_000_000_000,
    trillion: 1_000_000_000_000,
  }[match[2]?.toLowerCase() ?? ''] ?? 1;

  return Math.round(value * multiplier);
}

function formatProcessingTime(seconds: number) {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  return `${seconds.toFixed(1)}s`;
}
