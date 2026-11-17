"""Great Britain adapter: ONS Local Authority Districts → CountryDraft.

Source: ONS Open Geography Portal "Local Authority Districts (December 2024)
Boundaries UK BUC" feature service (sources/raw/official/gb/
lad-dec2024-uk-buc-query.json, 361 records; OGL v3.0 per the ONS licensing
page snapshot).

Source-verified facts (never guessed):
- fields LAD24CD (GSS code, first letter E/S/W/N = constituent country),
  LAD24NM (English name), LAD24NMW (Welsh name — out of locale scope).
- 361 LADs = England 296 + Scotland 32 + Wales 22 + NI 11.
- The legacy CLDR tree (217 subdivision rows) parents to the four
  constituent countries; SCT/WLS/NI legacy sets are LAD-tier, England's
  152 legacy rows are the ISO subset of the 296 England LADs.

Migration rule (design §7 — no heuristic re-parenting): a legacy row is
re-ided to gb-lad:{GSS} only on a unique exact source-name match within
its constituent country; everything else stays legacy with an explicit
unmapped record.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from tool.importers.common import SourceNode
except ModuleNotFoundError:  # script context: tool/ itself is sys.path[0]
    from importers.common import SourceNode

LAD_QUERY = Path('sources/raw/official/gb/lad-dec2024-uk-buc-query.json')
COUNTRY_BY_LETTER = {
    'E': 'iso3166-2:GB-ENG',
    'S': 'iso3166-2:GB-SCT',
    'W': 'iso3166-2:GB-WLS',
    'N': 'iso3166-2:GB-NIR',
}


def parse_lad_query(json_path) -> list:
    doc = json.loads(Path(json_path).read_text(encoding='utf-8'))
    out: list = []
    for feat in doc.get('features', []):
        a = feat.get('attributes', {})
        code = (a.get('LAD24CD') or '').strip()
        name = (a.get('LAD24NM') or '').strip()
        if not code:
            continue
        out.append(SourceNode(
            official_code=code,
            parent_code=code[:1],
            kind='local-authority',
            name=name,
            name_locale='en',
            name_quality='source-native',
            children_status='unknown',
            abolished=False,
        ))
    return out


def build_nodes(rows, legacy_nodes=()):
    """rows: ONS LAD SourceNode rows; legacy_nodes: existing seed GB
    subdivision dicts (id/code/name/parentId).

    Returns (lad_nodes, migrations, unmapped):
    - lad_nodes: all 361 LAD nodes (parented to constituent countries);
      rows matching a legacy node exactly-by-name-within-country carry
      the migrated identity (the legacy node is retired via migrations)
    - migrations: one record per re-ided legacy node (oldId/newId, method
      'unique-exact-source-name-match')
    - unmapped: legacy nodes with no unique LAD match (they stay legacy)
    """
    active: list = []
    migrations: list = []
    unmapped: list = []

    legacy_by_country: dict[str, list] = {}
    for leg in legacy_nodes:
        parent = str(leg.get('parentId') or '')
        if not parent.startswith('iso3166-2:GB-'):
            continue
        letter = {'ENG': 'E', 'SCT': 'S', 'WLS': 'W', 'NIR': 'N'}.get(
            parent.removeprefix('iso3166-2:GB-'), '')
        if letter:
            legacy_by_country.setdefault(letter, []).append(leg)

    used_legacy: set[str] = set()
    for n in rows:
        letter = n.parent_code[:1]
        country_id = COUNTRY_BY_LETTER.get(letter)
        if country_id is None:
            migrations.append({
                'officialCode': n.official_code, 'name': n.name,
                'disposition': 'unmapped',
                'reason': 'no country relation (GSS first letter outside E/S/W/N)',
            })
            continue
        candidates = [leg for leg in legacy_by_country.get(letter, [])
                      if leg['id'] not in used_legacy
                      and (leg.get('name') or '').strip() == n.name]
        active.append({
            'id': f'gb-lad:{n.official_code}',
            'parentId': country_id,
            'kind': 'local-authority',
            'code': n.official_code,
            'name': n.name,
            'nameLocale': 'en',
            'nameQuality': 'source-native',
            'childrenStatus': 'unknown',
            '_matchedLegacy': candidates[0]['id'] if len(candidates) == 1 else None,
        })
        if candidates:
            # identical-name legacy rows are tree duplicates of one real
            # entity — retire every duplicate in favour of the single LAD node
            for leg in candidates:
                used_legacy.add(leg['id'])
                migrations.append({
                    'oldId': leg['id'],
                    'newId': f'gb-lad:{n.official_code}',
                    'name': n.name,
                    'disposition': 're-id',
                    'method': 'unique-exact-source-name-match',
                })
            active[-1]['_matchedLegacy'] = True
    for node in active:
        node.pop('_matchedLegacy', None)
    # legacy rows with no unique LAD match stay legacy — record them
    for letter, legs in legacy_by_country.items():
        for leg in legs:
            if leg['id'] not in used_legacy:
                unmapped.append({
                    'oldId': leg['id'], 'name': leg.get('name'),
                    'reason': 'no unique exact-name match within the ONS LAD layer '
                              '(tier mismatch or renamed); legacy node kept',
                })
    return active, migrations, unmapped


def build(root, legacy_nodes=()):
    return build_nodes(parse_lad_query(Path(root) / LAD_QUERY), legacy_nodes)
