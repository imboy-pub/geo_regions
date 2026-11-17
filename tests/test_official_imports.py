"""Adapter-contract tests for the ten-country official completion (Phase 2).

Per docs/superpowers/plans/2026-11-16-ten-country-official-region-completion.md:
every country adapter is tested against a small fixed fixture covering the
normal hierarchy, duplicate/missing-parent/cycle errors, abolished entities,
and the ID rules (legacy IDs preserved, jp-municipality:{code} for new nodes).
"""
import csv
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JP_FIXTURE = REPO / 'tests/fixtures/official/jp/nodes.csv'


def load_rows(path):
    """Fixture rows as plain dicts (abolished normalized to bool upstream)."""
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


class CommonContractTests(unittest.TestCase):
    """SourceNode/CountryDraft/validate_draft — the shared adapter contract."""

    def test_validate_draft_accepts_wellformed_fixture(self):
        from tool.importers.common import SourceNode, CountryDraft, validate_draft
        rows = load_rows(JP_FIXTURE)
        nodes = [SourceNode(**{**r, 'abolished': r['abolished'] == 'true'}) for r in rows]
        draft = CountryDraft(nodes=nodes, migrations=[])
        self.assertIsNone(validate_draft(draft))

    def test_validate_draft_rejects_missing_parent(self):
        from tool.importers.common import SourceNode, CountryDraft, validate_draft
        rows = load_rows(JP_FIXTURE)
        rows[1] = dict(rows[1], parent_code='999999')  # 札幌市 → nonexistent parent
        nodes = [SourceNode(**{**r, 'abolished': r['abolished'] == 'true'}) for r in rows]
        err = validate_draft(CountryDraft(nodes=nodes, migrations=[]))
        self.assertIsNotNone(err)
        self.assertIn('missing parent', err)

    def test_validate_draft_rejects_duplicate_code(self):
        from tool.importers.common import SourceNode, CountryDraft, validate_draft
        rows = load_rows(JP_FIXTURE)
        rows = rows + [dict(rows[1])]
        nodes = [SourceNode(**{**r, 'abolished': r['abolished'] == 'true'}) for r in rows]
        err = validate_draft(CountryDraft(nodes=nodes, migrations=[]))
        self.assertIsNotNone(err)
        self.assertIn('duplicate', err)


class JpAdapterTests(unittest.TestCase):
    """tool.importers.jp — fixture-level adapter behaviour."""

    def test_build_nodes_prefixes_and_prefecture_crosswalk(self):
        from tool.importers.common import SourceNode
        from tool.importers.jp import build_nodes
        rows = [SourceNode(**{**r, 'abolished': r['abolished'] == 'true'})
                for r in load_rows(JP_FIXTURE)]
        active, migrations = build_nodes(rows)
        ids = {n['id'] for n in active}
        # prefecture keeps the legacy ISO id (011000 → JP-01 Hokkaidō)
        self.assertIn('iso3166-2:JP-01', ids)
        # municipality/ward ids use the official 6-digit code
        self.assertIn('jp-municipality:011002', ids)
        self.assertIn('jp-municipality:011011', ids)
        # ward parent = its ordinance-designated city
        ward = next(n for n in active if n['id'] == 'jp-municipality:011011')
        self.assertEqual(ward['parentId'], 'jp-municipality:011002')
        city = next(n for n in active if n['id'] == 'jp-municipality:011002')
        self.assertEqual(city['parentId'], 'iso3166-2:JP-01')
        # names stay Japanese source-native, never copied from CLDR/EN/zh
        self.assertEqual(city['name'], '札幌市')
        self.assertEqual(city['nameLocale'], 'ja')
        self.assertEqual(city['nameQuality'], 'source-native')

    def test_abolished_code_routes_to_migration_only(self):
        from tool.importers.common import SourceNode
        from tool.importers.jp import build_nodes
        rows = [SourceNode(**{**r, 'abolished': r['abolished'] == 'true'})
                for r in load_rows(JP_FIXTURE)]
        active, migrations = build_nodes(rows)
        self.assertNotIn('jp-municipality:013431', {n['id'] for n in active})
        self.assertTrue(any(m['officialCode'] == '013431' for m in migrations))

    def test_parse_official_xlsx_shape(self):
        from tool.importers.jp import parse_official_xlsx
        rows = parse_official_xlsx(
            REPO / 'sources/raw/official/jp/local-gov-code-000925835.xlsx')
        # 47 prefectures + 1,741 municipalities + 7 ordinance-city ward groups
        prefectures = [r for r in rows if r.kind == 'prefecture']
        municipalities = [r for r in rows if r.kind != 'prefecture']
        self.assertEqual(len(prefectures), 47)
        self.assertEqual(len(municipalities), 1747)
        self.assertTrue(all(r.name_locale == 'ja' for r in municipalities))

    def test_all_47_prefecture_ids_map_into_existing_seed(self):
        from tool.importers.jp import PREFECTURE_ISO
        with open(REPO / 'data/regions/JP.json') as f:
            regions = json.load(f)
        existing = {n['id'] for n in regions['nodes']}
        for two, iso in PREFECTURE_ISO.items():
            self.assertIn(f'iso3166-2:{iso}', existing, f'JP-{two} missing from seed')


