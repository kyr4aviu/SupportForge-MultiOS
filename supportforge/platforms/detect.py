from __future__ import annotations
import platform
from typing import Any


def current_platform() -> str:
    name = platform.system().lower()
    return {"linux": "linux", "windows": "windows", "darwin": "macos"}.get(name, "unknown")


def collect_platform_snapshot() -> dict[str, Any]:
    target = current_platform()
    if target == "linux":
        from .linux import collect_snapshot
    elif target == "windows":
        from .windows import collect_snapshot
    elif target == "macos":
        from .macos import collect_snapshot
    else:
        return {"platform": target, "supported": False, "error": "Unsupported operating system"}
    data = collect_snapshot()
    data.setdefault("platform", target)
    data.setdefault("supported", True)
    return data
