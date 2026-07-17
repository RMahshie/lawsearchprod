"""Retrieve stage: pull top-k Chunks per selected Division from Chroma."""

from __future__ import annotations

import re
import time
from typing import Any

from langgraph.types import Send

from app.services.rag.context import RAGContext
from app.services.rag.state import RAGState
from app.services.rag_prompting import DEFAULT_ANSWER_MODE, normalize_answer_mode
from app.services.vector_store_service import division_acronym


BREADTH_RETRIEVAL_MODES = {"broad_topic_total", "general_summary"}
_BROAD_PRIMARY_RESULT_FRACTION = 0.25
_BROAD_CONTEXT_NEIGHBOR_LIMIT = 4
_GENERAL_SUMMARY_COVERAGE_TERMS = (
    "account accounts program programs activities projects grants assistance operations "
    "administration oversight restrictions requirements authorities eligibility"
)
_ALIAS_BATCH_SIZE = 8
_FACET_SPLIT_RE = re.compile(r"\s*(?:,|;|\bor\b|\band\b)\s+", re.IGNORECASE)
_ALIAS_SPLIT_RE = re.compile(r"\s*(?:,|;|\.)\s*")
_FACET_PREFIX_RE = re.compile(
    r"^(?:what|which|how|where|when|does|do|is|are|summarize|explain)\b.*?\b(?:for|about|cover(?:s)?|treat(?:s)?)\b\s+",
    re.IGNORECASE,
)
_PHRASE_SUFFIXES = {
    "account",
    "accounts",
    "assistance",
    "authority",
    "authorities",
    "fund",
    "funds",
    "grant",
    "grants",
    "initiative",
    "initiatives",
    "loan",
    "loans",
    "care",
    "partnership",
    "partnerships",
    "payment",
    "payments",
    "program",
    "programs",
    "service",
    "services",
    "voucher",
    "vouchers",
}
_PHRASE_CONNECTORS = {"and", "for", "of", "the", "to"}
_TOPIC_STOPWORDS = {
    "account",
    "accounts",
    "agency",
    "agencies",
    "amount",
    "amounts",
    "available",
    "city",
    "does",
    "fund",
    "funding",
    "funds",
    "fy2026",
    "program",
    "programs",
    "seeking",
    "services",
    "what",
    "which",
}
_GENERIC_REWRITE_FACET_WORDS = {
    "appropriation",
    "appropriations",
    "budget",
    "funding",
    "fy",
    "total",
}
_CONTINUATION_START_RE = re.compile(
    r"^(?:[a-z]|[),;:]|\(?\d+\)|[ivxlcdm]+\)|of\b|and\b|or\b|for\b|to\b|with\b|including\b)",
)
_OBVIOUS_FRAGMENT_START_RE = re.compile(
    r"^(?:[),;:]|\(?\d+\)|[ivxlcdm]+\)|(?:of|and|or|for|to|with|including)\b|[a-z]\s+[A-Z])",
)
_STATUTORY_TITLE_FRAGMENT_RE = re.compile(
    r"^[A-Z][A-Za-z]+(?:,\s+[A-Z][A-Za-z]+){1,}.*\b(?:Act|Code)\b",
    re.DOTALL,
)


def _normalized_query(text: str | None) -> str:
    return " ".join((text or "").split())


def _query_facets(question: str) -> list[str]:
    """Extract user-stated topic facets without adding external vocabulary."""
    cleaned = re.sub(r"[?!.]+$", "", _normalized_query(question))
    facets: list[str] = []
    for raw_part in _FACET_SPLIT_RE.split(cleaned):
        part = _FACET_PREFIX_RE.sub("", raw_part).strip(" ,;:-")
        if " seeking " in part.lower():
            part = re.split(r"\bseeking\b", part, flags=re.IGNORECASE)[-1].strip(" ,;:-")
        words = part.split()
        if 1 < len(words) <= 10 and part.lower() not in {"fy2026", "funding", "appropriations"}:
            facets.append(part)
    unique: list[str] = []
    seen: set[str] = set()
    for facet in facets:
        key = facet.lower()
        if key not in seen:
            seen.add(key)
            unique.append(facet)
    return unique[:3]


def _is_phrase_word(word: str) -> bool:
    return bool(word) and (word[0].isupper() or word.isupper() or any(char.isdigit() for char in word))


