from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

def evidence_record(
    source: str,
    data: Any,
    *,
    command: list[str] | None = None,
    privilege: str = "user",
    category: str = "system",
) -> dict[str, Any]:
    serialized = json.dumps(
        data, sort_keys=True, ensure_ascii=False, default=str,
    ).encode("utf-8")
    data_summary: dict[str, Any] = {
        "type": type(data).__name__,
        "size_bytes": len(serialized),
        "sha256": hashlib.sha256(serialized).hexdigest(),
    }
    if isinstance(data, dict):
        data_summary["keys"] = sorted(str(key) for key in data)
    return {
        "source": source,
        "category": category,
        "privilege": privilege,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command or [],
        "data_summary": data_summary,
    }

def provenance_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "record_count": len(records),
        "sources": sorted({str(r.get("source","")) for r in records}),
        "privileges": sorted({str(r.get("privilege","")) for r in records}),
        "categories": sorted({str(r.get("category","")) for r in records}),
    }
