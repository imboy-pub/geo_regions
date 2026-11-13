"""Meaningful failure vectors; all geography/source snapshots here are synthetic.

These fixtures exercise the recorded-source contract. They are not administrative
facts and must never be imported into distributable geography data.
"""

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tool"))
import geo_data as geo
import semantic_audit as audit


def write(root, path, value):
    geo.write_json(root / path, value)


def read(root, path):
    return geo.load_json(root / path)


def fixture(root):
    """Use real-looking codes only as explicitly synthetic test identifiers."""
    root.mkdir()
    write(root, audit.CONTAINMENT, {"testOnly": "SYNTHETIC; NOT REAL ADMINISTRATIVE DATA", "supplemental": {
        "subdivisionContainment": {"JP": {"_contains": ["jp01"]}, "jp01": {"_contains": ["jp02"]}}}})
    write(root, "sources/source-lock.json", {"sources": [{"localPath": audit.CONTAINMENT,
          "commit": "a" * 40, "license": "Unicode-3.0", "repository": "https://github.com/unicode-org/cldr-json",
          "testOnly": "Synthetic local fixture; not fetched from the stated repository"}]})
    locales = ["en", "zh-Hans", "zh-Hant", "ar"]
    write(root, "config/data_policy.json", {"locales": locales,
          "localeAliases": {"zh-CN": "zh-Hans", "zh-HK": "zh-Hant", "en-US": "en", "ar-SA": "ar"},
          "requiredCountries": ["JP"], "requiredCatalogLocales": locales, "requireEveryCountryLocalePack": True})
    common = {"protocolVersion": "1.0", "datasetId": "synthetic-audit-test", "sourceRefs": [audit.CONTAINMENT]}
    write(root, "data/countries.json", dict(common, countries=[{"code": "JP", "name": "Test country", "rootId": "cc:JP"}]))
    nodes = [{"id": "cc:JP", "parentId": None, "kind": "country", "code": "JP", "name": "Test country", "childrenStatus": "partial"},
             {"id": "iso3166-2:JP-01", "parentId": "cc:JP", "kind": "subdivision", "code": "JP-01", "name": "Test alpha", "childrenStatus": "partial"},
             {"id": "iso3166-2:JP-02", "parentId": "iso3166-2:JP-01", "kind": "subdivision", "code": "JP-02", "name": "Test beta", "childrenStatus": "unknown"}]
    for node in nodes:
        node.update(nameLocale="en", nameQuality="approved-in-source")
    write(root, "data/regions/JP.json", dict(common, countryCode="JP", nodes=nodes))
    for locale in locales:
        names = {node["id"]: node["name"] for node in nodes} if locale in ("en", "zh-Hans") else {"cc:JP": "Test country"}
        quality = {node_id: "approved-in-source" for node_id in names}
        write(root, f"data/i18n/{locale}/JP.json", dict(common, countryCode="JP", locale=locale,
              names=names, coverage={"translationQualityById": quality}))
        write(root, f"data/catalog_i18n/{locale}.json", dict(common, locale=locale, names={"JP": "Test country"},
              coverage={"translationQualityById": {"JP": "approved-in-source"}}))
    metadata = []
    entries = []
    for depth, node in enumerate(nodes):
        key = "JP" if depth == 0 else "jp" + node["code"].split("-")[1]
        metadata.append({**{field: node[field] for field in ("id", "parentId", "kind", "code")},
                         "countryCode": "JP", "treeDepth": depth, "sourceNamespace": "cldr", "sourceKey": key,
                         "sourceRefs": [audit.CONTAINMENT], "administrativeLevel": None,
                         "administrativeType": None, "levelStatus": "source-hierarchy-only"})
        entries.append({"id": node["id"], "countryCode": "JP", "sourceNamespace": "cldr", "sourceKey": key,
                        "status": "active", "firstSeenRelease": "synthetic-v1"})
    write(root, audit.METADATA, {"schemaVersion": 1, "datasetId": common["datasetId"], "nodes": metadata})
    write(root, audit.REGISTRY, {"schemaVersion": 1, "datasetId": common["datasetId"], "entries": entries})
    refresh(root)


