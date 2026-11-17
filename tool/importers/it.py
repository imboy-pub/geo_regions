"""Italy adapter: ISTAT Limiti delle unità amministrative 2026 → CountryDraft.

Source: ISTAT "Limiti delle unità amministrative 2026" generalized edition
(sources/raw/official/it/Limiti01012026_g.zip; situation 1 January 2026;
attribute tables Reg/ProvCM/Com as DBF — the geometry generalization does not
affect codes or names; CC-BY-4.0 per the ISTAT note legali snapshot).

Facts encoded from source inspection (never guessed):
- 20 regions (COD_REG 1-20, DEN_REG Italian); 110 province-tier units
  (TIPO_UTS: Città metropolitana / Provincia / Provincia autonoma / Libero
  consorzio di comuni / Unità non amministrativa); 7,896 comuni.
- SIGLA is the province abbreviation — the same string family the legacy
  ISO 3166-2:IT province suffixes used, so precisely-mappable legacy
  province ids are preserved (IT-TO stays for the Torino metropolitan city:
  the province→metro-city conversion is the same entity, recorded by
  TIPO_UTS).
- The 2025 Sardinian reform re-created the provincial layer with new ISTAT
  codes 112-119 and REUSED siglas (OT now = Gallura Nord-Est Sardegna, CI =
  Sulcis Iglesiente, VS = Medio Campidano, OG = Ogliastra; SS/CA became
  metropolitan cities with COD_UTS 312/318). Sigla equality alone is not
  identity: legacy provinces whose region is Sardinia are removed with
  explicit superseded records — the release carries no predecessor column,
  so their identity against a 2026 entity cannot be established. Sardinia
  comunes parent the reform provinces purely by the official COD_PROV field.
- COMUNE_A is the source-provided bilingual alternative name (South Tyrol
  German, Aosta French) — written as the node alias when non-empty (124
  comuni), never generated.
- The boundaries release is a Gebietsstand snapshot: no abolished rows. The
  adapter routes abolished comune rows to migration records anyway
  (fixture-proven); real abolishments live in ISTAT's separate
  administrative-variation dataset.
- The RipGeo (ripartizione geografica) layer is a statistical grouping, not
  administration — never read as nodes.
- New nodes use official Italian names verbatim (nameLocale it, source-
  native); preserved legacy ids keep their inherited names per design §7.
"""
from __future__ import annotations

import struct
import zipfile
from pathlib import Path

try:
    from tool.importers.common import SourceNode
except ModuleNotFoundError:  # script context: tool/ itself is sys.path[0]
    from importers.common import SourceNode

SNAPSHOT = Path('sources/raw/official/it/Limiti01012026_g.zip')

# Legacy ISO 3166-2:IT region suffix → ISTAT COD_REG (official
# correspondence; keys are the bare suffix after 'iso3166-2:IT-').
REGION_ISO = {
    '21': '1', '23': '2', '25': '3', '32': '4', '34': '5', '36': '6',
    '42': '7', '45': '8', '52': '9', '55': '10', '57': '11', '62': '12',
    '65': '13', '67': '14', '72': '15', '75': '16', '77': '17', '78': '18',
    '82': '19', '88': '20',
}

SARDEGNA_COD_REG = '20'

PROV_KIND_BY_TIPO = {
    'Città metropolitana': 'citta-metropolitana',
    'Provincia': 'province',
    'Provincia autonoma': 'provincia-autonoma',
    'Libero consorzio di comuni': 'libero-consorzio',
    'Unità non amministrativa': 'unita-non-amministrativa',
}


def read_dbf(path) -> list:
    """Minimal fixed-schema DBF v3 reader (stdlib only). Accepts a path or a
    file-like object (e.g. a zip member)."""
    if hasattr(path, 'read'):
        buf = path.read()
    else:
        with open(path, 'rb') as f:
            buf = f.read()
    nrec = struct.unpack('<I', buf[4:8])[0]
    hlen = struct.unpack('<H', buf[8:10])[0]
    rlen = struct.unpack('<H', buf[10:12])[0]
    fields = []
    i = 32
    while buf[i] != 0x0D:
        name = buf[i:i + 11].split(b'\0')[0].decode('ascii')
        ln = buf[i + 16]
        fields.append((name, ln))
        i += 32
    recs = []
    off = hlen
    for _ in range(nrec):
        rec = buf[off:off + rlen]
        if rec[0:1] not in (b' ', b'*'):
            break
        vals = {}
        p = 1
        for name, ln in fields:
            vals[name] = rec[p:p + ln].decode('utf-8', errors='replace').strip()
            p += ln
        recs.append(vals)
        off += rlen
    return recs


