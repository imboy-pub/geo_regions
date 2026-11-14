#!/usr/bin/env python3
"""Fetch candidate-layer labels from Wikidata for ISO/dantai-coded volumes.

Companion to tool/fetch_wikidata_fr_labels.py (P374 INSEE). The candidate
countries whose nodes carry real external codes join Wikidata exactly:

- JP: P429 "dantai code" — the 6-digit 全国地方公共団体コード the Geolonia
  layer uses verbatim (jp-city:* nodes);
- GB/IT/RU/DE: P300 ISO 3166-2 codes for the iso3166-2:* subdivision nodes
  (GB-IOW, IT-52, IT-PD, RU-PRI, DE-SH …).

The synthetic CSC codes (csc-city:NNN, csc-county:NNN — US/RU/DE/GB/IT city
and county bulk) have no upstream counterpart; their residual cells belong
to the AI-generation track (tool/gen_seed_residuals.py pattern) or a future
P131 chain-matching pass, NOT to this script.

Staged extracts per country under staging/wikidata-cand/ — never committed
(candidate-layer discipline). Batch caches make reruns resume cleanly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

WORK = Path("staging/wikidata-cand/batches")
OUTDIR = Path("staging/wikidata-cand")
ENDPOINT = "https://query.wikidata.org/sparql"
LOCALES = ("en", "zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar")
QUERY_LANGS = ('"en", "zh-hans", "zh-hant", "zh-tw", "zh-hk", "zh", "ja", "ko", '
               '"ru", "de", "fr", "it", "ar"')
BATCH = 250
RETRIES = 6
USER_AGENT = "geo_regions-candidate-import/1.0 (https://github.com/imboy-pub/geo_regions)"

# {country: [(property, id-prefix filter, code normalizer, staged output)]}
# JP: jp-city nodes carry "JP-<dantai>" — strip the prefix for P429;
#     iso3166-2 nodes (JP-33 prefectures) join via P300 as-is.
COUNTRY_CONFIG = {
    "JP": [
        ("P429", "jp-city:", lambda c: c[3:] if c.startswith("JP-") else c, "jp-labels.json"),
        ("P300", "iso3166-2:", None, "jp-labels.json"),
    ],
    "GB": [("P300", "iso3166-2:", None, "gb-labels.json")],
    "IT": [("P300", "iso3166-2:", None, "it-labels.json")],
    "RU": [("P300", "iso3166-2:", None, "ru-labels.json")],
    "DE": [("P300", "iso3166-2:", None, "de-labels.json")],
}


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
        except Exception as error:
            last_error = error
            wait = 120 * (attempt + 1)
            print(f"  retry {attempt + 1}/{RETRIES} in {wait}s: {error}", flush=True)
            time.sleep(wait)
    raise SystemExit(f"SPARQL failed after {RETRIES} attempts: {last_error}")


def targets_for(root: Path, cc: str) -> dict[str, str]:
    regions = json.loads((root / f"datasets/csc-candidate/data/regions/{cc}.json")
                          .read_text("utf-8"))
    return {n["id"]: n["code"] for n in regions["nodes"] if n["kind"] != "country"}


def reduce_rows(rows: list[dict]) -> dict[str, dict[str, str]]:
    by_qid: dict[str, dict[str, str]] = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        lang = row["label"]["xml:lang"].lower()
        by_qid.setdefault(qid, {})[lang] = row["label"]["value"]
    return by_qid


def pick_labels(langs: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for locale in LOCALES:
        if locale == "zh-Hans":
            candidates = ("zh-hans", "zh-cn", "zh")
        elif locale == "zh-Hant":
            candidates = ("zh-hant", "zh-tw", "zh-hk", "zh")
        else:
            candidates = (locale.lower(),)
        for tag in candidates:
            if tag in langs and langs[tag]:
                out[locale] = langs[tag]
                break
    return out


def fetch_property(prop: str, codes: list[str], work: Path, batch_size: int) -> dict[str, dict]:
    batches = [codes[i:i + batch_size] for i in range(0, len(codes), batch_size)]
    merged: dict[str, dict] = {}
    for index, chunk in enumerate(batches):
        cache = work / f"{prop}-batch-{index:03d}.json"
        if cache.is_file():
            merged.update(json.loads(cache.read_text(encoding="utf-8")))
            continue
        values = " ".join(f'"{code}"' for code in chunk)
        rows = sparql(
            "SELECT ?code ?item ?label WHERE {\n"
            f"  VALUES ?code {{ {values} }}\n"
            f"  ?item wdt:{prop} ?code .\n"
            "  ?item rdfs:label ?label .\n"
            f"  FILTER(LANG(?label) IN ({QUERY_LANGS}))\n"
            "}"
        )
        qid_to_code = {}
        for row in rows:
            qid_to_code[row["item"]["value"].rsplit("/", 1)[-1]] = row["code"]["value"]
        result = {}
        for qid, langs in reduce_rows(rows).items():
            code = qid_to_code.get(qid)
            if code is None:
                continue
            picked = pick_labels(langs)
            if picked and code not in result:
                result[code] = {"qid": qid, "labels": picked}
        cache.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True),
                         encoding="utf-8")
        merged.update(result)
        label_count = sum(len(v["labels"]) for v in result.values())
        print(f"  batch {index + 1}/{len(batches)}: {len(chunk)} codes, "
              f"{len(result)} matched, {label_count} labels", flush=True)
        time.sleep(3)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--batch", type=int, default=BATCH)
    parser.add_argument("--countries", default=",".join(COUNTRY_CONFIG))
    args = parser.parse_args()
    root = args.root

    for cc in args.countries.split(","):
        nodes: dict[str, dict] = {}
        code_total = 0
        for prop, prefix, normalize, out_name in COUNTRY_CONFIG[cc]:
            targets = {nid: code for nid, code in targets_for(root, cc).items()
                       if nid.split(":")[0] + ":" == prefix}
            normalize = normalize or (lambda c: c)
            codes = sorted(set(normalize(code) for code in targets.values()))
            work = WORK / cc
            work.mkdir(parents=True, exist_ok=True)
            print(f"[{cc}/{prop}] {len(targets)} nodes via {prefix} prefix, "
                  f"{len(codes)} codes", flush=True)
            merged = fetch_property(prop, codes, work, args.batch)
            code_to_nodes: dict[str, list[str]] = {}
            for nid, raw_code in targets.items():
                code_to_nodes.setdefault(normalize(raw_code), []).append(nid)
            for code, entry in merged.items():
                for nid in code_to_nodes.get(code, []):
                    nodes[nid] = {"qid": entry["qid"], "labels": entry["labels"]}
            code_total += len(codes)

        document = {
            "source": f"Wikidata labels via {'/'.join(p for p, *_ in COUNTRY_CONFIG[cc])} ({cc} candidate nodes)",
            "endpoint": ENDPOINT,
            "retrievedAt": "2026-11-14",
            "license": "CC0-1.0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
            "locales": list(LOCALES),
            "codeCount": code_total,
            "nodeCount": len(nodes),
            "nodes": nodes,
        }
        text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
        out_path = OUTDIR / COUNTRY_CONFIG[cc][0][3]
        out_path.write_bytes(text)
        covered = sum(1 for e in nodes.values() if e["labels"])
        print(f"[{cc}] wrote {out_path} ({len(text):,} bytes): nodes={len(nodes)} "
              f"with-labels={covered} sha256={hashlib.sha256(text).hexdigest()[:16]}…",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
