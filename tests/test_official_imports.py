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


if __name__ == '__main__':
    unittest.main()
