import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ReactNode } from 'react';
import { useCallback, useState } from 'react';
import type { NumberAnnotation, QueryResponse, SourceDocument } from '../types/api';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';

interface QueryResultsProps {
  result: QueryResponse;
  question: string;
}

const POPOVER_COLLISION_PADDING = 12;
const SOURCE_POPOVER_CLASS = 'w-[min(640px,calc(100vw-2rem))] max-w-[var(--radix-popover-content-available-width)] rounded-sm';
const DERIVED_POPOVER_CLASS = 'w-[min(720px,calc(100vw-2rem))] max-w-[var(--radix-popover-content-available-width)] rounded-sm';

export default function QueryResults({ result, question }: QueryResultsProps) {
  const [popoverBoundary, setPopoverBoundary] = useState<HTMLDivElement | null>(null);
  const handlePopoverBoundaryRef = useCallback((node: HTMLDivElement | null) => {
    setPopoverBoundary(node);
  }, []);
  const answerWithFigureLinks = linkMarkdownFigures(result, result.answer, { scope: 'answer' });
  const excerpts = uniqueSources(result.sources ?? []);

  return (
    <div ref={handlePopoverBoundaryRef} className="flex flex-col gap-5">
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

                  return <FigurePopover citation={citation} result={result} collisionBoundary={popoverBoundary} />;
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
                      <AnnotatedMarkdown
                        markdown={division.answer}
                        result={result}
                        scope={{ scope: 'division', division: division.division }}
                        collisionBoundary={popoverBoundary}
                      />
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
  sources?: SourceDocument[];
  annotation?: NumberAnnotation;
}

interface AnnotationScope {
  scope: 'answer' | 'division';
  division?: string;
}

function AnnotatedMarkdown({
  markdown,
  result,
  scope,
  collisionBoundary,
}: {
  markdown: string;
  result: QueryResponse;
  scope: AnnotationScope;
  collisionBoundary: Element | null;
}) {
  const linked = linkMarkdownFigures(result, markdown, scope);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children }) => {
          const match = href?.match(/^#figure-(\d+)$/);
          if (!match) {
            return <a href={href}>{children}</a>;
          }

          const citation = linked.citations[Number(match[1])];
          if (!citation) return <>{children}</>;

          return <FigurePopover citation={citation} result={result} collisionBoundary={collisionBoundary} />;
        },
      }}
    >
      {linked.markdown}
    </ReactMarkdown>
  );
}

