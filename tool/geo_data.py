#!/usr/bin/env python3
"""Deterministic geo_regions development tools; Python 3.10+, standard library.

JSON Schema checks are opt-in and require the development-only jsonschema package.
No command downloads data or mutates upstream source snapshots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import unicodedata

PROTOCOL = "1.0"
MARKER = ".geo_regions-generated"
COUNTRY = re.compile(r"^[A-Z]{2}$")
REVISION = re.compile(r"^[sclm]-[a-f0-9]{16}$")
LANGUAGE_TAG = re.compile(
    r"^(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4}|[A-Za-z]{5,8})"
    r"(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?"
    r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*"
    r"(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*"
    r"(?:-x(?:-[A-Za-z0-9]{1,8})+)?$"
)
PRODUCTION_SOURCE_QUALITIES = {"approved-in-source", "cldr-json-qualified", "source-native", "contributed"}


class DataError(ValueError):
    """Invalid data, an unsafe path, or an unmet publication prerequisite."""


def require(condition, message):
    if not condition:
        raise DataError(message)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def load_json(path):
    path = Path(path)
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(DataError(f"non-JSON number: {value}")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DataError(f"{path}: {exc}") from exc


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def revision(prefix, value):
    return prefix + "-" + hashlib.sha256(canonical(value)).hexdigest()[:16]


def locale_revision(names, quality=None):
    return revision("l", {"names": names, "translationQualityById": quality or {}})


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_resource(root, relative):
    require(isinstance(relative, str) and "\\" not in relative, f"invalid resource path: {relative!r}")
    require("%" not in relative and not any(ord(char) < 32 or ord(char) == 127 for char in relative), f"encoded or control-character resource path: {relative!r}")
    rel = PurePosixPath(relative)
    require(relative != "" and not rel.is_absolute(), f"absolute/empty resource path: {relative!r}")
    require(all(part not in ("", ".", "..") for part in relative.split("/")), f"path traversal: {relative}")
    require(":" not in relative and "?" not in relative and "#" not in relative, f"non-file resource path: {relative}")
    root = Path(root).resolve()
    path = root.joinpath(*rel.parts)
    current = path
    while current != root:
        require(not current.is_symlink(), f"resource symlink forbidden: {current}")
        current = current.parent
    require(path.resolve().is_relative_to(root), f"resource escaped root: {relative}")
    require(path.is_file(), f"missing resource: {relative}")
    return path


def text_value(value, description):
    require(isinstance(value, str) and bool(value.strip()), f"{description}: non-empty string required")
    require(not any(ord(char) < 32 for char in value), f"{description}: control character")
    require(unicodedata.normalize("NFC", value) == value, f"{description}: must be NFC normalized")


def metadata(obj, description, dataset_id=None):
    require(isinstance(obj, dict), f"{description}: object required")
    require(obj.get("protocolVersion") == PROTOCOL, f"{description}: unsupported protocolVersion")
    text_value(obj.get("datasetId"), f"{description}.datasetId")
    if dataset_id is not None:
        require(obj["datasetId"] == dataset_id, f"{description}: datasetId mismatch")
    require(isinstance(obj.get("revision"), str) and REVISION.fullmatch(obj["revision"]), f"{description}: invalid revision")


def valid_locale(locale):
    require(isinstance(locale, str) and LANGUAGE_TAG.fullmatch(locale), f"invalid ordinary BCP 47 tag: {locale!r}")
    # Publication uses explicitly reviewed canonical tags from config/data_policy.json.
    # This syntax check does not claim full IANA registry or grandfathered-tag validation.


def discover(data):
    data = Path(data)
    entries = [("countries", data / "countries.json")]
    for pattern, kind in (("regions/*.json", "structure"), ("i18n/*/*.json", "locale"), ("catalog_i18n/*.json", "country-names")):
        entries.extend((kind, path) for path in sorted(data.glob(pattern)))
    return sorted(entries, key=lambda item: item[1].relative_to(data).as_posix())


def check_schema(root, kind, value):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise DataError("--schema requires development dependency: python3 -m pip install -r tool/requirements-ci.txt") from exc
    schema_path = Path(root) / "schemas" / (kind + ".schema.json")
    validator = Draft202012Validator(load_json(schema_path))
    errors = sorted(validator.iter_errors(value), key=lambda error: str(list(error.path)))
    if errors:
        raise DataError(f"{schema_path.name}: {list(errors[0].path)}: {errors[0].message}")


def verify_sources(root):
    root = Path(root).resolve()
    lock_path = root / "sources/source-lock.json"
    if not lock_path.exists():
        return None
    lock = load_json(lock_path)
    entries = lock.get("sources")
    require(isinstance(entries, list) and entries, "source lock requires sources array")
    known = set()
    for entry in entries:
        relative = entry.get("localPath")
        require(relative not in known, f"duplicate source path: {relative}")
        known.add(relative)
        path = safe_resource(root, relative)
        require(sha256(path) == entry.get("sha256"), f"source hash mismatch: {relative}")
        require(path.stat().st_size == entry.get("sizeBytes"), f"source byte count mismatch: {relative}")
        require(re.fullmatch(r"[a-f0-9]{40}", entry.get("commit", "")), f"source not pinned to full commit: {relative}")
        text_value(entry.get("license"), f"{relative}.license")
    # Derived extracts are committed reductions of an upstream dump (e.g. the
    # GeoNames CN rows). They are byte-pinned like sources but have no upstream
    # commit to point at; their provenance travels inside the file itself.
    for entry in lock.get("derivedSources", []):
        relative = entry.get("localPath")
        require(relative not in known, f"duplicate source path: {relative}")
        known.add(relative)
        path = safe_resource(root, relative)
        require(sha256(path) == entry.get("sha256"), f"derived source hash mismatch: {relative}")
        require(path.stat().st_size == entry.get("sizeBytes"), f"derived source byte count mismatch: {relative}")
        text_value(entry.get("license"), f"{relative}.license")
        require(entry.get("upstreamSha256") or entry.get("upstreamQuery"),
                f"derived source missing upstream pin: {relative}")
    # AI-generated extracts: byte-pinned project content with no upstream at
    # all — provenance is the recorded generation run inside the file.
    for entry in lock.get("generatedSources", []):
        relative = entry.get("localPath")
        require(relative not in known, f"duplicate source path: {relative}")
        known.add(relative)
        path = safe_resource(root, relative)
        require(sha256(path) == entry.get("sha256"), f"generated source hash mismatch: {relative}")
        require(path.stat().st_size == entry.get("sizeBytes"), f"generated source byte count mismatch: {relative}")
        text_value(entry.get("license"), f"{relative}.license")
        require(entry.get("reviewStatus"), f"generated source missing review status: {relative}")
    return known


def validate(root, check_manifest=True, schema=False, production=False):
    root = Path(root).resolve()
    data = root / "data"
    require(not data.is_symlink(), "dataset root must not be a symlink")
    catalog = load_json(data / "countries.json")
    metadata(catalog, "countries")
    dataset_id = catalog["datasetId"]
    source_paths = verify_sources(root)
    if production:
        require(source_paths is not None, "production validation requires pinned source-lock provenance")
    countries = {}
    require(isinstance(catalog.get("countries"), list) and catalog["countries"], "countries: non-empty list required")
    for row in catalog["countries"]:
        code = row.get("code")
        require(isinstance(code, str) and COUNTRY.fullmatch(code), f"invalid country code: {code}")
        require(code not in countries, f"duplicate country: {code}")
        require(row.get("rootId") == "cc:" + code, f"wrong country root: {code}")
        text_value(row.get("name"), f"country {code}.name")
        countries[code] = row
    require(catalog["revision"] == revision("c", catalog["countries"]), "country catalog revision does not match content")
    policy_path = root / "config" / "data_policy.json"
    policy = load_json(policy_path) if policy_path.exists() else {}
    allowed_locales = policy.get("locales", [])
    for locale in allowed_locales:
        valid_locale(locale)
    require(len(set(allowed_locales)) == len(allowed_locales), "duplicate policy locale")
    for alias, target in policy.get("localeAliases", {}).items():
        valid_locale(alias)
        require(target in allowed_locales, f"locale alias target missing: {alias} -> {target}")
    require(set(policy.get("requiredCountries", [])) <= countries.keys(), "required country missing")
    structures = {}
    global_ids = set()
    packs = []
    catalog_packs = []
    for kind, path in discover(data):
        relative = path.relative_to(data).as_posix()
        safe_resource(data, relative)
        obj = load_json(path)
        metadata(obj, relative, dataset_id)
        require(obj.get("coverage", {}).get("status") != "draft", f"{relative}: a scaffold draft cannot be published")
        if production:
            require(obj.get("coverage", {}).get("status") in ("reviewed", "production"), f"{relative}: explicit reviewed/production maturity required; research-seed or missing status is not production data")
        if source_paths is not None and kind != "countries":
            require(bool(obj.get("sourceRefs")), f"{relative}: sourceRefs required")
            require(set(obj["sourceRefs"]) <= source_paths, f"{relative}: unknown source reference")
        if schema:
            check_schema(root, kind, obj)
        if kind == "countries":
            continue
        if kind == "structure":
            code = obj.get("countryCode")
            require(code in countries and path.stem == code, f"{relative}: country/file mismatch")
            require(code not in structures, f"duplicate structure: {code}")
            nodes = obj.get("nodes")
            require(isinstance(nodes, list) and nodes, f"{relative}: nodes required")
            by_id = {}
            for node in nodes:
                node_id = node.get("id")
                text_value(node_id, f"{relative}.id")
                require(node_id not in by_id, f"{relative}: duplicate ID {node_id}")
                require(node_id not in global_ids, f"{relative}: ID reused across countries: {node_id}")
                text_value(node.get("name"), f"{node_id}.name")
                text_value(node.get("kind"), f"{node_id}.kind")
                require(node.get("childrenStatus") in ("complete", "partial", "unknown"), f"{node_id}: invalid childrenStatus")
                if node.get("nativeLocale") is not None:
                    valid_locale(node["nativeLocale"])
                if node.get("nameLocale") is not None:
                    valid_locale(node["nameLocale"])
                if node.get("nameQuality") is not None:
                    text_value(node["nameQuality"], f"{node_id}.nameQuality")
                if production:
                    require(node.get("nameQuality") in PRODUCTION_SOURCE_QUALITIES, f"{node_id}: unapproved or missing default-name quality")
                for alias in node.get("aliases", []):
                    text_value(alias, f"{node_id}.alias")
                by_id[node_id] = node
            root_id = countries[code]["rootId"]
            require(root_id in by_id, f"{code}: root missing")
            require([node["id"] for node in nodes if node.get("parentId") is None] == [root_id], f"{code}: exactly one declared root required")
            require(by_id[root_id]["kind"] == "country", f"{code}: root kind must be country")
            for node in nodes:
                if node["id"] == root_id:
                    continue
                parent_id = node.get("parentId")
                require(parent_id in by_id, f"{node['id']}: missing or cross-country parent {parent_id}")
                seen = {node["id"]}
                while parent_id is not None:
                    require(parent_id not in seen, f"{node['id']}: parent cycle at {parent_id}")
                    seen.add(parent_id)
                    parent_id = by_id[parent_id].get("parentId")
                    require(parent_id is None or parent_id in by_id, f"{node['id']}: missing ancestor {parent_id}")
                require(root_id in seen, f"{node['id']}: disconnected path")
            require(obj["revision"] == revision("s", nodes), f"{code}: structure revision does not match content")
            structures[code] = obj
            global_ids.update(by_id)
        elif kind == "locale":
            packs.append((relative, path, obj))
        elif kind == "country-names":
            catalog_packs.append((relative, path, obj))
    require(structures.keys() == countries.keys(), "catalog and structure countries differ")
    coverage = []
    for relative, path, obj in packs:
        code, locale = obj.get("countryCode"), obj.get("locale")
        require(code in structures and path.stem == code and path.parent.name == locale, f"{relative}: country/locale path mismatch")
        valid_locale(locale)
        require(not allowed_locales or locale in allowed_locales, f"{relative}: locale not reviewed in policy")
        structure = structures[code]
        require(obj.get("compatibleStructureRevision") == structure["revision"], f"{relative}: incompatible structure revision")
        names = obj.get("names")
        require(isinstance(names, dict), f"{relative}: names must be an object")
        valid_ids = {node["id"] for node in structure["nodes"]}
        require(names.keys() <= valid_ids, f"{relative}: dangling translation IDs {sorted(names.keys() - valid_ids)[:3]}")
        for node_id, name in names.items():
            text_value(name, f"{relative}.{node_id}")
        require(obj["revision"] == locale_revision(names, obj.get("coverage", {}).get("translationQualityById", {})), f"{relative}: locale revision does not match content")
        quality = obj.get("coverage", {}).get("translationQualityById", {})
        require(isinstance(quality, dict) and quality.keys() <= names.keys(), f"{relative}: quality map contains unknown translation ID")
        if source_paths is not None:
            require(quality.keys() == names.keys(), f"{relative}: every sourced name requires a quality marker")
        quality_counts = {}
        for node_id in names:
            status = quality.get(node_id, "unspecified")
            text_value(status, f"{relative}.{node_id}.quality")
            quality_counts[status] = quality_counts.get(status, 0) + 1
        if production:
            require(set(quality_counts) <= PRODUCTION_SOURCE_QUALITIES, f"{relative}: unapproved source translations in production profile: {sorted(set(quality_counts) - PRODUCTION_SOURCE_QUALITIES)}")
        coverage.append({"country": code, "locale": locale, "explicitNames": len(names), "nodes": len(valid_ids), "missingNames": len(valid_ids) - len(names), "sourceQualityCounts": quality_counts, "projectReviewVerifiedByThisTool": False})
    seen_catalog_locales = set()
    for relative, path, obj in catalog_packs:
        locale = obj.get("locale")
        valid_locale(locale)
        require(path.stem == locale and (not allowed_locales or locale in allowed_locales), f"{relative}: catalog locale mismatch")
        require(locale not in seen_catalog_locales, f"duplicate catalog locale: {locale}")
        seen_catalog_locales.add(locale)
        require(obj.get("compatibleCatalogRevision") == catalog["revision"], f"{relative}: incompatible catalog revision")
        names = obj.get("names")
        require(isinstance(names, dict) and names.keys() <= countries.keys(), f"{relative}: unknown country name key")
        require(names.keys() == countries.keys(), f"{relative}: country-name coverage must be complete")
        for code, name in names.items():
            text_value(name, f"{relative}.{code}")
        quality = obj.get("coverage", {}).get("translationQualityById", {})
        require(isinstance(quality, dict) and quality.keys() <= names.keys(), f"{relative}: quality map contains unknown country code")
        if source_paths is not None:
            require(quality.keys() == names.keys(), f"{relative}: every country name requires a quality marker")
        if production:
            require(quality.keys() == names.keys() and set(quality.values()) <= PRODUCTION_SOURCE_QUALITIES, f"{relative}: unapproved country-name quality in production profile")
        require(obj["revision"] == locale_revision(names, obj.get("coverage", {}).get("translationQualityById", {})), f"{relative}: locale revision does not match content")
    required_locales = set(policy.get("requiredCatalogLocales", []))
    require(required_locales <= seen_catalog_locales, "required catalog locale missing")
    if policy.get("requireEveryCountryLocalePack", False):
        pairs = {(obj["countryCode"], obj["locale"]) for _, _, obj in packs}
        require({(code, locale) for code in countries for locale in allowed_locales} <= pairs, "required country/locale pack missing")
    result = {"datasetId": dataset_id, "integrityStatus": "pass", "profile": "production-structure-gates" if production else "seed-integrity", "humanReviewVerified": False, "countries": len(countries), "structures": len(structures), "nodes": sum(len(obj["nodes"]) for obj in structures.values()), "localePacks": len(packs), "catalogLocalePacks": len(catalog_packs), "sourceFilesVerified": len(source_paths) if source_paths is not None else 0, "coverage": sorted(coverage, key=lambda item: (item["country"], item["locale"]))}
    if check_manifest:
        manifest = load_json(data / "manifest.json")
        verify_manifest(data, manifest, require_complete=True)
        if schema:
            check_schema(root, "manifest", manifest)
    return result


def manifest_value(data):
    catalog = load_json(Path(data) / "countries.json")
    resources = []
    for kind, path in discover(data):
        relative = path.relative_to(data).as_posix()
        safe_resource(data, relative)
        obj = load_json(path)
        entry = {"path": relative, "kind": kind, "revision": obj["revision"], "sha256": sha256(path), "bytes": path.stat().st_size}
        for key in ("countryCode", "locale", "compatibleStructureRevision", "compatibleCatalogRevision"):
            if key in obj:
                entry[key] = obj[key]
        resources.append(entry)
    return {"protocolVersion": PROTOCOL, "datasetId": catalog["datasetId"], "revision": revision("m", resources), "resources": resources}


def verify_manifest(data, manifest, require_complete=False):
    metadata(manifest, "manifest")
    resources = manifest.get("resources")
    require(isinstance(resources, list), "manifest.resources must be array")
    declared = [entry.get("path") for entry in resources]
    require(
        declared == sorted(declared),
        "manifest resources must be sorted by path",
    )
    paths = set()
    for entry in resources:
        relative = entry.get("path")
        require(relative not in paths, f"duplicate manifest path: {relative}")
        paths.add(relative)
        path = safe_resource(data, relative)
        require(entry.get("sha256") == sha256(path), f"hash mismatch: {relative}")
        require(type(entry.get("bytes")) is int and entry["bytes"] == path.stat().st_size, f"byte count mismatch: {relative}")
        obj = load_json(path)
        metadata(obj, relative, manifest["datasetId"])
        require(entry.get("revision") == obj["revision"], f"resource revision mismatch: {relative}")
        for key in ("countryCode", "locale", "compatibleStructureRevision", "compatibleCatalogRevision"):
            require(entry.get(key) == obj.get(key), f"resource metadata mismatch {key}: {relative}")
    require(manifest["revision"] == revision("m", resources), "manifest revision does not match resource list")
    if require_complete:
        require(manifest == manifest_value(Path(data)), "manifest not current/complete; regenerate intentionally")


def guard_output(root, output, replace=False):
    root, output = Path(root).resolve(), Path(output).absolute()
    for current in [output, *output.parents]:
        require(not current.is_symlink(), f"output path contains symlink: {current}")
    output = output.resolve()
    forbidden_exact = [Path("/"), Path.home().resolve(), root]
    forbidden_trees = [root / name for name in ("data", "sources", "tool", "schemas", "docs")]
    require(output not in forbidden_exact and not any(output == item or output.is_relative_to(item) for item in forbidden_trees), f"unsafe output: {output}")
    require(not root.is_relative_to(output), f"output is repository ancestor: {output}")
    if output.exists():
        require(output.is_dir(), "output already exists and is not a directory")
        require(replace and (output / MARKER).is_file(), "existing output requires --replace and a generated-directory marker")
    return output


def build_offline(root, config_path, output, replace=False, dry_run=False, asset_prefix=None):
    root = Path(root).resolve()
    validate(root)
    data = root / "data"
    manifest = load_json(data / "manifest.json")
    config = load_json(config_path)
    structures = config.get("structures", [])
    locales = config.get("locales", {})
    catalog_locales = config.get("catalogLocales", [])
    require(isinstance(structures, list) and len(set(structures)) == len(structures), "structures must be unique array")
    require(isinstance(locales, dict), "locales must be an object")
    for code in [*structures, *locales]:
        require(isinstance(code, str) and COUNTRY.fullmatch(code), f"invalid configured country: {code}")
    for tags in [*locales.values(), catalog_locales]:
        require(isinstance(tags, list) and len(tags) == len(set(tags)), "locale selections must be unique arrays")
        for tag in tags:
            valid_locale(tag)
    paths = {"countries.json"}
    paths.update(f"regions/{code}.json" for code in structures)
    paths.update(f"i18n/{locale}/{code}.json" for code, tags in locales.items() for locale in tags)
    paths.update(f"catalog_i18n/{locale}.json" for locale in catalog_locales)
    available = {entry["path"]: entry for entry in manifest["resources"]}
    require(paths <= available.keys(), f"selected resource missing: {sorted(paths - available.keys())}")
    output = guard_output(root, output, replace)
    if asset_prefix is None:
        require(output.is_relative_to(root), "output outside repository requires --asset-prefix with the host-relative asset directory")
        asset_prefix = output.relative_to(root).as_posix()
    require(isinstance(asset_prefix, str) and asset_prefix and "\\" not in asset_prefix and not PurePosixPath(asset_prefix).is_absolute(), "asset prefix must be a nonempty POSIX relative path")
    require("%" not in asset_prefix and not any(ord(char) < 32 or ord(char) == 127 for char in asset_prefix), "asset prefix contains URI encoding or control characters")
    require(all(part not in ("", ".", "..") for part in asset_prefix.split("/")), "asset prefix contains traversal or empty components")
    selected = [entry for entry in manifest["resources"] if entry["path"] in paths]
    notices = []
    for path in sorted((root / "licenses/third_party").glob("*")):
        if path.is_file():
            safe_resource(root, path.relative_to(root).as_posix())
            notices.append((path, "notices/" + path.name))
    for name in ("DATA_SOURCES.md", "LICENSE_POLICY.md"):
        path = root / "docs" / name
        if path.is_file():
            safe_resource(root, path.relative_to(root).as_posix())
            notices.append((path, "notices/" + name))
    asset_paths = sorted([*paths, "manifest.json", "registry.json", *[relative for _, relative in notices]])
    report = {"output": str(output), "assetPrefix": asset_prefix, "resources": sorted(paths), "resourceBytes": sum(item["bytes"] for item in selected), "assetFileCount": len(asset_paths), "dryRun": dry_run}
    if dry_run:
        return report
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".geo-assets-", dir=output.parent))
    backup = None
    try:
        for relative in sorted(paths):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_resource(data, relative), destination)
        subset = {"protocolVersion": PROTOCOL, "datasetId": manifest["datasetId"], "revision": revision("m", selected), "resources": selected}
        write_json(staging / "manifest.json", subset)
        write_json(staging / "registry.json", manifest)
        for source, relative in notices:
            (staging / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, staging / relative)
        fragment = "# Merge assets into the host's EXISTING flutter: block; do not create a second block.\nflutter:\n  assets:\n"
        fragment += "".join("    - " + json.dumps(asset_prefix + "/" + relative, ensure_ascii=False) + "\n" for relative in asset_paths)
        (staging / "assets.fragment.yaml").write_text(fragment, encoding="utf-8")
        (staging / MARKER).write_text("Generated by geo_regions; safe replacement requires this marker.\n", encoding="utf-8")
        verify_manifest(staging, subset)
        report["assetBytes"] = sum((staging / relative).stat().st_size for relative in asset_paths)
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix=".geo-backup-", dir=output.parent))
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(staging, output)
        except BaseException:
            if backup is not None:
                os.replace(backup, output)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return report
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def scaffold_country(root, country, output, dry_run=False):
    require(COUNTRY.fullmatch(country), "country must be ISO-style uppercase alpha-2")
    catalog = load_json(Path(root) / "data/countries.json")
    require(country not in {item["code"] for item in catalog["countries"]}, "country already exists; prepare an explicit update instead")
    output = guard_output(root, output)
    nodes = [{"id": "cc:" + country, "parentId": None, "kind": "country", "name": "REPLACE_WITH_SOURCED_NAME", "childrenStatus": "unknown"}]
    obj = {"protocolVersion": PROTOCOL, "datasetId": catalog["datasetId"], "countryCode": country, "revision": revision("s", nodes), "nodes": nodes, "coverage": {"status": "draft", "note": "Not publishable: obtain source, license, subdivision coverage and stable IDs."}, "sourceRefs": []}
    if not dry_run:
        write_json(output / "regions" / (country + ".json"), obj)
        (output / MARKER).write_text("Scaffold only; manually review before promotion.\n", encoding="utf-8")
    return {"status": "draft", "country": country, "output": str(output), "dryRun": dry_run}


def scaffold_locale(root, locale, output, dry_run=False):
    valid_locale(locale)
    output = guard_output(root, output)
    data = Path(root) / "data"
    require(not (data / "i18n" / locale).exists() and not (data / "catalog_i18n" / (locale + ".json")).exists(), "locale already exists; prepare an explicit update instead")
    catalog = load_json(data / "countries.json")
    before = {str(path): sha256(path) for path in sorted((data / "regions").glob("*.json"))}
    files = []
    for path in sorted((data / "regions").glob("*.json")):
        structure = load_json(path)
        obj = {"protocolVersion": PROTOCOL, "datasetId": catalog["datasetId"], "countryCode": structure["countryCode"], "locale": locale, "revision": locale_revision({}), "compatibleStructureRevision": structure["revision"], "names": {}, "coverage": {"status": "draft", "note": "Empty on purpose; add only sourced or reviewed names. Fallbacks are not translations."}, "sourceRefs": []}
        destination = output / "i18n" / locale / path.name
        files.append(str(destination))
        if not dry_run:
            write_json(destination, obj)
    names = {"protocolVersion": PROTOCOL, "datasetId": catalog["datasetId"], "locale": locale, "revision": locale_revision({}), "compatibleCatalogRevision": catalog["revision"], "names": {}, "coverage": {"status": "draft"}, "sourceRefs": []}
    if not dry_run:
        write_json(output / "catalog_i18n" / (locale + ".json"), names)
        (output / MARKER).write_text("Scaffold only; not included in published data.\n", encoding="utf-8")
    after = {str(path): sha256(path) for path in sorted((data / "regions").glob("*.json"))}
    require(before == after, "language scaffolding unexpectedly changed structure bytes")
    return {"status": "draft", "locale": locale, "files": files, "output": str(output), "structuresUnchanged": True, "dryRun": dry_run}


def diff_structures(old_path, new_path):
    old, new = load_json(old_path), load_json(new_path)
    require(old.get("datasetId") == new.get("datasetId") and old.get("countryCode") == new.get("countryCode"), "diff requires same dataset and country")
    before, after = ({node["id"]: node for node in obj["nodes"]} for obj in (old, new))
    common = before.keys() & after.keys()
    return {"countryCode": new["countryCode"], "added": sorted(after.keys() - before.keys()), "removed": sorted(before.keys() - after.keys()), "reparented": [{"id": node_id, "from": before[node_id].get("parentId"), "to": after[node_id].get("parentId")} for node_id in sorted(common) if before[node_id].get("parentId") != after[node_id].get("parentId")], "renamed": [{"id": node_id, "from": before[node_id]["name"], "to": after[node_id]["name"]} for node_id in sorted(common) if before[node_id]["name"] != after[node_id]["name"]], "migrationRequired": bool(before.keys() - after.keys()) or any(before[node_id].get("parentId") != after[node_id].get("parentId") for node_id in common)}


def validate_selection(root, selection_path, schema=False):
    root = Path(root).resolve()
    selection = load_json(selection_path)
    require(isinstance(selection, dict) and selection.get("protocolVersion") == PROTOCOL, "selection: unsupported protocol")
    code = selection.get("countryCode")
    require(isinstance(code, str) and COUNTRY.fullmatch(code), "selection: invalid country code")
    structure = load_json(safe_resource(root / "data", f"regions/{code}.json"))
    require(selection.get("datasetId") == structure["datasetId"], "selection: dataset mismatch")
    require(selection.get("dataRevision") == structure["revision"], "selection: stale structure revision")
    path = selection.get("pathIds")
    require(isinstance(path, list) and path and all(isinstance(item, str) for item in path), "selection: nonempty string path required")
    require(len(set(path)) == len(path), "selection: duplicate path ID")
    require(path[0] == "cc:" + code, "selection: path must include country root first")
    nodes = {node["id"]: node for node in structure["nodes"]}
    parent = None
    for node_id in path:
        require(node_id in nodes, f"selection: unknown node {node_id}")
        require(nodes[node_id]["parentId"] == parent, f"selection: missing or incorrect parent edge at {node_id}")
        parent = node_id
    if "displaySnapshot" in selection:
        require(isinstance(selection["displaySnapshot"], list) and len(selection["displaySnapshot"]) == len(path), "selection: snapshot must correspond to the complete path")
    if schema:
        check_schema(root, "selection", selection)
    return {"status": "valid-identity-path", "datasetId": structure["datasetId"], "countryCode": code, "pathIds": path, "dataRevision": structure["revision"], "businessSelectionPolicyChecked": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command", required=True)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--no-manifest", action="store_true")
    validate_parser.add_argument("--schema", action="store_true")
    validate_parser.add_argument("--production", action="store_true", help="add strict gates; this research seed intentionally fails")
    validate_parser.add_argument("--report", type=Path)
    manifest_parser = sub.add_parser("manifest")
    manifest_parser.add_argument("--check", action="store_true")
    offline_parser = sub.add_parser("offline")
    offline_parser.add_argument("--config", type=Path, required=True)
    offline_parser.add_argument("--out", type=Path, required=True)
    offline_parser.add_argument("--replace", action="store_true")
    offline_parser.add_argument("--dry-run", action="store_true")
    offline_parser.add_argument("--asset-prefix", help="host-relative asset directory; required if --out is outside this repository")
    country_parser = sub.add_parser("add-country")
    country_parser.add_argument("--country", required=True)
    country_parser.add_argument("--out", type=Path, required=True)
    country_parser.add_argument("--dry-run", action="store_true")
    locale_parser = sub.add_parser("add-locale")
    locale_parser.add_argument("--locale", required=True)
    locale_parser.add_argument("--out", type=Path, required=True)
    locale_parser.add_argument("--dry-run", action="store_true")
    diff_parser = sub.add_parser("diff")
    diff_parser.add_argument("--old", type=Path, required=True)
    diff_parser.add_argument("--new", type=Path, required=True)
    diff_parser.add_argument("--require-no-removals", action="store_true")
    selection_parser = sub.add_parser("selection")
    selection_parser.add_argument("--file", type=Path, required=True)
    selection_parser.add_argument("--schema", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            result = validate(args.root, not args.no_manifest, args.schema, args.production)
            if args.report:
                write_json(args.report, result)
            brief = {key: value for key, value in result.items() if key != "coverage"}
            print(json.dumps(brief, ensure_ascii=False, indent=2))
        elif args.command == "manifest":
            validate(args.root, check_manifest=False)
            obj = manifest_value(args.root.resolve() / "data")
            path = args.root / "data/manifest.json"
            if args.check:
                require(load_json(path) == obj, "manifest drift")
            else:
                write_json(path, obj)
            print(json.dumps({"path": str(path), "revision": obj["revision"], "resources": len(obj["resources"]), "checked": args.check}, indent=2))
        elif args.command == "offline":
            print(json.dumps(build_offline(args.root, args.config, args.out, args.replace, args.dry_run, args.asset_prefix), ensure_ascii=False, indent=2))
        elif args.command == "add-country":
            print(json.dumps(scaffold_country(args.root, args.country, args.out, args.dry_run), indent=2))
        elif args.command == "add-locale":
            print(json.dumps(scaffold_locale(args.root, args.locale, args.out, args.dry_run), indent=2))
        elif args.command == "diff":
            result = diff_structures(args.old, args.new)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.require_no_removals:
                require(not result["migrationRequired"], "removed or reparented IDs require an explicit reviewed migration plan")
        elif args.command == "selection":
            print(json.dumps(validate_selection(args.root, args.file, args.schema), ensure_ascii=False, indent=2))
    except (DataError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
