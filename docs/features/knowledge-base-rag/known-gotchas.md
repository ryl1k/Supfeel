# Known gotchas

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- 1536-d fits HNSW's 2000-dim limit; don't switch to `text-embedding-3-large` (3072-d) without `halfvec`.
- Strip YAML frontmatter before chunking; include doc title in chunk text for better recall.
- Running ingest on every Railway boot is fine *only* because unchanged hashes are skipped.
- OpenAI budget is $5 total — never embed in tests; use fixed fake vectors in `mock` mode.
