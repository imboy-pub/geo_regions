"""A production milestone cannot become green by removing its package."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tool"))
from check_readiness import check
from geo_data import DataError, write_json


class ReadinessTests(unittest.TestCase):
    def test_declared_package_missing_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "config/readiness.json",
                       {"productionSdkExpected": True, "expectedProductionGateRefusal": True})
            with self.assertRaisesRegex(DataError, "root pubspec.yaml is missing"):
                check(root)

    def test_present_package_without_tests_fails_even_before_milestone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "config/readiness.json",
                       {"productionSdkExpected": False, "expectedProductionGateRefusal": True})
            (root / "pubspec.yaml").write_text("name: geo_regions\n")
            (root / "lib").mkdir()
            (root / "lib/geo_regions.dart").write_text("library;\n")
            with self.assertRaisesRegex(DataError, "tests are missing"):
                check(root)

    def test_production_gate_switch_must_be_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "config/readiness.json", {"productionSdkExpected": False})
            with self.assertRaisesRegex(DataError, "expectedProductionGateRefusal must be an explicit boolean"):
                check(root)

    def test_research_seed_must_be_refused_by_production_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "config/readiness.json",
                       {"productionSdkExpected": False, "expectedProductionGateRefusal": True})
            report = check(root)  # empty fixture dataset is refused → expected refusal holds
            self.assertTrue(report["productionGateRefused"])

    def test_declared_pass_must_not_silently_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "config/readiness.json",
                       {"productionSdkExpected": False, "expectedProductionGateRefusal": False})
            with self.assertRaisesRegex(DataError, "production gate refused the data"):
                check(root)


if __name__ == "__main__":
    unittest.main()
