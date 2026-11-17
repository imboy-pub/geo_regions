"""France adapter: INSEE Code officiel géographique 2026 → CountryDraft.

Sources (sources/raw/official/fr/, COG 2026 = situation au 1er janvier 2026;
Institut national de la statistique et des études économiques; licence fr-lo =
Licence Ouverte / Open Licence 2.0 per the INSEE publisher record on
data.gouv.fr, id 58c984b088ee386cdb1261f3):
- v_region_2026.csv (18 régions), v_departement_2026.csv (101 départements),
  v_commune_2026.csv (37,496 rows).
- Overseas collectivities left the commune file in 2022: current units come
  from v_tom_depuis_1943.csv (9 current collectivités/territoires) and
  v_commune_outremer_depuis_1943.csv (95 current zonages, 85 nature COM),
  filtered by the COG 2026 reference date.

Facts encoded from source inspection (never guessed):
- TYPECOM column: COM (politically independent commune) / COMD (commune
  déléguée) / COMA (commune associée) / ARM (arrondissement municipal of
  Paris/Lyon/Marseille). COMPARENT carries the commune nouvelle code for
  COMD/COMA and the parent commune for ARM.
- The COG reuses the seat commune's code for a commune nouvelle: code 01015
  is BOTH the active COM "Arboys en Bugey" and the déléguée "Arbignieu"
  (1943-2016). A déléguée row therefore never becomes an active node — it is
  routed to an absorbed migration record whose newId is fr-commune:{COMPARENT}.
- CTCD rows (collectivités territoriales à compétences départementales, e.g.
  69M Métropole de Lyon) are a competence-body layer, not a profile tier:
  whole-layer exclusion.
- Overseas zonage natures: COM (commune — 85 rows kept), DIS (TAAF districts),
  CIR (Wallis circonscriptions), CDM (condominium), CPT (Clipperton) — the
  non-COM ones are not communes and are per-row excluded records.
- Legacy ISO↔INSEE correspondence (fixed official table, never name-guessed):
  12 métropole regions + FR-20R→94; departments carry the same number
  (FR-01→01 … FR-2A/2B, FR-6AE→69 Rhône); FR-75C→fr-commune:75056 Paris
  (commune à statut particulier exercising department competences); DROM
  FR-971..976 are the department codes; overseas collectivities
  FR-BL/MF/PM/WF/PF/NC/CP/TF → 977/978/975/986/987/988/989/984. FR-69M
  (Métropole de Lyon, CTCD tier) has no profile counterpart and stays legacy
  with an unmapped record.
- Names are the official French LIBELLE column verbatim (nameLocale fr,
  nameQuality source-native). Per the plan name rule, legacy names are NOT
  inherited on re-id: new ids start with source-native French names and other
  locales stay missing (sparse packs).
"""
from __future__ import annotations

import csv
from pathlib import Path

try:
    from tool.importers.common import SourceNode
except ModuleNotFoundError:  # script context: tool/ itself is sys.path[0]
    from importers.common import SourceNode

SOURCE_DIR = Path('sources/raw/official/fr')
REFERENCE_DATE = '2026-01-01'

# INSEE department codes that sit beneath a region (métropole 2-digit and the
# five DROM departments); overseas collectivity prefixes parent communes
# directly (no department tier in the COG).
DROM_DEPS = frozenset({'971', '972', '973', '974', '976'})

ZONAGE_KIND = {'DIS': 'overseas-district', 'CIR': 'overseas-circonscription',
               'CDM': 'overseas-condominium', 'CPT': 'overseas-territory'}

