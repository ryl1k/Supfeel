"""GitHub REST client: App installation tokens (preferred), PAT fallback, or anonymous for public repos.

Every request is traced as an `http` span. See docs/project/github-app-setup.md for the App setup.
"""

import base64
import hashlib
import hmac
import time
from typing import Any
from urllib.parse import quote

import httpx
import jwt

from app.config import get_settings
from app.obs import trace

MAX_TARBALL_BYTES = 120_000_000
FAILED_CONCLUSIONS = {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}


class GitHubError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"GitHub {status}: {message}")
        self.status = status


_installation_tokens: dict[int, tuple[str, float]] = {}


def _app_jwt() -> str:
    settings = get_settings()
    now = int(time.time())
    return jwt.encode(
        {"iat": now - 60, "exp": now + 540, "iss": settings.github_app_id},
        settings.github_private_key,
        algorithm="RS256",
    )


def verify_signature(body: bytes, signature_header: str | None) -> bool:
    secret = get_settings().github_webhook_secret
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


class GitHub:
    def __init__(self, token: str | None = None, auth: str = "anonymous", installation_id: int | None = None):
        self.token = token
        self.auth = auth  # app | token | anonymous
        self.installation_id = installation_id

    @property
    def can_write(self) -> bool:
        return self.auth in ("app", "token")

    def _headers(self, token: str | None = None) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        tok = token or self.token
        if tok:
            h["Authorization"] = f"Bearer {tok}"
        return h

    async def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        expected: tuple[int, ...] = (200, 201),
        **kw: Any,
    ) -> Any:
        url = path if path.startswith("http") else get_settings().github_api_url + path
        async with trace.span(f"github {method} {path.split('?')[0]}", kind="http", method=method) as sp:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as http:
                r = await http.request(method, url, headers=self._headers(token), **kw)
            sp.set(status=r.status_code)
            if r.status_code not in expected:
                try:
                    msg = r.json().get("message", r.text)
                except ValueError:
                    msg = r.text
                raise GitHubError(r.status_code, str(msg)[:300])
            return r.json() if r.content and "json" in r.headers.get("content-type", "") else r.content

    # ------------------------------------------------------------------ read

    async def get_repo(self, full_name: str) -> dict[str, Any]:
        return await self.request("GET", f"/repos/{full_name}")

    async def branch_head(self, full_name: str, branch: str) -> str:
        data = await self.request("GET", f"/repos/{full_name}/commits/{branch}")
        return data["sha"]

    async def tarball(self, full_name: str, ref: str) -> bytes:
        url = f"{get_settings().github_api_url}/repos/{full_name}/tarball/{ref}"
        async with trace.span("github GET tarball", kind="http", ref=ref) as sp:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as http:
                async with http.stream("GET", url, headers=self._headers()) as r:
                    if r.status_code != 200:
                        raise GitHubError(r.status_code, "tarball download failed")
                    buf = bytearray()
                    async for chunk in r.aiter_bytes():
                        buf.extend(chunk)
                        if len(buf) > MAX_TARBALL_BYTES:
                            raise GitHubError(413, "repository archive is too large")
            sp.set(bytes=len(buf))
            return bytes(buf)

    async def get_file(self, full_name: str, path: str, ref: str) -> str | None:
        try:
            data = await self.request("GET", f"/repos/{full_name}/contents/{quote(path)}?ref={quote(ref)}")
        except GitHubError as e:
            if e.status == 404:
                return None
            raise
        return base64.b64decode(data.get("content", "")).decode("utf-8")

    async def compare(self, full_name: str, base: str, head: str) -> list[dict[str, Any]]:
        data = await self.request("GET", f"/repos/{full_name}/compare/{base}...{head}")
        return [
            {"path": f["filename"], "status": f["status"], "previous": f.get("previous_filename")}
            for f in data.get("files", [])
        ]

    async def ci_status(self, full_name: str, sha: str) -> dict[str, Any]:
        """Combine check runs and commit statuses into one state: none | pending | success | failure."""
        runs = (await self.request("GET", f"/repos/{full_name}/commits/{sha}/check-runs?per_page=50")).get(
            "check_runs", []
        )
        combined = await self.request("GET", f"/repos/{full_name}/commits/{sha}/status")
        checks = [
            {"name": r["name"], "status": r["status"], "conclusion": r.get("conclusion"), "url": r.get("html_url")}
            for r in runs
        ] + [
            {"name": st["context"], "status": "completed" if st["state"] != "pending" else "in_progress",
             "conclusion": {"success": "success", "pending": None}.get(st["state"], "failure"), "url": st.get("target_url")}
            for st in combined.get("statuses", [])
        ]  # fmt: skip
        if not checks:
            state = "none"
        elif any(c["status"] != "completed" for c in checks):
            state = "pending"
        elif any(c["conclusion"] in FAILED_CONCLUSIONS for c in checks):
            state = "failure"
        else:
            state = "success"
        return {"state": state, "checks": checks}

    # ------------------------------------------------------------------ write

    async def commit_files(
        self, full_name: str, base_branch: str, branch: str, files: dict[str, str | None], message: str
    ) -> str:
        """Create (or force-update) `branch` from `base_branch` with one commit changing `files`
        (content, or None to delete). Returns the new commit sha."""
        base_sha = (await self.request("GET", f"/repos/{full_name}/git/ref/heads/{base_branch}"))["object"][
            "sha"
        ]
        base_tree = (await self.request("GET", f"/repos/{full_name}/git/commits/{base_sha}"))["tree"]["sha"]
        tree = [
            {
                "path": p,
                "mode": "100644",
                "type": "blob",
                **({"content": c} if c is not None else {"sha": None}),
            }
            for p, c in files.items()
        ]
        new_tree = await self.request(
            "POST", f"/repos/{full_name}/git/trees", json={"base_tree": base_tree, "tree": tree}
        )
        commit = await self.request(
            "POST",
            f"/repos/{full_name}/git/commits",
            json={"message": message, "tree": new_tree["sha"], "parents": [base_sha]},
        )
        try:
            await self.request(
                "POST",
                f"/repos/{full_name}/git/refs",
                json={"ref": f"refs/heads/{branch}", "sha": commit["sha"]},
            )
        except GitHubError as e:
            if e.status != 422:
                raise
            await self.request(
                "PATCH",
                f"/repos/{full_name}/git/refs/heads/{branch}",
                json={"sha": commit["sha"], "force": True},
            )
        return commit["sha"]

    async def create_pr(
        self, full_name: str, *, head: str, base: str, title: str, body: str
    ) -> dict[str, Any]:
        try:
            return await self.request(
                "POST",
                f"/repos/{full_name}/pulls",
                json={"head": head, "base": base, "title": title, "body": body},
            )
        except GitHubError as e:
            if e.status != 422:
                raise
            owner = full_name.split("/")[0]
            existing = await self.request("GET", f"/repos/{full_name}/pulls?head={owner}:{head}&state=open")
            if existing:
                return existing[0]
            raise

    async def create_issue(
        self, full_name: str, *, title: str, body: str, labels: list[str]
    ) -> dict[str, Any]:
        return await self.request(
            "POST", f"/repos/{full_name}/issues", json={"title": title, "body": body, "labels": labels}
        )


async def client_for(full_name: str, installation_id: int | None = None) -> GitHub:
    """Best available credentials for this repository."""
    settings = get_settings()
    if settings.github_app_configured:
        try:
            if installation_id is None:
                app = GitHub(_app_jwt(), auth="app-jwt")
                installation_id = (await app.request("GET", f"/repos/{full_name}/installation"))["id"]
            token = await _installation_token(installation_id)
            return GitHub(token, auth="app", installation_id=installation_id)
        except GitHubError:
            pass  # app not installed on this repo: fall through
    if settings.github_token:
        return GitHub(settings.github_token, auth="token")
    return GitHub(None, auth="anonymous")


async def _installation_token(installation_id: int) -> str:
    cached = _installation_tokens.get(installation_id)
    if cached and cached[1] > time.time() + 120:
        return cached[0]
    app = GitHub(_app_jwt(), auth="app-jwt")
    data = await app.request("POST", f"/app/installations/{installation_id}/access_tokens")
    # Tokens live one hour; refresh a little early.
    _installation_tokens[installation_id] = (data["token"], time.time() + 3300)
    return data["token"]


def auth_mode() -> str:
    s = get_settings()
    return "app" if s.github_app_configured else "token" if s.github_token else "anonymous"
