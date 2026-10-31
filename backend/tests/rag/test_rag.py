import pytest

from app.rag.ingest import ingest, load_chunks
from app.rag.retrieve import get_section, retrieve


@pytest.fixture(scope="module")
async def kb():
    await ingest()
    yield


def test_chunking_covers_all_docs():
    chunks = load_chunks()
    doc_ids = {c.doc_id for c in chunks}
    assert {"returns-and-exchanges", "agent-authority", "sizing-and-fit"} <= doc_ids
    assert all(c.heading and c.text for c in chunks)


async def test_ingest_is_idempotent(kb):
    second = await ingest()
    assert second["embedded"] == 0


@pytest.mark.parametrize(
    "query, expected_doc",
    [
        ("my sneakers are uncomfortable comfort guarantee exchange", "returns-and-exchanges"),
        ("package lost no tracking update", "shipping-and-delivery"),
        ("charged twice duplicate charge on my card", "payments-and-billing"),
        ("cancel my velora club membership", "velora-club-membership"),
    ],
)
async def test_retrieval_finds_relevant_policy(kb, query, expected_doc):
    results = await retrieve(query, k=4)
    assert expected_doc in [r.doc_id for r in results]


async def test_pinned_section(kb):
    sec = await get_section("agent-authority", "Actions that require explicit")
    assert sec is not None and "refund" in sec.text.lower()
