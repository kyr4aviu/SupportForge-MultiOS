from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def create_bundle(source_dir: Path, output_zip: Path) -> dict[str, Any]:
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"Source report directory not found: {source_dir}")

    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source_dir.name,
        "files": [],
    }
    for path in files:
        manifest["files"].append({
            "path": path.relative_to(source_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(source_dir).as_posix())
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"),
        )

    return {
        "ok": True,
        "bundle": str(output_zip),
        "file_count": len(files),
        "bundle_sha256": sha256_file(output_zip),
        "manifest": manifest,
    }
