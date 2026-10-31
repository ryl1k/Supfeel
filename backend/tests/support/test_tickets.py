import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import get_settings
from app.db.models import Notification, Repo, RepoChunk, Ticket
from app.db.session import session_scope
from app.obs.trace import load_trace
from app.support import assist, ci, fixer, service
from app.support.fixer import FixResult
from app.support.triage import rules_triage

from .conftest import by, collect

MAYA = {"name": "Maya Chen", "email": "maya@example.com", "ref": "c_maya"}
JORDAN = {"name": "Jordan Blake", "email": "jordan@example.com", "ref": "c_jordan"}


def test_rules_triage_categories():
    assert rules_triage("I try to checkout and it keeps saying invalid address").category == "bug"
    assert rules_triage("Why did I pay a delivery fee?").category == "misunderstanding"
    t = rules_triage("The app crashes, can you reorder my last order for me?")
    assert t.category == "assisted_action" and t.also_bug
    assert rules_triage("It would be nice to have gluten-free crust").category == "feature_request"


async def _notifications(ticket_id):
    async with session_scope() as s:
        return [
            n.kind
            for n in (await s.scalars(select(Notification).where(Notification.ticket_id == ticket_id))).all()
        ]


async def test_explanation_then_customer_confirms(slice_repo):
    events = await collect(
        service.create_ticket(slice_repo, MAYA, "Why did I pay a delivery fee on my last order?")
    )
    tid = by(events, "ticket")[0]["ticket_id"]
    done = by(events, "done")[0]
    assert done["status"] == "answered" and done["route"] == "explain"
    assert "".join(e["text"] for e in by(events, "token"))
    steps = {e["step"] for e in by(events, "step")}
    assert {"context", "triage", "explain", "respond"} <= steps

    events = await collect(service.post_message(tid, "thanks, that helps"))
    assert by(events, "done")[0]["status"] == "resolved"
    async with session_scope() as s:
        assert (await s.get(Ticket, tid)).learned
        chunk = await s.scalar(select(RepoChunk).where(RepoChunk.kind == "ticket", RepoChunk.path == tid))
    assert chunk is not None and "delivery fee" in chunk.text

    trace = await load_trace(tid)
    names = {s["name"] for s in trace["spans"]}
    assert {"ticket turn (message)", "context", "triage", "respond", "search code"} <= names


async def test_assisted_reorder_with_confirmation_and_verification(slice_repo, slice_api):
    msg = "The app crashes when I tap Reorder. Can you reorder my last order for me?"
    events = await collect(service.create_ticket(slice_repo, JORDAN, msg))
    tid = by(events, "ticket")[0]["ticket_id"]
    assert by(events, "done")[0]["status"] == "awaiting_confirmation"
    [proposed] = by(events, "action_proposed")[0]["actions"]
    assert proposed["operation_id"] == "create_order"
    assert proposed["args"]["body"]["customer_id"] == "c_jordan"
    assert "bug_reported" in await _notifications(tid)  # also_bug: the crash is reported

    before = len(slice_api.DB["orders"])
    events = await collect(service.confirm(tid, approved=True))
    assert by(events, "done")[0]["status"] == "resolved"
    [verified] = by(events, "verified")
    assert verified["ok"] and len(verified["checks"]) >= 3
    assert len(slice_api.DB["orders"]) == before + 1
    new = max(slice_api.DB["orders"].values(), key=lambda o: o["id"])
    assert new["customer_id"] == "c_jordan" and new["items"] == slice_api.DB["orders"]["o_1001"]["items"]
    assert "action_taken" in await _notifications(tid)

    t = await service.get_ticket(tid)
    assert t["actions"][0]["status"] == "done" and t["actions"][0]["verification"]["ok"]


async def test_declining_changes_nothing(slice_repo, slice_api):
    events = await collect(service.create_ticket(slice_repo, JORDAN, "Can you please reorder my last order?"))
    tid = by(events, "ticket")[0]["ticket_id"]
    before = len(slice_api.DB["orders"])
    events = await collect(service.post_message(tid, "no, not now"))
    assert by(events, "done")[0]["status"] == "open"
    assert len(slice_api.DB["orders"]) == before


async def test_authority_blocks_other_customers(slice_repo):
    from sqlalchemy import select as sel

    from app.db.models import ApiOperation

    async with session_scope() as s:
        repo = await s.get(Repo, slice_repo)
        ops = [{"operation_id": o.operation_id, "method": o.method, "path": o.path, "summary": o.summary,
                "parameters": o.parameters, "body_schema": o.body_schema}
               for o in (await s.scalars(sel(ApiOperation).where(ApiOperation.repo_id == slice_repo))).all()]  # fmt: skip
    create = next(o for o in ops if o["operation_id"] == "create_order")
    with pytest.raises(assist.ActionBlocked):
        assist.scope_to_customer(create, {"body": {"customer_id": "c_jordan"}}, "c_maya")
    assert (
        assist.scope_to_customer(create, {"body": {"items": []}}, "c_maya")["body"]["customer_id"] == "c_maya"
    )
    with pytest.raises(assist.ActionBlocked):
        assist.scope_to_customer(create, {"body": {}}, None)
    # Maya cannot cancel Jordan's order: ownership is read back first.
    cancel = next(o for o in ops if o["operation_id"] == "cancel_order")
    with pytest.raises(assist.ActionBlocked):
        await assist.check_ownership(repo, ops, cancel, {"path": {"order_id": "o_1001"}}, "c_maya")
    await assist.check_ownership(repo, ops, cancel, {"path": {"order_id": "o_1002"}}, "c_maya")


