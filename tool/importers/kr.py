"""South Korea adapter: MOIS 행정기관코드 (KIKcd_H) → CountryDraft.

Sources (sources/raw/official/kr/):
- jscode20261026.zip — active 행정기관 codes (2026-10-26 기준)
- jscode20261026-abolished-included.zip — same package including 말소 rows
- license: KOGL Type 1 (공공누리 출처표시) per the MOIS copyright policy page

Source-verified facts (never guessed):
- 16 metropolitan rows as of the integration epoch: 광주·전남 merged into
  전남광주통합특별시 (code 12) effective 2026-07-01 — the 말소 file shows
  전라남도 4600000000 말소 20260701. The seed's iso3166-2:KR-29 (Gwangju)
  and KR-46 (South Jeolla) are therefore replaced entities: the legacy nodes
  stay (ISO assignments persist) and the replacement is recorded in
  migrations/KR.json.
- 세종특별자치시 = 3600000000 (metropolitan row) → legacy iso3166-2:KR-50.
- 서울 구 rows are 자치구 (autonomous); 광역시 구 rows are 일반구
  (non-autonomous) — official type by parent city, never name matching.
- 읍면동/리 rows are outside the profile (D column non-empty → skipped).
"""
from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tool.importers.common import SourceNode
except ModuleNotFoundError:  # script context: tool/ itself is sys.path[0]
    from importers.common import SourceNode

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ACTIVE_ZIP = Path('sources/raw/official/kr/jscode20261026.zip')

# MOIS 2-digit metropolitan numbering → legacy seed ISO node ids.
# 12 (전남광주통합특별시) is NEW — no legacy id; KR-29/KR-46 are its
# replaced predecessors recorded in migrations.
METRO_ISO = {
    '11': 'KR-11', '26': 'KR-26', '27': 'KR-27', '28': 'KR-28',
    '30': 'KR-30', '31': 'KR-31', '36': 'KR-50', '41': 'KR-41',
    '43': 'KR-43', '44': 'KR-44', '47': 'KR-47', '48': 'KR-48',
    '50': 'KR-49', '51': 'KR-42', '52': 'KR-45',
}
SEOUL_TWO = '11'


def _kikcd_h_rows(zip_path):
    z = zipfile.ZipFile(zip_path)
    name = [n for n in z.namelist() if 'KIKcd_H' in n and n.endswith('.xlsx')][0]
    zz = zipfile.ZipFile(io.BytesIO(z.read(name)))
    ss = [''.join(t.text or '' for t in si.iter(f'{NS}t'))
          for si in ET.fromstring(zz.read('xl/sharedStrings.xml')).findall(f'{NS}si')]
    sheet = ET.fromstring(zz.read('xl/worksheets/sheet1.xml'))
    out = []
    for row in sheet.iter(f'{NS}row'):
        cells = {}
        for c in row.findall(f'{NS}c'):
            col = re.findall(r'[A-Z]+', c.get('r') or 'A')[0]
            t, v = c.get('t'), c.find(f'{NS}v')
            cells[col] = '' if v is None else (ss[int(v.text)] if t == 's' else v.text)
        out.append(cells)
    return out


def _kind_of(code, name, parent_two):
    suffix = name[-1:] if name else ''
    if suffix == '구':
        return 'autonomous-district' if parent_two == SEOUL_TWO else 'non-autonomous-district'
    if suffix == '군':
        return 'county'
    if suffix == '시':
        return 'city'
    return 'municipality'


def parse_active(zip_path=ACTIVE_ZIP):
    """Active 시도 + 시군구 SourceNode rows (읍면동/리 rows are outside the
    profile and skipped; 세종's duplicate umbrella row 3611000000 skipped)."""
    out = []
    for cells in _kikcd_h_rows(zip_path)[1:]:
        code = cells.get('A', '').strip()
        if not (code.isdigit() and len(code) == 10):
            continue
        sido = cells.get('B', '').strip()
        sigungu = cells.get('C', '').strip()
        if code.endswith('00000000'):
            out.append(SourceNode(code, '', 'metropolitan', sido, 'ko',
                                  'source-native', 'unknown', False))
            continue
        if code[5:] != '00000' or not sigungu or sigungu.endswith('출장소'):
            continue                      # 읍면동/리 and 출장소 branch offices — outside profile
        if code.startswith('3611'):
            continue                      # 세종 umbrella duplicate (metro row above)
        kind = _kind_of(code, sigungu, code[:2])
        out.append(SourceNode(code, code[:2], kind, sigungu, 'ko',
                              'source-native', 'unknown', False))
    return out


