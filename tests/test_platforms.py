import unittest
from supportforge.platforms import current_platform, collect_platform_snapshot
from unittest.mock import patch

from supportforge.postgres_v2 import collect_postgres_snapshot, find_postgres_command

class PlatformTests(unittest.TestCase):
    def test_platform_name(self):
        self.assertIn(current_platform(), {"linux","windows","macos","unknown"})

    def test_snapshot_is_mapping(self):
        self.assertIsInstance(collect_platform_snapshot(), dict)

    def test_postgres_bad_port(self):
        with self.assertRaises(ValueError):
            collect_postgres_snapshot(port=70000)

    @patch("supportforge.postgres_v2.shutil.which", return_value="/custom/bin/psql")
    def test_postgres_command_uses_path_when_available(self, _which):
        self.assertEqual(find_postgres_command("psql"), "/custom/bin/psql")

if __name__ == "__main__":
    unittest.main()