def refresh(root):
    catalog = read(root, "data/countries.json")
    catalog["revision"] = geo.revision("c", catalog["countries"])
    write(root, "data/countries.json", catalog)
    structure = read(root, "data/regions/JP.json")
    structure["revision"] = geo.revision("s", structure["nodes"])
    write(root, "data/regions/JP.json", structure)
    for path in (root / "data/i18n").glob("*/JP.json"):
        pack = geo.load_json(path)
        pack["compatibleStructureRevision"] = structure["revision"]
        pack["revision"] = geo.locale_revision(pack["names"], pack["coverage"]["translationQualityById"])
        geo.write_json(path, pack)
    for path in (root / "data/catalog_i18n").glob("*.json"):
        pack = geo.load_json(path)
        pack["compatibleCatalogRevision"] = catalog["revision"]
        pack["revision"] = geo.locale_revision(pack["names"], pack["coverage"]["translationQualityById"])
        geo.write_json(path, pack)
    lock = read(root, "sources/source-lock.json")
    for entry in lock["sources"]:
        path = root / entry["localPath"]
        entry.update(sha256=geo.sha256(path), sizeBytes=path.stat().st_size)
    write(root, "sources/source-lock.json", lock)
    write(root, "data/manifest.json", geo.manifest_value(root / "data"))


def remove_beta(root):
    structure = read(root, "data/regions/JP.json")
    structure["nodes"] = [node for node in structure["nodes"] if node["id"] != "iso3166-2:JP-02"]
    write(root, "data/regions/JP.json", structure)
    metadata = read(root, audit.METADATA)
    metadata["nodes"] = [node for node in metadata["nodes"] if node["id"] != "iso3166-2:JP-02"]
    write(root, audit.METADATA, metadata)
    registry = read(root, audit.REGISTRY)
    registry["entries"][-1]["status"] = "retired"
    write(root, audit.REGISTRY, registry)
    for path in (root / "data/i18n").glob("*/JP.json"):
        pack = geo.load_json(path)
        pack["names"].pop("iso3166-2:JP-02", None)
        pack["coverage"]["translationQualityById"].pop("iso3166-2:JP-02", None)
        geo.write_json(path, pack)
    refresh(root)


class SemanticAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "old"
        self.new = Path(self.temp.name) / "new"
        fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def copy(self):
        shutil.copytree(self.root, self.new)

    def mutate_node(self, **values):
        structure = read(self.root, "data/regions/JP.json")
        structure["nodes"][1].update(values)
        write(self.root, "data/regions/JP.json", structure)
        refresh(self.root)

    def test_source_hierarchy_and_missing_names_reported_separately(self):
        report = audit.check(self.root)
        self.assertFalse(report["administrativeLevelsVerified"])
        self.assertEqual(report["historicalStability"], "NOT_VERIFIED_BY_SINGLE_SNAPSHOT")
        row = next(row for row in report["coverage"] if row["locale"] == "zh-Hant")
        self.assertEqual((row["sourcePresent"], row["missingSourceNames"], row["fallbackCount"]), (1, 2, 2))

    def test_orphan_is_rejected_by_reused_integrity_checker(self):
        self.mutate_node(parentId="missing")
        with self.assertRaisesRegex(geo.DataError, "missing or cross-country parent"):
            audit.check(self.root)

    def test_stability_does_not_collapse_duplicate_ids(self):
        self.copy()
        structure = read(self.new, "data/regions/JP.json")
        structure["nodes"].append(copy.deepcopy(structure["nodes"][1]))
        write(self.new, "data/regions/JP.json", structure)
        refresh(self.new)
        with self.assertRaisesRegex(geo.DataError, "duplicate ID"):
            audit.stability(self.root, self.new)

    def test_nested_country_kind_is_rejected(self):
        self.mutate_node(kind="country")
        metadata = read(self.root, audit.METADATA)
        metadata["nodes"][1]["kind"] = "country"
        write(self.root, audit.METADATA, metadata)
        with self.assertRaisesRegex(geo.DataError, "non-root kind"):
            audit.check(self.root)

    def test_wrong_depth_is_rejected(self):
        metadata = read(self.root, audit.METADATA)
        metadata["nodes"][2]["treeDepth"] = 1
        write(self.root, audit.METADATA, metadata)
        with self.assertRaisesRegex(geo.DataError, "incorrect treeDepth"):
            audit.check(self.root)

    def test_plausible_parent_absent_from_source_is_rejected(self):
        structure = read(self.root, "data/regions/JP.json")
        structure["nodes"][2]["parentId"] = "cc:JP"
        write(self.root, "data/regions/JP.json", structure)
        metadata = read(self.root, audit.METADATA)
        metadata["nodes"][2].update(parentId="cc:JP", treeDepth=1)
        write(self.root, audit.METADATA, metadata)
        refresh(self.root)
        with self.assertRaisesRegex(geo.DataError, "parent edge absent"):
            audit.check(self.root)

    def test_tree_depth_cannot_be_laundered_as_administrative_level(self):
        metadata = read(self.root, audit.METADATA)
        metadata["nodes"][1]["administrativeLevel"] = 1
        write(self.root, audit.METADATA, metadata)
        with self.assertRaisesRegex(geo.DataError, "legal administrative levels"):
            audit.check(self.root)

    def test_filtered_locale_and_default_name_cannot_bypass_policy(self):
        for path in (self.root / "data/i18n").glob("*/JP.json"):
            pack = geo.load_json(path)
            if "iso3166-2:JP-01" in pack["names"]:
                pack["coverage"]["translationQualityById"]["iso3166-2:JP-01"] = "machine-translated-candidate"
            geo.write_json(path, pack)
        self.mutate_node(nameQuality="provisional")
        result = audit.resolve_name(self.root, "JP", "iso3166-2:JP-01", "zh-Hant")
        self.assertEqual((result["value"], result["quality"], result["resolvedLocale"]), ("iso3166-2:JP-01", "identifier", None))

    def test_traditional_request_does_not_resolve_simplified_resource(self):
        policy, _, _ = audit.name_context(self.root, "JP")
        policy["locales"] = ["zh-Hans", "en"]
        self.assertIsNone(audit.resource_locale("zh-Hant-HK", policy))
        self.assertIsNone(audit.resource_locale("zh", policy))

    def test_explicit_aliases_and_lookup_preserve_script(self):
        policy, _, _ = audit.name_context(self.root, "JP")
        for requested, expected in (("ZH-cn", "zh-Hans"), ("zh-HK", "zh-Hant"),
                                    ("zh-Hant-TW", "zh-Hant"), ("en-AU-u-ca-gregory", "en")):
            self.assertEqual(audit.resource_locale(requested, policy), expected)

    def test_explicit_alias_cannot_bypass_script_boundary(self):
        policy, _, _ = audit.name_context(self.root, "JP")
        policy["localeAliases"]["zh-Hant-HK"] = "zh-Hans"
        write(self.root, "config/data_policy.json", policy)
        with self.assertRaisesRegex(geo.DataError, "alias cannot change or discard an explicit script"):
            audit.check(self.root)
        with self.assertRaisesRegex(geo.DataError, "alias cannot change or discard an explicit script"):
            audit.resolve_name(self.root, "JP", "iso3166-2:JP-01", "zh-Hant-HK")
        for source, target in (("zh-Hans-CN", "zh-Hant"), ("sr-Cyrl-RS", "sr-Latn"), ("zh-Hant", "zh")):
            with self.subTest(source=source, target=target), self.assertRaisesRegex(geo.DataError, "explicit script"):
                audit.resource_locale(source, {"locales": [target], "localeAliases": {source: target}})
        self.assertEqual(audit.resource_locale("zh-CN", policy), "zh-Hans")

    def test_missing_translation_falls_back_without_filling_source_pack(self):
        before = (self.root / "data/i18n/zh-Hant/JP.json").read_bytes()
        result = audit.resolve_name(self.root, "JP", "iso3166-2:JP-01", "zh-Hant")
        self.assertEqual((result["resolvedLocale"], result["reason"], result["isFallback"]), ("en", "host-default", True))
        self.assertEqual(before, (self.root / "data/i18n/zh-Hant/JP.json").read_bytes())

    def test_same_snapshot_is_not_claimed_as_historical_stability(self):
        result = audit.stability(self.root, self.root)
        self.assertEqual(result["historicalStability"], "SAME_SNAPSHOT_ONLY")
        self.assertFalse(result["sourceHistoryCompletenessVerified"])

    def test_policy_change_is_bound_to_snapshot_and_stability_report(self):
        self.copy()
        policy = read(self.new, "config/data_policy.json")
        policy["localeAliases"]["en-GB"] = "en"
        write(self.new, "config/data_policy.json", policy)
        self.assertEqual(geo.sha256(self.root / "data/manifest.json"), geo.sha256(self.new / "data/manifest.json"))
        self.assertNotEqual(audit.snapshot_id(self.root), audit.snapshot_id(self.new))
        result = audit.stability(self.root, self.new)
        self.assertTrue(result["policyChanged"])
        self.assertNotEqual(result["fromSnapshot"], result["toSnapshot"])

    def test_rename_and_array_order_keep_entity_ids(self):
        self.copy()
        structure = read(self.new, "data/regions/JP.json")
        structure["nodes"][1]["name"] = "Renamed test alpha"
        structure["nodes"].reverse()
        write(self.new, "data/regions/JP.json", structure)
        refresh(self.new)
        result = audit.stability(self.root, self.new)
        self.assertEqual(result["added"], [])
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["renamed"][0]["id"], "iso3166-2:JP-01")

    def test_code_change_cannot_pass_as_no_change(self):
        self.mutate_node(code="JP-99")
        metadata = read(self.root, audit.METADATA)
        metadata["nodes"][1]["code"] = "JP-99"
        write(self.root, audit.METADATA, metadata)
        with self.assertRaisesRegex(geo.DataError, "code/source key mismatch"):
            audit.check(self.root)

    def test_retired_id_cannot_be_resurrected(self):
        self.copy()
        remove_beta(self.root)
        with self.assertRaisesRegex(geo.DataError, "retired ID reused"):
            audit.stability(self.root, self.new)

    def test_deleted_identity_requires_preserved_registry_history(self):
        self.copy()
        remove_beta(self.new)
        registry = read(self.new, audit.REGISTRY)
        registry["entries"].pop()
        write(self.new, audit.REGISTRY, registry)
        with self.assertRaisesRegex(geo.DataError, "registry history cannot be removed"):
            audit.stability(self.root, self.new)

    def test_retirement_needs_exact_reviewed_migration_and_hash(self):
        self.copy()
        remove_beta(self.new)
        with self.assertRaisesRegex(geo.DataError, "missing resource"):
            audit.stability(self.root, self.new)
        evidence = self.new / "audit/removal-review.txt"
        evidence.write_text("SYNTHETIC TEST REVIEW RECORD. Not real human approval.\n")
        event = {"id": "iso3166-2:JP-02", "change": "removed", "from": "active", "to": "retired",
                 "review": {"status": "reviewed", "reviewer": "synthetic-test", "reviewedAt": "2026-11-13",
                            "evidence": "audit/removal-review.txt", "evidenceSha256": geo.sha256(evidence)}}
        document = {"schemaVersion": 1, "datasetId": "synthetic-audit-test", "fromSnapshot": audit.snapshot_id(self.root),
                    "toSnapshot": audit.snapshot_id(self.new), "events": [event]}
        write(self.new, "audit/migrations.json", document)
        self.assertEqual(audit.stability(self.root, self.new)["reviewedMigrationRecords"], 1)
        evidence.write_text("Changed evidence\n")
        with self.assertRaisesRegex(geo.DataError, "evidence is empty or hash differs"):
            audit.stability(self.root, self.new)

    def test_duplicate_migration_records_are_not_double_counted(self):
        self.copy()
        remove_beta(self.new)
        evidence = self.new / "audit/review.txt"
        evidence.write_text("Synthetic\n")
        event = {"id": "iso3166-2:JP-02", "change": "removed", "from": "active", "to": "retired",
                 "review": {"status": "reviewed", "reviewer": "test", "reviewedAt": "2026-11-13",
                            "evidence": "audit/review.txt", "evidenceSha256": geo.sha256(evidence)}}
        write(self.new, "audit/migrations.json", {"schemaVersion": 1, "datasetId": "synthetic-audit-test",
              "fromSnapshot": audit.snapshot_id(self.root), "toSnapshot": audit.snapshot_id(self.new), "events": [event, event]})
        with self.assertRaisesRegex(geo.DataError, "duplicate migration event"):
            audit.stability(self.root, self.new)

    def test_same_id_cannot_be_rebound_to_another_source_entity(self):
        self.copy()
        structure = read(self.new, "data/regions/JP.json")
        structure["nodes"][2]["code"] = "JP-03"
        write(self.new, "data/regions/JP.json", structure)
        metadata = read(self.new, audit.METADATA)
        metadata["nodes"][2].update(code="JP-03", sourceKey="jp03")
        write(self.new, audit.METADATA, metadata)
        registry = read(self.new, audit.REGISTRY)
        registry["entries"][2]["sourceKey"] = "jp03"
        write(self.new, audit.REGISTRY, registry)
        raw = read(self.new, audit.CONTAINMENT)
        raw["supplemental"]["subdivisionContainment"]["jp01"]["_contains"] = ["jp03"]
        write(self.new, audit.CONTAINMENT, raw)
        refresh(self.new)
        with self.assertRaisesRegex(geo.DataError, "immutable registry identity changed"):
            audit.stability(self.root, self.new)

    def test_same_source_key_cannot_identify_two_active_entities(self):
        registry = read(self.root, audit.REGISTRY)
        registry["entries"][2]["sourceKey"] = "jp01"
        write(self.root, audit.REGISTRY, registry)
        with self.assertRaisesRegex(geo.DataError, "source key assigned to multiple active IDs"):
            audit.check(self.root)


if __name__ == "__main__":
    unittest.main()
