from __future__ import annotations
from typing import Any

RULESET_VERSION = "2026.08-beta2"

def evaluate_health(snapshot: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    if not snapshot.get("supported", True):
        findings.append(_f("critical","platform","SF-PLAT-001","Unsupported operating system"))

    services = snapshot.get("services", {})
    if _failed(services):
        findings.append(_f("warning","services","SF-SVC-001",
                           "Service diagnostic command failed or is unavailable"))
    elif _service_failures_present(services):
        findings.append(_f("warning","services","SF-SVC-002",
                           "Potential failed/stopped automatic services detected"))

    docker = snapshot.get("docker", {})
    if not docker.get("skipped"):
        if docker.get("installed") is False:
            findings.append(_f("info","docker","SF-DKR-001","Docker is not installed"))
        elif docker.get("installed") and not docker.get("available"):
            findings.append(_f("warning","docker","SF-DKR-002",
                               "Docker is installed but daemon/API is unavailable"))

    logs = snapshot.get("logs", {})
    if any(_output(v) for v in logs.values()):
        findings.append(_f("warning","logs","SF-LOG-001",
                           "Recent operating-system error events are present"))

    security = snapshot.get("security", {})
    for sf in security.get("findings", []):
        sev = str(sf.get("severity","info")).lower()
        if sev not in {"info","warning","critical"}:
            sev = "info"
        findings.append(_f(sev, str(sf.get("component","security")),
                           "SF-SEC-001", str(sf.get("message","Security finding"))))

    counts = {s: sum(1 for f in findings if f["severity"] == s)
              for s in ("critical","warning","info")}
    state = "critical" if counts["critical"] else "warning" if counts["warning"] else "healthy"
    return {
        "ruleset_version": RULESET_VERSION,
        "state": state,
        "counts": counts,
        "findings": findings,
    }

def _f(severity, component, rule_id, message):
    return {"severity":severity,"component":component,"rule_id":rule_id,"message":message}

def _failed(value: Any) -> bool:
    return isinstance(value, dict) and (
        value.get("available") is False or
        value.get("returncode") not in (None, 0) or
        "error" in value
    )

def _output(value: Any) -> bool:
    return isinstance(value, dict) and bool(str(value.get("output","")).strip())


def _service_failures_present(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    failed_count = value.get("failed_count")
    if isinstance(failed_count, int):
        return failed_count > 0
    return _output(value)
