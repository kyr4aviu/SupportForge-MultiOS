from __future__ import annotations
import shutil
from .common import base_snapshot, run_readonly


def ps(script: str):
    executable = shutil.which("powershell") or shutil.which("pwsh") or "powershell"
    return run_readonly(
        [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
         "Bypass", "-Command", script],
        timeout=15,
    )


def collect_snapshot():
    data = base_snapshot()
    data.update({
        "services_failed": ps(
            "Get-CimInstance Win32_Service | "
            "Where-Object {$_.StartMode -eq 'Auto' -and $_.State -ne 'Running'} | "
            "Select-Object -First 50 Name,DisplayName,State,StartMode | "
            "Format-Table -AutoSize | Out-String -Width 240"
        ),
        "network": ps("Get-NetIPConfiguration | Format-List | Out-String -Width 240"),
        "routes": ps(
            "Get-NetRoute | Sort-Object RouteMetric | Select-Object -First 100 "
            "DestinationPrefix,NextHop,RouteMetric,InterfaceAlias | "
            "Format-Table -AutoSize | Out-String -Width 240"
        ),
        "listening": ps(
            "Get-NetTCPConnection -State Listen | Select-Object -First 100 "
            "LocalAddress,LocalPort,OwningProcess | "
            "Format-Table -AutoSize | Out-String -Width 240"
        ),
        "disk": ps(
            "Get-Volume | Select-Object DriveLetter,FileSystemLabel,FileSystem,"
            "HealthStatus,SizeRemaining,Size | "
            "Format-Table -AutoSize | Out-String -Width 240"
        ),
        "recent_system_errors": ps(
            "Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; "
            "StartTime=(Get-Date).AddHours(-24)} -ErrorAction SilentlyContinue | "
            "Select-Object -First 100 TimeCreated,Id,ProviderName,Message | "
            "Format-List | Out-String -Width 240"
        ),
    })
    return data
