from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_HISTORY_DIR = Path.home() / ".supportforge" / "history"

def snapshot_stem(snapshot: dict[str, Any]) -> str:
    """Return the shared base name for history and exported scan artifacts."""
    raw = str(snapshot.get("generated_at_utc", "unknown"))
    stamp = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip("-") or "unknown"
    return f"snapshot-{stamp}"

def save_history_snapshot(snapshot: dict[str, Any], history_dir: Path = DEFAULT_HISTORY_DIR) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    path = history_dir / f"{snapshot_stem(snapshot)}.json"
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

def list_history(history_dir: Path = DEFAULT_HISTORY_DIR) -> list[Path]:
    if not history_dir.exists():
        return []
    return sorted(history_dir.glob("snapshot-*.json"), reverse=True)

def prune_history(max_entries: int = 50, history_dir: Path = DEFAULT_HISTORY_DIR) -> int:
    if max_entries < 1:
        raise ValueError("max_entries must be >= 1")
    files = list_history(history_dir)
    removed = 0
    for path in files[max_entries:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
