#!/usr/bin/env python3
"""Extract candidate-layer labels from GeoNames alternateNamesV2.

Final untried evidence channel for the candidate layer's residual cells
(small towns whose Wikidata items lack ja/ko/ar/ru labels and whose CSC
rows carry no translation). The join needs no SPARQL: alternateNamesV2
contains `wkdt`-tagged rows whose value IS the Wikidata QID, and the CSC
snapshot rows already carry wikiDataId — so one download + two streaming
passes replace the whole QID->P1566 chain:

  CSC row.wikiDataId (or staged FR/JP qid->nid bridges)
    -> wkdt row in alternateNamesV2 -> geonameid
    -> all alternateNames rows for that geonameid -> ja/ko/ar/ru/... labels

Community translations of varying depth: quality stays provisional in the
generator, license CC-BY-4.0 (attribution), staged extracts never committed.
FR/JP node ids come from the staged Wikidata bridges (INSEE / dantai joins);
csc-* countries use the direct `csc-city:{id}` / `csc-county:{id}` ids.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

WORK = Path("staging/geonames-alt")
DUMP = WORK / "alternateNamesV2.zip"
UPSTREAM_URL = "https://download.geonames.org/export/dump/alternateNamesV2.zip"
LOCALES = ("zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar")
# GeoNames isolanguage tags per project locale (order = fallback priority;
# plain "zh" is the ambiguous last resort for both zh locales, mirroring the
# Wikidata pick_labels chain).
LANG_CANDIDATES = {
    "zh-Hans": ("zh-CN", "zh-Hans"),
    "zh-Hant": ("zh-TW", "zh-HK", "zh-Hant"),
    "ja": ("ja",), "ko": ("ko",), "ru": ("ru",), "de": ("de",),
    "fr": ("fr",), "it": ("it",), "ar": ("ar",),
}
ZH_FALLBACK = "zh"


def qid_targets(root: Path) -> dict[str, dict[str, str]]:
    """{qid: {nid: country}} — CSC rows direct + FR/JP staged qid->nid bridges.

    FR/JP candidate nodes live in fr-commune:*/jp-city:* id spaces, so their
    direct CSC-row ids (csc-city:*) are useless as node keys — those two
    countries register ONLY through their staged bridge files.
    """
    out: dict[str, dict[str, str]] = {}
    bridges = {
        "FR": root / "staging/wikidata-fr/fr-labels.json",
        "JP": root / "staging/wikidata-cand/jp-labels.json",
    }
    for cc in ("US", "DE", "IT", "GB", "RU", "SA", "KR", "FR", "JP"):
        if cc not in bridges:
            for kind, prefix in (("cities", "csc-city"), ("counties", "csc-county")):
                path = root / f"staging/csc-snapshot/contributions/{kind}/{cc}.json"
                if not path.is_file():
                    continue
                for row in json.loads(path.read_text("utf-8")):
                    qid = (row.get("wikiDataId") or "").strip()
                    if qid.startswith("Q"):
                        out.setdefault(qid, {}).setdefault(f"{prefix}:{row['id']}", cc)
        bridge = bridges.get(cc)
        if bridge is not None and bridge.is_file():
            data = json.loads(bridge.read_text("utf-8"))
            for nid, entry in data["nodes"].items():
                out.setdefault(entry["qid"], {}).setdefault(nid, cc)
    return out


def pick_labels(rows: list[tuple[int, int, int, str]]) -> dict[str, str]:
    """rows = (preferred, short, nameId, name); tag lookup via LANG_TAGS."""
    by_tag: dict[str, list[tuple[int, int, int, str]]] = {}
    for preferred, short, name_id, name in rows:
        by_tag.setdefault(LANG_TAGS[name_id], []).append((preferred, short, name_id, name))
    out: dict[str, str] = {}
    for locale in LOCALES:
        candidates: list[tuple[int, int, int, str]] = []
        for tag in LANG_CANDIDATES[locale]:
            candidates.extend(by_tag.get(tag, []))
        if locale in ("zh-Hans", "zh-Hant"):
            candidates.extend(by_tag.get(ZH_FALLBACK, []))
        if not candidates:
            continue
        # preferred first, then non-short, then shortest text, then lowest id
        best = min(candidates, key=lambda r: (not r[0], not r[1], len(r[3]), r[2]))
        out[locale] = best[3]
    return out


LANG_TAGS: dict[int, str] = {}


def main() -> int:
    global LANG_TAGS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root

    if not DUMP.is_file():
        raise SystemExit(f"missing {DUMP} — download {UPSTREAM_URL} first")
    sha = hashlib.sha256(DUMP.read_bytes()).hexdigest()
    size = DUMP.stat().st_size
    print(f"dump: {size:,} bytes sha256={sha[:16]}…", flush=True)

    targets = qid_targets(root)
    print(f"targets: {len(targets)} qids from 9 countries", flush=True)

    # the zip ships several .txt members (language catalog, readme) — the main
    # dump is simply the largest one
    with zipfile.ZipFile(DUMP) as zf:
        name = max((n for n in zf.namelist() if n.endswith(".txt")),
                   key=lambda n: zf.getinfo(n).file_size)
        print(f"member: {name} ({zf.getinfo(name).file_size:,} bytes uncompressed)", flush=True)

    # pass 1: wkdt rows -> geonameid per qid
    qid_geonameid: dict[str, int] = {}
    with zipfile.ZipFile(DUMP) as zf:
        with io.TextIOWrapper(zf.open(name), encoding="utf-8", errors="replace") as fh:
            for line in fh:
                fields = line.rstrip("\n").split("\t")
                if len(fields) < 4 or fields[2] != "wkdt":
                    continue
                qid = fields[3]
                if qid in targets and qid not in qid_geonameid:
                    try:
                        qid_geonameid[qid] = int(fields[1])
                    except ValueError:
                        continue
    hit = len(qid_geonameid)
    print(f"pass 1: {hit}/{len(targets)} qids matched wkdt rows", flush=True)

    # pass 2: collect alt-name rows for the hit geonameids (skip colloquial/historic)
    geonames = set(qid_geonameid.values())
    LANG_TAGS = {}
    per_gid: dict[int, dict[str, list[tuple[int, int, int, str]]]] = {}
    wanted_langs = {t for cands in LANG_CANDIDATES.values() for t in cands} | {ZH_FALLBACK}
    with zipfile.ZipFile(DUMP) as zf:
        with io.TextIOWrapper(zf.open(name), encoding="utf-8", errors="replace") as fh:
            for line_no, line in enumerate(fh, 1):
                fields = line.rstrip("\n").split("\t")
                if len(fields) < 4:
                    continue
                try:
                    gid = int(fields[1])
                except ValueError:
                    continue
                if gid not in geonames or fields[2] not in wanted_langs:
                    continue
                try:
                    preferred = int(fields[4] or "0") if len(fields) > 4 else 0
                    short = int(fields[5] or "0") if len(fields) > 5 else 0
                    colloquial = int(fields[6] or "0") if len(fields) > 6 else 0
                    historic = int(fields[7] or "0") if len(fields) > 7 else 0
                except ValueError:
                    preferred = short = colloquial = historic = 0
                if colloquial or historic:
                    continue
                LANG_TAGS[line_no] = fields[2]
                per_gid.setdefault(gid, {}).setdefault(
                    fields[2], []).append((preferred, short, line_no, fields[3]))

    # assemble per-country staged extracts
    docs: dict[str, dict] = {cc: {"nodes": {}} for cc in
                             ("US", "DE", "IT", "GB", "RU", "SA", "KR", "FR", "JP")}
    for qid, gid in qid_geonameid.items():
        tags = per_gid.get(gid, {})
        flat = [row for rows in tags.values() for row in rows]
        labels = pick_labels(flat)
        if not labels:
            continue
        for nid, cc in targets[qid].items():
            docs[cc]["nodes"][nid] = {"qid": qid, "geonameid": gid, "labels": labels}

    for cc, doc in docs.items():
        document = {
            "source": f"GeoNames alternateNamesV2 join via CSC wikiDataId -> wkdt rows ({cc} candidate nodes)",
            "upstream": {"url": UPSTREAM_URL, "sha256": sha, "sizeBytes": size},
            "retrievedAt": "2026-11-14",
            "license": "CC-BY-4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "locales": list(LOCALES),
            "nodeCount": len(doc["nodes"]),
            "nodes": doc["nodes"],
        }
        text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
        out_path = WORK / f"{cc.lower()}-labels.json"
        out_path.write_bytes(text)
        print(f"[{cc}] wrote {out_path} ({len(text):,} bytes): nodes={len(doc['nodes'])} "
              f"sha256={hashlib.sha256(text).hexdigest()[:16]}…", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
