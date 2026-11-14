#!/usr/bin/env python3
"""Rebuild the auditable 10-country seed from pinned GitHub snapshots.

Python >=3.10, standard library only. No network in the default/check path.
The generated dataset is a research seed, not an authoritative gazetteer.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2t_places

COUNTRIES = ('CN', 'JP', 'KR', 'US', 'GB', 'DE', 'FR', 'IT', 'RU', 'SA')
LOCALES = ('zh-Hans', 'zh-Hant', 'en', 'ja', 'ko', 'ru', 'de', 'fr', 'it', 'ar')
UPSTREAM_LOCALES = {loc: 'zh' if loc == 'zh-Hans' else loc for loc in LOCALES}
DATASET_ID = 'geo-regions-seed'
PROTOCOL_VERSION = '1.0'
CN_EXCLUSIONS = {'cnhk', 'cnmo', 'cntw'}

# English romanization overlay for CN statistical nodes (PROVISIONAL quality).
# Source: GeoNames CN dump (CC-BY-4.0, attribution — no share-alike), reduced
# by tool/extract_geonames_cn.py to a committed extract. The dump itself never
# enters git; the extract carries its upstream URL + sha256 for provenance and
# any tampering shows up as stale-generated-output in --check.
GEONAMES_CN_ROWS = 'sources/raw/geonames/cn-adm-rows.json'
WIKIDATA_LABELS = 'sources/raw/wikidata/subdivision-labels.json'
# GeoNames uses FIPS codes for the four municipalities' admin1 (GB codes 11/12/31/50).
GEONAMES_FIPS_MUNICIPALITIES = {'11': '22', '12': '28', '31': '23', '50': '33'}
# Pinyin admin suffixes stripped from the display name ONLY when the bare form
# exists in the row's Latin alternatenames (evidence-based, never invented).
# English-word suffixes (District/Prefecture/City) are kept, mirroring how the
# seed keeps "Fairfax County".
GEONAMES_STRIP_SUFFIXES = (' Shi', ' Qu', ' Xian', ' Diqu', ' Zizhizhou', ' Meng', ' Qi')
# Display overrides where GeoNames' own asciiname is an upstream quirk; the
# replacement is evidenced inside the same row's Latin alternatenames:
# - 1305 邢台市: GeoNames ADM2 asciiname is "Xingtai County" (county form on a
#   prefecture row); "Xingtai" is among its alternatenames.
# - 1411 吕梁市: GeoNames asciiname "Lueliang" is a ü→ue transliteration
#   artifact; "Luliang" (Luliang Diqu) is among its alternatenames.
GEONAMES_EN_FIXES = {'1305': 'Xingtai', '1411': 'Luliang'}
# zh aliases where GeoNames lags an official rename: 襄樊市 → 襄阳市 (2010-12,
# State Council approval; GeoNames ADM2 4206 still carries 襄樊/襄樊市 while
# its Latin alternatenames already include Xiangyang).
GEONAMES_ZH_ALIASES = {'4206': {'襄阳市': ['襄樊市', '襄樊']}}
# Latin-script locales that use the standard pinyin romanization for Chinese
# place names (CLDR fr/de/it follow the same convention as en). Non-Latin
# scripts (ja/ko/ru/ar) need real transliteration work and stay on honest
# fallback — copying another script's text would be a fake translation.
GEONAMES_LOCALES = ('en', 'fr', 'de', 'it')
GROUP_NAMES = {'市辖区', '县', '省直辖县级行政区划', '自治区直辖县级行政区划'}
BAD_NAMES = {'↑↑↑', '∅∅∅'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(prefix, value):
    return prefix + '-' + hashlib.sha256(canonical(value)).hexdigest()[:16]


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def ensure_under(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes repository: {relative}')
    return path


def verify_sources(root, download=False):
    lock = read_json(root / 'sources/source-lock.json')
    for source in lock['sources']:
        path = ensure_under(root, source['localPath'])
        if download:
            # Refresh only the exact immutable revision. Never update source-lock silently.
            with urllib.request.urlopen(source['url'], timeout=45) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != source['sha256']:
                raise ValueError(f'Pinned source hash mismatch: {source["localPath"]}')
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + '.download.tmp')
            tmp.write_bytes(content)
            tmp.replace(path)
        if not path.is_file():
            raise ValueError(f'Missing snapshot: {source["localPath"]}; use --download if needed')
        content = path.read_bytes()
        if len(content) != source['sizeBytes'] or hashlib.sha256(content).hexdigest() != source['sha256']:
            raise ValueError(f'Source verification failed: {source["localPath"]}')
    # Derived extracts: byte-pinned like sources, no upstream commit / download
    # semantics (regenerate with the recorded generator from the pinned dump).
    for source in lock.get('derivedSources', []):
        path = ensure_under(root, source['localPath'])
        if not path.is_file():
            raise ValueError(f'Missing derived snapshot: {source["localPath"]}; '
                             f"regenerate with {source.get('generator', 'the recorded generator')}")
        content = path.read_bytes()
        if len(content) != source['sizeBytes'] or hashlib.sha256(content).hexdigest() != source['sha256']:
            raise ValueError(f'Derived source verification failed: {source["localPath"]}')
    return lock


def source_maps(root):
    raw = root / 'sources/raw/cldr'
    territories, subdivisions, qualities = {}, {}, {}
    for locale, upstream in UPSTREAM_LOCALES.items():
        territory_doc = read_json(raw / f'territories-{upstream}.json')
        territories[locale] = territory_doc['main'][upstream]['localeDisplayNames']['territories']
        subdivisions[locale], qualities[locale] = {}, {}
        # Parse only local, pinned XML. ElementTree does not fetch the external DTD.
        for element in ET.parse(raw / f'subdivisions-{upstream}.xml').findall('./localeDisplayNames/subdivisions/subdivision'):
            text = element.text
            if 'alt' in element.attrib or not text or text in BAD_NAMES:
                continue
            code = element.attrib['type']
            if code in subdivisions[locale]:
                raise ValueError(f'Duplicate non-alt CLDR entry: {locale}/{code}')
            subdivisions[locale][code] = text
            qualities[locale][code] = element.attrib.get('draft', 'approved-in-source')
    return territories, subdivisions, qualities


def node_id(cldr_code):
    return 'iso3166-2:' + cldr_code[:2].upper() + '-' + cldr_code[2:].upper()


def base_nodes(cc, containment, names, territories, qualities):
    nodes = [{'id': 'cc:' + cc, 'parentId': None, 'kind': 'country',
              'code': cc, 'name': territories['en'][cc], 'nameLocale': 'en',
              'nameQuality': 'cldr-json-qualified', 'childrenStatus': 'complete'}]
    index = {}
    queue = [(cc, 'cc:' + cc)]
    while queue:
        source_parent, parent = queue.pop(0)
        for code in containment.get(source_parent, {}).get('_contains', []):
            if cc == 'CN' and code in CN_EXCLUSIONS:
                continue
            if code in index:
                raise ValueError(f'Subdivision has multiple parents: {code}')
            if not code.startswith(cc.lower()):
                raise ValueError(f'Unexpected cross-country containment: {cc}/{code}')
            children = containment.get(code, {}).get('_contains', [])
            node = {'id': node_id(code), 'parentId': parent, 'kind': 'subdivision',
                    'code': cc + '-' + code[2:].upper(), 'name': names['en'].get(code, cc + '-' + code[2:].upper()),
                    'childrenStatus': 'complete' if children else 'unknown'}
            if code in names['en']:
                node['nameLocale'] = 'en'
                node['nameQuality'] = qualities['en'][code]
            else:
                node['nameQuality'] = 'identifier'
            nodes.append(node)
            index[code] = node
            queue.append((code, node['id']))
    return nodes, index


def add_cn(root, nodes, index, names, aliases):
    crosswalk, native_names = [], {}
    for province in read_json(root / 'sources/raw/modood/pca-code.json'):
        alias = aliases.get('cn' + province['code'], {}).get('_replacement')
        code, method = alias, 'CLDR-subdivisionAlias'
        if code not in index:
            # A published CLDR inconsistency exists for cn15: alias=cnmn, containment=cnnm.
            # Resolve only a unique exact source-name match, and preserve the exception record.
            matches = [k for k in index if names['zh-Hans'].get(k) == province['name']]
            if len(matches) != 1:
                raise ValueError(f'No unambiguous CN province crosswalk: {province["code"]} {province["name"]}')
            code, method = matches[0], 'unique-exact-source-name-match'
        provincial_node = index[code]
        provincial_node['name'] = province['name']
        provincial_node['nativeLocale'] = 'zh-Hans'
        provincial_node['nameLocale'] = 'zh-Hans'
        provincial_node['nameQuality'] = 'source-native'
        provincial_node['childrenStatus'] = 'complete'
        native_names[provincial_node['id']] = province['name']
        crosswalk.append({'statisticalProvinceCode': province['code'], 'cldrSubdivisionId': code,
                          'nodeId': provincial_node['id'], 'method': method,
                          'aliasReplacement': alias,
                          'sourceRefs': ['sources/raw/cldr/aliases.json', 'sources/raw/cldr/subdivisions-zh.xml',
                                         'sources/raw/cldr/subdivisionContainment.json', 'sources/raw/modood/pca-code.json']})
        for city in province.get('children', []):
            city_id = 'cn-stat:' + city['code']
            nodes.append({'id': city_id, 'parentId': provincial_node['id'],
                          'kind': 'statistical-group' if city['name'] in GROUP_NAMES else 'statistical-prefecture',
                          'code': city['code'], 'name': city['name'], 'nativeLocale': 'zh-Hans',
                          'nameLocale': 'zh-Hans', 'nameQuality': 'source-native',
                          'childrenStatus': 'complete' if city.get('children') else 'unknown'})
            native_names[city_id] = city['name']
            for area in city.get('children', []):
                if len(area['code']) not in (6, 9):
                    raise ValueError(f'Unexpected statistical code length: {area["code"]}')
                area_id = 'cn-stat:' + area['code']
                nodes.append({'id': area_id, 'parentId': city_id,
                              'kind': 'statistical-county' if len(area['code']) == 6 else 'statistical-township',
                              'code': area['code'], 'name': area['name'], 'nativeLocale': 'zh-Hans',
                              'nameLocale': 'zh-Hans', 'nameQuality': 'source-native',
                              'childrenStatus': 'unknown'})
                native_names[area_id] = area['name']
    return crosswalk, native_names


def _zh_keys(name):
    """Match keys for a statistical node's Chinese name: the exact name first,
    then progressively stripped admin suffixes (longest first)."""
    keys = [name]
    for suffix in ('自治州', '地区', '盟', '林区', '特区', '市', '区', '县'):
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            stripped = name[:-len(suffix)]
            if stripped not in keys:
                keys.append(stripped)
    return sorted(keys, key=len, reverse=True)


def _pick_row(rows, keys):
    """Unique row whose zh alternatenames contain one of [keys], exact first.
    Ambiguous or missing matches stay missing — never guess."""
    for key in keys:
        hits = [row for row in rows if key in row['zh']]
        if len(hits) == 1:
            return hits[0]
        if hits:
            return None
    return None


def _display_name(row):
    ascii_name = row['ascii']
    for suffix in GEONAMES_STRIP_SUFFIXES:
        if ascii_name.endswith(suffix):
            bare = ascii_name[:-len(suffix)].strip()
            if bare in row['latin']:
                return bare
            break
    return ascii_name


def geonames_cn_overlay(nodes, root):
    """Machine-matched English romanizations for CN statistical prefectures
    and counties from the committed GeoNames extract.

    Prefecture (4-digit GB code) → GeoNames ADM2 row with admin2 == code.
    County (6-digit) → ADM3 rows with admin2 == code[:4]; when the parent is
    a statistical grouping the row may sit elsewhere: municipality districts
    carry GeoNames' FIPS admin1 instead of a GB admin2, and province-direct
    counties (仙桃/济源/石河子…) are ADM3 rows with an empty admin2. Returns
    (names, meta); unmatched nodes stay missing so the coverage counters
    remain honest.
    """
    rows = read_json(root / GEONAMES_CN_ROWS)
    counts = rows['rowCounts']
    if counts['adm2'] != len(rows['adm2']) or counts['adm3'] != len(rows['adm3']):
        raise ValueError('GeoNames extract rowCounts disagree with its rows')
    by_admin2 = collections.defaultdict(list)
    by_admin1 = collections.defaultdict(list)
    by_province_direct = []
    for row in rows['adm3']:
        if row['a2']:
            by_admin2[row['a2']].append(row)
            by_admin1[row['a1']].append(row)
        else:
            by_province_direct.append(row)
    node_by_id = {n['id']: n for n in nodes}
    names = {}
    meta = {'prefectureMatched': 0, 'countyMatched': 0, 'unmatched': 0}
    for node in nodes:
        kind = node['kind']
        if kind not in ('statistical-prefecture', 'statistical-county'):
            continue
        keys = _zh_keys(node['name'])
        for alias in GEONAMES_ZH_ALIASES.get(node['code'][:4], {}).get(node['name'], []):
            keys.append(alias)
        chosen = None
        if kind == 'statistical-prefecture':
            row = rows['adm2'].get(node['code'])
            if row is not None:
                chosen = _pick_row([row], keys)
            if chosen is not None:
                names[node['id']] = GEONAMES_EN_FIXES.get(node['code'],
                                                          _display_name(chosen))
                meta['prefectureMatched'] += 1
                continue
        else:
            chosen = _pick_row(by_admin2.get(node['code'][:4], []), keys)
            if chosen is None:
                parent = node_by_id.get(node['parentId'])
                if parent is not None and parent['kind'] == 'statistical-group':
                    fips = GEONAMES_FIPS_MUNICIPALITIES.get(node['code'][:2])
                    if fips is not None:
                        chosen = _pick_row(by_admin1.get(fips, []), keys)
                    if chosen is None:
                        chosen = _pick_row(by_province_direct, keys)
            if chosen is not None:
                display = _display_name(chosen)
                # A county whose bare name equals its matched prefecture's
                # keeps the suffixed form (邢台市 "Xingtai" vs 邢台县 "Xingtai Xian").
                if names.get(node['parentId']) == display:
                    display = chosen['ascii']
                names[node['id']] = display
                meta['countyMatched'] += 1
                continue
        meta['unmatched'] += 1
    return names, meta


def quality_stats(names, quality, total):
    counts = collections.Counter(quality.values())
    return {'explicitNames': len(names), 'sourceApproved': counts['approved-in-source'],
            'sourceQualified': counts['cldr-json-qualified'] + counts['contributed'],
            'sourceProvisional': counts['provisional'], 'sourceUnconfirmed': counts['unconfirmed'],
            'sourceNative': counts['source-native'], 'missingNames': total - len(names),
            'projectReviewed': 0}


def build(root):
    wd_path = root / WIKIDATA_LABELS
    wd_extract = read_json(wd_path) if wd_path.is_file() else None
    if wd_extract is not None:
        counts = wd_extract['matchCount']
        if counts != len(wd_extract['labels']):
            raise ValueError('Wikidata extract matchCount disagrees with its rows')
    raw = root / 'sources/raw/cldr'
    containment = read_json(raw / 'subdivisionContainment.json')['supplemental']['subdivisionContainment']
    aliases = read_json(raw / 'aliases.json')['supplemental']['metadata']['alias']['subdivisionAlias']
    territories, translations, quality_maps = source_maps(root)
    out, country_reports = {}, []
    common = {'protocolVersion': PROTOCOL_VERSION, 'datasetId': DATASET_ID}
    country_list = [{'code': cc, 'name': territories['en'][cc], 'rootId': 'cc:' + cc} for cc in COUNTRIES]
    catalog = dict(common, revision=revision('c', country_list), countries=country_list)
    out['data/countries.json'] = encoded(catalog)
    for locale, upstream in UPSTREAM_LOCALES.items():
        country_names = {cc: territories[locale][cc] for cc in COUNTRIES}
        quality = {cc: 'cldr-json-qualified' for cc in COUNTRIES}
        out[f'data/catalog_i18n/{locale}.json'] = encoded(dict(common, locale=locale,
            revision=revision('l', {'names': country_names, 'translationQualityById': quality}),
            compatibleCatalogRevision=catalog['revision'], names=country_names,
            coverage={'status': 'research-seed', 'translationQualityById': quality,
                      'qualityMeaning': 'CLDR JSON export threshold is contributed or approved; no project review claimed.'},
            sourceRefs=[f'sources/raw/cldr/territories-{upstream}.json']))
    for cc in COUNTRIES:
        nodes, index = base_nodes(cc, containment, translations, territories, quality_maps)
        native_names = {}
        if cc == 'CN':
            crosswalk, native_names = add_cn(root, nodes, index, translations, aliases)
            out['sources/cn-province-crosswalk.json'] = encoded({'records': crosswalk})
        nodes.sort(key=lambda n: n['id'])
        ids = {n['id'] for n in nodes}
        if len(ids) != len(nodes):
            raise ValueError(f'Duplicate node IDs for {cc}')
        for n in nodes:
            if n['parentId'] is not None and n['parentId'] not in ids:
                raise ValueError(f'Missing parent for {n["id"]}')
        country_revision = revision('s', nodes)
        profile = 'CLDR-49-subdivision-containment'
        sources = ['sources/raw/cldr/subdivisionContainment.json', 'sources/raw/cldr/subdivisions-en.xml',
                   'sources/raw/cldr/territories-en.json']
        coverage = {'status': 'research-seed', 'profile': profile,
                    'cldrRelease': '49.0.0',
                    'scopeMeaning': 'All reachable nodes in the pinned source profile, not a claim of current official administrative completeness.',
                    'leafMeaning': 'childrenStatus unknown means lower subdivisions are outside this snapshot; it does not mean an administrative leaf.',
                    'defaultNameSource': 'CLDR English XML; node nameLocale/nameQuality preserve language and quality. Missing English names use code with identifier quality.',
                    'missingDefaultNames': [node_id(k) for k in index if k not in translations['en']]}
        if cc == 'CN':
            coverage.update(profile='CN-mainland-CLDR49-plus-modood-statistics-2023',
                            statisticalSnapshotDate='2023-06-30',
                            excludedSubdivisionIds=sorted(CN_EXCLUSIONS),
                            exclusionReason='Mainland starter profile; HK, MO and TW can be supplied as independently configured ISO catalog entries. No silent duplicate trees.',
                            containsStatisticalGroupingNodes=True,
                            defaultNameSource='modood source-native Chinese for mainland descendants; CLDR English country root. Per-node nameLocale/nameQuality govern fallback.',
                            warning='Upstream modood states the dataset is no longer updated. This seed is not 2026-current data.')
            sources += ['sources/raw/modood/pca-code.json', 'sources/raw/cldr/aliases.json', 'sources/raw/cldr/subdivisions-zh.xml']
        country_doc = dict(common, countryCode=cc, revision=country_revision, nodes=nodes,
                           coverage=coverage, sourceRefs=sources)
        out[f'data/regions/{cc}.json'] = encoded(country_doc)
        report = {'countryCode': cc, 'nodes': len(nodes), 'subdivisionNodes': len(nodes)-1,
                  'rootChildren': sum(n['parentId'] == 'cc:' + cc for n in nodes),
                  'kinds': dict(sorted(collections.Counter(n['kind'] for n in nodes).items())), 'locales': {}}
        gn_overlay, gn_meta = geonames_cn_overlay(nodes, root) if cc == 'CN' else ({}, {})
        node_by_id = {n['id']: n for n in nodes}
        wd_labels = wd_extract['labels'] if wd_extract else {}
        wd_match = wd_extract['matchCount'] if wd_extract else 0
        zh_hans_names = {'cc:' + cc: territories['zh-Hans'][cc]}
        for code in index:
            if code in translations['zh-Hans']:
                zh_hans_names[node_id(code)] = translations['zh-Hans'][code]
        if cc == 'CN':
            zh_hans_names.update(native_names)
        for locale, upstream in UPSTREAM_LOCALES.items():
            names = {'cc:' + cc: territories[locale][cc]}
            quality = {'cc:' + cc: 'cldr-json-qualified'}
            for code in index:
                if code in translations[locale]:
                    names[node_id(code)] = translations[locale][code]
                    quality[node_id(code)] = quality_maps[locale][code]
            refs = [f'sources/raw/cldr/territories-{upstream}.json', f'sources/raw/cldr/subdivisions-{upstream}.xml']
            territory_overlay = {}
            for nid, node in node_by_id.items():
                if nid in names or node['kind'] == 'country':
                    continue
                tcode = node['code'].split('-', 1)[1] if '-' in node['code'] else None
                if tcode and tcode in territories[locale]:
                    territory_overlay[nid] = territories[locale][tcode]
            if territory_overlay:
                names.update(territory_overlay)
                quality.update({k: 'cldr-json-qualified' for k in territory_overlay})
            if cc == 'CN' and locale == 'zh-Hans':
                names.update(native_names)
                quality.update({k: 'source-native' for k in native_names})
                refs.append('sources/raw/modood/pca-code.json')
            s2t_overlay, s2t_changed = {}, 0
            if locale == 'zh-Hant':
                for nid, text in zh_hans_names.items():
                    if nid in names:
                        continue
                    converted, changed = s2t_places.convert_place_name(text)
                    s2t_overlay[nid] = converted
                    s2t_changed += 1 if changed else 0
                names.update(s2t_overlay)
                quality.update({k: 'provisional' for k in s2t_overlay})
            gn_applied = {}
            if cc == 'CN' and locale in GEONAMES_LOCALES:
                gn_applied = gn_overlay
                names.update(gn_applied)
                quality.update({k: 'provisional' for k in gn_applied})
                refs.append(GEONAMES_CN_ROWS)
            wd_overlay = {}
            for nid, node in node_by_id.items():
                if nid in names or node['kind'] == 'country':
                    continue
                label = wd_labels.get(node['code'], {}).get('labels', {}).get(locale)
                if label:
                    wd_overlay[nid] = label
            if wd_overlay:
                names.update(wd_overlay)
                quality.update({k: 'provisional' for k in wd_overlay})
                refs.append(WIKIDATA_LABELS)
            stats = quality_stats(names, quality, len(nodes))
            locale_coverage = dict(stats, status='research-seed', translationQualityById=quality,
                policy='Default production policy rejects provisional and unconfirmed; demo may opt in explicitly. Missing or filtered names fall back, never fill by copying another language.')
            if territory_overlay:
                locale_coverage['cldrTerritoryNameFill'] = {
                    'filled': len(territory_overlay),
                    'note': 'Subdivision nodes whose ISO code is also a CLDR territory entry (e.g. US-AS, FR-BL) filled from the same pinned CLDR territories export; JSON export threshold quality.'}
            if wd_overlay:
                locale_coverage['wikidataLabelOverlay'] = {
                    'source': WIKIDATA_LABELS, 'license': 'CC0-1.0',
                    'filled': len(wd_overlay), 'matchCount': wd_match,
                    'note': 'Wikidata community labels fetched via exact P300 (ISO 3166-2) join; provisional quality, not human-reviewed.'}
            if gn_applied:
                locale_coverage['geoNamesLatinOverlay'] = dict(gn_meta, source=GEONAMES_CN_ROWS,
                    license='CC-BY-4.0', locales=list(GEONAMES_LOCALES),
                    meaning='Machine-matched GeoNames romanization shared by Latin-script locales for Chinese names; provisional quality, not human-reviewed.')
            if s2t_overlay:
                locale_coverage['zhHantScriptConversion'] = {
                    'table': 'tool/s2t_places.py', 'filled': len(s2t_overlay),
                    'changed': s2t_changed,
                    'note': 'Recorded conservative simplified-to-traditional conversion of the zh-Hans names; ambiguous characters stay unchanged and keep honest fallback. Provisional quality, not human-reviewed.'}
            locale_doc = dict(common, countryCode=cc, locale=locale,
                revision=revision('l', {'names': names, 'translationQualityById': quality}),
                compatibleStructureRevision=country_revision, names=names,
                coverage=locale_coverage,
                sourceRefs=refs)
            out[f'data/i18n/{locale}/{cc}.json'] = encoded(locale_doc)
            report['locales'][locale] = stats
        country_reports.append(report)
    report = {'protocolVersion': PROTOCOL_VERSION, 'datasetId': DATASET_ID,
              'status': 'research-seed', 'countries': country_reports,
              'totalNodes': sum(c['nodes'] for c in country_reports),
              'countryCount': len(COUNTRIES), 'localeCount': len(LOCALES),
              'countryNamesPerLocale': len(COUNTRIES)}
    out['sources/coverage-report.json'] = encoded(report)
    out['docs/DATA_COVERAGE.md'] = coverage_markdown(report).encode('utf-8')
    return out, report


def coverage_markdown(report):
    lines = ['# 数据覆盖报告 / Data coverage report', '',
             '生成日期 / Prepared: 2026-11-13。由 `tool/import_data.py` 从固定 GitHub 快照生成；可重现。', '',
             '**状态 / Status: research-seed。不是全球完整数据库，也不是所有行政节点已完成十语人工校审的正式发布。**', '',
             '**This is a reproducible research seed, not a globally complete or human-reviewed ten-language gazetteer.**', '',
             '## 实际覆盖 / Actual coverage', '',
             f'共 {report["countryCount"]} 个国家数据分片、{report["localeCount"]} 种语言、{report["totalNodes"]:,} 个节点（包括国家根节点）。', '',
             'Each of the ten small country-name packs has all ten catalog names. Region-name packs are sparse and carry per-ID upstream quality metadata.', '',
             '| 国家 / Country | 所有节点 / Nodes | 国家下直属节点 / Root children | 覆盖说明 / Scope |',
             '|---|---:|---:|---|']
    scopes = {'CN':'大陆31省 + 2023统计分组/地市/县区/部分乡镇；不含港澳台子树 / Mainland statistical snapshot',
              'JP':'CLDR47都道府县；不含市区町村 / 47 prefectures',
              'KR':'CLDR17省级；不含市郡区 / 17 first-level subdivisions',
              'US':'CLDR57州、地区及领地条目；不含县市 / 57 source subdivisions, including territories',
              'GB':'CLDR constituent countries + reachable subdivisions',
              'DE':'CLDR16州；不含市镇 / 16 states',
              'FR':'CLDR regions/overseas entries + reachable subdivisions',
              'IT':'CLDR regions + reachable subdivisions',
              'RU':'CLDR83条目；保留上游口径 / 83 entries in the pinned source profile',
              'SA':'CLDR13行政区；不含城市 / 13 regions'}
    for c in report['countries']:
        lines.append(f'| {c["countryCode"]} | {c["nodes"]:,} | {c["rootChildren"]} | {scopes[c["countryCode"]]} |')
    lines += ['', '## 名称覆盖矩阵 / Explicit-name coverage', '',
              '每格为“源中有显式名称 / 该国节点总数”；**存在不等于已审校**。数字包含国家根名称，不含运行时回退复制。', '',
              'Cells count explicit source names / total nodes, including the country root. Presence does not imply review. Runtime fallback is never counted as translation.', '',
              '| Country | ' + ' | '.join(LOCALES) + ' |', '|---|' + '---:|'*len(LOCALES)]
    for c in report['countries']:
        lines.append('| ' + c['countryCode'] + ' | ' + ' | '.join(f'{c["locales"][l]["explicitNames"]}/{c["nodes"]}' for l in LOCALES) + ' |')
    lines += ['', '## 上游质量统计 / Upstream quality counts', '',
              '| Locale | Explicit | Approved in XML | JSON-qualified / contributed | Provisional | Unconfirmed | Source-native | Missing | Project reviewed |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    keys = ['explicitNames','sourceApproved','sourceQualified','sourceProvisional','sourceUnconfirmed','sourceNative','missingNames','projectReviewed']
    for l in LOCALES:
        totals = {k:sum(c['locales'][l][k] for c in report['countries']) for k in keys}
        lines.append('| ' + l + ' | ' + ' | '.join(str(totals[k]) for k in keys) + ' |')
    lines += ['', '### 质量字段的准确含义 / Exact quality semantics', '',
              '- `approved-in-source`：CLDR XML该条无draft属性；不是本项目人工审校。 / XML has no draft attribute; not project review.',
              '- `cldr-json-qualified`：CLDR JSON仅输出达到contributed或approved阈值的数据，JSON未逐条保留二者区别。 / Meets the CLDR JSON export threshold; exact draft distinction is unavailable in JSON.',
              '- `provisional` / `unconfirmed` / `contributed`：逐条保留XML原值。 / Preserve upstream XML attributes literally.',
              '- `source-native`：CN历史源提供的原始中文名称；不是人工新翻译。 / Original Chinese names from the pinned historical source.',
              '- 缺失项不生成伪翻译。默认正式策略过滤provisional/unconfirmed；Demo可以明确开启预览并显示状态。 / Missing entries stay absent. Production defaults filter provisional/unconfirmed; demo preview must be explicit.', '',
              '## 已知边界 / Known limitations', '',
              '1. CN深层是2023-06-30统计快照。modood README已声明停更；不能称2026现势行政数据。 / CN lower levels are a frozen 2023 statistical snapshot.',
              '2. CN包含31个省级节点、342个中层节点、2974个6位第三层节点及82个9位第三层节点。后两类不能都叫“区县”；按原始代码长度区分statistical-county和statistical-township。 / Tree depth is not administrative rank.',
              '3. “市辖区”“县”“省直辖县级行政区划”等是源中统计分组，标为statistical-group；不伪造城市或跳过真实路径。 / Statistical grouping nodes remain explicit.',
              '4. CN采用大陆starter profile；源containment的cnhk/cnmo/cntw被显式排除。HK/MO/TW未作为本次10个catalog条目发布，应另立可配置profile和补数任务。US/FR保留源内含的领地/海外条目。这些数据口径不构成主权判断。 / Scope follows declared source profiles, not a sovereignty assertion.',
              '5. `childrenStatus=unknown`表示源覆盖到此结束，不表示该地不存在下级行政区。complete只说明当前声明profile内的子项齐备。 / Unknown leaves are not proof of no lower divisions.',
              '6. zh-Hant显式名=zh-Hans名的记录式保守简繁转换（tool/s2t_places.py，provisional；歧义字台/咸/峰/里等保持原形走真实回退）。CLDR繁中subdivision源仅有GB三条显式名称，本包从未用简体复制冒充繁中翻译。 / zh-Hant names are a recorded conservative s2t conversion of zh-Hans (provisional); ambiguous glyphs stay unchanged with honest fallback — never simplified text posing as traditional.',
              '7. CLDR cn15 alias指向cnmn，但同版containment与名称表使用cnnm。导入器只在唯一完全相同源中文名的条件下关联“内蒙古自治区”，并写入`sources/cn-province-crosswalk.json`。 / One source inconsistency is recorded and deterministically resolved by a unique exact source-name match.',
              '8. 结构默认名也携带nameLocale/nameQuality，必须经过与语言包相同的质量策略；不能先过滤provisional译名，再从默认名绕过过滤。没有可信名称时仅展示identifier状态的ID/代码。 / Apply quality policy to default names as well as locale packs.',
              '9. 地区ID中的ISO或统计码是固定快照映射。后续改名保留ID；代码重用、拆分和合并需人工确认迁移表，不能自动覆盖历史身份。 / Code reuse and boundary changes require explicit identity migration.',
              '10. CN市/县级英文名是GeoNames机器匹配的罗马字（provisional，CC-BY-4.0），未经人工审校；匹配失败的城市开发区等节点保持缺失，不伪造。 / CN prefecture/county English names are machine-matched GeoNames romanizations (provisional, CC-BY-4.0); unmatched nodes (development zones etc.) stay missing.', '',
              '## 下一版可并行补齐 / Parallel completion tracks', '',
              '| Track | Scope | Required evidence before merge |', '|---|---|---|',
              '| CN-current | 2023快照后的撤并/更名，港澳台独立profile | 官方变更来源、可再分发许可、ID迁移；不得用旧快照冒充现势 |',
              '| JP-KR | 市区町村/市郡区 | 固定源版本、父级关系、语言和许可记录 |',
              '| US-GB | 县市与UK地区当前口径核对 | 标准代码、非树状关系处理、删除/重用差异 |',
              '| DE-FR-IT | 市镇/commune/comune | 跨层级规则、当前覆盖日期、许可证兼容 |',
              '| RU-SA | 更深行政层级与来源profile核对 | 不混用不同立场/年份的代码和名称 |',
              '| zh-Hant | 人工审校机器转换的繁中条目 | 转换已由 tool/s2t_places.py 记录（167 个语料实测字对+歧义字保留清单）；补齐逐 ID 审校记录 |',
              '| locale-review | 其余9语的provisional条目审校 | 母语审校证据、原名称差异、逐IDreview metadata，不篡改CLDR原draft状态 |', '',
              '以上数据轨道按国家/语言文件拆分并行；仅由集成人生成全局manifest和覆盖报告。每条轨道必须通过源哈希、结构、跨文件、质量、打包选择与回归检查。', '',
              'Run country/locale tracks in parallel with disjoint ownership. A single integrator regenerates the shared manifest and reports after all checks pass.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--download', action='store_true', help='Re-fetch exact locked source bytes; never update pins')
    parser.add_argument('--check', action='store_true', help='Compare all generated outputs without writing')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        lock = verify_sources(root, args.download)
        outputs, report = build(root)
        differences = []
        for relative, content in outputs.items():
            path = ensure_under(root, relative)
            if args.check:
                if not path.is_file() or path.read_bytes() != content:
                    differences.append(relative)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        if differences:
            print(json.dumps({'status':'stale-generated-output','files':differences},ensure_ascii=False,indent=2))
            return 1
        print(json.dumps({'status':'verified' if args.check else 'generated', 'sources':len(lock['sources']),
                          'outputs':len(outputs),'countries':report['countryCount'],'locales':report['localeCount'],
                          'nodes':report['totalNodes']},ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError, KeyError, ET.ParseError) as error:
        print(f'Import failed: {error}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
