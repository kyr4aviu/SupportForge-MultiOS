from __future__ import annotations
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
    return {
        "source": source,
        "category": category,
        "privilege": privilege,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command or [],
        "data": data,
    }

def provenance_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "record_count": len(records),
        "sources": sorted({str(r.get("source","")) for r in records}),
        "privileges": sorted({str(r.get("privilege","")) for r in records}),
        "categories": sorted({str(r.get("category","")) for r in records}),
    }
