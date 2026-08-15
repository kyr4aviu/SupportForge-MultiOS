from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any
from .platforms.common import run_readonly


def find_postgres_command(name: str) -> str:
    """Find PostgreSQL tools, including common self-contained desktop installs."""
    found = shutil.which(name)
    if found:
        return found

    candidates = [
        Path("/Applications/Postgres.app/Contents/Versions/latest/bin") / name,
        Path.home() / "Applications/Postgres.app/Contents/Versions/latest/bin" / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return name

def collect_postgres_snapshot(
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str | None = None,
) -> dict[str, Any]:
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("PostgreSQL port must be between 1 and 65535")

    args = [find_postgres_command("pg_isready"), "-h", host, "-p", str(port), "-d", database]
    if user:
        args += ["-U", user]
    readiness = run_readonly(args, timeout=8)

    result: dict[str, Any] = {
        "schema":"supportforge.postgres.snapshot.v1",
        "target":{"host":host,"port":port,"database":database,"user":user or ""},
        "readiness":readiness,
        "server":{},
        "activity":{},
    }

    if readiness.get("returncode") == 0:
        base = [find_postgres_command("psql"),"-X","-A","-t","-h",host,"-p",str(port),"-d",database]
        if user:
            base += ["-U",user]
        result["server"] = run_readonly(
            base + ["-c", "SELECT version();"], timeout=8
        )
        result["activity"] = run_readonly(
            base + ["-c",
            "SELECT datname, count(*) FROM pg_stat_activity "
            "WHERE datname IS NOT NULL GROUP BY datname ORDER BY datname;"],
            timeout=8,
        )
    return result