async def test_bug_without_claude_is_reported_with_suspects(slice_repo):
    msg = "I try to order to 12 Oak St Apt #4B and the app keeps saying invalid address. Please help!"
    events = await collect(service.create_ticket(slice_repo, MAYA, msg))
    tid = by(events, "ticket")[0]["ticket_id"]
    assert by(events, "done")[0]["status"] == "reported"
    t = await service.get_ticket(tid)
    assert any("validation.py" in s for s in t["fix"]["suspects"])
    assert "bug_reported" in await _notifications(tid)


class FakeGitHub:
    auth, installation_id, can_write = "app", 1, True

    def __init__(self, files):
        self.files, self.commits, self.prs = files, [], []

    async def get_file(self, full_name, path, ref):
        return self.files.get(path)

    async def commit_files(self, full_name, base, branch, files, message):
        self.commits.append((branch, files, message))
        return "abc123"

    async def create_pr(self, full_name, *, head, base, title, body):
        self.prs.append({"head": head, "title": title, "body": body})
        return {"number": 7, "html_url": "https://github.com/demo/slice/pull/7"}

    async def ci_status(self, full_name, sha):
        return {
            "state": "success",
            "checks": [{"name": "test", "status": "completed", "conclusion": "success", "url": None}],
        }


async def test_bug_fix_pr_ci_and_merge_loop(slice_repo, monkeypatch):
    from app.config import REPO_ROOT

    validation = (REPO_ROOT / "examples/slice-pizza/slice_api/validation.py").read_text()
    old = '_STREET = re.compile(r"^\\d+[A-Za-z]?\\s+[A-Za-z0-9 .,\'-]+$")'
    assert old in validation
    new = old.replace(".,'-", ".,'#/-")

    async def fake_agent(repo_id, ticket_id, report):
        return FixResult(
            "fixed", root_cause="Street regex rejects '#' and '/' used in apartment numbers", summary="Allow # and / in street lines",
            test="test_accepts_apartment_numbers", confidence=0.9, workaround="Write 'Apt 4B' without the #",
            edits=[{"path": "slice_api/validation.py", "old_str": old, "new_str": new}],
            files={"slice_api/validation.py": validation.replace(old, new)}, originals={"slice_api/validation.py": validation},
        )  # fmt: skip

    gh = FakeGitHub({"slice_api/validation.py": validation})

    async def fake_client(full_name, installation_id=None):
        return gh

    monkeypatch.setattr(fixer, "run_agent", fake_agent)
    monkeypatch.setattr(fixer, "client_for", fake_client)
    monkeypatch.setattr(ci, "client_for", fake_client)
    monkeypatch.setattr(ci, "track", lambda ticket_id: None)  # drive CI manually below
    async with session_scope() as s:
        (await s.get(Repo, slice_repo)).source = "github"
    try:
        events = await collect(
            service.create_ticket(
                slice_repo, MAYA, "Checkout keeps saying invalid address for 12 Oak St Apt #4B"
            )
        )
        tid = by(events, "ticket")[0]["ticket_id"]
        assert by(events, "done")[0]["status"] == "fix_in_review"
        assert by(events, "fix")[0]["pr_url"].endswith("/pull/7")
        branch, files, _ = gh.commits[0]
        assert branch == f"supfeel/fix-{tid.lower()}" and "#/" in files["slice_api/validation.py"]
        assert tid in gh.prs[0]["body"] and "Root cause" in gh.prs[0]["body"]

        assert await ci.refresh(tid) == "success"
        t = await service.get_ticket(tid)
        assert t["status"] == "fix_verified" and t["ci"] == "success"
        assert [k for k in await _notifications(tid) if k in ("pr_opened", "ci_passed")] == [
            "pr_opened",
            "ci_passed",
        ]

        assert await ci.on_pr_closed("demo/slice", branch, merged=True) == [tid]
        t = await service.get_ticket(tid)
        assert t["status"] == "resolved" and t["learned"]
        assert "fix" in t["messages"][-1]["content"].lower()
    finally:
        async with session_scope() as s:
            (await s.get(Repo, slice_repo)).source = "local"


def _signed(body: dict, secret: str) -> tuple[bytes, str]:
    raw = json.dumps(body).encode()
    return raw, "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def test_webhook_signature_and_push(monkeypatch):
    from app.api import github as gh_api
    from app.main import app

    monkeypatch.setattr(get_settings(), "github_webhook_secret", "s3cret")
    calls = []

    async def fake_start(repo_id, trigger="manual", background=True):
        calls.append((repo_id, trigger))
        return "job_x"

    async def fake_repo(full_name):
        return Repo(id="owner__app", full_name="owner/app", default_branch="main", source="github")

    monkeypatch.setattr(gh_api, "start_job", fake_start)
    monkeypatch.setattr(gh_api, "_repo_for", fake_repo)
    client = TestClient(app)
    body = {"ref": "refs/heads/main", "repository": {"full_name": "owner/app"}}
    raw, sig = _signed(body, "wrong")
    assert (
        client.post(
            "/api/github/webhook", content=raw, headers={"x-hub-signature-256": sig, "x-github-event": "push"}
        ).status_code
        == 401
    )
    raw, sig = _signed(body, "s3cret")
    r = client.post(
        "/api/github/webhook", content=raw, headers={"x-hub-signature-256": sig, "x-github-event": "push"}
    )
    assert r.status_code == 202 and r.json()["reindex"] == "job_x"
    assert calls == [("owner__app", "push")]
    raw, sig = _signed({**body, "ref": "refs/heads/feature"}, "s3cret")
    client.post(
        "/api/github/webhook", content=raw, headers={"x-hub-signature-256": sig, "x-github-event": "push"}
    )
    assert len(calls) == 1
