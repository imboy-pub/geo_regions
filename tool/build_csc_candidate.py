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
# Upstream machine-translation leakage: city names rendered as common nouns
# (RU "Sistema"→系统, FR "Tagliatelle"→扁面条 …). Dropped; missing stays missing.
# IT state-code form fix: one retired numeric code → current ISO letter code
# (Wikidata: IT-AO = provincia di Aosta; CSC used the retired IT-23).
# NOTE: IT-S5830..S5833 are Sardinian internal-reform consortia (Gallura
# Nord-Est etc.) whose exact current ISO counterparts need the ISTAT file —
# mapping them (e.g. S5830 → IT-SU Sud Sardegna) was WRONG and reverted:
# S5830's entity is Gallura Nord-Est, not Sud Sardegna. OPEN pending ISTAT.
# Sardinia's four abolished provinces (CI/OG/OT/VS) are correctly ABSENT.
IT_CODE_FIXES = {"IT-23": "IT-AO"}
def fix_zh_suffix(en_name: str, zh_value: str):
    """Round-1 rules, now in-generator so regeneration keeps them:
    'Ageo Shi'→上尾史 becomes 上尾市; 'X Gun' 枪→郡; latin pass-through
    posing as zh is returned as None (missing stays missing)."""
    import re as _re
    if zh_value == en_name and _re.fullmatch(r"[A-Za-z `'\u2019\-]+", zh_value):
        return None
    if _re.search(r"[-_ ]?shi$", en_name, _re.I) and zh_value.endswith(("史", "士")):
        return zh_value[:-1] + "市"
    if _re.search(r"[-_ ]?gun$", en_name, _re.I) and zh_value.endswith("枪"):
        return zh_value[:-1] + "郡"
    return zh_value


ZH_GARBAGE_DROPS = {
    "csc-city:112126", "csc-city:112127", "csc-city:127553",  # US 钟声/面积
    "fr-commune:2B143",                                        # FR 扁面条
    "csc-city:137393",                                         # IT 系列
    "csc-city:101733", "csc-city:102272", "csc-city:99529",    # RU 系统/上系统/学习管理系统
}
# Confirmed upstream errors in zh-Hans packs (AI proof-reading round 1/3):
# values rewritten and quality flipped to machine-candidate — never approved.
# Japanese sisters of the RU truncation errors (same proof-reading rounds)
JA_FIXES = {
    ("RU", "Jewish"): "ユダヤ自治州",
    ("RU", "Nenets"): "ネネツ自治管区",
}
ZH_HANS_FIXES = {
    ("KR", "Seoul"): "首尔",
    ("RU", "Jewish"): "犹太自治州",
    ("RU", "Nenets"): "涅涅茨自治区",
    ("RU", "Khanty-Mansi"): "汉特-曼西自治区",
    ("US", "Texas"): "得克萨斯州",
}
ZH_HANT_FIXES = {
    ("KR", "Seoul"): "首爾",
    ("RU", "Jewish"): "猶太自治州",
    ("RU", "Nenets"): "涅涅茨自治區",
    ("RU", "Khanty-Mansi"): "漢特-曼西自治區",
    ("US", "Texas"): "得克薩斯州",
}
# 2026-current official layers (GSA-02 staged, sha256-pinned) replace the
# stale/partial CSC layers for FR (12% pre-merger communes) and JP (only
# ~65% of municipalities, kana-contaminated ja field).
INSEE_SOURCE = "staging/FR-insee-cog (INSEE Code Officiel Geographique millesime 2026, Licence Ouverte 2.0, current as of 2026-01-01)"
GEOLONIA_SOURCE = "staging/JP-geolonia (japanese-addresses-v2 ja.json, CC-BY-4.0, generated 2024-12-25; municipalities stable through 2026)"
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


def csc_translation_index(cc):
    """Map normalized names (ja/native/en) to CSC translations for inheritance."""
    idx = {}
    import unicodedata
    norm = lambda s: unicodedata.normalize("NFC", (s or "")).strip().lower()
    rows = load(f"contributions/cities/{cc}.json")
    states_path = SNAP / "contributions/states/states.json"
    if states_path.is_file():
        rows = rows + [r for r in json.loads(states_path.read_text(encoding="utf-8"))
                       if r.get("country_code") == cc]
    for row in rows:
        trans = row.get("translations") or {}
        for key in (row.get("name"), row.get("native"), trans.get("ja")):
            if key and norm(key) not in idx:
                idx[norm(key)] = trans
    return idx


