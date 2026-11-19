"""Offline contract rehearsal for the CN source-decision preparation work.

These tests reuse the existing CLDR-only audit fixture and APIs. The JP envelope
is only required by that fixture; TEST names, opaque IDs and JP-TEST* source keys
are invented. Nothing here is CN/MCA source data, a CN importer, a successor
selection algorithm, a licence clearance, or evidence of human review.

All roots and review records exist only in temporary directories. Existing
rename, retirement and source-key rebinding tests remain in test_semantic_audit;
this module adds cross-snapshot reparenting and saved-selection failure vectors.
"""

import copy
from pathlib import Path
import shutil
import tempfile
import unittest

# Import the helper module, not its TestCase: unittest discovery must not run
# the existing semantic-audit suite a second time through this module.
import test_semantic_audit as fixtures


geo = fixtures.geo
audit = fixtures.audit
DATASET = "synthetic-cn-migration-contract"
ROOT_ID = "cc:JP"
ALPHA = "synthetic:TEST-ALPHA"
BETA = "synthetic:TEST-BETA"
GAMMA = "synthetic:TEST-GAMMA"
STRUCTURE = "data/regions/JP.json"


def build_test_fixture(root):
    """Reuse the fixture, replacing numeric-looking identifiers with TEST keys."""
    fixtures.fixture(root)
    substitutions = {
        "synthetic-audit-test": DATASET,
        "iso3166-2:JP-01": ALPHA,
        "iso3166-2:JP-02": BETA,
        "JP-01": "JP-TESTALPHA",
        "JP-02": "JP-TESTBETA",
        "jp01": "jptestalpha",
        "jp02": "jptestbeta",
        "Test country": "TEST Country",
        "Test alpha": "TEST Alpha",
        "Test beta": "TEST Beta",
    }

    def substitute(value):
        if isinstance(value, str):
            return substitutions.get(value, value)
        if isinstance(value, list):
            return [substitute(item) for item in value]
        if isinstance(value, dict):
            return {substitute(key): substitute(item) for key, item in value.items()}
        return value

    for path in root.rglob("*.json"):
        geo.write_json(path, substitute(geo.load_json(path)))

    # A second invented child makes partial migration coverage observable.
    structure = fixtures.read(root, STRUCTURE)
    beta = next(node for node in structure["nodes"] if node["id"] == BETA)
    structure["nodes"].append({**beta, "id": GAMMA, "code": "JP-TESTGAMMA",
                               "name": "TEST Gamma"})
    fixtures.write(root, STRUCTURE, structure)
    for path, field in ((audit.METADATA, "nodes"), (audit.REGISTRY, "entries")):
        document = fixtures.read(root, path)
        row = copy.deepcopy(next(row for row in document[field] if row["id"] == BETA))
        row.update(id=GAMMA, sourceKey="jptestgamma")
        if "code" in row:
            row["code"] = "JP-TESTGAMMA"
        document[field].append(row)
        fixtures.write(root, path, document)
    raw = fixtures.read(root, audit.CONTAINMENT)
    raw["supplemental"]["subdivisionContainment"]["jptestalpha"]["_contains"].append("jptestgamma")
    fixtures.write(root, audit.CONTAINMENT, raw)
    for path in (root / "data/i18n").glob("*/JP.json"):
        pack = geo.load_json(path)
        if BETA in pack["names"]:
            pack["names"][GAMMA] = "TEST Gamma"
            pack["coverage"]["translationQualityById"][GAMMA] = pack["coverage"]["translationQualityById"][BETA]
            geo.write_json(path, pack)
    fixtures.refresh(root)


class CNPreparationRehearsalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="geo-cn-synthetic-rehearsal.")
        self.addCleanup(temporary.cleanup)
        self.space = Path(temporary.name)
        self.old = self.space / "old"
        self.new = self.space / "new"
        build_test_fixture(self.old)
        shutil.copytree(self.old, self.new)

    def reparent(self, *node_ids):
        """Move named TEST children to the root with matching synthetic source edges."""
        structure = fixtures.read(self.new, STRUCTURE)
        metadata = fixtures.read(self.new, audit.METADATA)
        raw = fixtures.read(self.new, audit.CONTAINMENT)
        containment = raw["supplemental"]["subdivisionContainment"]
        for node in structure["nodes"]:
            if node["id"] in node_ids:
                node["parentId"] = ROOT_ID
        for row in metadata["nodes"]:
            if row["id"] in node_ids:
                row.update(parentId=ROOT_ID, treeDepth=1)
                containment["jptestalpha"]["_contains"].remove(row["sourceKey"])
                containment["JP"]["_contains"].append(row["sourceKey"])
        fixtures.write(self.new, STRUCTURE, structure)
        fixtures.write(self.new, audit.METADATA, metadata)
        fixtures.write(self.new, audit.CONTAINMENT, raw)
        fixtures.refresh(self.new)

    @staticmethod
    def event(node_id=BETA):
        return {"id": node_id, "change": "reparented", "from": ALPHA, "to": ROOT_ID}

    def record_synthetic_review(self, events):
        evidence = self.new / "audit/TEST-review.txt"
        evidence.write_text(
            "TEST ONLY: invented migration review; not human approval, legal "
            "clearance or real administrative evidence.\n", encoding="utf-8")
        review = {"status": "reviewed", "reviewer": "TEST-SYNTHETIC-NOT-HUMAN",
                  "reviewedAt": "2026-11-19", "evidence": "audit/TEST-review.txt",
                  "evidenceSha256": geo.sha256(evidence)}
        fixtures.write(self.new, "audit/migrations.json", {
            "schemaVersion": 1, "datasetId": DATASET, "testOnly": True,
            "fromSnapshot": audit.snapshot_id(self.old),
            "toSnapshot": audit.snapshot_id(self.new),
            "events": [{**event, "review": review} for event in events],
        })

    def test_reparent_without_per_change_review_is_blocked(self):
        self.reparent(BETA)
        # Both snapshots are independently sound; missing review is the blocker.
        self.assertEqual(audit.check(self.old)["status"], "pass")
        self.assertEqual(audit.check(self.new)["status"], "pass")
        with self.assertRaisesRegex(geo.DataError, "missing resource"):
            audit.stability(self.old, self.new)

    def test_reparent_with_exact_snapshot_bound_review_passes(self):
        self.reparent(BETA)
        self.record_synthetic_review([self.event()])
        report = audit.stability(self.old, self.new)
        self.assertEqual(report["breakingChanges"], [self.event()])
        self.assertEqual(report["reviewedMigrationRecords"], 1)
        self.assertEqual((report["added"], report["removed"], report["renamed"]), ([], [], []))
        self.assertFalse(report["humanReviewVerified"])

    def test_review_with_wrong_target_is_rejected(self):
        self.reparent(BETA)
        self.record_synthetic_review([{**self.event(), "to": ALPHA}])
        with self.assertRaisesRegex(geo.DataError, "migration event does not match an actual change"):
            audit.stability(self.old, self.new)

    def test_one_review_cannot_cover_two_parent_changes(self):
        self.reparent(BETA, GAMMA)
        self.record_synthetic_review([self.event(BETA)])
        with self.assertRaisesRegex(geo.DataError, "unreviewed breaking changes remain"):
            audit.stability(self.old, self.new)

    def test_candidate_targets_cannot_replace_one_exact_event(self):
        self.reparent(BETA)
        # The correct target is first: the existing contract must not silently
        # select it from an ambiguous list. This is not a split/merge resolver.
        self.record_synthetic_review([{**self.event(), "to": [ROOT_ID, ALPHA]}])
        with self.assertRaisesRegex(geo.DataError, "migration event does not match an actual change"):
            audit.stability(self.old, self.new)

    def test_updating_revision_alone_cannot_repair_a_saved_old_parent_path(self):
        selection_path = self.space / "TEST-selection.json"
        selection = {
            "protocolVersion": "1.0", "datasetId": DATASET, "countryCode": "JP",
            "dataRevision": fixtures.read(self.old, STRUCTURE)["revision"],
            "pathIds": [ROOT_ID, ALPHA, BETA],
        }
        geo.write_json(selection_path, selection)
        self.assertEqual(geo.validate_selection(self.old, selection_path)["status"], "valid-identity-path")
        self.reparent(BETA)
        self.record_synthetic_review([self.event()])
        self.assertEqual(audit.stability(self.old, self.new)["status"], "pass")

        selection["dataRevision"] = fixtures.read(self.new, STRUCTURE)["revision"]
        geo.write_json(selection_path, selection)
        before = selection_path.read_bytes()
        with self.assertRaisesRegex(geo.DataError, "missing or incorrect parent edge"):
            geo.validate_selection(self.new, selection_path)
        self.assertEqual(selection_path.read_bytes(), before)

        # Explicitly reconstruct the evidenced path; no candidate is guessed.
        selection["pathIds"] = [ROOT_ID, BETA]
        geo.write_json(selection_path, selection)
        self.assertEqual(geo.validate_selection(self.new, selection_path)["status"], "valid-identity-path")


if __name__ == "__main__":
    unittest.main()
