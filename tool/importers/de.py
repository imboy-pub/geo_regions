"""Germany adapter: Destatis Gemeindeverzeichnis → CountryDraft.

Source: "Auszug aus dem Gemeindeverzeichnis, Quartalsausgabe 30.06.2026"
(sources/raw/official/de/AuszugGV2QAktuell.xlsx, sheet Onlineprodukt_
Gemeinden30062026; Herausgebergemeinschaft Statistische Ämter des Bundes und
der Länder; redistribution-with-attribution grant in the artifact footer,
Dl-DE-BY-2.0 naming on Destatis databases per the Impressum snapshot).

Facts encoded from source inspection (never guessed):
- rows carry Satzbart (level) in column A and the ARS split into
  Land(2)/RB(1)/Kreis(2)/Gemeindeverband(4)/Gemeinde(3) in columns C-G.
- 16 Land rows (01..16) — the legacy seed ids iso3166-2:DE-XX are preserved
  untouched; the crosswalk is the official Land-code order.
- 29 RB-tier rows: only the four RB-Länder (NW 05 / HE 06 / BW 08 / BY 09)
  carry current administrative Regierungsbezirke (19). Niedersachsen's
  "Statistische Region" rows and the "früher:" former RBs/Direktionsbezirke
  (RP 07x, SN 14x) are not current administration → per-row excluded records.
- 12 Satzbart-30 rows are the Baden-Württemberg planning "Regionen" between
  RB and Kreis — outside the declared profile → per-row excluded records.
- 401 Satzbart-40 rows are Kreise (Textkennzeichen 41/42 kreisfreie Städte +
  Stadtkreise, 43/44 Landkreise, 45 the Regionalverband Saarbrücken).
- 4,583 Satzbart-50 rows are the Gemeindeverband (Verwaltungsgemeinschaft,
  Amt, VVG …) association layer — not a profile tier; whole-layer exclusion
  (same pattern as US place/MCD), documented in the profile, no per-row
  records.
- 10,943 Satzbart-60 rows: 10,747 politically self-governing Gemeinden
  (TK 60-64, 67) and 196 gemeindefreie Gebiete/Bezirke (TK 65/66,
  unincorporated — not politically self-governing → per-row excluded
  records).
- AGS (8 digits) = Land2+RB1+Kreis2+Gemeinde3 = columns C+D+E+G; the
  quarterly Gebietsstand snapshot contains no abolished rows. The adapter
  still supports abolished AGS rows via an explicit successor map
  (fixture-proven): the old AGS never becomes an active node and the
  migration record carries de-gemeinde:{successor} as newId — never a
  name-guess.
- kreisfreie Städte exist at both tiers exactly as the official register
  lists them (Satzart 40 row + Satzart 60 row); the Gemeinde node parents
  to the Kreis node of the same entity.
- names are official German, verbatim, including statutory suffixes like
  "Flensburg, Stadt" or "Tüßling, M" (nameLocale de, source-native).
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
SNAPSHOT = Path('sources/raw/official/de/AuszugGV2QAktuell.xlsx')

# Official Land-code order → ISO 3166-2:DE subdivision codes. All 16 ids
# exist in the seed; the legacy state ids are preserved untouched.
LAND_ISO = {
    '01': 'DE-SH', '02': 'DE-HH', '03': 'DE-NI', '04': 'DE-HB',
    '05': 'DE-NW', '06': 'DE-HE', '07': 'DE-RP', '08': 'DE-BW',
    '09': 'DE-BY', '10': 'DE-SL', '11': 'DE-BE', '12': 'DE-BB',
    '13': 'DE-MV', '14': 'DE-SN', '15': 'DE-ST', '16': 'DE-TH',
}

# The four Länder whose current administrative structure contains
# Regierungsbezirke (per the source: only these carry unmarked RB rows).
RB_LANDS = frozenset({'05', '06', '08', '09'})

RB_TIER_EXCLUSION_MARKERS = ('früher:', 'Statistische Region')

KREIS_KIND_BY_TK = {'41': 'kreisfreie-stadt', '42': 'kreisfreie-stadt',
                    '45': 'regionalverband'}


def _data_sheet(z) -> str:
    """Resolve the Onlineprodukt_Gemeinden sheet target from the workbook."""
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid_target = {
        r.get('Id'): r.get('Target')
        for r in rels.iter('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
    }
    for s in wb.iter(f'{NS}sheet'):
        rid = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target = rid_target.get(rid, '')
        if (s.get('name') or '').startswith('Onlineprodukt_Gemeinden'):
            return 'xl/' + target.lstrip('/')
    raise ValueError('Onlineprodukt_Gemeinden sheet not found')


def parse_official_xlsx(path) -> list:
    """Parse the locked quarterly GV snapshot into SourceNode rows.

    Level routing (Satzart → kind): 10 land, 20 regierungsbezirk /
    statistical-region / former-regierungsbezirk, 30 region, 40 kreis /
    kreisfreie-stadt / regionalverband, 60 gemeinde / gemeindefreies-gebiet.
    Satzbart 50 (Gemeindeverband association layer) is not a profile tier
    and never becomes rows.
    """
    z = zipfile.ZipFile(path)
    ss = [''.join(t.text or '' for t in si.iter(f'{NS}t'))
          for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(f'{NS}si')]
    sheet = ET.fromstring(z.read(_data_sheet(z)))
    rows: list = []
    for row in sheet.iter(f'{NS}row'):
        cells = {}
        for c in row.findall(f'{NS}c'):
            col = re.findall(r'[A-Z]+', c.get('r') or '')[0]
            t, v = c.get('t'), c.find(f'{NS}v')
            cells[col] = '' if v is None else (ss[int(v.text)] if t == 's' else v.text)
        sa = cells.get('A', '').strip()
        if sa not in {'10', '20', '30', '40', '60'}:
            continue  # header, footers, and the Satzbart-50 association layer
        land = cells.get('C', '').strip()
        rb = cells.get('D', '').strip()
        kreis = cells.get('E', '').strip()
        gem = cells.get('G', '').strip()
        name = cells.get('H', '').strip()
        tk = (cells.get('B') or '').strip()
        if sa == '10':
            rows.append(SourceNode(
                official_code=land, parent_code='', kind='land', name=name,
                name_locale='de', name_quality='source-native',
                children_status='complete', abolished=False))
            continue
        if sa == '20':
            admin_rb = (land in RB_LANDS
                        and not name.startswith(RB_TIER_EXCLUSION_MARKERS))
            kind = 'regierungsbezirk' if admin_rb else (
                'statistical-region' if name.startswith('Statistische Region')
                else 'former-regierungsbezirk')
            rows.append(SourceNode(
                official_code=land + rb, parent_code=land, kind=kind,
                name=name, name_locale='de', name_quality='source-native',
                children_status='complete' if admin_rb else 'unknown',
                abolished=False))
            continue
        if sa == '30':
            rows.append(SourceNode(
                official_code=land + rb + kreis, parent_code=land + rb,
                kind='region', name=name, name_locale='de',
                name_quality='source-native', children_status='unknown',
                abolished=False))
            continue
        if sa == '40':
            kind = KREIS_KIND_BY_TK.get(tk, 'kreis')
            rows.append(SourceNode(
                official_code=land + rb + kreis,
                parent_code=land + rb if land in RB_LANDS else land,
                kind=kind, name=name, name_locale='de',
                name_quality='source-native', children_status='complete',
                abolished=False))
            continue
        # sa == '60'
        kind = 'gemeindefreies-gebiet' if tk in {'65', '66'} else 'gemeinde'
        rows.append(SourceNode(
            official_code=land + rb + kreis + gem,
            parent_code=land + rb + kreis, kind=kind, name=name,
            name_locale='de', name_quality='source-native',
            children_status='unknown', abolished=False))
    return rows


_EXCLUDED_REASON = {
    'statistical-region': ('statistical region, not current administrative '
                           'Regierungsbezirk'),
    'former-regierungsbezirk': ('marked "früher:" by the source — former '
                                'administrative unit retained for statistics'),
    'region': ('Baden-Württemberg planning Region between RB and Kreis; '
               'outside the declared profile'),
    'gemeindefreies-gebiet': ('unincorporated area; not politically '
                              'self-governing, outside the Gemeinde profile'),
}


def build_nodes(rows, successors=None) -> tuple[list, list]:
    """Normalize SourceNode rows into seed-shaped active nodes + migrations.

    - Land rows are crosswalk targets only: no node is emitted, the 16
      legacy iso3166-2:DE-XX ids stay untouched (verified by the caller).
    - regierungsbezirk → de-regbez:{ARS[:3]}; kreis-tier → de-kreis:{ARS[:5]};
      gemeinde → de-gemeinde:{AGS}.
    - Kreis under an RB-Land parents de-regbez:{RB}; otherwise the Land node.
    - statistical-region / former-regierungsbezirk / region /
      gemeindefreies-gebiet rows route to per-row excluded migration records.
    - Abolished AGS rows route to migrations; when an explicit successor map
      names the absorbing Gemeinde the record carries newId (never guessed).
    """
    successors = successors or {}
    active: list = []
    migrations: list = []
    seen: set = set()
    for n in rows:
        if n.kind == 'land':
            if n.official_code not in LAND_ISO:
                raise ValueError(f'unknown Land code: {n.official_code}')
            continue
        if n.abolished:
            rec = {'officialCode': n.official_code, 'name': n.name,
                   'disposition': 'abolished',
                   'reason': 'abolished AGS (Gebietsreform); the locked '
                             'quarterly snapshot is a Gebietsstand edition '
                             'and carries no abolished rows'}
            succ = successors.get(n.official_code)
            if succ:
                rec.update(disposition='merged',
                           newId=f'de-gemeinde:{succ}',
                           reason='Gebietsreform merge; successor recorded '
                                  'from an explicit successor map (never '
                                  'name-guessed)')
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
        if n.official_code in seen:
            raise ValueError(f'duplicate official code: {n.official_code}')
        seen.add(n.official_code)
        if n.kind == 'regierungsbezirk':
            node = {
                'id': f'de-regbez:{n.official_code}',
                'parentId': f'iso3166-2:{LAND_ISO[n.parent_code]}',
                'kind': n.kind, 'code': n.official_code, 'name': n.name,
                'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                'childrenStatus': n.children_status,
            }
        elif n.kind in ('kreis', 'kreisfreie-stadt', 'regionalverband'):
            parent_id = (f'de-regbez:{n.parent_code}'
                         if len(n.parent_code) == 3
                         else f'iso3166-2:{LAND_ISO[n.parent_code]}')
            node = {
                'id': f'de-kreis:{n.official_code}',
                'parentId': parent_id,
                'kind': n.kind, 'code': n.official_code, 'name': n.name,
                'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                'childrenStatus': n.children_status,
            }
        else:  # gemeinde
            node = {
                'id': f'de-gemeinde:{n.official_code}',
                'parentId': f'de-kreis:{n.parent_code}',
                'kind': n.kind, 'code': n.official_code, 'name': n.name,
                'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                'childrenStatus': n.children_status,
            }
        active.append(node)
    return active, migrations


def build(root, successors=None) -> tuple[list, list]:
    return build_nodes(parse_official_xlsx(Path(root) / SNAPSHOT), successors)
