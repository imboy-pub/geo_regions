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
            write_json(root / "config/readiness.json", {"productionSdkExpected": True})
            with self.assertRaisesRegex(DataError, "root pubspec.yaml is missing"):
                check(root)

    def test_present_package_without_tests_fails_even_before_milestone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "config/readiness.json", {"productionSdkExpected": False})
            (root / "pubspec.yaml").write_text("name: geo_regions\n")
            (root / "lib").mkdir()
            (root / "lib/geo_regions.dart").write_text("library;\n")
            with self.assertRaisesRegex(DataError, "tests are missing"):
                check(root)


if __name__ == "__main__":
    unittest.main()
