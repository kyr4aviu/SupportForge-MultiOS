from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .docker_diag import collect_docker_status
from .platforms import collect_platform_snapshot, current_platform
from .redaction import redact_payload
from .security_v2 import collect_security_snapshot
from .health_rules import evaluate_health
from .provenance import evidence_record, provenance_summary


def collect_workstation_snapshot(include_docker: bool = True) -> dict[str, Any]:
    """Collect a normalized read-only workstation snapshot."""
    raw = collect_platform_snapshot()
    platform_name = raw.get("platform", current_platform())

    snapshot: dict[str, Any] = {
        "schema": "supportforge.workstation.snapshot.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform_name,
        "supported": bool(raw.get("supported", True)),
        "system": {
            "hostname": raw.get("hostname"),
            "os": raw.get("os"),
            "release": raw.get("release"),
            "machine": raw.get("machine"),
            "python": raw.get("python"),
            "cpu_count": raw.get("cpu_count"),
        },
        "services": raw.get("services_failed", {}),
        "network": {
            "interfaces": raw.get("network", {}),
            "routes": raw.get("routes", {}),
            "listening": raw.get("listening", {}),
        },
        "storage": raw.get("disk", {}),
        "logs": _extract_logs(raw),
        "docker": collect_docker_status() if include_docker else {"skipped": True},
        "security": collect_security_snapshot(),
    }

    records = [
        evidence_record("platform", snapshot.get("system", {}), category="system"),
        evidence_record("services", snapshot.get("services", {}), category="services"),
        evidence_record("network", snapshot.get("network", {}), category="network"),
        evidence_record("storage", snapshot.get("storage", {}), category="storage"),
        evidence_record("logs", snapshot.get("logs", {}), category="logs"),
        evidence_record("docker", snapshot.get("docker", {}), category="docker"),
        evidence_record("security", snapshot.get("security", {}), category="security"),
    ]
    snapshot["provenance"] = {
        "summary": provenance_summary(records),
        "records": records,
    }
    snapshot["health"] = evaluate_health(snapshot)
    return snapshot

def summarize_health(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper for the versioned health rules engine."""
    return evaluate_health(snapshot)

def diff_snapshots(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Return a compact structural diff for support review."""
    changes: list[dict[str, Any]] = []
    _walk_diff("", previous, current, changes)
    return {
        "schema": "supportforge.workstation.diff.v1",
        "change_count": len(changes),
        "changes": changes,
    }


def save_snapshot(
    snapshot: dict[str, Any],
    path: Path,
    redaction: str = "standard",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = redact_payload(snapshot, redaction)
    path.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Snapshot not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid snapshot JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Snapshot root must be a JSON object")
    return payload


def _extract_logs(raw: dict[str, Any]) -> dict[str, Any]:
    logs = {}
    for key in ("recent_system_errors", "recent_errors"):
        if key in raw:
            logs[key] = raw[key]
    return logs


def _command_failed(value: Any) -> bool:
    return isinstance(value, dict) and (
        value.get("available") is False
        or value.get("returncode") not in (None, 0)
        or "error" in value
    )


def _has_nonempty_output(value: Any) -> bool:
    return isinstance(value, dict) and bool(str(value.get("output", "")).strip())


def _walk_diff(
    path: str,
    before: Any,
    after: Any,
    out: list[dict[str, Any]],
) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        keys = sorted(set(before) | set(after))
        for key in keys:
            child = f"{path}.{key}" if path else str(key)
            if key not in before:
                out.append({"path": child, "type": "added", "after": after[key]})
            elif key not in after:
                out.append({"path": child, "type": "removed", "before": before[key]})
            else:
                _walk_diff(child, before[key], after[key], out)
        return

    # Large command outputs are compared as values, but not recursively.
    if before != after:
        out.append({
            "path": path,
            "type": "changed",
            "before": _compact_diff_value(before),
            "after": _compact_diff_value(after),
        })


def _compact_diff_value(value: Any) -> Any:
    """Keep diffs readable when diagnostic commands return very large output."""
    if not isinstance(value, str) or len(value) <= 1000:
        return value
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()
    return {
        "summary": "large text output",
        "characters": len(value),
        "lines": len(value.splitlines()),
        "sha256": digest,
        "preview": value[:500],
    }
