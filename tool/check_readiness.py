#!/usr/bin/env python3
"""Fail CI when a declared production package has disappeared or is incomplete."""

import argparse
import json
from pathlib import Path
import re

from geo_data import DataError, load_json, require, validate


def production_gate(root, expected_refusal):
    """Bind the data-maturity tripwire to an explicit config switch.

    expected_refusal=true (research seed): the production gate MUST refuse the
    dataset, so nobody can flip maturity fields back to green unnoticed.
    expected_refusal=false (reviewed production data): the gate MUST pass.
    """
    try:
        validate(root, production=True)
        refused, reason = False, None
    except DataError as exc:
        refused, reason = True, str(exc)
    if expected_refusal and not refused:
        raise DataError(
            "research dataset unexpectedly passed the production gate; "
            "maturity must not be flipped without review — set "
            "expectedProductionGateRefusal=false only for reviewed production data")
    if not expected_refusal and refused:
        raise DataError("production gate refused the data while expectedProductionGateRefusal=false: " + reason)
    return {"expectedProductionGateRefusal": expected_refusal, "productionGateRefused": refused}


def check(root):
    root = Path(root).resolve()
    config = load_json(root / "config/readiness.json")
    expected = config.get("productionSdkExpected")
    require(type(expected) is bool, "productionSdkExpected must be an explicit boolean")
    expected_refusal = config.get("expectedProductionGateRefusal")
    require(type(expected_refusal) is bool, "expectedProductionGateRefusal must be an explicit boolean in config/readiness.json")
    present = (root / "pubspec.yaml").is_file()
    if expected or present:
        require(present, "production SDK is required, but root pubspec.yaml is missing")
        require((root / "lib/geo_regions.dart").is_file(), "production SDK public library lib/geo_regions.dart is missing")
        require(any((root / "test").rglob("*_test.dart")), "production SDK tests are missing")
        pubspec = (root / "pubspec.yaml").read_text(encoding="utf-8")
        require(re.search(r"(?m)^name:\s*['\"]?geo_regions['\"]?\s*(?:#.*)?$", pubspec), "root package name must be geo_regions")
    report = production_gate(root, expected_refusal)
    return {"productionSdkExpected": expected, "productionPackagePresent": present, "mode": "production-package-checks-required" if expected or present else "research-seed-and-demo-only", "productionComplete": False, **report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root), indent=2))
    except DataError as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
