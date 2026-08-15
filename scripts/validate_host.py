from __future__ import annotations
import json, platform, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from supportforge.workstation import collect_workstation_snapshot
from supportforge.permissions import get_permissions

def main() -> int:
    snapshot = collect_workstation_snapshot(include_docker=True)
    result = {
        "supportforge_validation_schema": "v1",
        "host": {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
        },
        "snapshot_schema": snapshot.get("schema"),
        "health": snapshot.get("health"),
        "provenance": snapshot.get("provenance", {}).get("summary", {}),
        "permissions_matrix": get_permissions(snapshot.get("platform", "")),
    }
    out = Path("supportforge-host-validation.json")
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nValidation artifact: {out.resolve()}")
    return 0 if snapshot.get("supported", False) else 2

if __name__ == "__main__":
    raise SystemExit(main())
