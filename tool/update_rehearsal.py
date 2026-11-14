#!/usr/bin/env python3
"""Rehearse the pinned-source update contract (docs/UPDATE_RUNBOOK.md).

--selftest   build synthetic old/new data roots in temp dirs and prove the
             contract chain (check → check → stability) plus that an
             undeclared deletion is blocked. Repository data is untouched;
             fixtures are synthetic test identifiers only.

--old-root A --new-root B
             run the same chain against two real data roots (each must carry
             audit/ sidecars, i.e. a CLDR-sample-style dataset). The stability
             report is written to build/reports/update-rehearsal.json inside
             the new root unless --report is given.

Exit codes: 0 = contract holds (no breaking changes or all reviewed),
1 = blocked (breaking changes without migration evidence / check failure).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo_data as geo  # noqa: E402
import semantic_audit as audit  # noqa: E402

LOCALES = ("en", "zh-Hans", "zh-Hant")


def _write(root, path, value):
    geo.write_json(root / path, value)


def _refresh(root):
    """Recompute revisions and manifest exactly like the contract expects."""
    catalog = geo.load_json(root / "data/countries.json")
    catalog["revision"] = geo.revision("c", catalog["countries"])
    _write(root, "data/countries.json", catalog)
    structure = geo.load_json(root / "data/regions/JP.json")
    structure["revision"] = geo.revision("s", structure["nodes"])
    _write(root, "data/regions/JP.json", structure)
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
    lock = geo.load_json(root / "sources/source-lock.json")
    for entry in lock["sources"]:
        path = root / entry["localPath"]
        entry.update(sha256=geo.sha256(path), sizeBytes=path.stat().st_size)
    _write(root, "sources/source-lock.json", lock)
    _write(root, "data/manifest.json", geo.manifest_value(root / "data"))


def build_fixture(root: Path) -> None:
    """Synthetic minimal dataset in the audit-sample shape (test identifiers only)."""
    (root / "data/i18n/en").mkdir(parents=True)
    containment = {"JP": {"_contains": ["jp01", "jp02"]},
                   "jp01": {"_contains": ["jp02"]}}
    _write(root, audit.CONTAINMENT, {"supplemental": {"subdivisionContainment": containment}})
    _write(root, "sources/source-lock.json", {"sources": [{
        "localPath": audit.CONTAINMENT, "commit": "b" * 40, "license": "Unicode-3.0",
        "repository": "https://github.com/unicode-org/cldr-json",
        "testOnly": "Synthetic rehearsal fixture; not fetched from the stated repository"}]})
    _write(root, "config/data_policy.json", {"locales": list(LOCALES),
        "localeAliases": {"zh-CN": "zh-Hans", "zh-HK": "zh-Hant"},
        "requiredCountries": ["JP"], "requiredCatalogLocales": list(LOCALES),
        "requireEveryCountryLocalePack": True})
    common = {"protocolVersion": "1.0", "datasetId": "rehearsal-selftest",
              "sourceRefs": [audit.CONTAINMENT]}
    _write(root, "data/countries.json", dict(common, countries=[
        {"code": "JP", "name": "Rehearsal country", "rootId": "cc:JP"}]))
    nodes = [
        {"id": "cc:JP", "parentId": None, "kind": "country", "code": "JP",
         "name": "Rehearsal country", "childrenStatus": "partial"},
        {"id": "iso3166-2:JP-01", "parentId": "cc:JP", "kind": "subdivision",
         "code": "JP-01", "name": "Rehearsal alpha", "childrenStatus": "unknown"},
        {"id": "iso3166-2:JP-02", "parentId": "iso3166-2:JP-01", "kind": "subdivision",
         "code": "JP-02", "name": "Rehearsal beta", "childrenStatus": "unknown"},
    ]
    for node in nodes:
        node.update(nameLocale="en", nameQuality="approved-in-source")
    _write(root, "data/regions/JP.json", dict(common, countryCode="JP", nodes=nodes))
    metadata, registry = [], []
    for depth, node in enumerate(nodes):
        key = "JP" if depth == 0 else "jp" + node["code"].split("-")[1]
        metadata.append({**{field: node[field] for field in ("id", "parentId", "kind", "code")},
                         "countryCode": "JP", "treeDepth": depth, "sourceNamespace": "cldr",
                         "sourceKey": key, "sourceRefs": [audit.CONTAINMENT],
                         "administrativeLevel": None, "administrativeType": None,
                         "levelStatus": "source-hierarchy-only"})
        registry.append({"id": node["id"], "countryCode": "JP", "sourceNamespace": "cldr",
                         "sourceKey": key, "status": "active", "firstSeenRelease": "rehearsal-v1"})
    _write(root, audit.METADATA, {"schemaVersion": 1, "datasetId": common["datasetId"], "nodes": metadata})
    _write(root, audit.REGISTRY, {"schemaVersion": 1, "datasetId": common["datasetId"], "entries": registry})
    for locale in LOCALES:
        names = {n["id"]: n["name"] for n in nodes}
        quality = {node_id: "approved-in-source" for node_id in names}
        _write(root, f"data/i18n/{locale}/JP.json", dict(common, countryCode="JP", locale=locale,
               names=names, coverage={"translationQualityById": quality}))
        _write(root, f"data/catalog_i18n/{locale}.json", dict(common, locale=locale,
               names={"JP": "Rehearsal country"},
               coverage={"translationQualityById": {"JP": "approved-in-source"}}))
    _refresh(root)


def undeclared_delete(root: Path) -> None:
    """Scenario A: node removed everywhere with no retirement entry — must block."""
    structure = geo.load_json(root / "data/regions/JP.json")
    structure["nodes"] = [n for n in structure["nodes"] if n["id"] != "iso3166-2:JP-02"]
    _write(root, "data/regions/JP.json", structure)
    meta = geo.load_json(root / audit.METADATA)
    meta["nodes"] = [n for n in meta["nodes"] if n["id"] != "iso3166-2:JP-02"]
    _write(root, audit.METADATA, meta)
    for path in (root / "data/i18n").glob("*/JP.json"):
        pack = geo.load_json(path)
        pack["names"].pop("iso3166-2:JP-02", None)
        pack["coverage"]["translationQualityById"].pop("iso3166-2:JP-02", None)
        geo.write_json(path, pack)
    _refresh(root)


def declared_retire(root: Path, old_root: Path) -> None:
    """Scenario B: retirement entry + per-change migration review evidence."""
    structure = geo.load_json(root / "data/regions/JP.json")
    structure["nodes"] = [n for n in structure["nodes"] if n["id"] != "iso3166-2:JP-02"]
    _write(root, "data/regions/JP.json", structure)
    for sidecar_path in (audit.METADATA,):
        doc = geo.load_json(root / sidecar_path)
        doc["nodes"] = [n for n in doc["nodes"] if n["id"] != "iso3166-2:JP-02"]
        _write(root, sidecar_path, doc)
    registry = geo.load_json(root / audit.REGISTRY)
    for entry in registry["entries"]:
        if entry["id"] == "iso3166-2:JP-02":
            entry["status"] = "retired"
    _write(root, audit.REGISTRY, registry)
    for path in (root / "data/i18n").glob("*/JP.json"):
        pack = geo.load_json(path)
        pack["names"].pop("iso3166-2:JP-02", None)
        pack["coverage"]["translationQualityById"].pop("iso3166-2:JP-02", None)
        geo.write_json(path, pack)
    _refresh(root)
    # Synthetic review evidence; the rehearsal never claims human review.
    evidence = root / "audit/rehearsal-review-note.txt"
    evidence.write_text(
        "Synthetic retirement review evidence for the rehearsal selftest only; "
        "humanReviewVerified=false. Real updates must attach real review records.\n",
        encoding="utf-8")
    _write(root, "audit/migrations.json", {
        "schemaVersion": 1, "datasetId": "rehearsal-selftest",
        "fromSnapshot": audit.snapshot_id(old_root),
        "toSnapshot": audit.snapshot_id(root),
        "events": [{"id": "iso3166-2:JP-02", "change": "removed",
                    "from": "active", "to": "retired",
                    "review": {"status": "reviewed", "reviewer": "rehearsal-selftest",
                               "reviewedAt": "2026-11-14",
                               "evidence": "audit/rehearsal-review-note.txt",
                               "evidenceSha256": geo.sha256(evidence)}}]})


def run_contract(old: Path, new: Path, report_path: Path) -> int:
    print(f"[1/3] semantic_audit check (old root: {old})")
    audit.check(old)
    print(f"[2/3] semantic_audit check (new root: {new})")
    try:
        audit.check(new)
    except geo.DataError as exc:
        print("BLOCKED at check:", exc)
        return 1
    print("[3/3] semantic_audit stability (old → new)")
    try:
        report = audit.stability(old, new)
    except geo.DataError as exc:
        print("BLOCKED at stability:", exc)
        return 1
    report_path.parent.mkdir(parents=True, exist_ok=True)
    geo.write_json(report_path, report)
    print(json.dumps({key: report[key] for key in (
        "status", "fromSnapshot", "toSnapshot", "added", "removed",
        "breakingChanges", "reviewedMigrationRecords")}, ensure_ascii=False, indent=2))
    if len(report["breakingChanges"]) > report["reviewedMigrationRecords"]:
        print("BLOCKED: breaking changes without per-change migration evidence")
        return 1
    print("OK: contract holds; report written to", report_path)
    return 0


def selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="geo-update-rehearsal.") as space:
        old = Path(space) / "old-root"
        build_fixture(old)
        blocked = Path(space) / "blocked-root"
        released = Path(space) / "released-root"
        shutil.copytree(old, blocked)
        shutil.copytree(old, released)
        undeclared_delete(blocked)
        declared_retire(released, old)
        print("=== scenario A: undeclared deletion (must block) ===")
        if run_contract(old, blocked, blocked / "build/reports/update-rehearsal.json") != 1:
            print("FAIL: an undeclared deletion was not blocked by the contract")
            return 1
        print("OK: undeclared deletion blocked (exit 1)\n")
        print("=== scenario B: declared retirement with evidence (must pass) ===")
        code = run_contract(old, released, released / "build/reports/update-rehearsal.json")
        if code != 0:
            print("FAIL: a fully evidenced retirement did not pass the contract")
            return 1
        print("OK: check → check → stability chain works end to end")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--old-root", type=Path)
    parser.add_argument("--new-root", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if not (args.old_root and args.new_root):
        parser.error("either --selftest or both --old-root and --new-root are required")
    report = args.report or (args.new_root / "build/reports/update-rehearsal.json")
    return run_contract(args.old_root.resolve(), args.new_root.resolve(), report)


if __name__ == "__main__":
    sys.exit(main())
