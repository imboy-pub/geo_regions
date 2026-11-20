import shutil
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

import test_geo_data


REPOSITORY = Path(__file__).resolve().parents[1]
GEO = test_geo_data.geo


class PackageReleaseTests(unittest.TestCase):
    def setUp(self):
        fixture = test_geo_data.DataToolsTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        self.fixture = fixture
        self.root = fixture.root
        shutil.copytree(REPOSITORY / "schemas", self.root / "schemas")

    def pack(self, *options, output="dist"):
        out = self.root.parent / output
        result = subprocess.run(
            [
                sys.executable, str(REPOSITORY / "tool/package_release.py"),
                "--root", str(self.root), "--tag", "data-v2026.11.20",
                "--out", str(out), *options,
            ],
            text=True,
            capture_output=True,
        )
        return result, out / "geo_regions-data-v2026.11.20.zip"

    def test_preview_is_reproducible_and_cannot_overwrite(self):
        first, archive = self.pack()
        self.assertEqual(first.returncode, 0, first.stderr)
        second, copy = self.pack(output="dist-copy")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(archive.read_bytes(), copy.read_bytes())
        with zipfile.ZipFile(archive) as bundle:
            self.assertIn(b"research seed", bundle.read("READ_FIRST.md"))
            self.assertEqual(bundle.read("data/manifest.json"), (self.root / "data/manifest.json").read_bytes())
        refused, _ = self.pack()
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("refusing to overwrite", refused.stderr)

    def test_production_packages_exact_frozen_files_and_rejects_tampering(self):
        self.fixture.make_production_fixture()
        self.fixture.manifest()
        profile_path = self.root / "config/production-profile.json"
        profile = {
            "profileId": "synthetic-profile", "datasetId": "test",
            "countries": ["CN", "JP"], "locales": ["en"], "catalogLocales": ["en"],
        }
        GEO.write_json(profile_path, profile)
        (self.root / "sources/SOURCES_NOTICE.md").write_text("Synthetic fixture provenance only.\n")
        manifest = {
            "profileId": "synthetic-profile",
            "inputTree": "a" * 40,
            "catalogReviewSha256": "b" * 64,
            "files": {
                item.relative_to(self.root).as_posix(): GEO.sha256(item)
                for item in self.root.rglob("*") if item.is_file()
            },
        }
        GEO.write_json(self.root / "BUILD_INPUTS.json", manifest)
        inside, invalid = self.pack("--production", output="repo/dist")
        self.assertNotEqual(inside.returncode, 0)
        self.assertIn("outside the input root", inside.stderr)
        self.assertFalse(invalid.parent.exists())
        result, archive = self.pack("--production")
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(archive) as bundle:
            self.assertCountEqual(bundle.namelist(), manifest["files"].keys() | {
                "BUILD_INPUTS.json", "BUILD.json", "READ_FIRST.md",
            })
            self.assertIn(b"production-profile", bundle.read("READ_FIRST.md"))
        GEO.write_json(profile_path, {**profile, "countries": ["CN"]})
        manifest["files"]["config/production-profile.json"] = GEO.sha256(profile_path)
        GEO.write_json(self.root / "BUILD_INPUTS.json", manifest)
        rejected, invalid = self.pack("--production", output="scope-mismatch")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("does not match manifest resources", rejected.stderr)
        self.assertFalse(invalid.exists())
        GEO.write_json(profile_path, profile)
        manifest["files"]["config/production-profile.json"] = GEO.sha256(profile_path)
        GEO.write_json(self.root / "BUILD_INPUTS.json", manifest)
        notice = self.root / "sources/SOURCES_NOTICE.md"
        original = notice.read_bytes()
        notice.write_text("Changed after freezing.\n")
        rejected, invalid = self.pack("--production", output="changed")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("production build input changed", rejected.stderr)
        self.assertFalse(invalid.exists())
        notice.write_bytes(original)
        (self.root / ".foreign").write_text("unlisted")
        rejected, invalid = self.pack("--production", output="invalid")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("does not match root files", rejected.stderr)
        self.assertFalse(invalid.exists())


if __name__ == "__main__":
    unittest.main()
