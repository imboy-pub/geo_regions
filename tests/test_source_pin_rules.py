"""Infrastructure proof for the ten-country design §4 dual pin forms.

The JP official snapshot is a live-web artifact with no versioned upstream
interface; the design doc mandates snapshot pinning (URL + fetch date +
official publish date + response hash) for exactly that case. This test
proves the admission rule accepts both forms and rejects the gaps.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tool'))
from geo_data import source_pin_admitted


class SourcePinRuleTests(unittest.TestCase):
    def test_commit_pinned_accepted(self):
        entry = {'commit': 'a' * 40, 'url': 'https://example.org/f.json',
                 'license': 'MIT'}
        self.assertTrue(source_pin_admitted(entry))

    def test_snapshot_pinned_accepted(self):
        entry = {'snapshotDate': '2024-01-01', 'retrievedAt': '2026-11-17',
                 'url': 'https://www.soumu.go.jp/main_content/000925835.xlsx',
                 'upstreamVersion': '令和6年1月1日更新', 'license': 'GoS-2.0'}
        self.assertTrue(source_pin_admitted(entry))

    def test_missing_snapshot_date_rejected(self):
        entry = {'retrievedAt': '2026-11-17', 'url': 'https://x.org/a.xlsx',
                 'upstreamVersion': 'v'}
        self.assertFalse(source_pin_admitted(entry))

    def test_bad_date_format_rejected(self):
        entry = {'snapshotDate': '20240101', 'retrievedAt': '2026-11-17',
                 'url': 'https://x.org/a.xlsx', 'upstreamVersion': 'v'}
        self.assertFalse(source_pin_admitted(entry))

    def test_http_url_rejected(self):
        entry = {'snapshotDate': '2024-01-01', 'retrievedAt': '2026-11-17',
                 'url': 'http://www.soumu.go.jp/a.xlsx', 'upstreamVersion': 'v'}
        self.assertFalse(source_pin_admitted(entry))

    def test_empty_version_rejected(self):
        entry = {'snapshotDate': '2024-01-01', 'retrievedAt': '2026-11-17',
                 'url': 'https://x.org/a.xlsx', 'upstreamVersion': '  '}
        self.assertFalse(source_pin_admitted(entry))


if __name__ == '__main__':
    unittest.main()
