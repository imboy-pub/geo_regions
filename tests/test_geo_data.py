"""Boundary and integrity checks for the reusable tooling, not UI snapshots."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "tool/geo_data.py"
spec = importlib.util.spec_from_file_location("geo_data", MODULE)
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)


class DataToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        # macOS puts TMPDIR under /var, which is a symlink; resolve() gives the
        # guard_output symlink-escape protection the real path it expects.
        self.root = Path(self.temp.name).resolve() / "repo"
        self.root.mkdir()
        self.data = self.root / "data"
        self.countries = [{"code": code, "name": code, "rootId": "cc:" + code} for code in ("CN", "JP")]
        self.catalog = {"protocolVersion": "1.0", "datasetId": "test", "revision": geo.revision("c", self.countries), "countries": self.countries}
        geo.write_json(self.data / "countries.json", self.catalog)
        for code in ("CN", "JP"):
            nodes = [{"id": "cc:" + code, "parentId": None, "name": code, "kind": "country", "childrenStatus": "complete"}, {"id": code + ":A", "parentId": "cc:" + code, "name": "A", "kind": "subdivision", "childrenStatus": "complete"}, {"id": code + ":B", "parentId": code + ":A", "name": "B", "kind": "subdivision", "childrenStatus": "unknown"}]
            for node in nodes:
                node["nameLocale"] = "en"
                node["nameQuality"] = "approved-in-source"
            obj = {"protocolVersion": "1.0", "datasetId": "test", "countryCode": code, "revision": geo.revision("s", nodes), "nodes": nodes}
            geo.write_json(self.data / "regions" / (code + ".json"), obj)
            names = {"cc:" + code: code, code + ":A": "A"}
            pack = {"protocolVersion": "1.0", "datasetId": "test", "countryCode": code, "locale": "en", "revision": geo.locale_revision(names), "compatibleStructureRevision": obj["revision"], "names": names}
            geo.write_json(self.data / "i18n/en" / (code + ".json"), pack)
        names = {"CN": "China", "JP": "Japan"}
        geo.write_json(self.data / "catalog_i18n/en.json", {"protocolVersion": "1.0", "datasetId": "test", "locale": "en", "revision": geo.locale_revision(names), "compatibleCatalogRevision": self.catalog["revision"], "names": names})
        self.manifest()

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        geo.write_json(self.data / "manifest.json", geo.manifest_value(self.data))

    def change_structure(self, transform):
        path = self.data / "regions/CN.json"
        obj = geo.load_json(path)
        transform(obj)
        obj["revision"] = geo.revision("s", obj["nodes"])
        geo.write_json(path, obj)

    def test_valid_seed_and_missing_translation_count(self):
        result = geo.validate(self.root)
        self.assertEqual(result["nodes"], 6)
        self.assertEqual(result["coverage"][0]["missingNames"], 1)
        self.assertFalse(result["coverage"][0]["projectReviewVerifiedByThisTool"])

    def test_selection_checks_complete_parent_path(self):
        structure = geo.load_json(self.data / "regions/CN.json")
        selection = {"protocolVersion": "1.0", "datasetId": "test", "countryCode": "CN", "dataRevision": structure["revision"], "pathIds": ["cc:CN", "CN:B"]}
        path = self.root / "selection.json"
        geo.write_json(path, selection)
        with self.assertRaisesRegex(geo.DataError, "incorrect parent edge"):
            geo.validate_selection(self.root, path)
        selection["pathIds"] = ["cc:CN", "CN:A", "CN:B"]
        geo.write_json(path, selection)
        self.assertEqual(geo.validate_selection(self.root, path)["status"], "valid-identity-path")

    def test_selection_rejects_stale_revision(self):
        path = self.root / "selection.json"
        geo.write_json(path, {"protocolVersion": "1.0", "datasetId": "test", "countryCode": "CN", "dataRevision": "s-0000000000000000", "pathIds": ["cc:CN"]})
        with self.assertRaisesRegex(geo.DataError, "stale structure revision"):
            geo.validate_selection(self.root, path)

    def test_duplicate_json_keys_rejected(self):
        path = self.root / "duplicate.json"
        path.write_text('{"names":{"x":"one","x":"two"}}')
        with self.assertRaisesRegex(geo.DataError, "duplicate JSON key"):
            geo.load_json(path)

    def test_duplicate_ids_rejected(self):
        self.change_structure(lambda obj: obj["nodes"].append(copy.deepcopy(obj["nodes"][1])))
        with self.assertRaisesRegex(geo.DataError, "duplicate ID"):
            geo.validate(self.root, check_manifest=False)

    def test_cycle_rejected(self):
        self.change_structure(lambda obj: obj["nodes"][1].update(parentId="CN:B"))
        with self.assertRaisesRegex(geo.DataError, "parent cycle"):
            geo.validate(self.root, check_manifest=False)

    def test_cross_country_parent_rejected(self):
        self.change_structure(lambda obj: obj["nodes"][1].update(parentId="cc:JP"))
        with self.assertRaisesRegex(geo.DataError, "cross-country parent"):
            geo.validate(self.root, check_manifest=False)

    def test_stale_locale_structure_revision_rejected(self):
        self.change_structure(lambda obj: obj["nodes"][1].update(name="Changed"))
        with self.assertRaisesRegex(geo.DataError, "incompatible structure"):
            geo.validate(self.root, check_manifest=False)

    def test_dangling_translation_rejected(self):
        path = self.data / "i18n/en/CN.json"
        obj = geo.load_json(path)
        obj["names"]["nonexistent"] = "No"
        obj["revision"] = geo.locale_revision(obj["names"])
        geo.write_json(path, obj)
        with self.assertRaisesRegex(geo.DataError, "dangling translation"):
            geo.validate(self.root, check_manifest=False)

    def test_country_name_key_rejected(self):
        path = self.data / "catalog_i18n/en.json"
        obj = geo.load_json(path)
        obj["names"]["XX"] = "Unknown"
        obj["revision"] = geo.locale_revision(obj["names"])
        geo.write_json(path, obj)
        with self.assertRaisesRegex(geo.DataError, "unknown country name"):
            geo.validate(self.root, check_manifest=False)

    def test_hash_damage_rejected(self):
        path = self.data / "i18n/en/CN.json"
        path.write_text(path.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(geo.DataError, "hash mismatch"):
            geo.validate(self.root)

    def test_manifest_path_traversal_rejected(self):
        manifest = geo.load_json(self.data / "manifest.json")
        manifest["resources"][0]["path"] = "../outside.json"
        with self.assertRaisesRegex(geo.DataError, "path traversal"):
            geo.verify_manifest(self.data, manifest)

    def test_manifest_unsorted_resources_rejected(self):
        manifest = geo.load_json(self.data / "manifest.json")
        manifest["resources"].reverse()
        with self.assertRaisesRegex(geo.DataError, "sorted by path"):
            geo.verify_manifest(self.data, manifest)

    def test_resource_symlink_rejected(self):
        path = self.data / "regions/CN.json"
        external = self.root / "external.json"
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaisesRegex(geo.DataError, "symlink"):
            geo.validate(self.root)

    def test_offline_subset_and_safe_replacement(self):
        config = self.root / "offline.json"
        geo.write_json(config, {"structures": ["CN"], "locales": {"CN": ["en"]}, "catalogLocales": ["en"]})
        out = self.root / "generated/assets"
        report = geo.build_offline(self.root, config, out)
        self.assertEqual(len(report["resources"]), 4)
        self.assertFalse((out / "regions/JP.json").exists())
        self.assertTrue((out / "registry.json").exists())
        fragment = (out / "assets.fragment.yaml").read_text()
        self.assertIn('"generated/assets/regions/CN.json"', fragment)
        self.assertNotIn("regions/JP.json", fragment)
        geo.verify_manifest(out, geo.load_json(out / "manifest.json"))
        with self.assertRaisesRegex(geo.DataError, "existing output"):
            geo.build_offline(self.root, config, out)
        geo.build_offline(self.root, config, out, replace=True)
        with self.assertRaisesRegex(geo.DataError, "unsafe output"):
            geo.build_offline(self.root, config, self.data, replace=True)

    def test_failed_offline_build_preserves_old_assets(self):
        config = self.root / "offline.json"
        geo.write_json(config, {"structures": ["CN"], "locales": {}, "catalogLocales": []})
        out = self.root / "generated/assets"
        geo.build_offline(self.root, config, out)
        before = (out / "regions/CN.json").read_bytes()
        damaged = self.data / "regions/CN.json"
        damaged.write_bytes(damaged.read_bytes() + b" ")
        with self.assertRaises(geo.DataError):
            geo.build_offline(self.root, config, out, replace=True)
        self.assertEqual(before, (out / "regions/CN.json").read_bytes())

    def test_add_language_never_changes_structure(self):
        before = {path.name: path.read_bytes() for path in (self.data / "regions").glob("*.json")}
        out = self.root / "staging/locale-es"
        report = geo.scaffold_locale(self.root, "es", out)
        self.assertTrue(report["structuresUnchanged"])
        self.assertEqual(geo.load_json(out / "i18n/es/CN.json")["names"], {})
        self.assertEqual(before, {path.name: path.read_bytes() for path in (self.data / "regions").glob("*.json")})

    def test_dry_run_has_no_output(self):
        out = self.root / "staging/country-ES"
        geo.scaffold_country(self.root, "ES", out, dry_run=True)
        self.assertFalse(out.exists())

    def test_home_project_output_allowed_but_home_itself_protected(self):
        with patch.object(Path, "home", return_value=self.root.parent):
            self.assertEqual(geo.guard_output(self.root, self.root / "generated/assets"), self.root / "generated/assets")
            with self.assertRaisesRegex(geo.DataError, "unsafe output"):
                geo.guard_output(self.root, self.root.parent)

    def test_removed_id_requires_migration(self):
        old = self.data / "regions/CN.json"
        new = self.root / "next.json"
        obj = geo.load_json(old)
        obj["nodes"].pop()
        geo.write_json(new, obj)
        report = geo.diff_structures(old, new)
        self.assertEqual(report["removed"], ["CN:B"])
        self.assertTrue(report["migrationRequired"])

    def make_production_fixture(self):
        raw = self.root / "sources/raw/test.txt"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("Only synthetic test provenance.\n")
        relative = raw.relative_to(self.root).as_posix()
        geo.write_json(self.root / "sources/source-lock.json", {"sources": [{"localPath": relative, "commit": "a" * 40, "sha256": geo.sha256(raw), "sizeBytes": raw.stat().st_size, "license": "MIT"}]})
        for kind, path in geo.discover(self.data):
            obj = geo.load_json(path)
            obj["coverage"] = {"status": "reviewed"}
            obj["sourceRefs"] = [relative]
            if kind in ("locale", "country-names"):
                quality = {key: "approved-in-source" for key in obj["names"]}
                obj["coverage"]["translationQualityById"] = quality
                obj["revision"] = geo.locale_revision(obj["names"], quality)
            geo.write_json(path, obj)

    def test_percent_encoded_manifest_path_rejected(self):
        for path in ("%2e%2e/outside.json", "regions%2fCN.json", "regions/CN.json\n"):
            with self.assertRaisesRegex(geo.DataError, "encoded or control"):
                geo.safe_resource(self.data, path)

    def test_production_requires_provenance(self):
        with self.assertRaisesRegex(geo.DataError, "requires pinned source-lock"):
            geo.validate(self.root, check_manifest=False, production=True)

    def test_production_requires_explicit_maturity(self):
        self.make_production_fixture()
        path = self.data / "countries.json"
        obj = geo.load_json(path)
        obj.pop("coverage")
        geo.write_json(path, obj)
        with self.assertRaisesRegex(geo.DataError, "explicit reviewed/production maturity"):
            geo.validate(self.root, check_manifest=False, production=True)

    def test_unrecognized_quality_rejected_in_production(self):
        self.make_production_fixture()
        path = self.data / "i18n/en/CN.json"
        obj = geo.load_json(path)
        quality = {node_id: "approved-in-source" for node_id in obj["names"]}
        quality["CN:A"] = "machine-translated-candidate"
        obj["coverage"]["translationQualityById"] = quality
        obj["revision"] = geo.locale_revision(obj["names"], quality)
        geo.write_json(path, obj)
        with self.assertRaisesRegex(geo.DataError, "machine-translated-candidate"):
            geo.validate(self.root, check_manifest=False, production=True)

    def test_default_name_cannot_bypass_quality_filter(self):
        self.make_production_fixture()
        self.change_structure(lambda obj: obj["nodes"][1].update(nameQuality="machine-translated-candidate"))
        with self.assertRaisesRegex(geo.DataError, "unapproved or missing default-name quality"):
            geo.validate(self.root, check_manifest=False, production=True)

    def test_seed_cannot_be_claimed_as_production(self):
        self.make_production_fixture()
        path = self.data / "regions/CN.json"
        obj = geo.load_json(path)
        obj["coverage"] = {"status": "research-seed"}
        geo.write_json(path, obj)
        with self.assertRaisesRegex(geo.DataError, "research-seed or missing status is not production"):
            geo.validate(self.root, check_manifest=False, production=True)


if __name__ == "__main__":
    unittest.main()
