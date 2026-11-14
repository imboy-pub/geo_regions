#!/usr/bin/env python3
"""Extract the GeoNames CN admin rows the seed's English overlay matches against.

GeoNames (https://www.geonames.org/) is CC-BY-4.0 — attribution, no
share-alike — so it may feed the product layer's provisional English names,
unlike the ODbL CSC snapshot. The full CN dump (~32MB zip, 132MB text) never
enters git; this script reduces it to the committed extract
`sources/raw/geonames/cn-adm-rows.json`:

- `adm2` rows keyed by the GB/T 2260 4-digit prefecture code that GeoNames
  carries verbatim in its admin2 column (e.g. 3401 = Hefei);
- `adm3` rows (county level) keyed by GeoNames' own columns: FIPS admin1
  (Beijing=22, Tianjin=28, Shanghai=23, Chongqing=33 — GeoNames uses FIPS,
  not GB codes, for the four municipalities) plus the admin2 column, which
  is empty/internal for municipalities;
- per row: `ascii` (asciiname), `zh` (CJK alternatenames, used to match the
  statistical node's Chinese name) and `latin` (ASCII alternatenames, used
  as evidence for the bare-name rule in tool/import_data.py).

Matching itself lives in `tool/import_data.py` so `--check` stays
reproducible from committed sources alone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
import zipfile
from pathlib import Path

SOURCE_URL = "https://download.geonames.org/export/dump/CN.zip"
OUT_DEFAULT = Path("sources/raw/geonames/cn-adm-rows.json")
COLUMNS = ("geonameid", "name", "asciiname", "alternatenames", "latitude",
           "longitude", "featureClass", "featureCode", "countryCode", "cc2",
           "admin1", "admin2", "admin3", "admin4", "population", "elevation",
           "dem", "timezone", "modificationDate")


def is_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def is_ascii(text: str) -> bool:
    return text.isascii() and text.isprintable() and not text.isspace()


def clean_alts(raw: str) -> tuple[list[str], list[str]]:
    zh, latin = [], []
    for candidate in raw.split(","):
        candidate = unicodedata.normalize("NFC", candidate).strip()
        if not candidate:
            continue
        if is_cjk(candidate):
            if candidate not in zh:
                zh.append(candidate)
        elif is_ascii(candidate) and candidate not in latin:
            latin.append(candidate)
    return sorted(zh), sorted(latin)


def row_record(ascii_name: str, alts: str) -> dict:
    zh, latin = clean_alts(alts)
    return {"ascii": ascii_name, "zh": zh, "latin": latin}


def extract(zip_path: Path) -> dict:
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    adm2: dict[str, dict] = {}
    adm3: list[dict] = []
    with zipfile.ZipFile(zip_path) as bundle:
        names = [n for n in bundle.namelist()
                 if n.endswith(".txt") and n != "readme.txt"]
        if len(names) != 1:
            raise SystemExit(f"expected exactly one data .txt in {zip_path}, got {names}")
        with bundle.open(names[0]) as stream:
            for raw_line in stream:
                line = raw_line.decode("utf-8").rstrip("\n")
                if not line:
                    continue
                fields = line.split("\t")
                if len(fields) != len(COLUMNS):
                    raise SystemExit(f"unexpected column count: {len(fields)}")
                row = dict(zip(COLUMNS, fields))
                if row["countryCode"] != "CN":
                    continue
                if row["featureCode"] == "ADM2":
                    code = row["admin2"]
                    if not code:
                        continue
                    record = row_record(row["asciiname"], row["alternatenames"])
                    if code in adm2:
                        raise SystemExit(f"duplicate GeoNames ADM2 row for GB code {code}")
                    adm2[code] = record
                elif row["featureCode"] == "ADM3":
                    record = row_record(row["asciiname"], row["alternatenames"])
                    adm3.append({"a1": row["admin1"], "a2": row["admin2"], **record})
    adm3.sort(key=lambda r: (r["a1"], r["a2"], r["ascii"]))
    return {
        "source": "GeoNames CN dump",
        "sourceUrl": SOURCE_URL,
        "upstreamSha256": digest,
        "license": "CC-BY-4.0",
        "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
        "extractedAt": "2026-11-14",
        "rowCounts": {"adm2": len(adm2), "adm3": len(adm3)},
        "adm2": dict(sorted(adm2.items())),
        "adm3": adm3,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=Path("staging/geonames-cn/CN.zip"))
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    if not args.zip.is_file():
        raise SystemExit(f"missing GeoNames dump: {args.zip}")
    document = extract(args.zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    args.out.write_bytes(payload)
    counts = document["rowCounts"]
    print(f"wrote {args.out} ({len(payload):,} bytes): "
          f"adm2={counts['adm2']} adm3={counts['adm3']} "
          f"upstream sha256={document['upstreamSha256'][:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
