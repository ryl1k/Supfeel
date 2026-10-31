"""Generated explanations of a repository: one summary per module (directory) and a repo overview.

Claude writes them in live mode; otherwise (mock mode, budget cap, API error) a deterministic summary is built
from file outlines and the README. Inputs are hashed, so unchanged modules are never regenerated.
"""

import asyncio
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from app.config import get_settings
from app.llm.client import BudgetExceeded, LlmUnavailable, complete_text

MODULE_SYSTEM = """You document software repositories for a customer-support team and for engineers.
Given one module (a directory) of a repository — its files, their top-level symbols and excerpts — write a
concise markdown summary with exactly these sections:

### Purpose
One or two sentences.
### Key files
Bullets: `path` — what it does.
### How it works
Short bullets on the main flow, data and dependencies.
### Customer-facing behavior
Bullets on what end users would experience because of this code (features, limits, error messages, rules).
Write "None (internal)" if not user-facing.

Rules: only state what the excerpts support; name real files and symbols; no preamble; under 300 words."""

OVERVIEW_SYSTEM = """You document software repositories for a customer-support team and for engineers.
Given a repository's README, file tree, languages and per-module summaries, write a markdown overview with
these sections:

## What it is
## Architecture
(bullets: components and how they talk to each other)
## Main user flows
(numbered: what a user can do, and which modules implement it)
## Business rules and limits
(bullets: rules a support agent must know: validation, limits, pricing, permissions, error cases)
## Glossary
## Where to look
(bullets: "to debug X, start in `path`")

Rules: only state what the inputs support; reference real paths; no preamble; under 700 words."""


@dataclass
class Module:
    key: str
    files: list[str] = field(default_factory=list)
    size: int = 0


def module_key(path: str) -> str:
    parts = PurePosixPath(path).parts[:-1]
    return "/".join(parts[:2]) if parts else "."


def group_modules(files: dict[str, str]) -> list[Module]:
    modules: dict[str, Module] = {}
    for path, text in files.items():
        m = modules.setdefault(module_key(path), Module(module_key(path)))
        m.files.append(path)
        m.size += len(text)
    return sorted(modules.values(), key=lambda m: -m.size)


def module_input(
    m: Module, files: dict[str, str], outlines: dict[str, list[dict]], budget: int = 14_000
) -> str:
    lines = [f"Module: {m.key}", f"Files ({len(m.files)}):"]
    for p in sorted(m.files)[:80]:
        syms = ", ".join(o["symbol"] for o in outlines.get(p, [])[:12])
        lines.append(f"- {p}" + (f": {syms}" if syms else ""))
    lines.append("\nExcerpts:")
    used = sum(len(x) for x in lines)
    readme_first = sorted(m.files, key=lambda p: (not p.lower().endswith("readme.md"), -len(files[p])))
    for p in readme_first[:6]:
        excerpt = "\n".join(files[p].splitlines()[:70])[: max(0, min(3500, budget - used))]
        if not excerpt:
            break
        lines.append(f"\n--- {p} ---\n{excerpt}")
        used += len(excerpt)
    return "\n".join(lines)


def rules_module_summary(m: Module, outlines: dict[str, list[dict]], files: dict[str, str]) -> str:
    langs = Counter(PurePosixPath(p).suffix or PurePosixPath(p).name for p in m.files)
    out = [
        "### Purpose",
        f"`{m.key}` contains {len(m.files)} file(s) ({', '.join(f'{k} ×{v}' for k, v in langs.most_common(4))}).",
        "### Key files",
    ]
    for p in sorted(m.files, key=lambda p: -len(files[p]))[:8]:
        syms = ", ".join(f"`{o['symbol']}`" for o in outlines.get(p, [])[:6])
        out.append(f"- `{p}`" + (f": {syms}" if syms else ""))
    readme = next((p for p in m.files if p.lower().endswith("readme.md")), None)
    if readme:
        first = next((ln for ln in files[readme].splitlines() if ln.strip() and not ln.startswith("#")), "")
        out += ["### How it works", first[:400]]
    return "\n".join(out)


def rules_overview(
    full_name: str, files: dict[str, str], modules: list[Module], summaries: dict[str, str]
) -> str:
    readme = next((files[p] for p in files if p.lower() == "readme.md"), "")
    langs = Counter(PurePosixPath(p).suffix for p in files if PurePosixPath(p).suffix)
    out = ["## What it is", readme or f"`{full_name}` (no README found).", "", "## Modules"]
    for m in modules[:25]:
        first = next((ln for ln in summaries.get(m.key, "").splitlines()[1:2]), "")
        out.append(f"- `{m.key}`: {first}")
    out += ["", "## Languages", ", ".join(f"{k} ({v})" for k, v in langs.most_common(8))]
    return "\n".join(out)


def input_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def summarize_module(text: str, job_id: str) -> tuple[str, str] | None:
    """Returns (body, "llm") or None when Claude is unavailable."""
    try:
        body = await complete_text(
            node="repo_module_summary",
            system=MODULE_SYSTEM,
            user=text,
            max_tokens=700,
            conversation_id=f"job:{job_id}",
            session_cap=get_settings().index_cap_usd,
        )
        return body.strip(), "llm"
    except (LlmUnavailable, BudgetExceeded):
        return None


async def summarize_overview(text: str, job_id: str) -> str | None:
    try:
        return (
            await complete_text(
                node="repo_overview",
                system=OVERVIEW_SYSTEM,
                user=text,
                max_tokens=1600,
                conversation_id=f"job:{job_id}",
                session_cap=get_settings().index_cap_usd,
            )
        ).strip()
    except (LlmUnavailable, BudgetExceeded):
        return None


def overview_input(
    full_name: str, files: dict[str, str], modules: list[Module], summaries: dict[str, str]
) -> str:
    readme = next((files[p] for p in files if p.lower() == "readme.md"), "")
    tree = defaultdict(int)
    for p in files:
        tree[module_key(p)] += 1
    langs = Counter(PurePosixPath(p).suffix for p in files if PurePosixPath(p).suffix)
    parts = [
        f"Repository: {full_name}",
        "Languages: " + ", ".join(f"{k} ({v})" for k, v in langs.most_common(10)),
        "Tree (module: files): " + ", ".join(f"{k}: {v}" for k, v in sorted(tree.items())[:60]),
        "README:\n" + readme[:6000],
        "Module summaries:",
    ]
    for m in modules[:30]:
        parts.append(f"\n#### {m.key}\n{summaries.get(m.key, '')[:1200]}")
    return "\n".join(parts)


async def gather_limited(coros, limit: int = 4):
    sem = asyncio.Semaphore(limit)

    async def run(c):
        async with sem:
            return await c

    return await asyncio.gather(*(run(c) for c in coros))
