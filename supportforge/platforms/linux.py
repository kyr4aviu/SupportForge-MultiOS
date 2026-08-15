from __future__ import annotations
from .common import base_snapshot, run_readonly


def collect_snapshot():
    data = base_snapshot()

    listening = run_readonly(["ss", "-lntup"])
    if listening.get("returncode") not in (0, None):
        listening = run_readonly(["ss", "-lntu"])

    data.update({
        "services_failed": run_readonly(
            ["systemctl", "--failed", "--no-pager", "--plain", "--no-legend"],
            timeout=8,
        ),
        "network": run_readonly(["ip", "-brief", "address"]),
        "routes": run_readonly(["ip", "route"]),
        "listening": listening,
        "disk": run_readonly(["df", "-h"]),
        "recent_errors": run_readonly([
            "journalctl", "--no-pager", "-p", "0..3", "--since", "24 hours ago",
            "-n", "100",
        ], timeout=12),
    })
    return data
