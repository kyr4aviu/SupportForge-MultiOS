import unittest
from unittest.mock import patch

from supportforge.platforms import linux, macos
from supportforge.platforms.common import run_readonly


class HardeningTests(unittest.TestCase):
    def test_readonly_output_limit_keeps_recent_tail(self):
        result = run_readonly(
            ["/usr/bin/printf", "1234567890"], max_output_chars=4,
        )
        self.assertTrue(result["output_truncated"])
        self.assertEqual(result["original_output_chars"], 10)
        self.assertTrue(result["output"].endswith("7890"))

    def test_launchd_filter_only_keeps_nonzero_status(self):
        result = macos._failed_launchd_services({
            "available": True,
            "returncode": 0,
            "output": "PID Status Label\n100 0 ok.service\n- 78 failed.service\n",
            "stderr": "",
            "command": ["launchctl", "list"],
        })
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(result["inspected_count"], 2)
        self.assertIn("failed.service", result["output"])
        self.assertNotIn("ok.service", result["output"])

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
        log_call = next(call for call in run.call_args_list if call.args[0][0] == "log")
        self.assertEqual(log_call.kwargs["max_output_chars"], 200_000)


if __name__ == "__main__":
    unittest.main()