def _facet_sort_score(facet: str, question: str | None) -> int:
    if not question:
        return 0
    question_roots = {
        token.removesuffix("ness").removesuffix("s")
        for token in re.findall(r"[a-z0-9]+", question.lower())
        if len(token) > 2
    }
    score = 0
    for token in re.findall(r"[a-z0-9]+", facet.lower()):
        root = token.removesuffix("ness").removesuffix("s")
        if root in question_roots:
            score += 1
    return score


def _retrieval_phrase_facets(retrieval_query: str, question: str | None = None) -> list[str]:
    """Extract account/program-like phrases from the LLM rewrite without adding vocabulary."""
    normalized_query = _normalized_query(retrieval_query)
    delimited_facets: list[str] = []
    # Rewrite emits semicolon-delimited headings. Treat those boundaries as
    # authoritative so adjacent account names cannot be fused into one query.
    # Keep the suffix parser below as a fallback for older or nonconforming
    # rewrite output.
    for delimited_part in re.split(r"\s*[;|]\s*", normalized_query):
        part = delimited_part.strip(" ,;:-")
        part_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9&/-]*", part)
        meaningful_words = [
            word
            for word in part_words
            if not word.isdigit()
            and word.lower() not in _GENERIC_REWRITE_FACET_WORDS
            and not re.fullmatch(r"fy\d{2,4}", word, re.IGNORECASE)
        ]
        if (
            1 < len(part_words) <= 8
            and meaningful_words
        ):
            delimited_facets.append(" ".join(part_words))

    # When the rewrite obeys the delimiter contract, its explicit boundaries
    # and order are more trustworthy than suffix inference. Re-sorting these
    # headings by literal question overlap used to demote the rewrite's major
    # formula/block-grant headings simply because the public-facing question
    # used different words.
    if ";" in normalized_query or "|" in normalized_query:
        unique_delimited: list[str] = []
        seen_delimited: set[str] = set()
        for facet in delimited_facets:
            key = facet.lower()
            if key not in seen_delimited:
                seen_delimited.add(key)
                unique_delimited.append(facet)
        if unique_delimited:
            return unique_delimited[:12]

    facets: list[str] = []
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9&/-]*", normalized_query)
    last_suffix_index = -1
    for index, word in enumerate(words):
        if word.lower() not in _PHRASE_SUFFIXES:
            continue
        if facets and index == last_suffix_index + 1 and words[index - 1].lower() in _PHRASE_SUFFIXES:
            combined_words = [*facets[-1].split(), word]
            if len(combined_words) <= 6:
                facets[-1] = " ".join(combined_words)
                last_suffix_index = index
                continue
        start = index
        while start > last_suffix_index + 1 and index - start < 5:
            previous = words[start - 1]
            previous_key = previous.lower()
            if previous_key in _PHRASE_CONNECTORS or _is_phrase_word(previous):
                start -= 1
                continue
            break
        candidate_words = words[start : index + 1]
        while candidate_words and candidate_words[0].lower() in _PHRASE_CONNECTORS:
            candidate_words = candidate_words[1:]
        candidate = " ".join(candidate_words)
        if 1 < len(candidate_words) <= 6 and any(_is_phrase_word(part) for part in candidate_words):
            facets.append(candidate)
        last_suffix_index = index

    unique: list[str] = []
    seen: set[str] = set()
    for facet in facets:
        key = facet.lower()
        if key not in seen:
            seen.add(key)
            unique.append(facet)
    unique.sort(key=lambda facet: -_facet_sort_score(facet, question))
    # A broad question commonly spans more headings than the ten-result
    # coverage lane can retain. Keep a slightly larger candidate pool so the
    # question-overlap ranking, rather than early string position, determines
    # which headings receive retrieval slots.
    return unique[:12]


def _round_robin_chunks(chunk_groups: list[list[dict[str, Any]]], *, limit: int) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    positions = [0 for _ in chunk_groups]

    while len(merged) < limit:
        advanced = False
        for group_index, group in enumerate(chunk_groups):
            while positions[group_index] < len(group):
                chunk = group[positions[group_index]]
                positions[group_index] += 1
                chunk_id = chunk.get("chunk_id")
                if isinstance(chunk_id, str) and chunk_id:
                    if chunk_id in seen_chunk_ids:
                        continue
                    seen_chunk_ids.add(chunk_id)
                merged.append(chunk)
                advanced = True
                break
            if len(merged) >= limit:
                break
        if not advanced:
            break
    return merged