class KrAdapterTests(unittest.TestCase):
    """tool.importers.kr — fixture-level adapter behaviour."""

    KR_FIXTURE = REPO / 'tests/fixtures/official/kr/nodes.csv'

    def _rows(self):
        from tool.importers.common import SourceNode
        return [SourceNode(**{**r, 'abolished': r['abolished'] == 'true'})
                for r in load_rows(self.KR_FIXTURE)]

    def test_metro_crosswalk_and_new_integration_city(self):
        from tool.importers.kr import build_nodes
        active, migrations = build_nodes(self._rows())
        ids = {n['id'] for n in active}
        # legacy Seoul id preserved; the integration city is NEW (no ISO id)
        self.assertIn('iso3166-2:KR-11', ids)
        self.assertIn('kr-municipality:1200000000', ids)
        # 서울 구 = autonomous; 광역시 구 = non-autonomous (official type by parent)
        kinds = {n['id']: n['kind'] for n in active}
        self.assertEqual(kinds['kr-municipality:1111000000'], 'autonomous-district')
        self.assertEqual(kinds['kr-municipality:2729000000'], 'non-autonomous-district')
        self.assertEqual(kinds['kr-municipality:4872000000'], 'county')

    def test_parents_resolve_to_metro_ids(self):
        from tool.importers.kr import build_nodes
        active, _ = build_nodes(self._rows())
        by_id = {n['id']: n for n in active}
        self.assertEqual(by_id['kr-municipality:1111000000']['parentId'], 'iso3166-2:KR-11')
        self.assertEqual(by_id['kr-municipality:2729000000']['parentId'], 'iso3166-2:KR-27')
        self.assertEqual(by_id['kr-municipality:4872000000']['parentId'], 'iso3166-2:KR-48')

    def test_old_integrated_city_routes_to_migration(self):
        from tool.importers.kr import build_nodes
        active, migrations = build_nodes(self._rows())
        self.assertNotIn('kr-municipality:4135000000', {n['id'] for n in active})
        self.assertTrue(any(m['officialCode'] == '4135000000' for m in migrations))

    def test_parse_active_shape(self):
        from tool.importers.kr import parse_active
        rows = parse_active(REPO / 'sources/raw/official/kr/jscode20261026.zip')
        metros = [r for r in rows if r.kind == 'metropolitan']
        self.assertEqual(len(metros), 16)  # 15 legacy-mapped + 전남광주통합특별시
        self.assertEqual(len(rows) - len(metros), 268)  # 268 standard 시군구 (출장소/branch rows excluded)
        self.assertTrue(all(r.name_locale == 'ko' for r in rows))

    def test_abolished_packages_yield_migrations(self):
        from tool.importers.kr import parse_abolished, build_nodes
        abolished = parse_abolished(REPO / 'sources/raw/official/kr/jscode20261026-abolished-included.zip')
        self.assertTrue(len(abolished) > 100)
        rows = self._rows() + []
        active, migrations = build_nodes(rows, abolished)
        self.assertTrue(len(migrations) >= len(abolished))


