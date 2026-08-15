from __future__ import annotations
import compileall, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    compile_ok = bool(compileall.compile_dir(ROOT / "supportforge", quiet=1))
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT, text=True, capture_output=True
    )
    result = {
        "compileall": compile_ok,
        "tests": tests.returncode == 0,
        "test_output": (tests.stdout + tests.stderr)[-8000:],
    }
    print(json.dumps(result, indent=2))
    return 0 if compile_ok and tests.returncode == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
