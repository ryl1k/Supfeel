# Known gotchas

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- 1536-d fits HNSW's 2000-dim limit; don't switch to `text-embedding-3-large` (3072-d) without `halfvec`.
- Strip YAML frontmatter before chunking; include doc title in chunk text for better recall.
- Running ingest on every Render boot (including cold starts) is fine *only* because unchanged hashes are skipped.
- OpenAI budget is $5 total — never embed in tests; use fixed fake vectors in `mock` mode.
- Mock mode uses `mock-hash-v1` (hashed bag-of-words). Rows are tagged with `embedding_model`, so mock and OpenAI vectors never mix; switching modes needs one ingest run.
- 11 KB files → 56 chunks. A full OpenAI ingest is ~10k tokens ≈ $0.0002.
