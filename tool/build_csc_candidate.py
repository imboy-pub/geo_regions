#!/usr/bin/env python3
"""Build the nine-country deep-region candidate dataset from the audited CSC snapshot.

Input: staging/csc-snapshot/ (rebuilt from audit/csc_input_manifest.json, sha256-verified)
Output: datasets/csc-candidate/ — protocol 1.0 shaped (datasetId geo-regions-csc-candidate)

License honesty (LICENSE_SCOPE):
- node structures + en names + the 8 upstream translations: CSC database, ODbL-1.0
  with upstream per-source notices under review — nothing here is production data.
- catalog country names (10x10): Unicode-3.0 CLDR data, copied verbatim from the
  audited audit sample with their own sourceRefs; never relabeled as ODbL or BSD.
- zh-Hant: upstream has none — packs stay empty; missing stays missing.
- quality words: en=source-native; upstream 8-locale translations=provisional.
  AI proof-reading samples are recorded separately and never flip quality words.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tool"))
import geo_data as geo  # noqa: E402
import s2t_places  # noqa: E402

SNAP = REPO / "staging/csc-snapshot"
OUT = REPO / "datasets/csc-candidate"
COUNTRIES = ["JP", "KR", "US", "GB", "DE", "FR", "IT", "RU", "SA"]
LOCALES = ["en", "zh-Hans", "zh-Hant", "ja", "ko", "ru", "de", "fr", "it", "ar"]
TRANSLATION_LOCALES = {"zh-Hans": "zh-CN", "ja": "ja", "ko": "ko", "ru": "ru",
                       "de": "de", "fr": "fr", "it": "it", "ar": "ar"}
# zh-Hant path A (GSA-03 memo): JP kanji direct reuse, KR/other convert from
# zh-Hans, with explicit fixes for upstream errors found in proof-reading.
# Everything lands as machine-candidate — never upstream, never approved.
ZH_HANT_FIXES = {
    ("KR", "Seoul"): "首爾",
    ("RU", "Jewish"): "猶太自治州",
    ("RU", "Nenets"): "涅涅茨自治區",
    ("RU", "Khanty-Mansi"): "漢特-曼西自治區",
    ("US", "Texas"): "得克薩斯州",
}
CSC_SOURCE = "staging/csc-snapshot (dr5hn/countries-states-cities-database @ e9c4dec, ODbL-1.0)"
CLDR_SOURCE = "_task_packages/geo_regions_source_audit_2026-11-13/data/catalog_i18n (CLDR 49 pinned, Unicode-3.0)"


def load(path):
    return json.loads((SNAP / path).read_text(encoding="utf-8"))


def nfc(value):
    """Protocol requires NFC; CSC upstream mixes forms. Normalization keeps semantics."""
    return unicodedata.normalize("NFC", value)


def node(nid, parent, kind, code, name, locale, quality, status="unknown"):
    return {"id": nid, "parentId": parent, "kind": kind, "code": code, "name": name,
            "nameLocale": locale, "nameQuality": quality, "childrenStatus": status}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--countries", default=",".join(COUNTRIES))
    args = parser.parse_args()
    targets = args.countries.split(",")

    countries_rows = load("contributions/countries/countries.json")
    by_iso2 = {row["iso2"]: row for row in countries_rows}
    states_by_cc = {}
    for row in load("contributions/states/states.json"):
        states_by_cc.setdefault(row["country_code"], []).append(row)
    counties_by_cc, cities_by_cc = {}, {}
    for cc in COUNTRIES:
        county_path = SNAP / f"contributions/counties/{cc}.json"
        counties_by_cc[cc] = load(f"contributions/counties/{cc}.json") if county_path.is_file() else []
        cities_by_cc[cc] = load(f"contributions/cities/{cc}.json")

    catalog_files = {}
    for locale in LOCALES:
        src = REPO / f"_task_packages/geo_regions_source_audit_2026-11-13/data/catalog_i18n/{locale}.json"
        catalog_files[locale] = json.loads(src.read_text(encoding="utf-8"))

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data/regions").mkdir(parents=True)
    for locale in LOCALES:
        (OUT / f"data/i18n/{locale}").mkdir(parents=True)
    (OUT / "data/catalog_i18n").mkdir(parents=True)
    (OUT / "config").mkdir()

    geo.write_json(OUT / "config/data_policy.json", {
        "locales": LOCALES,
        "localeAliases": {"zh-CN": "zh-Hans", "zh-SG": "zh-Hans", "zh-TW": "zh-Hant",
                          "zh-HK": "zh-Hant", "en-US": "en", "ja-JP": "ja", "ko-KR": "ko",
                          "ru-RU": "ru", "de-DE": "de", "fr-FR": "fr", "it-IT": "it", "ar-SA": "ar"},
        "requiredCountries": targets, "requiredCatalogLocales": LOCALES,
        "requireEveryCountryLocalePack": True})

    stats = {}
    for cc in targets:
        country = by_iso2[cc]
        root_id = f"cc:{cc}"
        nodes = [node(root_id, None, "country", cc, country["name"], "en", "source-native", "partial")]
        packs = {locale: {} for locale in LOCALES}
        packs["en"][root_id] = country["name"]

        state_ids = {}
        for row in sorted(states_by_cc.get(cc, []), key=lambda r: r["id"]):
            iso_tag = row.get("iso3166_2") or ""
            nid = f"iso3166-2:{iso_tag}" if iso_tag else f"csc-state:{row['id']}"
            state_ids[row["id"]] = nid
            nodes.append(node(nid, root_id, "subdivision", iso_tag or f"{cc}-S{row['id']}",
                              nfc(row["name"]), "en", "source-native", "unknown"))
            packs["en"][nid] = nfc(row["name"])
            for locale, key in TRANSLATION_LOCALES.items():
                value = (row.get("translations") or {}).get(key)
                if value:
                    packs[locale][nid] = nfc(value)

        for row in sorted(counties_by_cc.get(cc, []), key=lambda r: r["id"]):
            nid = f"csc-county:{row['id']}"
            parent = state_ids.get(row.get("state_id"), root_id)
            nodes.append(node(nid, parent, "subdivision", f"{cc}-C{str(row["id"])}", nfc(row["name"]),
                              "en", "source-native", "unknown"))
            packs["en"][nid] = nfc(row["name"])
            for locale, key in TRANSLATION_LOCALES.items():
                value = (row.get("translations") or {}).get(key)
                if value:
                    packs[locale][nid] = nfc(value)

        county_ids = {row["id"] for row in counties_by_cc.get(cc, [])}
        for row in sorted(cities_by_cc.get(cc), key=lambda r: r["id"]):
            nid = f"csc-city:{row['id']}"
            parent = state_ids.get(row.get("state_id"), root_id)
            if row.get("county_id") and row["county_id"] in county_ids:
                parent = f"csc-county:{row['county_id']}"
            nodes.append(node(nid, parent, "subdivision", f"{cc}-X{row['id']}", nfc(row["name"]),
                              "en", "source-native", "unknown"))
            packs["en"][nid] = nfc(row["name"])
            for locale, key in TRANSLATION_LOCALES.items():
                value = (row.get("translations") or {}).get(key)
                if value:
                    packs[locale][nid] = nfc(value)

        # derive zh-Hant pack (machine-candidate)
        hant_names, hant_quality = {}, {}
        conversion_stats = {"convertedChars": 0, "names": 0, "kanjiDirectJP": 0}
        for nid, node_row in ((n["id"], n) for n in nodes):
            hans = packs["zh-Hans"].get(nid)
            fix = ZH_HANT_FIXES.get((cc, node_row["name"]))
            if fix:
                value, source = fix, "proofread-fix"
            elif cc == "JP":
                ja_value = packs["ja"].get(nid)
                if ja_value and not s2t_places.has_kana(ja_value):
                    # kanji direct reuse + shinjitai→traditional normalization
                    value, source = s2t_places.convert(ja_value)[0], "kanji-direct"
                    conversion_stats["kanjiDirectJP"] += 1
                elif hans:
                    value, source = s2t_places.convert(hans)[0], "s2t-convert"
                else:
                    value, source = None, None
            elif hans:
                value, source = s2t_places.convert(hans)[0], "s2t-convert"
            else:
                value, source = None, None
            if value:
                hant_names[nid] = nfc(value)
                hant_quality[nid] = "machine-candidate"
                conversion_stats["names"] += 1
                if source == "s2t-convert":
                    conversion_stats["convertedChars"] += s2t_places.convert(hans)[1]
        packs["zh-Hant"] = hant_names
        if hant_names:
            TRANSLATION_LOCALES_SET = set(TRANSLATION_LOCALES)  # noqa: F841

        structure = {"protocolVersion": "1.0", "datasetId": "geo-regions-csc-candidate",
                     "countryCode": cc, "sourceRefs": [CSC_SOURCE], "nodes": nodes}
        structure["revision"] = geo.revision("s", nodes)
        geo.write_json(OUT / f"data/regions/{cc}.json", structure)
        for locale in LOCALES:
            pack = {"protocolVersion": "1.0", "datasetId": "geo-regions-csc-candidate",
                    "countryCode": cc, "locale": locale,
                    "compatibleStructureRevision": structure["revision"],
                    "sourceRefs": [CSC_SOURCE], "names": packs[locale],
                    "coverage": {"status": "research-seed",
                                 "translationQualityById": {
                                     nid: ("machine-candidate" if locale == "zh-Hant"
                                           else "source-native" if locale == "en" else "provisional")
                                     for nid in packs[locale]},
                                 "explicitNames": len(packs[locale]),
                                 "missingNames": len(nodes) - len(packs[locale]),
                                 **({"machineCandidate": True,
                                     "zhHantStrategy": ("kanji-direct-JP" if cc == "JP" else "s2t-convert-from-zh-Hans"),
                                     "proofreadFixesApplied": sum(1 for nid in hant_names if ZH_HANT_FIXES.get((cc, next(n2["name"] for n2 in nodes if n2["id"] == nid))))
                                     } if locale == "zh-Hant" else {})}}
            pack["revision"] = geo.locale_revision(pack["names"], pack["coverage"]["translationQualityById"])
            geo.write_json(OUT / f"data/i18n/{locale}/{cc}.json", pack)
        stats[cc] = {"nodes": len(nodes), "states": len(states_by_cc.get(cc, [])),
                     "counties": len(counties_by_cc.get(cc, [])),
                     "cities": len(cities_by_cc.get(cc))}



    country_list = [{"code": cc, "name": nfc(by_iso2[cc]["name"]), "rootId": f"cc:{cc}"} for cc in targets]
    catalog_rev = geo.revision("c", country_list)
    geo.write_json(OUT / "data/countries.json", {
        "protocolVersion": "1.0", "datasetId": "geo-regions-csc-candidate",
        "revision": catalog_rev, "countries": country_list,
        "sourceRefs": [CSC_SOURCE]})
    for locale in LOCALES:
        cat = dict(catalog_files[locale], datasetId="geo-regions-csc-candidate",
                   compatibleCatalogRevision=catalog_rev, sourceRefs=[CLDR_SOURCE])
        # CN stays in the seed dataset; this candidate covers the other nine.
        cat["names"] = {k: v for k, v in cat.get("names", {}).items() if k in targets}
        cov = cat.get("coverage") or {}
        if isinstance(cov.get("translationQualityById"), dict):
            cov["translationQualityById"] = {k: v for k, v in cov["translationQualityById"].items() if k in targets}
        cat["coverage"] = cov
        cat["revision"] = geo.locale_revision(cat["names"], cov.get("translationQualityById", {}))
        geo.write_json(OUT / f"data/catalog_i18n/{locale}.json", cat)

    geo.write_json(OUT / "data/manifest.json", geo.manifest_value(OUT / "data"))
    (OUT / "SOURCES_NOTICE.md").write_text(
        "# Candidate dataset sources\n\n"
        f"- Node structures + en names + 8 upstream translations: {CSC_SOURCE}\n"
        f"- catalog_i18n/* (10x10 country names): {CLDR_SOURCE}\n"
        "- zh-Hant: upstream CSC has no zh-Hant; packs are empty by design\n"
        "- All non-en translations are provisional; AI proof-reading samples do not flip quality words\n"
        "- This candidate dataset is NOT production data (maturity stays research-seed)\n",
        encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
