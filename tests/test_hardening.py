import unittest
from unittest.mock import patch

from supportforge.platforms import linux, macos


class HardeningTests(unittest.TestCase):
    @patch("supportforge.platforms.linux.run_readonly")
    def test_linux_ss_falls_back_without_process_flag(self, run):
        run.side_effect = [
            {"available": True, "returncode": 1, "output": "", "stderr": "denied", "command": []},
            {"available": True, "returncode": 0, "output": "ok", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
        ]
        with patch("supportforge.platforms.linux.base_snapshot", return_value={}):
            linux.collect_snapshot()
        calls = [args[0][0] for args in run.call_args_list]
        self.assertIn(["ss", "-lntup"], calls)
        self.assertIn(["ss", "-lntu"], calls)

    @patch("supportforge.platforms.macos.run_readonly")
    def test_macos_lsof_fallback(self, run):
        run.side_effect = [
            {"available": False, "returncode": 127, "output": "", "stderr": "missing", "command": []},
            {"available": True, "returncode": 0, "output": "tcp", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
            {"available": True, "returncode": 0, "output": "", "stderr": "", "command": []},
        ]
        with patch("supportforge.platforms.macos.base_snapshot", return_value={}):
            macos.collect_snapshot()
        calls = [args[0][0] for args in run.call_args_list]
        self.assertIn(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], calls)
        self.assertIn(["netstat", "-anv", "-p", "tcp"], calls)


if __name__ == "__main__":
    unittest.main()
