import tempfile
import unittest
import json
import zipfile
from pathlib import Path

from supportforge.bundle import create_bundle
from supportforge.evidence import search_evidence, filter_findings
from supportforge.health_rules import evaluate_health
from supportforge.history import save_history_snapshot, list_history, snapshot_stem
from supportforge.html_report import generate_html_report
from supportforge.gui import (
    combine_snapshots,
    comparison_rows,
    default_export_stem,
    snapshot_export_stem,
)
from supportforge.permissions import get_permissions
from supportforge.provenance import evidence_record, provenance_summary
from supportforge.redaction import redact_payload
from supportforge.workstation import diff_snapshots

class CoreTests(unittest.TestCase):
    def test_health_healthy(self):
        result = evaluate_health({
            "supported": True,
            "services": {"available": True, "returncode": 0, "output": ""},
            "logs": {}, "docker": {"skipped": True},
            "security": {"findings": []},
        })
        self.assertEqual(result["state"], "healthy")

    def test_diff(self):
        d = diff_snapshots({"a": 1}, {"a": 2})
        self.assertEqual(d["change_count"], 1)

    def test_diff_compacts_large_command_output(self):
        result = diff_snapshots({"output": "a" * 2000}, {"output": "b" * 2000})
        change = result["changes"][0]
        self.assertEqual(change["before"]["summary"], "large text output")
        self.assertEqual(change["after"]["characters"], 2000)

    def test_side_by_side_comparison_marks_new_changed_and_removed_rows(self):
        older, newer, changed = comparison_rows(
            {"same": 1, "changed": "before", "removed": True},
            {"same": 1, "changed": "after", "added": True},
        )
        self.assertEqual(older["same"], newer["same"])
        self.assertEqual(changed, {"changed", "removed", "added"})

    def test_evidence_search_and_filter(self):
        self.assertEqual(search_evidence({"system":{"hostname":"node-a"}}, "node-a")[0]["path"],
                         "system.hostname")
        fs=[{"severity":"warning"},{"severity":"info"}]
        self.assertEqual(len(filter_findings(fs, "warning")), 1)

    def test_history_and_html(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            save_history_snapshot({"generated_at_utc":"2026-08-15T00:00:00+00:00"}, d)
            self.assertEqual(len(list_history(d)), 1)
            p=d/"r.html"
            generate_html_report({
                "schema":"x","generated_at_utc":"now","platform":"linux",
                "system":{},"health":{"state":"healthy","counts":{"critical":0,"warning":0,"info":0},
                "findings":[]},"network":{},"storage":{},"docker":{},"security":{},"logs":{}
            }, p)
            self.assertTrue(p.exists())

    def test_permissions_and_provenance(self):
        for name in ("linux","windows","macos"):
            self.assertTrue(get_permissions(name))
        rec=evidence_record("system", {}, category="system")
        self.assertEqual(provenance_summary([rec])["record_count"], 1)
        self.assertNotIn("data", rec)
        self.assertEqual(rec["data_summary"]["type"], "dict")
        self.assertEqual(len(rec["data_summary"]["sha256"]), 64)

    def test_strict_redaction_removes_home_paths_and_command_users(self):
        safe = redact_payload({
            "user": "d",
            "output": "opened /Users/d/private/report.txt",
            "command": ["psql", "-U", "d", "--file", "/Users/d/query.sql"],
        }, "strict")
        encoded = json.dumps(safe)
        self.assertNotIn("/Users/d", encoded)
        self.assertNotIn('"user": "d"', encoded)
        self.assertNotIn('"-U", "d"', encoded)
        self.assertIn("<user:", encoded)

    def test_service_output_with_zero_failed_count_is_healthy(self):
        result = evaluate_health({
            "supported": True,
            "services": {
                "available": True,
                "returncode": 0,
                "output": "ordinary service listing",
                "failed_count": 0,
            },
            "logs": {}, "docker": {"skipped": True},
            "security": {"findings": []},
        })
        self.assertEqual(result["state"], "healthy")

    def test_postgres_snapshot_is_included_in_exports(self):
        workstation = {"schema": "supportforge.workstation.snapshot.v1"}
        postgres = {
            "schema": "supportforge.postgres.snapshot.v1",
            "target": {"host": "localhost", "port": 5432, "database": "d"},
        }
        combined = combine_snapshots(workstation, postgres)
        self.assertEqual(combined["postgresql"], postgres)
        self.assertNotIn("postgresql", workstation)

        postgres["target"]["database"] = "changed"
        self.assertEqual(combined["postgresql"]["target"]["database"], "d")

    def test_bundle_contains_json_html_and_private_source_name(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "incident"
            root.mkdir()
            (root / "supportforge-workstation-snapshot.json").write_text("{}")
            (root / "supportforge-incident-report.html").write_text("<html></html>")
            target = Path(td) / "incident.zip"
            result = create_bundle(root, target)
            self.assertEqual(result["manifest"]["source"], "incident")
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"manifest.json", "supportforge-workstation-snapshot.json",
                     "supportforge-incident-report.html"},
                )
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["source"], "incident")

    def test_default_export_stem_uses_timestamp(self):
        stem = default_export_stem("supportforge-incident")
        self.assertRegex(stem, r"^supportforge-incident-\d{8}-\d{6}$")

    def test_snapshot_export_stem_is_stable_for_same_scan(self):
        snapshot = {"generated_at_utc": "2026-08-15T12:22:37+00:00"}
        first = snapshot_export_stem(snapshot)
        second = snapshot_export_stem(snapshot)
        self.assertEqual(first, second)
        self.assertEqual(first, snapshot_stem(snapshot))
        with tempfile.TemporaryDirectory() as td:
            history_path = save_history_snapshot(snapshot, Path(td))
            self.assertEqual(history_path.stem, first)


if __name__ == "__main__":
    unittest.main()
