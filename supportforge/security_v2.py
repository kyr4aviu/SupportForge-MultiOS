from __future__ import annotations

from pathlib import Path
from typing import Any

from .platforms import current_platform
from .platforms.common import run_readonly


def collect_security_snapshot() -> dict[str, Any]:
    os_name = current_platform()
    findings: list[dict[str, str]] = []
    evidence: dict[str, Any] = {}

    if os_name == "linux":
        evidence["firewall_ufw"] = run_readonly(["ufw", "status"])
        evidence["ssh_config"] = _read_ssh_policy()
        evidence["failed_logins"] = _linux_failed_logins()
    elif os_name == "windows":
        evidence["defender"] = _powershell(
            "Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,"
            "AntispywareEnabled,BehaviorMonitorEnabled,AntivirusSignatureLastUpdated | "
            "Format-List | Out-String -Width 240"
        )
        evidence["firewall"] = _powershell(
            "Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,"
            "DefaultOutboundAction | Format-Table -AutoSize | Out-String -Width 240"
        )
        evidence["local_admins"] = _powershell(
            "Get-LocalGroupMember -Group Administrators -ErrorAction SilentlyContinue | "
            "Select-Object Name,ObjectClass,PrincipalSource | "
            "Format-Table -AutoSize | Out-String -Width 240"
        )
    elif os_name == "macos":
        evidence["firewall"] = run_readonly(
            ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"]
        )
        evidence["gatekeeper"] = run_readonly(["spctl", "--status"])
        evidence["filevault"] = run_readonly(["fdesetup", "status"])
        evidence["sip"] = run_readonly(["csrutil", "status"])
    else:
        findings.append({
            "severity": "critical",
            "component": "security",
            "message": "Unsupported platform",
        })

    for name, result in evidence.items():
        if isinstance(result, dict) and result.get("available") is False:
            findings.append({
                "severity": "info",
                "component": name,
                "message": "Security evidence source is unavailable on this host",
            })
        elif isinstance(result, dict) and result.get("returncode") not in (None, 0):
            findings.append({
                "severity": "warning",
                "component": name,
                "message": "Security diagnostic command returned a non-zero status",
            })

    return {
        "schema": "supportforge.security.snapshot.v1",
        "platform": os_name,
        "findings": findings,
        "evidence": evidence,
    }


def _powershell(script: str) -> dict[str, Any]:
    return run_readonly(
        [
            "powershell",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        timeout=15,
    )


def _read_ssh_policy() -> dict[str, Any]:
    path = Path("/etc/ssh/sshd_config")
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return {
            "available": False,
            "returncode": 127,
            "output": "",
            "stderr": f"Not found: {path}",
            "command": [],
        }
    except OSError as exc:
        return {
            "available": False,
            "returncode": 126,
            "output": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "command": [],
        }

    wanted = {"permitrootlogin", "passwordauthentication", "pubkeyauthentication"}
    selected = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key = line.split(None, 1)[0].lower()
        if key in wanted:
            selected.append(line)
    return {
        "available": True,
        "returncode": 0,
        "output": "\n".join(selected),
        "stderr": "",
        "command": [],
    }


def _linux_failed_logins() -> dict[str, Any]:
    result = run_readonly(["lastb", "-n", "20"])
    if result.get("available") is False:
        return result
    return result
