#!/usr/bin/env python3
"""Fetch FR candidate-layer labels from Wikidata via P374 (INSEE codes).

The candidate dataset's FR communes/departments/regions carry 5-digit INSEE
codes as their `code` field; Wikidata stores the same codes in P374, so the
join is exact (zero homonym risk) and CC0-licensed. This fills the largest
translation gap in the candidate layer (FR × 9 locales ≈ 220k cells) with
community labels instead of AI generation.

The extract is a STAGED artifact (staging/wikidata-fr/), never committed —
the candidate layer body is regenerable and stays out of git by the repo
slimming decision. The batch cache inside the work directory makes reruns
resume after rate-limit interruptions.

Per-batch labels are filtered in-query to the project locales (plus plain
"zh" as a fallback for items lacking explicit zh-Hans/zh-Hant labels).
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

WORK = Path("staging/wikidata-fr/batches")
OUT = Path("staging/wikidata-fr/fr-labels.json")
ENDPOINT = "https://query.wikidata.org/sparql"
LOCALES = ("en", "zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar")
QUERY_LANGS = '"en", "zh-hans", "zh-hant", "zh-tw", "zh-hk", "zh", "ja", "ko", "ru", "de", "fr", "it", "ar"'
BATCH = 250
RETRIES = 6
USER_AGENT = "geo_regions-candidate-import/1.0 (https://github.com/imboy-pub/geo_regions)"


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
        except Exception as error:  # 429 / SSL EOF / timeouts — back off hard
            last_error = error
            wait = 120 * (attempt + 1)
            print(f"  retry {attempt + 1}/{RETRIES} in {wait}s: {error}", flush=True)
            time.sleep(wait)
    raise SystemExit(f"SPARQL failed after {RETRIES} attempts: {last_error}")


def fr_targets(root: Path) -> dict[str, str]:
    """{nodeId: INSEE code} for every non-country FR node."""
    regions = json.loads((root / "datasets/csc-candidate/data/regions/FR.json")
                          .read_text("utf-8"))
    return {n["id"]: n["code"] for n in regions["nodes"] if n["kind"] != "country"}


def reduce_rows(rows: list[dict]) -> dict[str, dict[str, str]]:
    """{qid: {lang: text}} from SPARQL rows."""
    by_qid: dict[str, dict[str, str]] = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        lang = row["label"]["xml:lang"].lower()
        text = row["label"]["value"]
        by_qid.setdefault(qid, {})[lang] = text
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--batch", type=int, default=BATCH)
    args = parser.parse_args()
    root = args.root
    targets = fr_targets(root)
    codes = sorted(set(targets.values()))
    print(f"targets: {len(targets)} nodes, {len(codes)} distinct INSEE codes", flush=True)

    code_to_nodes: dict[str, list[str]] = {}
    for nid, code in targets.items():
        code_to_nodes.setdefault(code, []).append(nid)

    WORK.mkdir(parents=True, exist_ok=True)
    batches = [codes[i:i + args.batch] for i in range(0, len(codes), args.batch)]
    for index, chunk in enumerate(batches):
        cache = WORK / f"batch-{index:03d}.json"
        if cache.is_file():
            continue
        values = " ".join(f'"{code}"' for code in chunk)
        query = (
            "SELECT ?code ?item ?label WHERE {\n"
            f"  VALUES ?code {{ {values} }}\n"
            "  ?item wdt:P374 ?code .\n"
            "  ?item rdfs:label ?label .\n"
            f"  FILTER(LANG(?label) IN ({QUERY_LANGS}))\n"
            "}"
        )
        rows = sparql(query)
        by_qid = reduce_rows(rows)
        qid_to_code = {}
        for row in rows:
            qid_to_code[row["item"]["value"].rsplit("/", 1)[-1]] = row["code"]["value"]
        result = {}
        for qid, langs in by_qid.items():
            code = qid_to_code.get(qid)
            if code is None:
                continue
            picked = pick_labels(langs)
            if picked and code not in result:
                result[code] = {"qid": qid, "labels": picked}
        cache.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True),
                         encoding="utf-8")
        matched_labels = sum(len(v["labels"]) for v in result.values())
        print(f"batch {index + 1}/{len(batches)}: {len(chunk)} codes, "
              f"{len(result)} matched, {matched_labels} labels", flush=True)
        time.sleep(3)  # gentle pacing between batches

    merged: dict[str, dict] = {}
    for cache in sorted(WORK.glob("batch-*.json")):
        merged.update(json.loads(cache.read_text(encoding="utf-8")))

    nodes: dict[str, dict] = {}
    for code, entry in merged.items():
        for nid in code_to_nodes.get(code, []):
            nodes[nid] = {"qid": entry["qid"], "labels": entry["labels"]}

    document = {
        "source": "Wikidata labels via P374 (INSEE municipality/department/region codes)",
        "endpoint": ENDPOINT,
        "retrievedAt": "2026-11-14",
        "license": "CC0-1.0",
        "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "locales": list(LOCALES),
        "codeCount": len(codes),
        "matchCount": len(merged),
        "nodeCount": len(nodes),
        "nodes": nodes,
    }
    text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    OUT.write_bytes(text)
    covered = sum(1 for e in nodes.values() if e["labels"])
    print(f"wrote {OUT} ({len(text):,} bytes): nodes={len(nodes)} "
          f"with-labels={covered} sha256={hashlib.sha256(text).hexdigest()[:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
