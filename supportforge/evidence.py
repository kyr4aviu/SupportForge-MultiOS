from __future__ import annotations
import json
from typing import Any

def flatten_evidence(value: Any, prefix: str = "") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_evidence(value[key], child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            rows.extend(flatten_evidence(item, f"{prefix}[{idx}]"))
    else:
        rows.append({"path": prefix or "$", "value": _stringify(value)})
    return rows

def search_evidence(snapshot: dict[str, Any], query: str = "") -> list[dict[str, str]]:
    rows = flatten_evidence(snapshot)
    needle = query.strip().casefold()
    if not needle:
        return rows
    return [
        row for row in rows
        if needle in row["path"].casefold() or needle in row["value"].casefold()
    ]

def filter_findings(findings: list[dict[str, Any]], severity: str = "all") -> list[dict[str, Any]]:
    wanted = severity.strip().casefold()
    if wanted in ("", "all"):
        return list(findings)
    return [f for f in findings if str(f.get("severity", "")).casefold() == wanted]

def _stringify(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
