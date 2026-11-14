#!/usr/bin/env python3
"""Fetch candidate-layer labels by the QIDs already present in the CSC snapshot.

The pinned CSC snapshot rows carry a `wikiDataId` column (US 75%, DE 97%,
IT 96%, FR 97%, GB 88%, RU 83%, SA 93%, JP 86%, KR 65% of rows) — so for
these nodes no code join is needed at all: the item QID ships with the row.
This closes most of the candidate layer's remaining synthetic-code gap with
community labels (CC0).

Node ids follow the generator's construction: counties → `csc-county:{id}`,
cities → `csc-city:{id}`. QIDs claimed by several rows are dropped (never
guessed). Staged extracts per country under staging/wikidata-qid/ — never
committed (candidate-layer discipline). Batch caches make reruns resume.
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

WORK = Path("staging/wikidata-qid/batches")
OUTDIR = Path("staging/wikidata-qid")
ENDPOINT = "https://query.wikidata.org/sparql"
LOCALES = ("en", "zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar")
QUERY_LANGS = ('"en", "zh-hans", "zh-hant", "zh-tw", "zh-hk", "zh", "ja", "ko", '
               '"ru", "de", "fr", "it", "ar"')
BATCH = 250
RETRIES = 6
USER_AGENT = "geo_regions-candidate-import/1.0 (https://github.com/imboy-pub/geo_regions)"
KIND_NODE_PREFIX = {"counties": "csc-county", "cities": "csc-city"}


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


def qid_targets(root: Path, cc: str) -> dict[str, dict]:
    """{qid: {"nodeIds": [...], "name": str}} from the CSC snapshot rows."""
    out: dict[str, dict] = {}
    for kind, prefix in KIND_NODE_PREFIX.items():
        path = root / f"staging/csc-snapshot/contributions/{kind}/{cc}.json"
        if not path.is_file():
            continue
        for row in json.loads(path.read_text("utf-8")):
            qid = (row.get("wikiDataId") or "").strip()
            if not qid.startswith("Q"):
                continue
            nid = f"{prefix}:{row['id']}"
            entry = out.setdefault(qid, {"nodeIds": [], "name": row["name"]})
            entry["nodeIds"].append(nid)
    return out


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


def fetch_labels(qids: list[str], work: Path, batch_size: int) -> dict[str, dict[str, str]]:
    batches = [qids[i:i + batch_size] for i in range(0, len(qids), batch_size)]
    merged: dict[str, dict[str, str]] = {}
    for index, chunk in enumerate(batches):
        cache = work / f"batch-{index:04d}.json"
        if cache.is_file():
            merged.update(json.loads(cache.read_text(encoding="utf-8")))
            continue
        values = " ".join(f"wd:{qid}" for qid in chunk)
        rows = sparql(
            "SELECT ?item ?label WHERE {\n"
            f"  VALUES ?item {{ {values} }}\n"
            "  ?item rdfs:label ?label .\n"
            f"  FILTER(LANG(?label) IN ({QUERY_LANGS}))\n"
            "}"
        )
        result = {}
        for qid, langs in reduce_rows(rows).items():
            picked = pick_labels(langs)
            if picked:
                result[qid] = picked
        cache.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True),
                         encoding="utf-8")
        merged.update(result)
        print(f"  batch {index + 1}/{len(batches)}: {len(chunk)} qids, "
              f"{len(result)} with labels", flush=True)
        time.sleep(3)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--batch", type=int, default=BATCH)
    parser.add_argument("--countries", default="US,DE,IT,GB,RU,SA,KR")
    args = parser.parse_args()
    root = args.root

    for cc in args.countries.split(","):
        targets = qid_targets(root, cc)
        qids = sorted(targets)
        work = WORK / cc
        work.mkdir(parents=True, exist_ok=True)
        print(f"[{cc}] {len(targets)} qid-bearing rows", flush=True)

        labels = fetch_labels(qids, work, args.batch)
        nodes: dict[str, dict] = {}
        for qid, picked in labels.items():
            for nid in targets[qid]["nodeIds"]:
                nodes[nid] = {"qid": qid, "labels": picked}
        document = {
            "source": f"Wikidata labels by QID (CSC snapshot wikiDataId column, {cc} rows)",
            "endpoint": ENDPOINT,
            "retrievedAt": "2026-11-14",
            "license": "CC0-1.0",
            "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
            "locales": list(LOCALES),
            "qidCount": len(qids),
            "nodeCount": len(nodes),
            "nodes": nodes,
        }
        text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
        out_path = OUTDIR / f"{cc.lower()}-labels.json"
        out_path.write_bytes(text)
        print(f"[{cc}] wrote {out_path} ({len(text):,} bytes): nodes={len(nodes)} "
              f"sha256={hashlib.sha256(text).hexdigest()[:16]}…", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
