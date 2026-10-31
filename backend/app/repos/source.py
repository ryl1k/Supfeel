"""Repository snapshots: the text files of one commit, filtered for indexing.

GitHub repos are downloaded as a single tarball (one API request). Local directories are supported for
development and tests (admin only, `ALLOW_LOCAL_REPOS=true`).
"""

import hashlib
import io
import subprocess
import tarfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from app.config import get_settings
from app.repos.github import GitHub

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", ".next", "out", "__pycache__", ".venv", "venv", "env",
    "target", "coverage", ".idea", ".vscode", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".turbo",
    ".gradle", "bin", "obj", ".llm-cache", "site-packages", "bower_components", ".terraform",
}  # fmt: skip
SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "uv.lock", "poetry.lock", "Cargo.lock", "Gemfile.lock",
    "composer.lock", "go.sum", "Pipfile.lock", ".DS_Store", "bun.lockb",
}  # fmt: skip
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff", ".pdf", ".zip", ".gz", ".tgz", ".tar",
    ".7z", ".rar", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp3", ".mp4", ".mov", ".avi", ".webm", ".wav",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".pyc", ".o", ".a", ".bin", ".db", ".sqlite", ".psd",
    ".map", ".lockb", ".pem", ".key", ".p12", ".pfx",
}  # fmt: skip
SECRET_NAMES = {".env", ".env.local", ".env.production", ".npmrc", ".pypirc", "id_rsa", "credentials.json"}


@dataclass
class Snapshot:
    sha: str
    files: dict[str, str]
    skipped: dict[str, int] = field(default_factory=dict)
    total_bytes: int = 0


def keep_path(path: str) -> str | None:
    """Return a skip reason, or None if the file should be indexed."""
    p = PurePosixPath(path)
    if any(part in SKIP_DIRS for part in p.parts[:-1]):
        return "ignored_dir"
    name = p.name
    if name in SKIP_FILES:
        return "lockfile"
    if name in SECRET_NAMES or name.startswith(".env."):
        return "secret"
    suffix = p.suffix.lower()
    if suffix in BINARY_EXT or name.endswith((".min.js", ".min.css")):
        return "binary"
    return None


class _Collector:
    def __init__(self):
        s = get_settings()
        self.max_files, self.max_file_bytes, self.max_total = (
            s.repo_max_files,
            s.repo_max_file_bytes,
            s.repo_max_total_bytes,
        )
        self.files: dict[str, str] = {}
        self.skipped: dict[str, int] = {}
        self.total = 0

    def skip(self, reason: str) -> None:
        self.skipped[reason] = self.skipped.get(reason, 0) + 1

    def want(self, path: str, size: int) -> bool:
        reason = keep_path(path)
        if reason is None and size > self.max_file_bytes:
            reason = "too_large"
        if reason is None and (len(self.files) >= self.max_files or self.total + size > self.max_total):
            reason = "limit"
        if reason:
            self.skip(reason)
            return False
        return True

    def add(self, path: str, data: bytes) -> None:
        if b"\x00" in data[:8000]:
            self.skip("binary")
            return
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            self.skip("not_utf8")
            return
        if not text.strip():
            self.skip("empty")
            return
        self.files[path] = text
        self.total += len(data)


def from_tarball(blob: bytes, sha: str) -> Snapshot:
    c = _Collector()
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            # GitHub archives have a single top-level directory "<owner>-<repo>-<sha>/".
            parts = member.name.split("/", 1)
            if len(parts) < 2 or ".." in PurePosixPath(parts[1]).parts:
                continue
            path = parts[1]
            if not c.want(path, member.size):
                continue
            f = tar.extractfile(member)
            if f is not None:
                c.add(path, f.read())
    return Snapshot(sha=sha, files=c.files, skipped=c.skipped, total_bytes=c.total)


def from_directory(root: Path) -> Snapshot:
    c = _Collector()
    root = root.resolve()
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(root).as_posix()
        if c.want(rel, p.stat().st_size):
            c.add(rel, p.read_bytes())
    try:
        sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = ""
    if not sha:
        sha = hashlib.sha1(
            "".join(
                f"{k}\n{hashlib.sha1(v.encode()).hexdigest()}" for k, v in sorted(c.files.items())
            ).encode()
        ).hexdigest()
    return Snapshot(sha=sha, files=c.files, skipped=c.skipped, total_bytes=c.total)


async def fetch(source: str, full_name: str, ref: str, gh: GitHub | None, local_path: str | None) -> Snapshot:
    if source == "local":
        if not local_path:
            raise ValueError("local repo without a path")
        return from_directory(Path(local_path))
    assert gh is not None
    sha = await gh.branch_head(full_name, ref)
    return from_tarball(await gh.tarball(full_name, sha), sha)
