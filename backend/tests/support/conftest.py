import shutil

import httpx
import pytest
from sqlalchemy import delete

import app.main  # noqa: F401  (puts the Slice demo store on sys.path)
from app.config import REPO_ROOT
from app.db.models import Repo
from app.db.session import session_scope
from app.repos.indexer import start_job
from app.support import assist

SLICE = REPO_ROOT / "examples" / "slice-pizza"
RID = "local__demo__slice-tickets"


@pytest.fixture(scope="module")
async def slice_repo(tmp_path_factory):
    root = tmp_path_factory.mktemp("slice") / "slice"
    shutil.copytree(SLICE, root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    async with session_scope() as s:
        await s.execute(delete(Repo).where(Repo.id == RID))
        s.add(
            Repo(
                id=RID, full_name="demo/slice", source="local", local_path=str(root),
                settings={"api_base_url": "http://slice.test", "api_token": "demo-service-token", "business_name": "Slice"},
            )
        )  # fmt: skip
    await start_job(RID, trigger="import", background=False)
    yield RID
    async with session_scope() as s:
        await s.execute(delete(Repo).where(Repo.id == RID))


@pytest.fixture(autouse=True)
def slice_api():
    from slice_api import store
    from slice_api.main import app as slice_app

    store.reset()
    assist.transport = httpx.ASGITransport(app=slice_app)
    yield store
    assist.transport = None


async def collect(events):
    out = []
    async for ev in events:
        out.append(ev)
    return out


def by(events, name):
    return [e["data"] for e in events if e["event"] == name]
