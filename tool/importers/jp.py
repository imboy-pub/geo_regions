"""Japan adapter: MIC 全国地方公共団体コード → CountryDraft.

Source: 総務省「都道府県コード及び市区町村コード」(sources/raw/official/jp/
local-gov-code-000925835.xlsx, 令和6年1月1日更新 = effective 2024-01-01,
GoS-2.0 per the e-Stat terms snapshot in the same directory).

Facts encoded from source inspection (never guessed):
- 6-digit codes; prefecture rows have code[2:5]=='000', municipalities the rest.
- 47 prefecture rows (010006 北海道 .. 470007 沖縄県); municipality names are
  Japanese official (漢字 column), nameLocale ja, nameQuality source-native.
- Known source quirks, normalized deterministically:
  * 7 rows carry a trailing half-width-kana run glued onto the 漢字 name cell
    (色丹村シコタンムラ .. 那珂川市ナカガワシ) → strip the kana run.
  * rows 016951..016993 are 北方地域 historical codes (色丹村/泊村トマリ/
    留夜別村/留別村/紗那村) — retained in the official table but not current
    administration → routed to the migration record, never into active nodes.
- 政令指定都市の区 are NOT listed in this source (札幌市 is followed directly
  by 函館市; only the 23 Tokyo special wards appear as 区-suffix rows). Per
  design §3 the sub-level gap stays explicit: ordinance cities keep
  childrenStatus=complete-with-gap? no — unknown, and the gap is recorded in
  sources/migrations/JP.json for the follow-up ward-source slice.
"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tool.importers.common import SourceNode
except ModuleNotFoundError:  # script context: tool/ itself is sys.path[0]
    from importers.common import SourceNode

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
SNAPSHOT = Path('sources/raw/official/jp/local-gov-code-000925835.xlsx')
HALFWIDTH_KANA = re.compile(r'[ｦ-ﾟ]+')

# Tokyo special wards are the only 区 rows in this source.
ORDINANCE_CITY_CODES = frozenset({
    '011002', '041001', '111001', '121001', '141001', '141301', '141911',
    '151001', '221001', '221311', '231001', '261001', '271001', '271401',
    '281001', '331001', '341001', '401001', '401301', '431001',
})
# 北方地域 historical codes retained by the official table (not current
# administration; excluded source-faithfully and routed to migrations).
NORTHERN_TERRITORY_CODES = frozenset({
    '016951', '016969', '016977', '016985', '016993',
})

PREFECTURE_ISO = {
    '01': 'JP-01', '02': 'JP-02', '03': 'JP-03', '04': 'JP-04', '05': 'JP-05',
    '06': 'JP-06', '07': 'JP-07', '08': 'JP-08', '09': 'JP-09', '10': 'JP-10',
    '11': 'JP-11', '12': 'JP-12', '13': 'JP-13', '14': 'JP-14', '15': 'JP-15',
    '16': 'JP-16', '17': 'JP-17', '18': 'JP-18', '19': 'JP-19', '20': 'JP-20',
    '21': 'JP-21', '22': 'JP-22', '23': 'JP-23', '24': 'JP-24', '25': 'JP-25',
    '26': 'JP-26', '27': 'JP-27', '28': 'JP-28', '29': 'JP-29', '30': 'JP-30',
    '31': 'JP-31', '32': 'JP-32', '33': 'JP-33', '34': 'JP-34', '35': 'JP-35',
    '36': 'JP-36', '37': 'JP-37', '38': 'JP-38', '39': 'JP-39', '40': 'JP-40',
    '41': 'JP-41', '42': 'JP-42', '43': 'JP-43', '44': 'JP-44', '45': 'JP-45',
    '46': 'JP-46', '47': 'JP-47',
}


def normalize_name(name: str) -> str:
    """Strip a trailing half-width-kana run glued onto the 漢字 name cell
    (official-file quirk on 7 rows; the kana is kept in the source snapshot)."""
    return HALFWIDTH_KANA.sub('', name).strip()


def classify_kind(code: str, name: str) -> str:
    suffix = name[-1:] if name else ''
    if suffix == '市':
        return 'city'
    if suffix == '区':
        return 'special-ward' if code.startswith('131') else 'ward'
    if suffix == '町':
        return 'town'
    if suffix == '村':
        return 'village'
    return 'municipality'


def parse_official_xlsx(path) -> list:
    """Parse the locked MIC listing into SourceNode rows (active-only logic
    lives in build_nodes; parsing stays source-faithful)."""
    z = zipfile.ZipFile(path)
    ns = NS
    ss = [''.join(t.text or '' for t in si.iter(f'{ns}t'))
          for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(f'{ns}si')]
    sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows: list = []
    for row in sheet.iter(f'{ns}row'):
        cells = {}
        for c in row.findall(f'{ns}c'):
            col = re.findall(r'[A-Z]+', c.get('r') or '')[0]
            t, v = c.get('t'), c.find(f'{ns}v')
            cells[col] = '' if v is None else (ss[int(v.text)] if t == 's' else v.text)
        rows.append(cells)
    rows_out: list = []
    for cells in rows[1:]:
        code = cells.get('A', '').strip()
        if not (code.isdigit() and len(code) == 6):
            continue  # header / non-data row
        name = normalize_name(cells.get('C', '').strip())
        if code[2:5] == '000':
            kind = 'prefecture'
        else:
            kind = classify_kind(code, name)
        abolished = code in NORTHERN_TERRITORY_CODES
        rows_out.append(SourceNode(
            official_code=code,
            parent_code='' if kind == 'prefecture' else code[:2],
            kind=kind,
            name=name if kind != 'prefecture' else normalize_name(cells.get('B', '').strip()),
            name_locale='ja',
            name_quality='source-native',
            children_status='unknown',
            abolished=abolished,
        ))
    return rows_out


def build_nodes(rows) -> tuple[list, list]:
    """Normalize SourceNode rows into seed-shaped active nodes + migrations.

    - prefecture rows keep the legacy seed ids (iso3166-2:JP-XX crosswalk)
    - municipalities/wards get jp-municipality:{6-digit official code}
    - parent resolution: ward→ordinance city by nearest preceding ordinance
      row; city/town/village→prefecture via the 2-digit prefix
    - abolished/北方地域 rows are routed to migrations, never to active nodes
    """
    active: list = []
    migrations: list = []
    ordinance_stack: list[str] = []   # codes of ordinance-designated cities seen so far
    for n in rows:
        if n.abolished or n.official_code in NORTHERN_TERRITORY_CODES:
            migrations.append({
                'officialCode': n.official_code,
                'name': n.name,
                'disposition': 'excluded',
                'reason': ('北方地域 historical code retained by the official table; '
                           'not current administration'),
            })
            continue
        if n.kind == 'prefecture':
            two = n.official_code[:2]
            node = {
                'id': f'iso3166-2:{PREFECTURE_ISO[two]}',
                'kind': 'subdivision',
                'code': f'JP-{two}',
                'name': n.name,
                'nameLocale': 'ja',
                'nameQuality': 'source-native',
                'childrenStatus': n.children_status,
                '_prefCode': n.official_code,
            }
            active.append(node)
            continue
        two = n.official_code[:2]
        parent_id = f'iso3166-2:{PREFECTURE_ISO[two]}'
        if n.official_code in ORDINANCE_CITY_CODES:
            ordinance_stack.append(n.official_code)
        elif n.kind == 'ward' and ordinance_stack:
            parent_id = f'jp-municipality:{ordinance_stack[-1]}'
        node = {
            'id': f'jp-municipality:{n.official_code}',
            'parentId': parent_id,
            'kind': n.kind,
            'code': n.official_code,
            'name': n.name,
            'nameLocale': 'ja',
            'nameQuality': 'source-native',
            'childrenStatus': n.children_status,
        }
        active.append(node)
    # strip internal helper keys
    for node in active:
        node.pop('_prefCode', None)
    return active, migrations


def build(root) -> tuple[list, list]:
    """Full pipeline: locked snapshot → SourceNode rows → draft pieces.

    Returns (active_nodes, migrations) for import_data.build() to merge;
    prefecture rows are NOT merged (the seed already carries the 47 ISO
    nodes and their CLDR names — legacy ids preserved by construction).
    """
    rows = parse_official_xlsx(Path(root) / SNAPSHOT)
    return build_nodes(rows)