def _interleave_coverage_queries(
    rewrite_phrases: list[str],
    question_facets: list[str],
) -> list[str]:
    """Give both the rewrite and each user-stated need an early coverage lane."""
    queries: list[str] = []
    for index in range(max(len(rewrite_phrases), len(question_facets))):
        if index < len(rewrite_phrases):
            queries.append(rewrite_phrases[index])
        if index < len(question_facets):
            queries.append(question_facets[index])
    return queries


def _phrase_coverage_score(chunk: dict[str, Any], phrase: str) -> int:
    """Prefer a phrase's account-heading/amount Chunk over incidental mentions."""
    phrase_words = re.findall(r"[a-z0-9]+", phrase.lower())
    # A rewrite may prefix an account heading with its statutory alias (for
    # example, "Section 8"). The bill's actual heading often omits that alias.
    # Score the heading core in that common structural case so an exact account
    # heading with its appropriation outranks an incidental statutory mention.
    match_words = phrase_words
    if (
        len(phrase_words) > 3
        and phrase_words[0] == "section"
        and phrase_words[1].isdigit()
    ):
        match_words = phrase_words[2:]
    phrase_text = " ".join(match_words)
    content = str(chunk.get("content") or "")
    content_text = " ".join(re.findall(r"[a-z0-9$]+", content.lower()))
    if not phrase_text or not content_text:
        return 0

    phrase_tokens = set(phrase_text.split())
    content_tokens = set(content_text.split())
    score = len(phrase_tokens & content_tokens)
    phrase_words = phrase_text.split()
    raw_phrase_pattern = re.compile(
        r"\b" + r"[\s-]+".join(re.escape(word) for word in phrase_words) + r"\b",
        re.IGNORECASE,
    )
    for line in content.splitlines():
        line_text = " ".join(re.findall(r"[a-z0-9]+", line.lower()))
        if line_text == phrase_text or (
            raw_phrase_pattern.search(line) and len(line_text.split()) <= len(phrase_words) + 2
        ):
            score += 10
            break
    phrase_position = content_text.find(phrase_text)
    if phrase_position >= 0:
        score += 10
        if phrase_position <= 600:
            score += 2
        dollar_positions = [match.start() for match in re.finditer(r"\$\d", content_text)]
        if dollar_positions and min(abs(position - phrase_position) for position in dollar_positions) <= 600:
            score += 8
    if "$" in content:
        score += 1
    return score