function FigurePopover({
  citation,
  result,
  collisionBoundary,
}: {
  citation: FigureCitation;
  result: QueryResponse;
  collisionBoundary: Element | null;
}) {
  if (citation.annotation?.kind === 'derived') {
    return <DerivedFigurePopover annotation={citation.annotation} result={result} collisionBoundary={collisionBoundary} />;
  }

  if (citation.annotation?.kind === 'source') {
    return <SourceAnnotationPopover annotation={citation.annotation} result={result} collisionBoundary={collisionBoundary} />;
  }

  const { figure } = citation;
  const sources = citation.sources ?? [];
  const leadSummary = sources.find((source) => source.chunk_summary?.trim())?.chunk_summary?.trim();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="font-medium text-blue-700 underline decoration-blue-300 underline-offset-2 hover:bg-blue-50">
          {figure}
        </button>
      </PopoverTrigger>
      <PopoverContent
        collisionBoundary={collisionBoundary ?? undefined}
        collisionPadding={POPOVER_COLLISION_PADDING}
        className={SOURCE_POPOVER_CLASS}
      >
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
                    <HighlightedSourceSnippet content={source.content_snippet} figure={figure} />
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

function SourceAnnotationPopover({
  annotation,
  result,
  collisionBoundary,
}: {
  annotation: NumberAnnotation;
  result: QueryResponse;
  collisionBoundary: Element | null;
}) {
  if (annotation.kind !== 'source') return null;
  const source = sourceForAnnotation(annotation, result);
  const content = source?.content_snippet ?? '';
  const summary = source?.chunk_summary;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="font-medium text-blue-700 underline decoration-blue-300 underline-offset-2 hover:bg-blue-50">
          {annotation.figure}
        </button>
      </PopoverTrigger>
      <PopoverContent
        collisionBoundary={collisionBoundary ?? undefined}
        collisionPadding={POPOVER_COLLISION_PADDING}
        className={SOURCE_POPOVER_CLASS}
      >
        <div className="flex flex-col gap-3">
          <div>
            <div className="text-sm font-medium">{annotation.figure}</div>
            <p className="mt-1 text-sm text-muted-foreground">{annotation.label}</p>
            {summary && <p className="mt-1 text-xs text-muted-foreground">{summary}</p>}
          </div>
          <Separator />
          <div className="border bg-background p-3">
            <div className="mb-2 flex items-center gap-2 text-xs">
              <Badge variant="outline" className="rounded-sm">[{source?.division_acronym ?? 'SRC'}]</Badge>
              <span className="text-muted-foreground">{annotation.source.chunk_id}</span>
            </div>
            <pre className="whitespace-pre-wrap text-xs leading-relaxed">
              {content ? <HighlightedSourceSnippet content={content} figure={annotation.figure} /> : 'Source chunk unavailable.'}
            </pre>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

function DerivedFigurePopover({
  annotation,
  result,
  collisionBoundary,
}: {
  annotation: NumberAnnotation;
  result: QueryResponse;
  collisionBoundary: Element | null;
}) {
  if (annotation.kind !== 'derived') return null;
  const annotationsById = new Map(result.number_annotations.map((item) => [item.id, item]));
  const sourceInputs = annotation.derived.source_input_ids
    .map((id) => annotationsById.get(id))
    .filter((item): item is NumberAnnotation & { kind: 'source' } => item?.kind === 'source');

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="font-medium text-blue-700 underline decoration-blue-300 underline-offset-2 hover:bg-blue-50">
          {annotation.figure}
        </button>
      </PopoverTrigger>
      <PopoverContent
        side="bottom"
        collisionBoundary={collisionBoundary ?? undefined}
        collisionPadding={POPOVER_COLLISION_PADDING}
        className={DERIVED_POPOVER_CLASS}
      >
        <div className="flex flex-col gap-4">
          <div>
            <div className="text-sm font-medium">{annotation.figure}</div>
            {annotation.derived.rationale && <p className="mt-1 text-xs text-muted-foreground">{annotation.derived.rationale}</p>}
          </div>
          <Separator />
          <div>
            <div className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Included line items
            </div>
            <div>
              <div className="flex flex-col gap-2">
                {sourceInputs.map((input) => (
                  <DerivedInputRow key={input.id} input={input} result={result} />
                ))}
              </div>
            </div>
          </div>
          <Separator />
          <div>
            <div className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Calculation
            </div>
            <p className="whitespace-pre-wrap text-xs leading-relaxed text-muted-foreground">
              {annotation.derived.equation}
            </p>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

function DerivedInputRow({ input, result }: { input: NumberAnnotation & { kind: 'source' }; result: QueryResponse }) {
  const [expanded, setExpanded] = useState(false);
  const source = sourceForAnnotation(input, result);
  const content = source?.content_snippet ?? '';
  const summary = source?.chunk_summary;

  return (
    <div className="border bg-background">
      <button
        type="button"
        aria-expanded={expanded}
        className="flex w-full cursor-pointer items-start gap-2 p-2.5 text-left transition-colors hover:bg-muted/60"
        onClick={() => setExpanded((value) => !value)}
      >
        <span className="tabular-nums text-foreground">
          {input.figure}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm leading-snug">{input.label}</span>
          {source?.chunk_snapshot && (
            <span className="mt-1 block text-xs text-muted-foreground">{source.chunk_snapshot}</span>
          )}
        </span>
        <span className="flex shrink-0 items-center gap-2 text-xs">
          <Badge variant="outline" className="rounded-sm">[{source?.division_acronym ?? 'SRC'}]</Badge>
          <span className="text-muted-foreground">{expanded ? 'Hide' : 'Show'}</span>
        </span>
      </button>
      {expanded && (
        <div className="border-t bg-muted/20 p-3">
          <div className="mb-2 flex items-center gap-2 text-xs">
            <Badge variant="outline" className="rounded-sm">[{source?.division_acronym ?? 'SRC'}]</Badge>
            <span className="text-muted-foreground">{input.source.chunk_id}</span>
          </div>
          {summary && <p className="mb-2 text-xs text-muted-foreground">{summary}</p>}
          <pre className="whitespace-pre-wrap border bg-background p-3 text-xs leading-relaxed">
            {content ? <HighlightedSourceSnippet content={content} figure={input.figure} /> : 'Source chunk unavailable.'}
          </pre>
        </div>
      )}
      </div>
  );
}

function sourceForAnnotation(annotation: NumberAnnotation & { kind: 'source' }, result: QueryResponse) {
  return (result.sources ?? []).find((item) => item.chunk_id === annotation.source.chunk_id);
}

function linkMarkdownFigures(result: QueryResponse, sourceMarkdown: string, scope: AnnotationScope) {
  if (result.number_annotations?.length) {
    return linkAnnotatedFigures(result, sourceMarkdown, scope);
  }
  if (scope.scope === 'answer') {
    return linkLegacyAnswerFigures(result, sourceMarkdown);
  }
  return { markdown: stripNumberMarkers(sourceMarkdown), citations: [] };
}

function linkAnnotatedFigures(result: QueryResponse, sourceMarkdown: string, scope: AnnotationScope) {
  const citations: FigureCitation[] = [];
  const annotationsById = new Map(result.number_annotations.map((annotation) => [annotation.id, annotation]));

  const markdown = sourceMarkdown.replace(
    new RegExp(`(${FIGURE_PATTERN_SOURCE})([\\*_~]*)\\s*\\[\\[num:([A-Za-z0-9_-]+)\\]\\]`, 'gi'),
    (_fullMatch, figure, _value, _scale, markdownClose, annotationId) => {
      const annotation = annotationsById.get(annotationId);
      if (!annotation || !annotationTargetsScope(annotation, scope)) {
        return `${figure}${markdownClose}`;
      }

      const citationIndex = citations.length;
      citations.push({ figure, annotation });
      return `[${figure}](#figure-${citationIndex})${markdownClose}`;
    },
  );

  return { markdown: stripNumberMarkers(markdown), citations };
}

function annotationTargetsScope(annotation: NumberAnnotation, scope: AnnotationScope) {
  return annotation.targets.some((target) => {
    if (target.scope !== scope.scope) return false;
    if (scope.scope === 'answer') return true;
    return target.division === scope.division;
  });
}

function stripNumberMarkers(markdown: string) {
  return markdown.replace(/\s*\[\[num:[A-Za-z0-9_-]+\]\]/g, '');
}

function linkLegacyAnswerFigures(result: QueryResponse, sourceMarkdown: string) {
  const citations: FigureCitation[] = [];
  const sources = result.sources ?? [];
  const sourcesByChunkId = new Map(sources.map((source) => [source.chunk_id, source]));

  const markdown = stripNumberMarkers(sourceMarkdown).replace(createFigurePattern(), (figure, _value, _scale, offset) => {
    const matchingSources = sources.filter((source) => sourceContainsFigure(source.content_snippet, figure));
    const nearbyMarker = nearbyDivisionMarker(sourceMarkdown, offset);
    const fallbackSources = sourcesForNearbyDivisionMarker(result.division_results, sourcesByChunkId, nearbyMarker);
    const citedSources = matchingSources.length > 0
      ? matchingSources
      : fallbackSources;
    const uniqueCitationSources = uniqueSources(citedSources);

    if (uniqueCitationSources.length === 0) return figure;

    const citationIndex = citations.length;
    citations.push({ figure, sources: uniqueCitationSources });
    return `[${figure}](#figure-${citationIndex})`;
  });

  return { markdown, citations };
}

function sourceContainsFigure(content: string, figure: string) {
  const normalizedFigure = normalizeFigure(figure);
  if (!normalizedFigure) return content.includes(figure);

  const sourceFigures = extractFigures(content);
  return sourceFigures.some((sourceFigure) => normalizeFigure(sourceFigure) === normalizedFigure);
}

function nearbyDivisionMarker(answer: string, figureOffset: number) {
  const markerWindow = answer.slice(figureOffset, figureOffset + 80);
  return markerWindow.match(/\[([A-Z]{2,8})\]/)?.[1] ?? null;
}

function sourcesForNearbyDivisionMarker(
  divisionResults: QueryResponse['division_results'],
  sourcesByChunkId: Map<string, SourceDocument>,
  marker: string | null,
) {
  if (!marker) return [];

  const division = divisionResults.find((item) => item.division_acronym === marker);
  if (!division) return [];

  return division.source_chunk_ids
    .map((chunkId) => sourcesByChunkId.get(chunkId))
    .filter((source): source is SourceDocument => Boolean(source));
}

interface HighlightedSourceSnippetProps {
  content: string;
  figure: string;
}

function HighlightedSourceSnippet({ content, figure }: HighlightedSourceSnippetProps) {
  const normalizedFigure = normalizeFigure(figure);
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const figurePattern = createFigurePattern();

  while ((match = figurePattern.exec(content)) !== null) {
    const matchedFigure = match[0];
    const isMatch = normalizedFigure
      ? normalizeFigure(matchedFigure) === normalizedFigure
      : matchedFigure === figure;

    if (!isMatch) continue;

    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }

    parts.push(
      <mark
        key={`${match.index}-${matchedFigure}`}
        className="rounded-sm bg-amber-200 px-0.5 font-semibold text-amber-950"
      >
        {matchedFigure}
      </mark>,
    );
    lastIndex = match.index + matchedFigure.length;
  }

  if (parts.length === 0) return <>{content}</>;

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return <>{parts}</>;
}

const FIGURE_PATTERN_SOURCE = String.raw`\$([\d,]+(?:\.\d+)?)(?:\s*(thousand|million|billion|trillion))?`;

function createFigurePattern() {
  return new RegExp(FIGURE_PATTERN_SOURCE, 'gi');
}

function extractFigures(content: string) {
  return content.match(createFigurePattern()) ?? [];
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