# Legacy ISO 3166-2:FR → INSEE codes (official correspondence; department
# numbers are shared by ISO and INSEE and handled separately). Keys are the
# id suffix AFTER stripping 'iso3166-2:FR-' (the GB batch hit this exact
# removeprefix trap: 'FR-ARA' would never match).
REGION_ISO = {
    'ARA': '84', 'BFC': '27', 'BRE': '53', 'CVL': '24',
    'GES': '44', 'HDF': '32', 'IDF': '11', 'NOR': '28',
    'NAQ': '75', 'OCC': '76', 'PAC': '93', 'PDL': '52',
    '20R': '94',
}
OVERSEAS_ISO = {
    'BL': '977', 'CP': '989', 'MF': '978', 'NC': '988',
    'PF': '987', 'PM': '975', 'TF': '984', 'WF': '986',
}
DROM_DEP_ISO = {'971': '971', '972': '972', '973': '973',
                '974': '974', '976': '976'}
SPECIAL_ISO = {'6AE': ('fr-department', '69'),      # Rhône
               '75C': ('fr-commune', '75056')}      # Paris


def _rows(csv_path):
    with open(csv_path, encoding='utf-8') as f:
        yield from csv.DictReader(f)


def _is_current(date_fin: str) -> bool:
    return (not date_fin) or date_fin >= REFERENCE_DATE


def parse_official_files(source_dir=SOURCE_DIR) -> list:
    """Parse the locked COG 2026 files into SourceNode rows.

    Absorbed rows (COMD/COMA) are marked abolished=True with parent_code =
    COMPARENT (the commune nouvelle successor); routing happens in
    build_nodes. ARM and non-COM overseas zonages keep abolished=False and
    route by kind.
    """
    d = Path(source_dir)
    rows: list = []
    for r in _rows(d / 'v_region_2026.csv'):
        rows.append(SourceNode(
            official_code=r['REG'].strip(), parent_code='', kind='region',
            name=r['LIBELLE'].strip(), name_locale='fr',
            name_quality='source-native', children_status='complete',
            abolished=False))
    for r in _rows(d / 'v_departement_2026.csv'):
        rows.append(SourceNode(
            official_code=r['DEP'].strip(), parent_code=r['REG'].strip(),
            kind='department', name=r['LIBELLE'].strip(), name_locale='fr',
            name_quality='source-native', children_status='complete',
            abolished=False))
    for r in _rows(d / 'v_commune_2026.csv'):
        typecom = r['TYPECOM'].strip()
        code = r['COM'].strip()
        name = r['LIBELLE'].strip()
        if typecom == 'COM':
            rows.append(SourceNode(
                official_code=code, parent_code=r['DEP'].strip(),
                kind='commune', name=name, name_locale='fr',
                name_quality='source-native', children_status='unknown',
                abolished=False))
        elif typecom in ('COMD', 'COMA'):
            kind = 'commune-deleguee' if typecom == 'COMD' else 'commune-associee'
            rows.append(SourceNode(
                official_code=code, parent_code=(r['COMPARENT'] or '').strip(),
                kind=kind, name=name, name_locale='fr',
                name_quality='source-native', children_status='unknown',
                abolished=True))
        elif typecom == 'ARM':
            rows.append(SourceNode(
                official_code=code, parent_code=(r['COMPARENT'] or '').strip(),
                kind='arrondissement-municipal', name=name, name_locale='fr',
                name_quality='source-native', children_status='unknown',
                abolished=False))
        else:
            raise ValueError(f'unknown TYPECOM: {typecom}')
    # overseas collectivities + their communes (outside v_commune since 2022)
    overseas_com_prefixes = set()
    for r in _rows(d / 'v_commune_outremer_depuis_1943.csv'):
        if not _is_current(r['DATE_FIN'].strip()):
            continue
        code = r['COM_COMER'].strip()
        nature = r['NATURE_ZONAGE'].strip()
        name = r['LIBELLE'].strip()
        if nature == 'COM':
            overseas_com_prefixes.add(code[:3])
            rows.append(SourceNode(
                official_code=code, parent_code=code[:3], kind='commune',
                name=name, name_locale='fr', name_quality='source-native',
                children_status='unknown', abolished=False))
        else:
            rows.append(SourceNode(
                official_code=code, parent_code='', kind=ZONAGE_KIND[nature],
                name=name, name_locale='fr', name_quality='source-native',
                children_status='unknown', abolished=False))
    for r in _rows(d / 'v_tom_depuis_1943.csv'):
        if not _is_current(r['DATE_FIN'].strip()):
            continue
        code = r['COMER'].strip()
        rows.append(SourceNode(
            official_code=code, parent_code='', kind='collectivite-outremer',
            name=r['LIBELLE'].strip(), name_locale='fr',
            name_quality='source-native',
            children_status='complete' if code in overseas_com_prefixes
            else 'unknown',
            abolished=False))
    return rows