def _merge_phrase_coverage_chunks(
    keyword_chunks: list[dict[str, Any]],
    vector_chunks: list[dict[str, Any]],
    *,
    phrase: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Merge lexical and semantic results, ranking likely account headings first."""
    merged = _round_robin_chunks([keyword_chunks, vector_chunks], limit=limit)
    indexed = list(enumerate(merged))
    indexed.sort(
        key=lambda item: (-_phrase_coverage_score(item[1], phrase), item[0])
    )
    if not indexed:
        return []

    _, top_chunk = indexed[0]
    try:
        top_index = int((top_chunk.get("metadata") or {}).get("chunk_index"))
    except (TypeError, ValueError):
        top_index = -1
    continuations: list[tuple[int, int, dict[str, Any]]] = []
    remaining: list[tuple[int, dict[str, Any]]] = []
    for original_position, chunk in indexed[1:]:
        try:
            chunk_index = int((chunk.get("metadata") or {}).get("chunk_index"))
        except (TypeError, ValueError):
            chunk_index = -1
        distance = chunk_index - top_index if top_index >= 0 and chunk_index >= 0 else -1
        if 1 <= distance <= 3:
            continuations.append((distance, original_position, chunk))
        else:
            remaining.append((original_position, chunk))
    continuations.sort(key=lambda item: (item[0], item[1]))
    return [
        top_chunk,
        *(chunk for _, _, chunk in continuations),
        *(chunk for _, chunk in remaining),
    ]


def _append_unique_chunks(
    target: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    seen_chunk_ids: set[str],
    *,
    limit: int,
    max_to_add: int | None = None,
) -> int:
    added = 0
    for chunk in chunks:
        if len(target) >= limit:
            break
        if max_to_add is not None and added >= max_to_add:
            break
        chunk_id = chunk.get("chunk_id")
        if isinstance(chunk_id, str) and chunk_id:
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)
        target.append(chunk)
        added += 1
    return added


def _topic_roots(text: str | None) -> set[str]:
    roots: set[str] = set()
    for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", (text or "").lower()):
        if token in _TOPIC_STOPWORDS:
            continue
        roots.add(token.removesuffix("ness").removesuffix("s"))
    return roots


def _previous_context_score(chunk: dict[str, Any], question_roots: set[str]) -> int:
    content = str(chunk.get("content") or "")
    stripped = content.lstrip()
    if not stripped:
        return 0

    normalized_content = stripped.lower()
    content_roots = _topic_roots(normalized_content[:1200])
    overlap = len(question_roots & content_roots)
    statutory_title_fragment = bool(_STATUTORY_TITLE_FRAGMENT_RE.search(stripped[:220]))
    starts_continued = bool(_CONTINUATION_START_RE.search(stripped[:80]))
    obvious_fragment = bool(_OBVIOUS_FRAGMENT_START_RE.search(stripped[:80]))
    if not starts_continued and not statutory_title_fragment and not obvious_fragment:
        return 0
    if overlap <= 0 and not statutory_title_fragment and not obvious_fragment:
        return 0

    score = min(overlap, 4)
    if starts_continued:
        score += 3
    if obvious_fragment:
        score += 3
    if statutory_title_fragment:
        score += 2
    if "$" in stripped[:900]:
        score += 1
    if any(term in normalized_content[:1200] for term in ("grant", "assistance", "cleanup", "loan", "authority")):
        score += 1
    return score


def _following_context_score(chunk: dict[str, Any], question_roots: set[str]) -> int:
    content = str(chunk.get("content") or "")
    stripped = content.strip()
    if not stripped:
        return 0
    normalized_content = stripped.lower()
    tail = normalized_content[-1200:]
    overlap = len(question_roots & _topic_roots(tail))
    heading_cue = bool(
        re.search(
            r"\b(?:assistance|grants?|programs?|fund|account|section\s+\d+)\b",
            tail,
        )
    )
    ends_open = stripped.endswith((",", ";", ":", "--")) or tail.endswith(
        ("under this heading", "of which", "provided further, that", "provided, that")
    )
    if overlap <= 0 or not (heading_cue or ends_open):
        return 0
    score = min(overlap, 4)
    if heading_cue:
        score += 2
    if ends_open:
        score += 2
    return score


def _merge_preserving_primary_chunks(
    primary_chunks: list[dict[str, Any]],
    variant_groups: list[list[dict[str, Any]]],
    *,
    limit: int,
    primary_floor: int,
) -> list[dict[str, Any]]:
    """Merge variants without crowding out the highest-ranked primary vector hits."""
    merged: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    _append_unique_chunks(
        merged,
        primary_chunks,
        seen_chunk_ids,
        limit=limit,
        max_to_add=min(primary_floor, limit),
    )
    if len(merged) < limit and variant_groups:
        variant_chunks = _round_robin_chunks(variant_groups, limit=limit)
        _append_unique_chunks(merged, variant_chunks, seen_chunk_ids, limit=limit)
    if len(merged) < limit:
        _append_unique_chunks(merged, primary_chunks, seen_chunk_ids, limit=limit)
    return merged


def _with_context_neighbors(
    chunks: list[dict[str, Any]],
    *,
    division: str,
    question: str,
    ctx: RAGContext,
    vectorstore_root: str | None,
    embedding_model: str | None,
    limit: int,
    neighbor_limit: int,
) -> list[dict[str, Any]]:
    """Insert a small number of adjacent Chunks for split source provisions."""
    get_chunk_by_index = getattr(ctx.vectorstores, "get_chunk_by_index", None)
    if not callable(get_chunk_by_index) or not chunks or neighbor_limit <= 0:
        return chunks

    question_roots = _topic_roots(question)
    scored_candidates: list[tuple[int, int, str, int]] = []
    for position, chunk in enumerate(chunks):
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            continue
        previous_score = _previous_context_score(chunk, question_roots)
        if previous_score > 0:
            scored_candidates.append((previous_score, -position, chunk_id, -1))
        following_score = _following_context_score(chunk, question_roots)
        if following_score > 0:
            scored_candidates.append((following_score, -position, chunk_id, 1))
    scored_candidates.sort(reverse=True)
    selected_neighbors = {
        (chunk_id, offset) for _, _, chunk_id, offset in scored_candidates[:neighbor_limit]
    }
    if not selected_neighbors:
        return chunks

    expanded: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    neighbors_added = 0
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        metadata = chunk.get("metadata", {}) or {}
        chunk_index = metadata.get("chunk_index")
        try:
            previous_index = int(chunk_index) - 1
        except (TypeError, ValueError):
            previous_index = -1
        add_previous = isinstance(chunk_id, str) and (chunk_id, -1) in selected_neighbors
        add_following = isinstance(chunk_id, str) and (chunk_id, 1) in selected_neighbors
        if add_previous and previous_index >= 0 and neighbors_added < neighbor_limit and len(expanded) <= limit - 2:
            previous = get_chunk_by_index(
                division=division,
                chunk_index=previous_index,
                vectorstore_root=vectorstore_root,
                embedding_model=embedding_model,
            )
            previous_id = previous.get("chunk_id") if isinstance(previous, dict) else None
            if isinstance(previous, dict) and isinstance(previous_id, str) and previous_id not in seen_chunk_ids:
                _append_unique_chunks(expanded, [previous], seen_chunk_ids, limit=limit)
                neighbors_added += 1
        _append_unique_chunks(expanded, [chunk], seen_chunk_ids, limit=limit)
        next_index = previous_index + 2
        if add_following and next_index >= 1 and neighbors_added < neighbor_limit and len(expanded) <= limit - 2:
            following = get_chunk_by_index(
                division=division,
                chunk_index=next_index,
                vectorstore_root=vectorstore_root,
                embedding_model=embedding_model,
            )
            following_id = following.get("chunk_id") if isinstance(following, dict) else None
            if isinstance(following, dict) and isinstance(following_id, str) and following_id not in seen_chunk_ids:
                _append_unique_chunks(expanded, [following], seen_chunk_ids, limit=limit)
                neighbors_added += 1
        if len(expanded) >= limit:
            break
    if len(expanded) < limit:
        _append_unique_chunks(expanded, chunks, seen_chunk_ids, limit=limit)
    return expanded


def _should_diversify_retrieval(state: RAGState, retrieval_query: str) -> bool:
    mode = normalize_answer_mode(state.get("answer_mode", DEFAULT_ANSWER_MODE))  # type: ignore[arg-type]
    max_results = int(state["max_results"])
    return (
        mode in BREADTH_RETRIEVAL_MODES
        and max_results >= 4
        and (
            mode == "general_summary"
            or _normalized_query(retrieval_query).lower()
            != _normalized_query(state["question"]).lower()  # type: ignore[typeddict-item]
        )
    )


def _breadth_coverage_queries(state: RAGState, ctx: RAGContext, division: str) -> list[str]:
    """Build reusable coverage queries for breadth answers from existing Division metadata."""
    mode = normalize_answer_mode(state.get("answer_mode", DEFAULT_ANSWER_MODE))  # type: ignore[arg-type]
    if mode != "general_summary":
        return []
    settings = getattr(ctx, "settings", None)
    aliases = getattr(settings, "routing_aliases", {}) or {}
    alias_text = aliases.get(division, "")
    question = str(state.get("question", "") or "")
    base_query = _normalized_query(
        " ".join(
            part
            for part in [
                question,
                division,
                alias_text if mode == "general_summary" else "",
                _GENERAL_SUMMARY_COVERAGE_TERMS,
            ]
            if part
        )
    )
    queries = [base_query] if mode == "general_summary" and base_query else []
    alias_parts = [
        part.strip()
        for part in _ALIAS_SPLIT_RE.split(str(alias_text))
        if len(part.strip()) > 2
    ]
    for index in range(0, len(alias_parts), _ALIAS_BATCH_SIZE):
        batch = alias_parts[index : index + _ALIAS_BATCH_SIZE]
        batch_query = _normalized_query(
            " ".join(
                part
                for part in [
                    question,
                    *batch,
                    _GENERAL_SUMMARY_COVERAGE_TERMS,
                ]
                if part
            )
        )
        if batch_query and batch_query.lower() not in {query.lower() for query in queries}:
            queries.append(batch_query)
    return queries[:4]


def fan_out_divisions(state: RAGState, ctx: RAGContext) -> list[Send]:
    """Create LangGraph Send events that retrieve chunks for each selected division.

    The ``ctx`` argument is unused here but kept for parity with other stages and
    so the graph builder can pass it through unconditionally.
    """
    del ctx  # not needed; retrieval Sends are pure state transformations.
    division_queries = state.get("division_queries") or [
        {
            "division": division,
            "division_acronym": division_acronym(division),
            "query": state["question"],
        }
        for division in state.get("selected_divisions", [])
    ]
    return [
        Send(
            "retrieve_division",
            {
                "question": state["question"],
                "query_id": state.get("query_id", "unknown"),
                "division": item["division"],
                "retrieval_query": item["query"],
                "max_results": state["max_results"],
                "vector_store_id": state.get("vector_store_id"),
                "vector_store_root": state.get("vector_store_root"),
                "vector_store_embedding_model": state.get("vector_store_embedding_model"),
                "answer_mode": state.get("answer_mode", DEFAULT_ANSWER_MODE),
                "answer_mode_flags": state.get("answer_mode_flags", {}),
            },
        )
        for item in division_queries
    ]


def retrieve_division(state: RAGState, ctx: RAGContext) -> dict[str, Any]:
    """Retrieve relevant source chunks for one division from the active vector store."""
    start_time = time.time()
    division = state["division"]  # type: ignore[typeddict-item]
    ctx.emit_progress(
        state,
        "retrieving",
        "Searching source text",
        division=division_acronym(division),
    )
    retrieval_query = state.get("retrieval_query", state["question"])  # type: ignore[typeddict-item]
    chunks = ctx.vectorstores.retrieve(
        question=retrieval_query,
        division=division,
        k=state["max_results"],
        vectorstore_root=state.get("vector_store_root"),
        embedding_model=state.get("vector_store_embedding_model"),
    )
    diversified = False
    if _should_diversify_retrieval(state, retrieval_query):  # type: ignore[arg-type]
        mode = normalize_answer_mode(state.get("answer_mode", DEFAULT_ANSWER_MODE))  # type: ignore[arg-type]
        max_results = int(state["max_results"])
        question_facets = _query_facets(state["question"])  # type: ignore[typeddict-item]
        rewrite_phrase_facets = _retrieval_phrase_facets(
            retrieval_query,
            state["question"],  # type: ignore[typeddict-item]
        )
        breadth_coverage_queries = _breadth_coverage_queries(state, ctx, division)
        if mode == "general_summary":
            variant_queries = [
                state["question"],  # type: ignore[typeddict-item]
                *rewrite_phrase_facets,
                *question_facets,
            ]
        else:
            variant_queries = [
                state["question"],  # type: ignore[typeddict-item]
                *rewrite_phrase_facets,
                *question_facets,
            ]
        seen_queries = {_normalized_query(retrieval_query).lower()}
        keyword_groups: list[tuple[str, list[dict[str, Any]]]] = []
        vector_groups: list[tuple[str, list[dict[str, Any]]]] = []
        keyword_retrieve = getattr(ctx.vectorstores, "keyword_retrieve", None)
        if callable(keyword_retrieve):
            seen_keyword_queries: set[str] = set()
            if mode == "general_summary":
                keyword_queries = [
                    *breadth_coverage_queries,
                    *question_facets,
                    state["question"],  # type: ignore[typeddict-item]
                ]
            else:
                keyword_queries = [
                    *rewrite_phrase_facets,
                    state["question"],  # type: ignore[typeddict-item]
                    *question_facets,
                ]
            for keyword_query in keyword_queries:
                normalized_keyword = _normalized_query(keyword_query)
                key = normalized_keyword.lower()
                if not normalized_keyword or key in seen_keyword_queries:
                    continue
                seen_keyword_queries.add(key)
                keyword_chunks = keyword_retrieve(
                    question=normalized_keyword,
                    division=division,
                    k=max_results,
                    vectorstore_root=state.get("vector_store_root"),
                    embedding_model=state.get("vector_store_embedding_model"),
                )
                if keyword_chunks:
                    keyword_groups.append((key, keyword_chunks))
        for variant_query in variant_queries:
            normalized_variant = _normalized_query(variant_query)
            key = normalized_variant.lower()
            if not normalized_variant or key in seen_queries:
                continue
            seen_queries.add(key)
            variant_chunks = ctx.vectorstores.retrieve(
                question=normalized_variant,
                division=division,
                k=max_results,
                vectorstore_root=state.get("vector_store_root"),
                embedding_model=state.get("vector_store_embedding_model"),
            )
            vector_groups.append((key, variant_chunks))
        if mode == "general_summary":
            variant_groups = [
                chunks for _, chunks in [*keyword_groups, *vector_groups]
            ]
        else:
            # For broad questions, keep the lexical and semantic lanes for
            # each rewrite-derived account phrase adjacent.  Listing every
            # lexical lane first meant a fixed result budget often never
            # reached the semantic result that contained the actual account
            # heading and appropriation.
            keyword_by_query = dict(keyword_groups)
            vector_by_query = dict(vector_groups)
            rewrite_keys = {
                _normalized_query(phrase).lower(): phrase
                for phrase in rewrite_phrase_facets
            }
            ordered_query_keys: list[str] = []
            if ";" in retrieval_query or "|" in retrieval_query:
                ordered_coverage_queries = [
                    *rewrite_phrase_facets,
                    *question_facets,
                ]
            else:
                ordered_coverage_queries = _interleave_coverage_queries(
                    rewrite_phrase_facets,
                    question_facets,
                )
            for coverage_query in [
                *ordered_coverage_queries,
                state["question"],  # type: ignore[typeddict-item]
            ]:
                key = _normalized_query(coverage_query).lower()
                if key and key not in ordered_query_keys:
                    ordered_query_keys.append(key)
            variant_groups = []
            for key in ordered_query_keys:
                keyword_chunks = keyword_by_query.get(key, [])
                vector_chunks = vector_by_query.get(key, [])
                if key in rewrite_keys:
                    combined = _merge_phrase_coverage_chunks(
                        keyword_chunks,
                        vector_chunks,
                        phrase=rewrite_keys[key],
                        limit=max_results,
                    )
                else:
                    combined = _round_robin_chunks(
                        [keyword_chunks, vector_chunks],
                        limit=max_results,
                    )
                if combined:
                    variant_groups.append(combined)
        if mode == "general_summary":
            chunks = _round_robin_chunks([chunks, *variant_groups], limit=max_results)
        else:
            # Keep a three-Chunk minimum at small K values so one split
            # provision plus its context neighbor cannot be erased by the
            # coverage lanes. At the production K=16, the 25% policy yields
            # four primary/context slots and twelve breadth slots.
            primary_floor = max(3, int(max_results * _BROAD_PRIMARY_RESULT_FRACTION))
            # Add split-provision context to the primary result lane before
            # merging coverage variants.  Expanding after the merge used to
            # truncate the tail, which is exactly where phrase/facet results
            # lived and could silently discard a requested topic.
            primary_with_context = _with_context_neighbors(
                chunks,
                division=division,
                question=state["question"],  # type: ignore[typeddict-item]
                ctx=ctx,
                vectorstore_root=state.get("vector_store_root"),
                embedding_model=state.get("vector_store_embedding_model"),
                limit=max_results,
                neighbor_limit=_BROAD_CONTEXT_NEIGHBOR_LIMIT,
            )
            chunks = _merge_preserving_primary_chunks(
                primary_with_context,
                variant_groups,
                limit=max_results,
                primary_floor=primary_floor,
            )
        diversified = True
    ctx.debug_log(
        "retrieve query_id=%s division=%s requested_k=%s returned=%s duration=%.2fs query_chars=%s diversified=%s",
        state.get("query_id", "unknown"),
        division_acronym(division),
        state["max_results"],
        len(chunks),
        time.time() - start_time,
        len(state.get("retrieval_query", state["question"])),  # type: ignore[typeddict-item]
        diversified,
    )
    return {"retrieved_chunks": chunks}


__all__ = ["fan_out_divisions", "retrieve_division"]
