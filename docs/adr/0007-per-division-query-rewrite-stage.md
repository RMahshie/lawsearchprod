# Per-Division query rewrite before retrieval

The Query Pipeline includes a dedicated **Rewrite** stage between Route and Retrieve. For each selected Division, an LLM rewrites the user's question into a Division-tailored retrieval query. DOD's store is queried with a different phrasing than LHHS's store, even when the original user question was identical.

## Why

Many real questions span multiple Divisions, but the relevant content lives in different forms across them — DOD talks about "operation and maintenance accounts," LHHS talks about "Pell grants" — and the user's natural-language phrasing rarely matches all of them well. Sending the raw question to every Division's store produced noisy retrieval: low-similarity hits from Divisions where the content didn't exist crowded out high-similarity hits from Divisions where it did. Rewriting per Division narrows each retrieval to the language each store actually contains.

## Trade-off accepted

One extra LLM call per selected Division (run on a cheap model). In exchange, retrieval recall on cross-Division questions improves substantially, and the noise rate at the Map stage drops — fewer wasted Map calls on irrelevant chunks downstream.
