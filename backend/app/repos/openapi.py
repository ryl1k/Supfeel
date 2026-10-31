"""Discover business API operations from an OpenAPI 3 / Swagger 2 spec (in the repo, or at a URL)."""

import json
import re
from pathlib import PurePosixPath
from typing import Any

import httpx
import yaml

from app.obs import trace

METHODS = ("get", "post", "put", "patch", "delete")
SPEC_NAMES = re.compile(r"^(openapi|swagger|api-?spec)[\w.-]*\.(json|ya?ml)$", re.I)


def parse(text: str) -> dict[str, Any] | None:
    try:
        doc = json.loads(text)
    except ValueError:
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError:
            return None
    if (
        isinstance(doc, dict)
        and ("openapi" in doc or "swagger" in doc)
        and isinstance(doc.get("paths"), dict)
    ):
        return doc
    return None


def find_specs(files: dict[str, str]) -> list[tuple[str, dict[str, Any]]]:
    found = []
    for path, text in files.items():
        if SPEC_NAMES.match(PurePosixPath(path).name) and (doc := parse(text)):
            found.append((path, doc))
    return found


def _resolve(doc: dict[str, Any], node: Any, depth: int = 0) -> Any:
    """Inline local $refs (bounded depth) so the planner sees concrete schemas."""
    if depth > 6:
        return node
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            target: Any = doc
            for part in ref[2:].split("/"):
                target = target.get(part, {}) if isinstance(target, dict) else {}
            return _resolve(doc, target, depth + 1)
        return {
            k: _resolve(doc, v, depth + 1) for k, v in node.items() if k not in ("example", "examples", "xml")
        }
    if isinstance(node, list):
        return [_resolve(doc, v, depth + 1) for v in node]
    return node


def operations(doc: dict[str, Any], source: str) -> list[dict[str, Any]]:
    ops = []
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        shared = item.get("parameters", [])
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            params = []
            for p in [*shared, *op.get("parameters", [])]:
                p = _resolve(doc, p)
                if isinstance(p, dict) and p.get("in") in ("path", "query"):
                    params.append(
                        {
                            "name": p.get("name"),
                            "in": p.get("in"),
                            "required": bool(p.get("required") or p.get("in") == "path"),
                            "schema": p.get("schema") or {"type": p.get("type", "string")},
                            "description": (p.get("description") or "")[:200],
                        }
                    )
            body = None
            content = (op.get("requestBody") or {}).get("content") or {}
            if "application/json" in content:
                body = _resolve(doc, content["application/json"].get("schema"))
            op_id = op.get("operationId") or f"{method}_{re.sub(r'[^A-Za-z0-9]+', '_', path).strip('_')}"
            ops.append(
                {
                    "operation_id": op_id[:200],
                    "method": method.upper(),
                    "path": path,
                    "summary": (op.get("summary") or op.get("description") or "")[:500],
                    "parameters": params,
                    "body_schema": body,
                    "source": source,
                }
            )
    return ops


async def fetch_spec(url: str) -> dict[str, Any] | None:
    async with trace.span("fetch openapi spec", kind="http", url=url):
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as http:
            r = await http.get(url)
    return parse(r.text) if r.status_code == 200 else None


def describe(op: dict[str, Any]) -> str:
    """Compact text for embedding / prompting."""
    params = ", ".join(f"{p['name']}{'*' if p['required'] else ''} ({p['in']})" for p in op["parameters"])
    body = ""
    if isinstance(op.get("body_schema"), dict):
        props = (op["body_schema"].get("properties") or {}).keys()
        body = f" body: {', '.join(props)}" if props else ""
    return f"{op['method']} {op['path']} [{op['operation_id']}] {op['summary']} params: {params or '-'}{body}"