_EXCLUDED_REASON = {
    'arrondissement-municipal': ('arrondissement municipal — sub-commune '
                                 'administrative unit of Paris/Lyon/Marseille, '
                                 'outside the commune profile'),
    'overseas-district': ('TAAF district — administrative sub-zonage, not a '
                          'commune'),
    'overseas-circonscription': ('Wallis-et-Futuna circonscription '
                                 'territoriale — not a commune'),
    'overseas-condominium': ('condominium zonage — not a commune'),
    'overseas-territory': ('non-commune territory zonage — not a commune'),
}


def _map_legacy(legacy_id: str, dept_codes: set) -> tuple | None:
    """Return (idPrefix, inseeCode) for a legacy iso3166-2:FR-… id, or None."""
    suffix = legacy_id.removeprefix('iso3166-2:FR-')
    if suffix in REGION_ISO:
        return ('fr-region', REGION_ISO[suffix])
    if suffix in OVERSEAS_ISO:
        return ('fr-region', OVERSEAS_ISO[suffix])
    if suffix in DROM_DEP_ISO:
        return ('fr-department', DROM_DEP_ISO[suffix])
    if suffix in SPECIAL_ISO:
        return SPECIAL_ISO[suffix]
    if suffix in dept_codes:
        return ('fr-department', suffix)
    return None


def identity_keys(node) -> str:
    """Tier-aware identity key for validate_draft: INSEE legally reuses the
    same number across tiers (region 01 Guadeloupe vs department 01 Ain), so
    the bare official_code is not an identity — the tier-prefixed id is."""
    if node.kind in ('region', 'collectivite-outremer'):
        return f'fr-region:{node.official_code}'
    if node.kind == 'department':
        return f'fr-department:{node.official_code}'
    if node.kind == 'commune':
        return f'fr-commune:{node.official_code}'
    return f'{node.kind}:{node.official_code}'


def parent_identity_key(node) -> str:
    """Mirror of the build_nodes parent rule, for validate_draft lookups."""
    if node.kind == 'department':
        return f'fr-region:{node.parent_code}'
    if node.kind == 'commune':
        return (f'fr-department:{node.parent_code}'
                if (len(node.parent_code) == 2
                    or node.parent_code in DROM_DEPS)
                else f'fr-region:{node.parent_code}')
    if node.kind == 'arrondissement-municipal':
        return f'fr-commune:{node.parent_code}'
    return f'fr-region:{node.parent_code}' if node.parent_code else ''


