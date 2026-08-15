from pathlib import Path

PLUGIN = {
    "name": "disk-mounts",
    "version": "1.0.0",
    "description": "Counts mounted filesystems from /proc/mounts.",
}

def run(context):
    path = Path("/proc/mounts")
    if not path.exists():
        return {"available": False, "mount_count": 0}
    mounts = [
        line for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip()
    ]
    return {"available": True, "mount_count": len(mounts)}
