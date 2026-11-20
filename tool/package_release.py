#!/usr/bin/env python3
"""Build an immutable, deterministic research-seed data ZIP and checksum."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from geo_data import COUNTRY, DataError, load_json, preview_files, require, safe_resource, sha256, valid_locale, validate


def production_files(root):
    input_manifest = safe_resource(root, "BUILD_INPUTS.json")
    input_manifest_hash = sha256(input_manifest)
    inputs = load_json(input_manifest)
    profile = load_json(safe_resource(root, "config/production-profile.json"))
    require(inputs.get("profileId") == profile.get("profileId") and inputs.get("profileId"),
            "production profile identity mismatch")
    manifest = load_json(safe_resource(root, "data/manifest.json"))
    require(profile.get("datasetId") == manifest["datasetId"], "production profile dataset mismatch")
    for name in ("countries", "locales", "catalogLocales"):
        values = profile.get(name)
        require(isinstance(values, list) and values and all(isinstance(value, str) for value in values)
                and len(set(values)) == len(values), f"production profile {name} must be a nonempty unique list")
    countries = profile["countries"]
    for code in countries:
        require(COUNTRY.fullmatch(code), f"invalid production profile country: {code}")
    for locale in profile["locales"] + profile["catalogLocales"]:
        valid_locale(locale)
    selected = {"countries.json"}
    selected.update(f"regions/{code}.json" for code in countries)
    selected.update(f"i18n/{locale}/{code}.json" for code in countries for locale in profile["locales"])
    selected.update(f"catalog_i18n/{locale}.json" for locale in profile["catalogLocales"])
    require(selected == {resource["path"] for resource in manifest["resources"]},
            "production profile does not match manifest resources")
    for name, width in (("inputTree", 40), ("catalogReviewSha256", 64)):
        require(isinstance(inputs.get(name), str) and re.fullmatch(rf"[0-9a-f]{{{width}}}", inputs[name]),
                f"invalid production build input: {name}")
    hashes = inputs.get("files")
    require(isinstance(hashes, dict) and
            {"config/production-profile.json", "data/manifest.json", "sources/SOURCES_NOTICE.md"} <= hashes.keys(),
            "production build manifest is missing required inputs")
    reserved = {"BUILD_INPUTS.json", "BUILD.json", "READ_FIRST.md"}
    require(not reserved.intersection(hashes), "production build manifest lists reserved entries")
    paths = []
    for relative, digest in hashes.items():
        path = safe_resource(root, relative)
        require(path.is_file() and sha256(path) == digest, f"production build input changed: {relative}")
        paths.append(path)
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"release symlink forbidden: {path}")
        require(path.is_file() or path.is_dir(), f"release special file forbidden: {path}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == hashes.keys() | {"BUILD_INPUTS.json"}, "production build manifest does not match root files")
    return paths + [input_manifest], {**hashes, "BUILD_INPUTS.json": input_manifest_hash}, {
        "profileId": inputs["profileId"],
        "manifestSha256": hashes["data/manifest.json"],
        "inputTree": inputs["inputTree"],
        "catalogReviewSha256": inputs["catalogReviewSha256"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--source-commit", help="full commit verified by release CI")
    args = parser.parse_args()
    if not re.fullmatch(r"data-v[0-9]{4}\.[0-9]{2}\.[0-9]{2}(?:\.[0-9]+)?", args.tag):
        parser.error("tag must be data-vYYYY.MM.DD or data-vYYYY.MM.DD.N")
    root = args.root.absolute()
    if any(path.is_symlink() for path in (root, *root.parents)):
        parser.error("release root cannot use a symlink")
    root = root.resolve()
    try:
        validate(root, schema=True, production=args.production)
        if args.production:
            files, expected_hashes, build_fields = production_files(root)
    except (DataError, OSError) as error:
        parser.error(str(error))
    if args.source_commit is not None and not re.fullmatch(r"[a-f0-9]{40}", args.source_commit):
        parser.error("--source-commit must be a full commit SHA")
    for path in (args.out.absolute(), *args.out.absolute().parents):
        if path.is_symlink():
            parser.error(f"release output cannot use a symlink: {path}")
    if args.production and args.out.resolve().is_relative_to(root):
        parser.error("production output must be outside the input root")
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / f"geo_regions-{args.tag}.zip"
    checksum_path = output.with_suffix(".zip.sha256")
    if output.exists() or checksum_path.exists():
        parser.error("refusing to overwrite an existing release ZIP or checksum")
    if not args.production:
        files = preview_files(root)
        expected_hashes = {}
        build_fields = {}
    try:
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(files):
                relative = path.relative_to(root).as_posix()
                content = safe_resource(root, relative).read_bytes()
                if args.production:
                    require(hashlib.sha256(content).hexdigest() == expected_hashes[relative],
                            f"production build input changed while packaging: {relative}")
                info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)
            info = zipfile.ZipInfo("READ_FIRST.md", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            if args.production:
                archive.writestr(info, "# geo_regions production-profile data\n\nSee config/production-profile.json for the selected scope and sources/SOURCES_NOTICE.md for provenance, limitations and license notices.\n")
            else:
                archive.writestr(info, "# geo_regions research seed\n\nThis is a source-traceable research seed, not current official coverage.\nRead docs/DATA_COVERAGE.md for snapshot dates, missing levels, and translation quality.\nData retains the original licenses under licenses/third_party/.\nCode BSD-3-Clause does not replace those data licenses.\n\nRaw sources, lock, crosswalk, coverage evidence and the importer are included.\nRun `python3 tool/import_data.py --check` to reproduce outputs offline.\nRun `python3 -m pip install -r tool/requirements-ci.txt`, then `python3 tool/geo_data.py validate --schema` for schema/integrity checks.\n\nThis data-release ZIP excludes the Flutter demo and execution plans; the development handoff ZIP includes them.\n")
            info = zipfile.ZipInfo("BUILD.json", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, json.dumps({"tag": args.tag, "testedCommit": args.source_commit, **build_fields, "note": "A null commit denotes a local artifact, not a CI-verified Git commit."}, indent=2) + "\n")
    except DataError as error:
        output.unlink()
        parser.error(str(error))
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    with checksum_path.open("x", encoding="utf-8") as stream:
        stream.write(f"{checksum}  {output.name}\n")
    print(f"created {output} ({output.stat().st_size} bytes); sha256={checksum}")


if __name__ == "__main__":
    main()
