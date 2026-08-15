from __future__ import annotations
import json
from typing import Any
from .utils import run_command

def collect_docker_status() -> dict[str, Any]:
    rc, version, err = run_command(["docker", "version", "--format", "{{json .}}"], timeout=8)
    if rc == 127:
        return {"installed": False, "available": False, "error": err}
    if rc != 0:
        return {"installed": True, "available": False, "error": err or version}

    try:
        version_data = json.loads(version)
    except json.JSONDecodeError:
        version_data = {"raw": version}

    rc_ps, stdout, stderr = run_command(
        ["docker", "ps", "-a", "--format", "{{json .}}"], timeout=10
    )
    containers = []
    if rc_ps == 0:
        for line in stdout.splitlines():
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                containers.append({"raw": line})

    return {
        "installed": True,
        "available": rc_ps == 0,
        "version": version_data,
        "container_count": len(containers),
        "containers": containers,
        "error": stderr if rc_ps != 0 else "",
    }
