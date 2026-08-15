from __future__ import annotations
from .common import base_snapshot, run_readonly


def collect_snapshot():
    data = base_snapshot()

    listening = run_readonly(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], timeout=10)
    if listening.get("available") is False:
        listening = run_readonly(["netstat", "-anv", "-p", "tcp"], timeout=10)

    services = _failed_launchd_services(
        run_readonly(["launchctl", "list"], timeout=10)
    )

    data.update({
        "system": run_readonly(
            ["system_profiler", "SPSoftwareDataType", "SPHardwareDataType"],
            timeout=20,
        ),
        "services_failed": services,
        "network": run_readonly(["ifconfig"]),
        "routes": run_readonly(["netstat", "-rn"]),
        "listening": listening,
        "disk": run_readonly(["df", "-h"]),
        "recent_errors": run_readonly([
            "log", "show", "--last", "24h", "--style", "compact",
            "--predicate", "messageType == error",
        ], timeout=20, max_output_chars=200_000),
    })
    return data


def _failed_launchd_services(result):
    if result.get("returncode") not in (0, None):
        return result
    lines = str(result.get("output", "")).splitlines()
    failed = []
    inspected = 0
    for line in lines:
        parts = line.split(maxsplit=2)
        if len(parts) < 3 or parts[0].upper() == "PID":
            continue
        inspected += 1
        try:
            status = int(parts[1])
        except ValueError:
            continue
        if status != 0:
            failed.append(line)
    result = dict(result)
    result["output"] = "\n".join(failed) + ("\n" if failed else "")
    result["failed_count"] = len(failed)
    result["inspected_count"] = inspected
    return result
