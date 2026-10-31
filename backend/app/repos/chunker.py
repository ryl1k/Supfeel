"""Code-aware chunking and symbol outlines (deterministic, no LLM).

Code is split at top-level definitions (functions, classes, types…) and packed into chunks of roughly
CHUNK_CHARS. Markdown splits on headings. Anything else uses overlapping line windows.
"""

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

CHUNK_CHARS = 1800
WINDOW_LINES = 60
OVERLAP_LINES = 8

LANGUAGES = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".rb": "ruby", ".php": "php", ".cs": "csharp", ".swift": "swift", ".c": "c", ".h": "c", ".cpp": "cpp",
    ".hpp": "cpp", ".scala": "scala", ".sql": "sql", ".sh": "shell", ".md": "markdown", ".mdx": "markdown",
    ".rst": "text", ".txt": "text", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".html": "html", ".css": "css", ".scss": "css", ".vue": "vue", ".svelte": "svelte", ".graphql": "graphql",
    ".proto": "proto", ".tf": "terraform", ".ini": "config", ".cfg": "config", ".env.example": "config",
}  # fmt: skip
SPECIAL_NAMES = {"dockerfile": "docker", "makefile": "make", "procfile": "config"}

# Top-level definition starts, per language family. Group 1 = kind keyword, group 2 = symbol name.
_DEFS = {
    "python": re.compile(r"^(?:async\s+)?(def|class)\s+([A-Za-z_]\w*)"),
    "javascript": re.compile(
        r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?(function\*?|class|const|let|var|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
    ),
    "go": re.compile(r"^(func|type)\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"),
    "rust": re.compile(
        r"^(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(fn|struct|enum|trait|impl|mod)\s+([A-Za-z_]\w*)"
    ),
    "jvm": re.compile(
        r"^\s{0,4}(?:public|private|protected|internal)?\s*(?:static\s+|final\s+|abstract\s+|data\s+|open\s+)*(class|interface|enum|object|fun|record)\s+([A-Za-z_]\w*)"
    ),
    "ruby": re.compile(r"^\s{0,2}(def|class|module)\s+([A-Za-z_][\w.?!]*)"),
    "php": re.compile(
        r"^\s{0,4}(?:public\s+|private\s+|protected\s+|static\s+|abstract\s+|final\s+)*(function|class|interface|trait)\s+([A-Za-z_]\w*)"
    ),
}
_FAMILY = {
    "python": "python", "javascript": "javascript", "typescript": "javascript", "vue": "javascript",
    "svelte": "javascript", "go": "go", "rust": "rust", "java": "jvm", "kotlin": "jvm", "csharp": "jvm",
    "scala": "jvm", "swift": "jvm", "ruby": "ruby", "php": "php",
}  # fmt: skip
_HEADING = re.compile(r"^(#{1,4})\s+(.+)")


@dataclass
class Chunk:
    path: str
    kind: str  # code | doc
    symbol: str
    start_line: int  # 1-based, inclusive
    end_line: int
    text: str

    def embed_text(self, language: str) -> str:
        header = f"{self.path} ({language}) lines {self.start_line}-{self.end_line}"
        if self.symbol:
            header += f" · {self.symbol}"
        return f"{header}\n\n{self.text}"


def language_for(path: str) -> str:
    p = PurePosixPath(path)
    name = p.name.lower()
    if name in SPECIAL_NAMES:
        return SPECIAL_NAMES[name]
    if name.endswith(".env.example"):
        return "config"
    return LANGUAGES.get(p.suffix.lower(), "text")


def is_doc(path: str, language: str) -> bool:
    return language in ("markdown", "text") or PurePosixPath(path).parts[:1] == ("docs",)


def outline(text: str, language: str) -> list[dict]:
    """Top-level symbols with line numbers, e.g. [{"symbol": "create_order", "kind": "def", "line": 12}]."""
    if language == "markdown":
        return [
            {"symbol": m.group(2).strip()[:120], "kind": "h" + str(len(m.group(1))), "line": i + 1}
            for i, line in enumerate(text.splitlines())
            if (m := _HEADING.match(line))
        ][:80]
    pattern = _DEFS.get(_FAMILY.get(language, ""))
    if pattern is None:
        return []
    out = []
    for i, line in enumerate(text.splitlines()):
        m = pattern.match(line)
        if m:
            out.append({"symbol": m.group(2)[:120], "kind": m.group(1), "line": i + 1})
    return out[:200]


def _windows(path: str, kind: str, lines: list[str], offset: int, symbol: str) -> list[Chunk]:
    chunks, i = [], 0
    while i < len(lines):
        part = lines[i : i + WINDOW_LINES]
        text = "\n".join(part).strip()
        if text:
            chunks.append(Chunk(path, kind, symbol, offset + i + 1, offset + i + len(part), text))
        if i + WINDOW_LINES >= len(lines):
            break
        i += WINDOW_LINES - OVERLAP_LINES
    return chunks


def _blocks(lines: list[str], starts: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    """(start_idx, end_idx_exclusive, symbol) blocks; a preamble before the first definition is its own block."""
    if not starts:
        return [(0, len(lines), "")]
    blocks = []
    if starts[0][0] > 0:
        blocks.append((0, starts[0][0], ""))
    for n, (idx, sym) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        blocks.append((idx, end, sym))
    return blocks


def chunk_file(path: str, text: str, language: str) -> list[Chunk]:
    lines = text.splitlines()
    kind = "doc" if is_doc(path, language) else "code"
    if language == "markdown":
        starts = [
            (i, m.group(2).strip()[:120]) for i, line in enumerate(lines) if (m := _HEADING.match(line))
        ]
    else:
        starts = [(o["line"] - 1, o["symbol"]) for o in outline(text, language)]
    if not starts and len(text) <= CHUNK_CHARS:
        return [Chunk(path, kind, "", 1, len(lines), text.strip())] if text.strip() else []

    chunks: list[Chunk] = []
    pending: list[tuple[int, int, str]] = []  # small adjacent blocks packed together

    def flush():
        if not pending:
            return
        s, e = pending[0][0], pending[-1][1]
        body = "\n".join(lines[s:e]).strip()
        if body:
            symbols = ", ".join(sym for _, _, sym in pending if sym)[:200]
            chunks.append(Chunk(path, kind, symbols, s + 1, e, body))
        pending.clear()

    for s, e, sym in _blocks(lines, starts):
        size = sum(len(x) + 1 for x in lines[s:e])
        if size > CHUNK_CHARS:
            flush()
            chunks.extend(_windows(path, kind, lines[s:e], s, sym))
            continue
        pending_size = sum(len(x) + 1 for x in lines[pending[0][0] : pending[-1][1]]) if pending else 0
        if pending and pending_size + size > CHUNK_CHARS:
            flush()
        pending.append((s, e, sym))
    flush()
    return chunks
