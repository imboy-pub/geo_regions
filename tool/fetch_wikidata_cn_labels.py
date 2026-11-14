#!/usr/bin/env python3
"""Fetch CN node labels from Wikidata for the committed seed extract.

Companion to tool/fetch_wikidata_labels.py (P300, non-CN countries). Chinese
administrative nodes carry no P300, but Wikidata stores the official
administration codes in two dedicated properties:

- P300 for provinces (ISO 3166-2:CN, e.g. "CN-AH") — exact join;
- P13971 "China division code by MCA" for prefecture/county nodes (e.g.
  340100 for Hefei, 340102 for Yaohai) — exact join after the recorded
  normalization: seed 4-digit prefecture codes pad to 6 digits with "00";
  6-digit county codes join verbatim; 9-digit townships and statistical
  grouping nodes (市辖区/县/省直辖县级行政区划…) have no Wikidata entity
  and are skipped.

The GB/T code IS the node identity, so the join is deterministic; codes
claimed by more than one Wikidata item are dropped, never guessed. Every
matched node keeps a `nameDrift` flag when its Wikidata zh label differs
from the seed's snapshot name (2023 snapshot vs current names) — recorded
for review, never used to reject the code-level match.

License CC0-1.0; the extract is byte-pinned via `derivedSources`
(upstreamQuery class — a live SPARQL endpoint has no dump revision).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DEFAULT = Path("sources/raw/wikidata/cn-node-labels.json")
ENDPOINT = "https://query.wikidata.org/sparql"
LOCALES = ("en", "zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar")
WIKI_TAGS = {"zh-Hans": "zh-hans", "zh-Hant": "zh-hant"}
MCA_PROP = "P13971"
BATCH = 500
RETRIES = 3
USER_AGENT = "geo_regions-seed-import/1.0 (https://github.com/imboy-pub/geo_regions)"
GROUP_NAMES = {'市辖区', '县', '省直辖县级行政区划', '自治区直辖县级行政区划'}


def sparql(query: str) -> list[dict]:
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            request = urllib.request.Request(
                ENDPOINT, data=data,
                headers={"User-Agent": USER_AGENT,
                         "Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.load(response)
            return payload.get("results", {}).get("bindings", [])
        except Exception as error:  # transient SSL EOF / 5xx — retry, then fail
            last_error = error
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"SPARQL failed after {RETRIES} attempts: {last_error}")


def build_targets(root: Path) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Returns ({nodeId: (property, query code)}, [province ISO codes])."""
    regions = json.loads((root / "data/regions/CN.json").read_text("utf-8"))
    targets: dict[str, tuple[str, str]] = {}
    province_iso: list[str] = []
    for node in regions["nodes"]:
        kind, code = node["kind"], node["code"]
        if kind == "country":
            continue
        if kind == "subdivision":
            province_iso.append(code)          # CN-AH … via P300
            targets[node["id"]] = ("P300", code)
        elif kind == "statistical-prefecture":
            if node["name"] in GROUP_NAMES:
                continue                        # grouping node, no Wikidata entity
            targets[node["id"]] = (MCA_PROP, code + "00")
        elif kind == "statistical-county":
            targets[node["id"]] = (MCA_PROP, code)
        # statistical-township (9-digit): outside Wikidata scope, honest miss
    return targets, sorted(set(province_iso))


def fetch_labels(prop: str, codes: list[str]) -> tuple[dict[str, dict], list[str]]:
    """Returns ({code: {qid, labels}}, [ambiguous codes])."""
    labels: dict[str, dict] = {}
    owners: dict[str, str] = {}
    ambiguous: set[str] = set()
    for start in range(0, len(codes), BATCH):
        chunk = codes[start:start + BATCH]
        values = " ".join(f'"{code}"' for code in chunk)
        rows = sparql(
            "SELECT ?code ?item ?label WHERE {\n"
            f"  VALUES ?code {{ {values} }}\n"
            f"  ?item wdt:{prop} ?code .\n"
            "  ?item rdfs:label ?label .\n"
            "}")
        for row in rows:
            code = row["code"]["value"]
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            lang = row["label"]["xml:lang"]
            text = row["label"]["value"]
            if code in owners and owners[code] != qid:
                ambiguous.add(code)
                labels.pop(code, None)
                continue
            owners[code] = qid
            entry = labels.setdefault(code, {"qid": qid, "labels": {}})
            project = next((loc for loc, tag in WIKI_TAGS.items() if tag == lang), lang)
            if project in LOCALES and project not in entry["labels"]:
                entry["labels"][project] = text
    return labels, sorted(ambiguous)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    targets, province_iso = build_targets(args.root)

    nodes: dict[str, dict] = {}
    ambiguous_total: list[str] = []
    mca_codes = sorted({code for prop, code in targets.values() if prop == MCA_PROP})
    mca_labels, ambiguous = fetch_labels(MCA_PROP, mca_codes)
    ambiguous_total += ambiguous
    code_to_node: dict[tuple[str, str], str] = {}
    for nid, (prop, code) in targets.items():
        if prop == MCA_PROP:
            code_to_node[(MCA_PROP, code)] = nid
    for code, entry in mca_labels.items():
        nid = code_to_node.get((MCA_PROP, code))
        if nid is not None:
            nodes[nid] = entry

    if province_iso:
        p300_labels, ambiguous = fetch_labels("P300", province_iso)
        ambiguous_total += ambiguous
        iso_to_node = {code: nid for nid, (prop, code) in targets.items() if prop == "P300"}
        for code, entry in p300_labels.items():
            nid = iso_to_node.get(code)
            if nid is not None:
                nodes[nid] = entry

    # Record where the current Wikidata zh label differs from the snapshot name.
    regions = json.loads((args.root / "data/regions/CN.json").read_text("utf-8"))
    names = {n["id"]: n["name"] for n in regions["nodes"]}
    drift = 0
    for nid, entry in nodes.items():
        zh = entry["labels"].get("zh-Hans") or entry["labels"].get("zh")
        if zh and names.get(nid) != zh:
            entry["nameDrift"] = {"snapshot": names.get(nid), "wikidata": zh}
            drift += 1

    document = {
        "source": "Wikidata labels via P300 (CN provinces) and P13971 China division code by MCA (prefecture/county)",
        "endpoint": ENDPOINT,
        "retrievedAt": "2026-11-14",
        "license": "CC0-1.0",
        "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "normalization": "seed 4-digit prefecture codes pad with trailing 00 for P13971; county codes join verbatim; grouping nodes and 9-digit townships skipped",
        "locales": list(LOCALES),
        "targetCount": len(targets),
        "matchCount": len(nodes),
        "ambiguousCount": len(ambiguous_total),
        "ambiguousCodes": ambiguous_total,
        "nameDriftCount": drift,
        "nodes": nodes,
    }
    text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(text)
    covered = sum(1 for entry in nodes.values() if entry["labels"])
    print(f"wrote {args.out} ({len(text):,} bytes): targets={len(targets)} "
          f"matched={len(nodes)} with-labels={covered} ambiguous={len(ambiguous_total)} "
          f"nameDrift={drift}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