def build_nodes(rows, legacy_nodes=()) -> tuple[list, list, list]:
    """Normalize SourceNode rows into seed-shaped active nodes + records.

    Returns (active, migrations, unmapped):
    - active: fr-region/fr-department/fr-commune nodes (parent chains complete)
    - migrations: absorbed COMD/COMA records (newId from COMPARENT) and
      per-row excluded ARM/non-commune-zonage records
    - unmapped: legacy nodes with no crosswalk target (kept as legacy nodes)
    """
    active: list = []
    migrations: list = []
    seen: set = set()  # node ids — INSEE reuses numbers across tiers
    dept_codes = {n.official_code for n in rows if n.kind == 'department'}
    for n in rows:
        if n.abolished:  # COMD/COMA — absorbed into the commune nouvelle
            rec = {'officialCode': n.official_code, 'name': n.name,
                   'disposition': 'absorbed',
                   'reason': ('former commune merged into a commune nouvelle; '
                              'the COG COMPARENT column carries the successor '
                              'code, which may reuse the seat commune code')}
            if n.parent_code:
                rec['newId'] = f'fr-commune:{n.parent_code}'
            migrations.append(rec)
            continue
        if n.kind in _EXCLUDED_REASON:
            migrations.append({
                'officialCode': n.official_code, 'name': n.name,
                'disposition': 'excluded',
                'reason': _EXCLUDED_REASON[n.kind] + '; per-row excluded '
                          'record, never an active node',
            })
            continue
        if n.kind == 'region':
            node = {'id': f'fr-region:{n.official_code}', 'parentId': 'cc:FR',
                    'kind': n.kind, 'code': n.official_code, 'name': n.name,
                    'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                    'childrenStatus': n.children_status}
        elif n.kind == 'collectivite-outremer':
            node = {'id': f'fr-region:{n.official_code}', 'parentId': 'cc:FR',
                    'kind': n.kind, 'code': n.official_code, 'name': n.name,
                    'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                    'childrenStatus': n.children_status}
        elif n.kind == 'department':
            node = {'id': f'fr-department:{n.official_code}',
                    'parentId': f'fr-region:{n.parent_code}',
                    'kind': n.kind, 'code': n.official_code, 'name': n.name,
                    'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                    'childrenStatus': n.children_status}
        else:  # commune
            parent = (f'fr-department:{n.parent_code}'
                      if (len(n.parent_code) == 2
                          or n.parent_code in DROM_DEPS)
                      else f'fr-region:{n.parent_code}')
            node = {'id': f'fr-commune:{n.official_code}',
                    'parentId': parent,
                    'kind': n.kind, 'code': n.official_code, 'name': n.name,
                    'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                    'childrenStatus': n.children_status}
        if node['id'] in seen:
            raise ValueError(f'duplicate active node id: {node["id"]}')
        seen.add(node['id'])
        active.append(node)

    # legacy ISO crosswalk: re-id through the fixed official correspondence,
    # record every row; nodes without a counterpart stay legacy (unmapped).
    # Two passes: a mapped legacy parent may be removed while its unmapped
    # child stays, so unmapped records carry the parent's reParentedTo target
    # (an explicit parent change per design §7, applied by the import loop).
    active_ids = {n['id'] for n in active}
    unmapped: list = []
    targets: dict = {}
    reid_by_old: dict = {}
    for leg in legacy_nodes:
        leg_id = str(leg.get('id') or '')
        targets[leg_id] = (_map_legacy(leg_id, dept_codes)
                           if leg_id.startswith('iso3166-2:FR-') else None)
    for leg_id, target in targets.items():
        if target is None:
            continue
        prefix, code = target
        new_id = f'{prefix}:{code}'
        if new_id not in active_ids:
            raise ValueError(f'crosswalk target missing from COG rows: '
                             f'{leg_id} → {new_id}')
        reid_by_old[leg_id] = new_id
        migrations.append({'oldId': leg_id, 'newId': new_id,
                           'name': next(leg.get('name') for leg in legacy_nodes
                                        if str(leg.get('id') or '') == leg_id),
                           'method': 'official-iso-insee-crosswalk'})
    for leg in legacy_nodes:
        leg_id = str(leg.get('id') or '')
        if targets.get(leg_id) is not None:
            continue
        rec = {'oldId': leg_id, 'name': leg.get('name'),
               'reason': ('not an iso3166-2:FR- id' if not leg_id.startswith('iso3166-2:FR-')
                          else 'no region/department/commune counterpart in '
                               'the COG 2026 (tier mismatch or outside the '
                               'profile); legacy node kept')}
        old_parent = str(leg.get('parentId') or '')
        if old_parent in reid_by_old:
            rec['reParentedTo'] = reid_by_old[old_parent]
        unmapped.append(rec)
    return active, migrations, unmapped


def build(root, legacy_nodes=()) -> tuple[list, list, list]:
    return build_nodes(parse_official_files(Path(root) / SOURCE_DIR),
                       legacy_nodes)
