from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typing import Any

def run_command(args: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    """Run a fixed command safely without invoking a shell."""
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return completed.returncode, completed.stdout.strip(), completed.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {args[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout:.1f}s"
    except OSError as exc:
        return 126, "", f"Unable to execute {args[0]}: {exc}"

def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return default

def load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON configuration: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read configuration: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object")
    return data
