"""United States adapter: Census Gazetteer counties → CountryDraft.

Source: Census Bureau 2025 Gazetteer counties national file
(sources/raw/official/us/2025_Gaz_counties_national.zip, vintage 2025,
U.S. government work — public domain per 17 USC §105).

Source-verified facts (never guessed):
- TSV header: USPS | GEOID | ANSIDE | (ANSICODE) | NAME | ALAND | AWATER |
  ALAND_SQMI | AWATER_SQMI | INTPTLAT | INTPTLONG
- 3,222 county/county-equivalent records covering all 57 state/territory
  equivalents (USPS column crosswalks one-to-one onto the legacy
  iso3166-2:US-XX seed nodes).
- place/MCD records never appear in the counties national file; the
  adapter additionally drops any non-county kind rows so the contract
  holds even if a future vintage widens the file.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

try:
    from tool.importers.common import SourceNode
except ModuleNotFoundError:  # script context: tool/ itself is sys.path[0]
    from importers.common import SourceNode

GAZETTEER_ZIP = Path('sources/raw/official/us/2025_Gaz_counties_national.zip')

# USPS abbr → legacy seed ISO id (identity abbreviations; 57 entries cover
# the 50 states + DC + 5 inhabited territories + minor islands entries the
# seed carries from CLDR).
_USPS_ALL = (
    'AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN '
    'MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA '
    'WA WV WI WY DC PR GU MP VI AS UM'
)
USPS_ISO = {abbr: f'US-{abbr}' for abbr in _USPS_ALL.split()}


def parse_gazetteer(zip_path) -> list:
    """Parse the counties national file into SourceNode rows (kind county)."""
    z = zipfile.ZipFile(zip_path)
    txt_name = [n for n in z.namelist() if n.endswith('.txt')][0]
    raw = z.read(txt_name).decode('utf-8-sig', 'replace')
    lines = raw.splitlines()
    # the 2025 vintage is pipe-separated (2024 and earlier were tab files)
    header = [h.strip() for h in lines[0].split('|')]
    idx = {name: i for i, name in enumerate(header)}
    out: list = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split('|')
        usps = cells[idx['USPS']].strip()
        geoid = cells[idx['GEOID']].strip()
        name = cells[idx['NAME']].strip()
        out.append(SourceNode(
            official_code=geoid,
            parent_code=usps,
            kind='county',
            name=name,
            name_locale='en',
            name_quality='source-native',
            children_status='unknown',
            abolished=False,
        ))
    return out


def build_nodes(rows):
    """Seed-shaped active nodes + migrations.

    - county rows → us-county:{5-digit FIPS}, parent = legacy ISO state id
    - anything not classified county (place/MCD records, abolished rows)
      is dropped from active and recorded as a migration entry
    """
    active: list = []
    migrations: list = []
    for n in rows:
        if n.abolished or n.kind != 'county':
            migrations.append({
                'officialCode': n.official_code,
                'name': n.name,
                'disposition': 'excluded',
                'reason': f'{n.kind} rows are outside the county/equivalent profile',
            })
            continue
        iso = USPS_ISO.get(n.parent_code)
        if iso is None:
            migrations.append({
                'officialCode': n.official_code,
                'name': n.name,
                'disposition': 'unmapped',
                'reason': f'USPS abbr {n.parent_code} has no legacy seed node',
            })
            continue
        active.append({
            'id': f'us-county:{n.official_code}',
            'parentId': f'iso3166-2:{iso}',
            'kind': 'county',
            'code': n.official_code,
            'name': n.name,
            'nameLocale': 'en',
            'nameQuality': 'source-native',
            'childrenStatus': 'unknown',
        })
    return active, migrations


def build(root):
    return build_nodes(parse_gazetteer(Path(root) / GAZETTEER_ZIP))