class UsAdapterTests(unittest.TestCase):
    """tool.importers.us — fixture-level adapter behaviour."""

    US_FIXTURE = REPO / 'tests/fixtures/official/us/nodes.csv'

    def _rows(self):
        from tool.importers.common import SourceNode
        rows = []
        for r in load_rows(self.US_FIXTURE):
            rows.append(SourceNode(
                official_code=r['geoid'], parent_code=r['usps'], kind=r['kind'],
                name=r['name'], name_locale='en', name_quality='source-native',
                children_status='unknown', abolished=r['abolished'] == 'true'))
        return rows

    def test_county_ids_are_five_digit_fips_with_iso_parents(self):
        from tool.importers.us import build_nodes
        active, migrations = build_nodes(self._rows())
        ids = {n['id'] for n in active}
        self.assertIn('us-county:01001', ids)
        self.assertIn('us-county:11001', ids)
        self.assertIn('us-county:72001', ids)
        by_id = {n['id']: n for n in active}
        self.assertEqual(by_id['us-county:01001']['parentId'], 'iso3166-2:US-AL')
        self.assertEqual(by_id['us-county:11001']['parentId'], 'iso3166-2:US-DC')
        self.assertEqual(by_id['us-county:72001']['parentId'], 'iso3166-2:US-PR')

    def test_place_records_never_become_nodes(self):
        from tool.importers.us import build_nodes
        active, _ = build_nodes(self._rows())
        self.assertNotIn('us-county:06075', {n['id'] for n in active})
        self.assertFalse(any(n['kind'] == 'place' for n in active))

    def test_parse_gazetteer_shape(self):
        from tool.importers.us import parse_gazetteer
        rows = parse_gazetteer(REPO / 'sources/raw/official/us/2025_Gaz_counties_national.zip')
        self.assertEqual(len(rows), 3222)
        self.assertTrue(all(r.kind == 'county' for r in rows))
        self.assertTrue(all(r.name_locale == 'en' for r in rows))

    def test_all_57_state_ids_map_into_existing_seed(self):
        from tool.importers.us import USPS_ISO
        with open(REPO / 'data/regions/US.json') as f:
            regions = json.load(f)
        existing = {n['id'] for n in regions['nodes']}
        for usps, iso in USPS_ISO.items():
            self.assertIn(f'iso3166-2:{iso}', existing, f'{usps} missing from seed')
        self.assertEqual(len(USPS_ISO), 57)


class GbAdapterTests(unittest.TestCase):
    """tool.importers.gb — fixture-level adapter behaviour."""

    GB_FIXTURE = REPO / 'tests/fixtures/official/gb/nodes.csv'

    def _rows(self):
        from tool.importers.common import SourceNode
        rows = []
        for r in load_rows(self.GB_FIXTURE):
            rows.append(SourceNode(
                official_code=r['gss_code'], parent_code=r['country_letter'],
                kind='local-authority', name=r['name'], name_locale='en',
                name_quality='source-native', children_status='unknown',
                abolished=r['abolished'] == 'true'))
        return rows

    def test_lads_parent_to_constituent_countries(self):
        from tool.importers.gb import build_nodes
        active, migrations, unmapped = build_nodes(self._rows())
        by_id = {n['id']: n for n in active}
        self.assertEqual(by_id['gb-lad:E06000001']['parentId'], 'iso3166-2:GB-ENG')
        self.assertEqual(by_id['gb-lad:S12000049']['parentId'], 'iso3166-2:GB-SCT')
        self.assertEqual(by_id['gb-lad:W06000015']['parentId'], 'iso3166-2:GB-WLS')
        self.assertEqual(by_id['gb-lad:N09000002']['parentId'], 'iso3166-2:GB-NIR')

    def test_no_country_relation_routes_to_migration(self):
        from tool.importers.gb import build_nodes
        active, migrations, unmapped = build_nodes(self._rows())
        self.assertNotIn('gb-lad:X99999999', {n['id'] for n in active})
        rec = next(m for m in migrations if m['officialCode'] == 'X99999999')
        self.assertEqual(rec['disposition'], 'unmapped')
        self.assertIn('country', rec['reason'])

    def test_no_country_relation_breaks_validate_draft(self):
        from tool.importers.common import CountryDraft, validate_draft
        from tool.importers.gb import build_nodes
        # if such a record were ever carried as an active node with an
        # unresolvable parent, the shared contract must refuse the draft
        active, _, _ = build_nodes(self._rows())
        draft_nodes = [type('N', (), {'official_code': 'gb-lad:X99999999',
                                      'parent_code': 'gb:XX',
                                      'abolished': False})()]
        err = validate_draft(CountryDraft(nodes=draft_nodes, migrations=[]))
        self.assertIsNotNone(err)
        self.assertIn('missing parent', err)

    def test_parse_lad_query_shape(self):
        from tool.importers.gb import parse_lad_query
        rows = parse_lad_query(REPO / 'sources/raw/official/gb/lad-dec2024-uk-buc-query.json')
        self.assertEqual(len(rows), 361)
        prefixes = {r.official_code[0] for r in rows}
        self.assertEqual(prefixes, set('ESWN'))
        self.assertTrue(all(r.name_locale == 'en' for r in rows))

    def test_all_four_constituent_ids_exist_in_seed(self):
        regions = json.load(open(REPO / 'data/regions/GB.json'))
        with open(REPO / 'data/regions/GB.json') as f:
            regions = json.load(f)
        existing = {n['id'] for n in regions['nodes']}
        for iso in ('GB-ENG', 'GB-SCT', 'GB-WLS', 'GB-NIR'):
            self.assertIn(f'iso3166-2:{iso}', existing)


if __name__ == '__main__':
    unittest.main()