def parse_abolished(zip_path=Path('sources/raw/official/kr/jscode20261026-abolished-included.zip')):
    """말소 rows at 시군구 level (metropolitan rows recorded too when the
    integration epoch replaced them) — migration records, never active."""
    out = []
    for cells in _kikcd_h_rows(zip_path)[1:]:
        code = cells.get('A', '').strip()
        if not (code.isdigit() and len(code) == 10):
            continue
        malso = cells.get('F', '').strip()
        if not malso:
            continue
        if code[5:] != '00000':
            continue                      # 읍면동-level history stays in the snapshot
        sido = cells.get('B', '').strip()
        sigungu = cells.get('C', '').strip()
        kind = ('metropolitan' if code.endswith('00000000')
                else _kind_of(code, sigungu, code[:2]))
        out.append(SourceNode(code, code[:2], kind,
                              sigungu or sido, 'ko', 'source-native', 'unknown', True))
    return out


def build_nodes(rows, abolished_rows=()):
    """Seed-shaped active nodes + migration records.

    Metropolitan crosswalk: legacy ISO ids preserved for the 15 mapping
    metros; 전남광주통합특별시 (code 12) is new — kr-municipality:1200000000.
    KR-29/KR-46 replacements are recorded for the import step to attach to
    the legacy CLDR nodes' coverage."""
    active, migrations = [], []
    replaced_legacy = []
    metro_by_two = {}
    for n in rows:
        if n.abolished:
            migrations.append({
                'officialCode': n.official_code,
                'name': n.name,
                'disposition': 'abolished',
                'note': '말소코드 (MOIS 말소코드포함 package)',
            })
            continue
        if n.kind == 'metropolitan':
            iso = METRO_ISO.get(n.official_code[:2])
            node_id = f'iso3166-2:{iso}' if iso else f'kr-municipality:{n.official_code}'
            if n.official_code == '1200000000':
                replaced_legacy.append('iso3166-2:KR-29')
                replaced_legacy.append('iso3166-2:KR-46')
            node = {'id': node_id, 'parentId': 'cc:KR', 'kind': 'subdivision',
                    'code': iso or n.official_code,
                    'name': n.name, 'nameLocale': 'ko', 'nameQuality': 'source-native',
                    'childrenStatus': n.children_status}
            active.append(node)
            metro_by_two[n.official_code[:2]] = node_id
            continue
        node = {
            'id': f'kr-municipality:{n.official_code}',
            'parentId': metro_by_two.get(n.parent_code[:2], f'iso3166-2:{METRO_ISO.get(n.parent_code[:2])}'),
            'kind': n.kind,
            'code': n.official_code[:5],
            'name': n.name,
            'nameLocale': 'ko',
            'nameQuality': 'source-native',
            'childrenStatus': n.children_status,
        }
        active.append(node)
    for n in abolished_rows:
        migrations.append({
            'officialCode': n.official_code,
            'name': n.name,
            'disposition': 'abolished',
            'abolishedAt': None,
            'note': '말소코드 (MOIS 말소코드포함 package); pre-integration entities',
        })
    for legacy in replaced_legacy:
        migrations.append({
            'officialCode': legacy,
            'name': None,
            'disposition': 'replaced-by',
            'replacedById': 'kr-municipality:1200000000',
            'effectiveDate': '2026-07-01',
            'note': '광주·전남 통합: 전남광주통합특별시 launched 2026-07-01 (말소 4600000000=20260701); ISO assignments persist, legacy nodes stay with recorded replacement',
        })
    return active, migrations


def build(root):
    root = Path(root)
    rows = parse_active(root / ACTIVE_ZIP)
    abolished = parse_abolished(root / 'sources/raw/official/kr/jscode20261026-abolished-included.zip')
    return build_nodes(rows, abolished)
