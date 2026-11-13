#!/usr/bin/env python3
"""Build an immutable, deterministic research-seed data ZIP and checksum."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from geo_data import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--source-commit", help="full commit verified by release CI")
    args = parser.parse_args()
    if not re.fullmatch(r"data-v[0-9]{4}\.[0-9]{2}\.[0-9]{2}(?:\.[0-9]+)?", args.tag):
        parser.error("tag must be data-vYYYY.MM.DD or data-vYYYY.MM.DD.N")
    root = Path(__file__).resolve().parents[1]
    validate(root, schema=True)
    if args.source_commit is not None and not re.fullmatch(r"[a-f0-9]{40}", args.source_commit):
        parser.error("--source-commit must be a full commit SHA")
    for path in (args.out.absolute(), *args.out.absolute().parents):
        if path.is_symlink():
            parser.error(f"release output cannot use a symlink: {path}")
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / f"geo_regions-{args.tag}.zip"
    checksum_path = output.with_suffix(".zip.sha256")
    if output.exists() or checksum_path.exists():
        parser.error("refusing to overwrite an existing release ZIP or checksum")
    files = []
    for folder in ("data", "sources", "schemas", "licenses/third_party"):
        files.extend(path for path in (root / folder).rglob("*") if path.is_file())
    for relative in ("LICENSE", "tool/import_data.py", "tool/geo_data.py", "tool/requirements-ci.txt", "config/data_policy.json", "config/offline.example.json", "docs/DATA_SOURCES.md", "docs/DATA_COVERAGE.md", "docs/LICENSE_POLICY.md"):
        path = root / relative
        if path.is_file():
            files.append(path)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            if path.is_symlink():
                raise ValueError(f"release symlink forbidden: {path}")
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("READ_FIRST.md", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, "# geo_regions research seed\n\nThis is a source-traceable research seed, not current official coverage.\nRead docs/DATA_COVERAGE.md for snapshot dates, missing levels, and translation quality.\nData retains the original licenses under licenses/third_party/.\nCode BSD-3-Clause does not replace those data licenses.\n\nRaw sources, lock, crosswalk, coverage evidence and the importer are included.\nRun `python3 tool/import_data.py --check` to reproduce outputs offline.\nRun `python3 -m pip install -r tool/requirements-ci.txt`, then `python3 tool/geo_data.py validate --schema` for schema/integrity checks.\n\nThis data-release ZIP excludes the Flutter demo and execution plans; the development handoff ZIP includes them.\n")
        info = zipfile.ZipInfo("BUILD.json", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, json.dumps({"tag": args.tag, "testedCommit": args.source_commit, "note": "A null commit denotes a local artifact, not a CI-verified Git commit."}, indent=2) + "\n")
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    with checksum_path.open("x", encoding="utf-8") as stream:
        stream.write(f"{checksum}  {output.name}\n")
    print(f"created {output} ({output.stat().st_size} bytes); sha256={checksum}")


if __name__ == "__main__":
    main()
