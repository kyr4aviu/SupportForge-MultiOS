import tempfile
import unittest
from pathlib import Path

from supportforge.history import save_history_snapshot
from supportforge.platforms.common import run_readonly

class ReviewTests(unittest.TestCase):
    def test_run_readonly_rejects_empty(self):
        with self.assertRaises(ValueError):
            run_readonly([])

    def test_missing_command_is_reported(self):
        result = run_readonly(["definitely-not-a-real-supportforge-command-xyz"])
        self.assertFalse(result["available"])
        self.assertIn(result["returncode"], (126, 127))

    def test_history_filename_is_portable(self):
        with tempfile.TemporaryDirectory() as td:
            p = save_history_snapshot(
                {"generated_at_utc": "2026-08-15T12:34:56+03:00"},
                Path(td),
            )
            self.assertNotIn(":", p.name)
            self.assertTrue(p.exists())

if __name__ == "__main__":
    unittest.main()
