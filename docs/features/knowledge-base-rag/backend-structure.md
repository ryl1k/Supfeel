# Backend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

```
backend/app/rag/
  embeddings.py  embed(texts) → batching, OpenAI client, cost logging to llm_usage (provider=openai),
                 cache lookup/insert
  ingest.py      chunking + hashing + upsert; CLI entry
  retrieve.py    retrieve(query, k, audience=None) → list[Chunk]
```
