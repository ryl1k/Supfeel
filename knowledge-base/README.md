# Velora support knowledge base

Velora is the **fictional** online footwear and apparel store used in the Supfeel demo. The agent retrieves from these documents (RAG) to ground its decisions in policy.

## Structure

| Folder | Audience | Content |
|---|---|---|
| `policies/` | Customer-facing + agent | Returns, exchanges, refunds, shipping, payments, membership, warranty, account |
| `policies/agent-authority.md` | **Internal, agent only** | What the agent may do on its own, what needs confirmation, when to escalate |
| `faq/` | Customer-facing | Sizing and fit, product care, general store info |

## Authoring rules

- Each file starts with YAML frontmatter: `id`, `title`, `audience`, `tags`.
- Use `##` sections. The ingester chunks on `##` headings, so keep each section self-contained (roughly 80–300 words) and repeat key nouns instead of saying "this policy".
- Put concrete numbers in (days, amounts, thresholds). The agent must not guess them.
- After editing, re-run ingestion so the embeddings (`.npz`) are refreshed. Only changed chunks are re-embedded.
