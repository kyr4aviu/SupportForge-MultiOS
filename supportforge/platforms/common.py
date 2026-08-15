from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys
from typing import Any


def base_snapshot() -> dict[str, Any]:
    return {
        "platform": _platform_name(),
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "supported": _platform_name() in {"linux", "windows", "macos"},
    }


def run_readonly(
    args: list[str],
    timeout: float = 10.0,
    max_output_chars: int | None = None,
) -> dict[str, Any]:
    if not args or not all(isinstance(x, str) and x for x in args):
        raise ValueError("Command arguments must be a non-empty list of strings")
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        output, output_meta = _bounded_text(proc.stdout, max_output_chars)
        stderr, stderr_meta = _bounded_text(proc.stderr, max_output_chars)
        return {
            "available": True,
            "returncode": proc.returncode,
            "output": output,
            "stderr": stderr,
            "command": args,
            **output_meta,
            **{f"stderr_{key}": value for key, value in stderr_meta.items()},
        }
    except FileNotFoundError:
        return {
            "available": False,
            "returncode": 127,
            "output": "",
            "stderr": f"Command not found: {args[0]}",
            "command": args,
        }
    except subprocess.TimeoutExpired as exc:
        output, output_meta = _bounded_text(_as_text(exc.stdout), max_output_chars)
        return {
            "available": True,
            "returncode": 124,
            "output": output,
            "stderr": f"Command timed out after {timeout} seconds",
            "command": args,
            **output_meta,
        }
    except OSError as exc:
        code = 127 if getattr(exc, "errno", None) == 2 else 126
        return {
            "available": False,
            "returncode": code,
            "output": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "command": args,
        }


def _platform_name() -> str:
    name = platform.system().lower()
    if name == "darwin":
        return "macos"
    if name.startswith("win"):
        return "windows"
    if name == "linux":
        return "linux"
    return "unknown"


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _bounded_text(text: str, limit: int | None) -> tuple[str, dict[str, Any]]:
    if limit is None or len(text) <= limit:
        return text, {}
    marker = f"[SupportForge truncated {len(text) - limit} earlier characters]\n"
    return marker + text[-limit:], {
        "output_truncated": True,
        "original_output_chars": len(text),
    }