def official_2026_layers():
    """Load INSEE FR (region/dept/commune) and Geolonia JP municipalities."""
    import csv
    import unicodedata
    nfc = lambda s: unicodedata.normalize("NFC", s)
    regions, depts, communes = [], [], []
    with (SNAP.parent / "FR-insee-cog/region_2026.csv").open(encoding="utf-8") as f:
        regions = list(csv.DictReader(f))
    with (SNAP.parent / "FR-insee-cog/departement_2026.csv").open(encoding="utf-8") as f:
        depts = list(csv.DictReader(f))
    with (SNAP.parent / "FR-insee-cog/commune_depuis_1943.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["TYPECOM"] in ("COM", "ARM") and not row["DATE_FIN"]:
                communes.append(row)
    geo = json.loads((SNAP.parent / "JP-geolonia/ja.json").read_text(encoding="utf-8"))
    jp_munis = []
    for i, pref in enumerate(geo["data"]):
        iso = f"JP-{i+1:02d}"
        for city in pref.get("cities", []):
            jp_munis.append({"iso": iso, "code": str(city["code"]), "city": city["city"],
                             "romaji": city.get("city_r"), "kana": city.get("city_k"),
                             "point": city.get("point")})
    return nfc, regions, depts, communes, jp_munis


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

    # Only clear generator-owned subtrees; root-level documents
    # (PROOFREADING_REPORT.md, DATA_VERIFICATION_2026.md, samples) survive.
    if (OUT / "data").exists():
        shutil.rmtree(OUT / "data")
    if (OUT / "config").exists():
        shutil.rmtree(OUT / "config")
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

    nfc, insee_regions, insee_depts, insee_communes, jp_munis = official_2026_layers()
    stats = {}
    for cc in targets:
        country = by_iso2[cc]
        root_id = f"cc:{cc}"
        nodes = [node(root_id, None, "country", cc, country["name"], "en", "source-native", "partial")]
        packs = {locale: {} for locale in LOCALES}
        packs["en"][root_id] = country["name"]
        country_trans = country.get("translations") or {}
        for locale in LOCALES:
            # CLDR catalog names win (higher-trust source); CSC translations fallback
            v = catalog_files[locale]["names"].get(cc) or country_trans.get(TRANSLATION_LOCALES.get(locale, ""))
            if v:
                packs[locale][root_id] = nfc(v)
                if locale in ("zh-Hans", "zh-Hant"):
                    packs.setdefault("_hant_qualified", set()).add(root_id)

        state_ids = {}
        kr_fix = None
        if cc == "KR":
            fake = [r for r in states_by_cc[cc] if "Integrated" in r["name"]]
            kr_fix = fake[0] if fake else None
            states_by_cc[cc] = [r for r in states_by_cc[cc] if kr_fix is None or r["id"] != kr_fix["id"]]
            states_by_cc[cc].extend([
                {"id": 17000000, "name": "South Jeolla", "iso2": "17", "iso3166_2": "KR-46",
                 "type": "province", "level": 1, "parent_id": None,
                 "translations": {"zh-CN": "全罗南道", "ja": "全羅南道", "ko": "전라남도"}},
                {"id": 18000000, "name": "Gwangju", "iso2": "18", "iso3166_2": "KR-29",
                 "type": "metropolitan city", "level": 1, "parent_id": None,
                 "translations": {"zh-CN": "光州", "ja": "光州", "ko": "광주"}}])
            # corrections carry their provenance in the node rows below
        for row in sorted(states_by_cc.get(cc, []), key=lambda r: r["id"]):
            iso_tag = row.get("iso3166_2") or ""
            if cc == "IT":
                iso_tag = IT_CODE_FIXES.get(iso_tag, iso_tag)
            nid = f"iso3166-2:{iso_tag}" if iso_tag else f"csc-state:{row['id']}"
            state_ids[row["id"]] = nid
            nodes.append(node(nid, root_id, "subdivision", iso_tag or f"{cc}-S{row['id']}",
                              nfc(row["name"]), "en", "source-native", "unknown"))
            packs["en"][nid] = nfc(row["name"])
            hans_fix = ZH_HANS_FIXES.get((cc, row["name"]))
            ja_fix = JA_FIXES.get((cc, row["name"]))
            for locale, key in TRANSLATION_LOCALES.items():
                if locale == "zh-Hans" and hans_fix:
                    packs[locale][nid] = nfc(hans_fix)
                    packs.setdefault("_zh_fixed", {})[nid] = True
                    continue
                if locale == "ja" and ja_fix:
                    packs[locale][nid] = nfc(ja_fix)
                    packs.setdefault("_ja_fixed", {})[nid] = True
                    continue
                value = (row.get("translations") or {}).get(key)
                if value and nid not in ZH_GARBAGE_DROPS:
                    packs[locale][nid] = nfc(value)

        for row in sorted(counties_by_cc.get(cc, []), key=lambda r: r["id"]):
            nid = f"csc-county:{row['id']}"
            parent = state_ids.get(row.get("state_id"), root_id)
            nodes.append(node(nid, parent, "subdivision", f"{cc}-C{str(row["id"])}", nfc(row["name"]),
                              "en", "source-native", "unknown"))
            packs["en"][nid] = nfc(row["name"])
            for locale, key in TRANSLATION_LOCALES.items():
                value = (row.get("translations") or {}).get(key)
                if value and nid not in ZH_GARBAGE_DROPS:
                    packs[locale][nid] = nfc(value)

        county_ids = {row["id"] for row in counties_by_cc.get(cc, [])}
        if cc == "JP":
            csc_idx = csc_translation_index(cc)
            source_refs_jp = [GEOLONIA_SOURCE, CSC_SOURCE]
            for m in sorted(jp_munis, key=lambda r: r["code"]):
                nid = f"jp-city:{m['code']}"
                en_name = m["romaji"] or m["city"]
                nodes.append(node(nid, f"iso3166-2:{m['iso']}", "subdivision",
                                  f"JP-{m['code'][-2:]}" if False else f"JP-{m['code']}",
                                  nfc(en_name), "en", "source-native", "unknown"))
                packs["en"][nid] = nfc(en_name)
                inherited = (csc_idx.get(m["city"].lower()) or csc_idx.get(m.get("kana", "").lower())
                             or csc_idx.get(en_name.lower()) or {})
                for locale, key in TRANSLATION_LOCALES.items():
                    value = inherited.get(key)
                    if value and nid not in ZH_GARBAGE_DROPS:
                        packs[locale][nid] = nfc(value)
            stats_jp_note = {"jpMunisGeolonia": len(jp_munis)}
            # JP uses no CSC city rows
            cities_by_cc[cc] = []
        if cc == "FR":
            # FR wholesale replacement: region/dept/commune from INSEE 2026
            source_refs_fr = [INSEE_SOURCE, CSC_SOURCE]
            nodes = [node(root_id, None, "country", cc, nfc(country["name"]), "en", "source-native", "partial")]
            packs = {locale: {} for locale in LOCALES}
            packs["en"][root_id] = nfc(country["name"])
            for locale in LOCALES:
                v = catalog_files[locale]["names"].get(cc) or country_trans.get(TRANSLATION_LOCALES.get(locale, ""))
                if v:
                    packs[locale][root_id] = nfc(v)
            csc_idx = csc_translation_index(cc)
            reg_ids = {}
            FR_REGION_ZH = {"Guadeloupe": "瓜德罗普", "Martinique": "马提尼克", "Guyane": "圭亚那",
                "La Réunion": "留尼汪", "Mayotte": "马约特", "Île-de-France": "法兰西岛",
                "Centre-Val de Loire": "中央-卢瓦尔河谷", "Bourgogne-Franche-Comté": "勃艮第-弗朗什-孔泰",
                "Normandie": "诺曼底", "Hauts-de-France": "上法兰西", "Grand Est": "大东部",
                "Pays de la Loire": "卢瓦尔河地区", "Bretagne": "布列塔尼", "Nouvelle-Aquitaine": "新阿基坦",
                "Occitanie": "奥克西塔尼", "Auvergne-Rhône-Alpes": "奥弗涅-罗讷-阿尔卑斯",
                "Provence-Alpes-Côte d'Azur": "普罗旺斯-阿尔卑斯-蓝色海岸", "Corse": "科西嘉"}
            for row in sorted(insee_regions, key=lambda r: r["REG"]):
                nid = f"fr-region:{row['REG']}"
                reg_ids[row["REG"]] = nid
                nodes.append(node(nid, root_id, "subdivision", row["REG"],
                                  nfc(row["LIBELLE"]), "fr", "source-native", "unknown"))
                packs["en"][nid] = nfc(row["LIBELLE"])
                zh_value = FR_REGION_ZH.get(row["LIBELLE"])
                if zh_value:
                    packs["zh-Hans"][nid] = nfc(zh_value)
                    packs["zh-Hant"][nid] = nfc(s2t_places.convert(zh_value)[0])
                    hant_q = packs.setdefault("_hant_quality", {})
                for locale, key in TRANSLATION_LOCALES.items():
                    v = (csc_idx.get(row["LIBELLE"].lower()) or {}).get(key)
                    if v and locale not in ("zh-Hans", "zh-Hant"):
                        packs[locale][nid] = nfc(v)
            dept_ids = {}
            for row in sorted(insee_depts, key=lambda r: r["DEP"]):
                nid = f"fr-dept:{row['DEP']}"
                parent = reg_ids.get(row["REG"], root_id)
                dept_ids[row["DEP"]] = nid
                nodes.append(node(nid, parent, "subdivision", row["DEP"],
                                  nfc(row["LIBELLE"]), "fr", "source-native", "unknown"))
                packs["en"][nid] = nfc(row["LIBELLE"])
                for locale, key in TRANSLATION_LOCALES.items():
                    v = (csc_idx.get(row["LIBELLE"].lower()) or {}).get(key)
                    if v:
                        packs[locale][nid] = nfc(v)
            for row in sorted(insee_communes, key=lambda r: r["COM"]):
                nid = f"fr-commune:{row['COM']}"
                dept_code = row["COM"][:2] if not row["COM"].startswith(("97", "98")) else row["COM"][:3]
                parent = dept_ids.get(dept_code, root_id)
                nodes.append(node(nid, parent, "subdivision", row["COM"],
                                  nfc(row["LIBELLE"]), "fr", "source-native", "unknown"))
                packs["en"][nid] = nfc(row["LIBELLE"])
                for locale, key in TRANSLATION_LOCALES.items():
                    v = (csc_idx.get(row["NCCENR"].lower()) or csc_idx.get(row["LIBELLE"].lower()) or {}).get(key)
                    if v and nid not in ZH_GARBAGE_DROPS:
                        packs[locale][nid] = nfc(v)
            cities_by_cc[cc] = []
            counties_by_cc[cc] = []
            states_by_cc[cc] = []
        county_ids = {row["id"] for row in counties_by_cc.get(cc, [])}
        if cc == "KR" and kr_fix:
            gwangju_districts = {"Gwangju", "Gwangsan-gu", "Buk-gu", "Dong-gu", "Nam-gu", "Seo-gu"}
            for row in cities_by_cc[cc]:
                if row.get("state_id") == kr_fix["id"]:
                    row["state_id"] = 18000000 if row["name"] in gwangju_districts else 17000000
        for row in sorted(cities_by_cc.get(cc), key=lambda r: r["id"]):
            nid = f"csc-city:{row['id']}"
            parent = state_ids.get(row.get("state_id"), root_id)
            if row.get("county_id") and row["county_id"] in county_ids:
                parent = f"csc-county:{row['county_id']}"
            nodes.append(node(nid, parent, "subdivision", f"{cc}-X{row['id']}", nfc(row["name"]),
                              "en", "source-native", "unknown"))
            packs["en"][nid] = nfc(row["name"])
            hans_fix = ZH_HANS_FIXES.get((cc, row["name"]))
            for locale, key in TRANSLATION_LOCALES.items():
                if locale == "zh-Hans" and hans_fix:
                    packs[locale][nid] = nfc(hans_fix)
                    packs.setdefault("_zh_fixed", {})[nid] = True
                    continue
                value = (row.get("translations") or {}).get(key)
                if value and nid not in ZH_GARBAGE_DROPS:
                    packs[locale][nid] = nfc(value)

        # CSC-translations bridge for FR/JP (ODbL): these layers inherit CSC
        # translations by normalized-name matching, which silently drops rows
        # whose name diverges from the official layer (INSEE LIBELLE vs CSC
        # spelling, Geolonia romaji vs CSC name). The rows' wikiDataId QIDs
        # give an exact second join: CSC row -> QID -> staged Wikidata extract
        # -> candidate nid. Fill-missing; garbage drops still apply; filled
        # values flow through the s2t/fix_zh_suffix pipeline below like any
        # other upstream translation.
        if cc in ("FR", "JP"):
            bridge_paths = {
                "FR": [("staging/wikidata-fr/fr-labels.json",
                        "staging/wikidata-fr/fr-labels.json (Wikidata P374 join reused as qid->nid bridge, CC0-1.0, tool/fetch_wikidata_fr_labels.py)")],
                "JP": [("staging/wikidata-cand/jp-labels.json",
                        "staging/wikidata-cand/jp-labels.json (Wikidata P429/P300 join reused as qid->nid bridge, CC0-1.0, tool/fetch_wikidata_candidate_labels.py)")],
            }[cc]
            qid_to_nid = {}
            for wd_path, _ref in bridge_paths:
                if not (REPO / wd_path).is_file():
                    continue
                wd_data = json.loads((REPO / wd_path).read_text(encoding="utf-8"))
                for bridge_nid, bridge_entry in wd_data["nodes"].items():
                    qid_to_nid.setdefault(bridge_entry.get("qid"), bridge_nid)
            bridge_rows = load(f"contributions/cities/{cc}.json")
            bridge_counties = SNAP / f"contributions/counties/{cc}.json"
            if bridge_counties.is_file():
                bridge_rows = bridge_rows + json.loads(bridge_counties.read_text(encoding="utf-8"))
            bridged_nodes = 0
            for row in bridge_rows:
                bridge_nid = qid_to_nid.get((row.get("wikiDataId") or "").strip())
                if not bridge_nid or bridge_nid in ZH_GARBAGE_DROPS:
                    continue
                trans = row.get("translations") or {}
                filled = False
                for locale, key in TRANSLATION_LOCALES.items():
                    if bridge_nid in packs[locale]:
                        continue
                    value = trans.get(key)
                    if value:
                        packs[locale][bridge_nid] = nfc(value)
                        filled = True
                if filled:
                    bridged_nodes += 1
            if bridged_nodes:
                packs["_bridge_refs"] = [ref for p, ref in bridge_paths if (REPO / p).is_file()]
                print(f"{cc} csc-translations qid bridge: {bridged_nodes} nodes filled")

        # derive zh-Hant pack (machine-candidate)
        hant_names, hant_quality = {}, {}
        conversion_stats = {"convertedChars": 0, "names": 0, "kanjiDirectJP": 0}
        for nid, node_row in ((n["id"], n) for n in nodes):
            if nid in packs["zh-Hant"]:
                # CLDR catalog direct value (roots) wins over conversion
                hant_names[nid] = packs["zh-Hant"][nid]
                hant_quality[nid] = "cldr-json-qualified"
                continue
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

        # finalize zh-Hans pack with the rule-based fixes (idempotent)
        en_by_id = {n["id"]: n["name"] for n in nodes}
        for nid in list(packs["zh-Hans"]):
            fixed = fix_zh_suffix(en_by_id.get(nid, ""), packs["zh-Hans"][nid])
            if fixed is None:
                del packs["zh-Hans"][nid]
                packs["zh-Hans"].pop(nid, None)
            elif fixed != packs["zh-Hans"][nid]:
                packs["zh-Hans"][nid] = nfc(fixed)
                packs.setdefault("_zh_fixed", {})[nid] = True

        # Wikidata community-label overlays (CC0, staged extracts): fill the
        # 9 translation locales where a node's external code matches an
        # upstream record (FR: P374 INSEE; JP: P429 dantai + P300; GB/IT/RU/
        # DE: P300 ISO). Fill-missing only; quality stays provisional
        # (community labels, humanReviewVerified=false).
        WD_STAGED = {
            "FR": [("staging/wikidata-fr/fr-labels.json",
                    "staging/wikidata-fr/fr-labels.json (Wikidata P374 INSEE-code label join, CC0-1.0, tool/fetch_wikidata_fr_labels.py)"),
                   ("staging/geonames-alt/fr-labels.json",
                    "staging/geonames-alt/fr-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "JP": [("staging/wikidata-cand/jp-labels.json",
                    "staging/wikidata-cand/jp-labels.json (Wikidata P429 dantai-code + P300 label join, CC0-1.0, tool/fetch_wikidata_candidate_labels.py)"),
                   ("staging/geonames-alt/jp-labels.json",
                    "staging/geonames-alt/jp-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "GB": [("staging/wikidata-cand/gb-labels.json",
                    "staging/wikidata-cand/gb-labels.json (Wikidata P300 label join, CC0-1.0, tool/fetch_wikidata_candidate_labels.py)"),
                   ("staging/wikidata-qid/gb-labels.json",
                    "staging/wikidata-qid/gb-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/gb-labels.json",
                    "staging/geonames-alt/gb-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "IT": [("staging/wikidata-cand/it-labels.json",
                    "staging/wikidata-cand/it-labels.json (Wikidata P300 label join, CC0-1.0, tool/fetch_wikidata_candidate_labels.py)"),
                   ("staging/wikidata-qid/it-labels.json",
                    "staging/wikidata-qid/it-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/it-labels.json",
                    "staging/geonames-alt/it-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "RU": [("staging/wikidata-cand/ru-labels.json",
                    "staging/wikidata-cand/ru-labels.json (Wikidata P300 label join, CC0-1.0, tool/fetch_wikidata_candidate_labels.py)"),
                   ("staging/wikidata-qid/ru-labels.json",
                    "staging/wikidata-qid/ru-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/ru-labels.json",
                    "staging/geonames-alt/ru-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "DE": [("staging/wikidata-cand/de-labels.json",
                    "staging/wikidata-cand/de-labels.json (Wikidata P300 label join, CC0-1.0, tool/fetch_wikidata_candidate_labels.py)"),
                   ("staging/wikidata-qid/de-labels.json",
                    "staging/wikidata-qid/de-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/de-labels.json",
                    "staging/geonames-alt/de-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "US": [("staging/wikidata-qid/us-labels.json",
                    "staging/wikidata-qid/us-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/us-labels.json",
                    "staging/geonames-alt/us-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "SA": [("staging/wikidata-qid/sa-labels.json",
                    "staging/wikidata-qid/sa-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/sa-labels.json",
                    "staging/geonames-alt/sa-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
            "KR": [("staging/wikidata-qid/kr-labels.json",
                    "staging/wikidata-qid/kr-labels.json (Wikidata labels by CSC wikiDataId QID, CC0-1.0, tool/fetch_wikidata_by_qid.py)"),
                   ("staging/geonames-alt/kr-labels.json",
                    "staging/geonames-alt/kr-labels.json (GeoNames alternateNamesV2 join via CSC wikiDataId->wkdt rows, CC-BY-4.0, tool/fetch_geonames_alt_names.py)")],
        }
        if cc in WD_STAGED:
            wd_filled = set()
            wd_pairs = set()
            wd_refs = []
            for wd_path, wd_ref in WD_STAGED[cc]:
                if not (REPO / wd_path).is_file():
                    continue
                wd_data = json.loads((REPO / wd_path).read_text(encoding="utf-8"))
                for n_row in nodes:
                    nid = n_row["id"]
                    entry = wd_data["nodes"].get(nid)
                    if not entry:
                        continue
                    for locale in list(TRANSLATION_LOCALES) + ["zh-Hant"]:
                        if nid in packs[locale]:
                            continue
                        label = entry["labels"].get(locale)
                        if label:
                            packs[locale][nid] = nfc(label)
                            wd_filled.add(nid)
                            wd_pairs.add((nid, locale))
                wd_refs.append(wd_ref)
            if wd_filled:
                packs["_wd_pairs"] = wd_pairs
                packs["_wd_refs"] = wd_refs
            print(f"{cc} wikidata overlay: {len(wd_filled)} nodes filled, "
                  f"{len(wd_refs)} staged sources applied")

        # rule-transcription overlay (last fill-missing stage): derived
        # machine-candidate transcriptions for cells no evidence source
        # covers (tool/gen_candidate_rule_transcriptions.py; eval-gated,
        # deterministic tables, humanReviewVerified=false).
        RULE_STAGED = {
            "RU": [(f"staging/ai-cand/ru-transcriptions.json", loc,
                    "staging/ai-cand/ru-transcriptions.json (rule-table Cyrillic->katakana/hangul/Latin transcription, machine-candidate, tool/gen_candidate_rule_transcriptions.py)")
                   for loc in ("ja", "ko", "de", "fr")],
        }
        if cc in RULE_STAGED:
            rule_filled = set()
            rule_pairs = set()
            rule_refs = []
            for rule_path, rule_locale, rule_ref in RULE_STAGED[cc]:
                if not (REPO / rule_path).is_file():
                    continue
                rule_data = json.loads((REPO / rule_path).read_text(encoding="utf-8"))
                for n_row in nodes:
                    nid = n_row["id"]
                    entry = rule_data["nodes"].get(nid)
                    if not entry:
                        continue
                    if nid in packs[rule_locale]:
                        continue
                    label = entry["labels"].get(rule_locale)
                    if label:
                        packs[rule_locale][nid] = nfc(label)
                        rule_filled.add(nid)
                        rule_pairs.add((nid, rule_locale))
                if rule_ref not in rule_refs:
                    rule_refs.append(rule_ref)
            if rule_filled:
                packs["_rule_pairs"] = rule_pairs
                packs["_rule_refs"] = rule_refs
            print(f"{cc} rule-transcription overlay: {len(rule_filled)} nodes filled")

        structure = {"protocolVersion": "1.0", "datasetId": "geo-regions-csc-candidate",
                     "countryCode": cc,
                     "sourceRefs": ([INSEE_SOURCE, CSC_SOURCE] if cc == "FR" else
                                    [GEOLONIA_SOURCE, CSC_SOURCE] if cc == "JP" else [CSC_SOURCE]),
                     "nodes": nodes}
        structure["revision"] = geo.revision("s", nodes)
        geo.write_json(OUT / f"data/regions/{cc}.json", structure)
        for locale in LOCALES:
            fr_refs = [CSC_SOURCE]
            if cc == "FR":
                fr_refs.append(INSEE_SOURCE)
            fr_refs.extend(packs.get("_wd_refs", []))
            fr_refs.extend(packs.get("_bridge_refs", []))
            fr_refs.extend(packs.get("_rule_refs", []))
            pack = {"protocolVersion": "1.0", "datasetId": "geo-regions-csc-candidate",
                    "countryCode": cc, "locale": locale,
                    "compatibleStructureRevision": structure["revision"],
                    "sourceRefs": fr_refs, "names": packs[locale],
                    "coverage": {"status": "research-seed",
                                 "translationQualityById": {
                                     nid: ("provisional" if (nid, locale) in packs.get("_wd_pairs", set())
                                           else "machine-candidate" if (nid, locale) in packs.get("_rule_pairs", set())
                                           or locale == "zh-Hant" and nid not in packs.get("_hant_qualified", set())
                                           or (locale == "zh-Hans" and nid in packs.get("_zh_fixed", {}))
                                           else "source-native" if locale == "en"
                                           else "cldr-json-qualified" if nid == root_id and locale in ("zh-Hans", "zh-Hant")
                                           else "provisional")
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
        "- FR x9 locales: Wikidata P374 community labels fill missing cells "
        "(CC0-1.0, staged extract, provisional)\n"
        "- US/DE/IT/GB/RU/SA/KR: Wikidata labels joined by the snapshot rows' "
        "own wikiDataId QIDs (CC0-1.0, staged extracts, provisional)\n"
        "- GeoNames alternateNamesV2 labels via CSC wikiDataId -> wkdt rows "
        "(CC-BY-4.0, staged extracts, provisional; fills what Wikidata lacks)\n"
        "- RU ja/ko/de/fr: rule-table Cyrillic->katakana/hangul/Latin "
        "transcriptions (machine-candidate, eval-gated, "
        "tool/gen_candidate_rule_transcriptions.py)\n"
        "- FR/JP: CSC upstream translations re-joined through the staged "
        "qid->nid bridge for rows the name-matching inheritance missed "
        "(ODbL-1.0, provisional)\n"
        "- zh-Hant: zh-Hant is s2t-derived machine-candidate + FR wikidata "
        "community labels\n"
        "- All non-en translations are provisional; AI proof-reading samples do not flip quality words\n"
        "- This candidate dataset is NOT production data (maturity stays research-seed)\n",
        encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