def parse_official_zip(zip_path) -> dict:
    """Parse the locked ISTAT zip into SourceNode rows + binding maps.

    Returns {rows, sigla_by_provcod, uts_by_provcod, aliases_by_com}.
    """
    z = zipfile.ZipFile(zip_path)
    members = {m.split('/')[-1]: m for m in z.namelist() if m.endswith('.dbf')}
    reg_dbf = next(m for name, m in members.items() if name.startswith('Reg'))
    prov_dbf = next(m for name, m in members.items() if name.startswith('ProvCM'))
    com_dbf = next(m for name, m in members.items() if name.startswith('Com'))

    rows: list = []
    sigla_by_provcod: dict = {}
    uts_by_provcod: dict = {}
    aliases_by_com: dict = {}
    for r in read_dbf(z.open(reg_dbf)):
        rows.append(SourceNode(
            official_code=r['COD_REG'].strip(), parent_code='', kind='region',
            name=r['DEN_REG'].strip(), name_locale='it',
            name_quality='source-native', children_status='complete',
            abolished=False))
    for r in read_dbf(z.open(prov_dbf)):
        cod = r['COD_PROV'].strip()
        tipo = r['TIPO_UTS'].strip()
        kind = PROV_KIND_BY_TIPO.get(tipo)
        if kind is None:
            raise ValueError(f'unknown TIPO_UTS: {tipo}')
        sigla_by_provcod[cod] = r['SIGLA'].strip()
        uts_by_provcod[cod] = r['COD_UTS'].strip()
        rows.append(SourceNode(
            official_code=cod, parent_code=r['COD_REG'].strip(), kind=kind,
            name=r['DEN_UTS'].strip(), name_locale='it',
            name_quality='source-native', children_status='complete',
            abolished=False))
    for r in read_dbf(z.open(com_dbf)):
        code = r['PRO_COM_T'].strip()
        alias = r['COMUNE_A'].strip()
        if alias:
            aliases_by_com[code] = alias
        rows.append(SourceNode(
            official_code=code, parent_code=r['COD_PROV'].strip(),
            kind='comune', name=r['COMUNE'].strip(), name_locale='it',
            name_quality='source-native', children_status='unknown',
            abolished=False))
    return {'rows': rows, 'sigla_by_provcod': sigla_by_provcod,
            'uts_by_provcod': uts_by_provcod, 'aliases_by_com': aliases_by_com}


def _legacy_province_suffixes(legacy_nodes) -> dict:
    """alpha-suffix legacy province nodes keyed by suffix, with their region."""
    out = {}
    for leg in legacy_nodes:
        leg_id = str(leg.get('id') or '')
        if not leg_id.startswith('iso3166-2:IT-'):
            continue
        suffix = leg_id.removeprefix('iso3166-2:IT-')
        if not suffix.isalpha():
            continue  # region suffixes are numeric; handled via REGION_ISO
        parent_suffix = (str(leg.get('parentId') or '')
                         .removeprefix('iso3166-2:IT-'))
        out[suffix] = {'node': leg, 'region_suffix': parent_suffix}
    return out


def _province_bindings(parsed, legacy_nodes):
    """Final province-tier node id per COD_PROV + crosswalk records.

    Returns (provcod→final node id, records). Legacy province ids are
    preserved where the sigla maps outside the Sardinia reform; Sardinia
    legacy provinces are superseded (removed by the import loop via the
    record's oldId); everything else gets a new it-prov:{COD_UTS} node.
    """
    sigla_by_provcod = parsed['sigla_by_provcod']
    uts_by_provcod = parsed['uts_by_provcod']
    legacy_by_sigla = _legacy_province_suffixes(legacy_nodes)
    records: list = []
    prov_id_by_cod: dict = {}
    for row in parsed['rows']:
        if row.kind == 'region' or row.kind == 'comune':
            continue
        cod = row.official_code
        sigla = sigla_by_provcod.get(cod, '')
        if row.parent_code == SARDEGNA_COD_REG:
            prov_id_by_cod[cod] = f'it-prov:{uts_by_provcod[cod]}'
            continue
        leg = legacy_by_sigla.get(sigla)
        if leg is not None:
            prov_id_by_cod[cod] = f'iso3166-2:IT-{sigla}'
            records.append({'id': f'iso3166-2:IT-{sigla}', 'sigla': sigla,
                            'istatCode': cod,
                            'name': leg['node'].get('name'),
                            'disposition': 'preserved'})
        else:
            prov_id_by_cod[cod] = f'it-prov:{uts_by_provcod[cod]}'
    return prov_id_by_cod, records


def _sardinia_region_suffixes(legacy_nodes) -> set:
    out = set()
    for suffix, info in _legacy_province_suffixes(legacy_nodes).items():
        if REGION_ISO.get(info['region_suffix']) == SARDEGNA_COD_REG:
            out.add(suffix)
    return out


