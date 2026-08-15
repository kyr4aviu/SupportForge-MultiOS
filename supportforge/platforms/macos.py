from __future__ import annotations
from .common import base_snapshot, run_readonly


def collect_snapshot():
    data = base_snapshot()

    listening = run_readonly(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], timeout=10)
    if listening.get("available") is False:
        listening = run_readonly(["netstat", "-anv", "-p", "tcp"], timeout=10)

    data.update({
        "system": run_readonly(
            ["system_profiler", "SPSoftwareDataType", "SPHardwareDataType"],
            timeout=20,
        ),
        "services_failed": run_readonly(["launchctl", "list"], timeout=10),
        "network": run_readonly(["ifconfig"]),
        "routes": run_readonly(["netstat", "-rn"]),
        "listening": listening,
        "disk": run_readonly(["df", "-h"]),
        "recent_errors": run_readonly([
            "log", "show", "--last", "24h", "--style", "compact",
            "--predicate", "messageType == error",
        ], timeout=20),
    })
    return data
