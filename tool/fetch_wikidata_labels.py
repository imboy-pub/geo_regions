#!/usr/bin/env python3
"""Fetch subdivision labels from Wikidata for the committed seed extract.

Wikidata is CC0-1.0, so unlike the ODbL CSC snapshot its labels may feed the
product layer (provisional quality — community labels, never human-reviewed
by this project). The join is EXACT: Wikidata's P300 stores the same ISO
3166-2 code the seed uses for subdivision nodes (e.g. FR-04, GB-ANN), so
matching carries zero homonym risk. CN statistical nodes are skipped — their
GB/T codes are not P300 values, and label+parent-chain matching is the
translation-generation track, not this script.

The full label dump never enters git; this script reduces it to the committed
extract `sources/raw/wikidata/subdivision-labels.json` (only the ten project
locales are kept). The extract is byte-pinned via the `derivedSources`
section of sources/source-lock.json; provenance (endpoint + the exact SPARQL
query + retrieval date) travels inside the file.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DEFAULT = Path("sources/raw/wikidata/subdivision-labels.json")
ENDPOINT = "https://query.wikidata.org/sparql"
LOCALES = ("en", "zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar")
# Wikidata language tags (BCP-47 lower-case) that differ from project tags.
WIKI_TAGS = {"zh-Hans": "zh-hans", "zh-Hant": "zh-hant"}
COUNTRIES = ("JP", "KR", "US", "GB", "DE", "FR", "IT", "RU", "SA")
USER_AGENT = "geo_regions-seed-import/1.0 (https://github.com/imboy-pub/geo_regions)"


def build_query(codes: list[str]) -> str:
    values = " ".join(f'"{code}"' for code in codes)
    lang_list = ", ".join(
        f'"{WIKI_TAGS.get(loc, loc)}"' for loc in LOCALES
    )
    return (
        "SELECT ?code ?item ?label WHERE {\n"
        f"  VALUES ?code {{ {values} }}\n"
        "  ?item wdt:P300 ?code .\n"
        "  ?item rdfs:label ?label .\n"
        f"  FILTER(LANG(?label) IN ({lang_list}))\n"
        "}"
    )


def subdivision_codes(root: Path) -> list[str]:
    codes = set()
    for cc in COUNTRIES:
        regions = json.loads((root / f"data/regions/{cc}.json").read_text("utf-8"))
        for node in regions["nodes"]:
            if node["id"] == f"cc:{cc}" or node["kind"] == "country":
                continue
            codes.add(node["code"])
    return sorted(codes)


def fetch(query: str) -> dict:
    # POST keeps long VALUES lists off the URL (GET trips 414 URI Too Long).
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    request = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"User-Agent": USER_AGENT,
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def reduce_rows(rows: list[dict], codes: list[str]) -> tuple[dict, list[str]]:
    labels: dict[str, dict] = {}
    owners: dict[str, str] = {}
    ambiguous: set[str] = set()
    for row in rows:
        code = row["code"]["value"]
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        lang = row["label"]["xml:lang"]
        text = row["label"]["value"]
        if code in owners and owners[code] != qid:
            # Two items claim the same P300 (e.g. FR-69 Rhône vs Métropole de
            # Lyon). Choosing one would be a guess — drop the code honestly.
            ambiguous.add(code)
            labels.pop(code, None)
            continue
        owners[code] = qid
        entry = labels.setdefault(code, {"qid": qid, "labels": {}})
        project = next((loc for loc, tag in WIKI_TAGS.items() if tag == lang), lang)
        if project in LOCALES and project not in entry["labels"]:
            entry["labels"][project] = text
    unknown = set(labels) - set(codes)
    if unknown:
        raise SystemExit(f"unexpected codes returned: {sorted(unknown)[:5]}")
    return labels, sorted(ambiguous)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    codes = subdivision_codes(args.root)
    if not codes:
        raise SystemExit("no subdivision codes found")
    query = build_query(codes)
    payload = fetch(query)
    rows = payload.get("results", {}).get("bindings", [])
    labels, ambiguous = reduce_rows(rows, codes)
    document = {
        "source": "Wikidata labels via P300 (ISO 3166-2)",
        "endpoint": ENDPOINT,
        "query": query,
        "retrievedAt": "2026-11-14",
        "license": "CC0-1.0",
        "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "locales": list(LOCALES),
        "codeCount": len(codes),
        "matchCount": len(labels),
        "ambiguousCount": len(ambiguous),
        "ambiguousCodes": ambiguous,
        "labels": labels,
    }
    text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(text)
    covered = sum(1 for entry in labels.values() if entry["labels"])
    print(f"wrote {args.out} ({len(text):,} bytes): codes={len(codes)} "
          f"P300-matched={len(labels)} with-labels={covered}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
