# Backend structure

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

```
backend/app/rag/
  embeddings.py  embed(texts): mock-hash-v1 (LLM_MODE=mock or no key) or OpenAI with embedding_cache +
                 ledger (provider=openai) + cap check
  ingest.py      chunking + hashing + upsert; CLI entry
  retrieve.py    retrieve(query, k, audience=None, min_score) → list[RetrievedChunk];
                 get_section(doc_id, heading_prefix) pins a must-have policy section
```