def _region_iso_suffix(cod_reg: str) -> str:
    for suffix, reg in REGION_ISO.items():
        if reg == cod_reg:
            return suffix
    raise ValueError(f'unknown COD_REG: {cod_reg}')


def build_nodes(parsed, legacy_nodes=()) -> tuple[list, list]:
    """Normalize parsed ISTAT rows into seed-shaped active nodes + records.

    - region rows are crosswalk targets only: the 20 legacy iso3166-2:IT-XX
      ids stay untouched, no region node is emitted.
    - province-tier rows: preserved legacy ids are not re-emitted; new nodes
      (Sardinia reform entities, Valle d'Aosta province) use
      it-prov:{COD_UTS} with childrenStatus complete.
    - comunes: it-comune:{PRO_COM_T}, parented by the official COD_PROV
      binding; COMUNE_A aliases carried verbatim.
    - abolished comune rows route to migration records (fixture-proven).
    """
    rows = parsed['rows']
    aliases_by_com = parsed['aliases_by_com']
    prov_id_by_cod, records = _province_bindings(parsed, legacy_nodes)
    # legacy provinces superseded by the Sardinia reform (identity cannot be
    # established from this release) — removed by the import loop via oldId
    sardinia_suffixes = _sardinia_region_suffixes(legacy_nodes)
    legacy_by_sigla = _legacy_province_suffixes(legacy_nodes)
    for suffix in sorted(sardinia_suffixes):
        leg = legacy_by_sigla[suffix]
        records.append({'oldId': f'iso3166-2:IT-{suffix}',
                        'name': leg['node'].get('name'),
                        'disposition': 'superseded',
                        'reason': ('the 2025 Sardinian reform re-created the '
                                   'provincial layer with new ISTAT codes '
                                   '112-119 and reused siglas; the boundaries '
                                   'release carries no predecessor column, so '
                                   'the legacy entity cannot be mapped to a '
                                   '2026 entity without name-guessing')})
    active: list = []
    seen: set = set()
    for n in rows:
        if n.kind == 'region':
            if n.official_code not in set(REGION_ISO.values()):
                raise ValueError(f'unknown COD_REG: {n.official_code}')
            continue
        if n.abolished:
            records.append({'officialCode': n.official_code, 'name': n.name,
                            'disposition': 'abolished',
                            'reason': 'abolished/merged comune; the boundaries '
                                      'release is a Gebietsstand snapshot and '
                                      'carries no abolished rows'})
            continue
        if n.kind == 'comune':
            node = {'id': f'it-comune:{n.official_code}',
                    'parentId': prov_id_by_cod[n.parent_code],
                    'kind': n.kind, 'code': n.official_code, 'name': n.name,
                    'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                    'childrenStatus': n.children_status}
            alias = aliases_by_com.get(n.official_code)
            if alias:
                node['aliases'] = [alias]
        else:  # new province-tier node (no preserved legacy id)
            node_id = prov_id_by_cod[n.official_code]
            if not node_id.startswith('it-prov:'):
                continue  # preserved legacy id — the seed node stays as-is
            node = {'id': node_id,
                    'parentId': f'iso3166-2:IT-{_region_iso_suffix(n.parent_code)}',
                    'kind': n.kind, 'code': n.official_code, 'name': n.name,
                    'nameLocale': n.name_locale, 'nameQuality': n.name_quality,
                    'childrenStatus': n.children_status}
        if node['id'] in seen:
            raise ValueError(f'duplicate active node id: {node["id"]}')
        seen.add(node['id'])
        active.append(node)
    return active, records


def draft_keys(parsed, legacy_nodes=()):
    """Tier-aware identity/parent-identity callables for validate_draft.

    ISTAT legally reuses the same number across tiers (region 1 Piemonte vs
    province 1 Torino), so the bare official_code is not an identity — the
    final node id is.
    """
    prov_id_by_cod, _ = _province_bindings(parsed, legacy_nodes)

    def identity(n):
        if n.kind == 'region':
            return f'it-region:{n.official_code}'
        if n.kind == 'comune':
            return f'it-comune:{n.official_code}'
        return prov_id_by_cod.get(n.official_code,
                                  f'{n.kind}:{n.official_code}')

    def parent_identity(n):
        if n.kind == 'region':
            return ''
        if n.kind == 'comune':
            return prov_id_by_cod.get(n.parent_code, '')
        return f'it-region:{n.parent_code}'

    return identity, parent_identity


def build(root, legacy_nodes=()) -> tuple[list, list]:
    return build_nodes(parse_official_zip(Path(root) / SNAPSHOT), legacy_nodes)
