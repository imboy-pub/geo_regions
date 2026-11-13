// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_data.dart';

void main() {
  canonicalGoldenGroup();
  canonicalControlGroup();
  canonicalLiteralGroup();
  canonicalRejectionGroup();
  localeRevisionGoldenGroup();
  publishedRevisionGroup();
  structureRevisionGroup();
  localePackRevisionGroup();
  catalogRevisionGroup();
  revisionShapeGroup();
}

void canonicalGoldenGroup() {
  test('C(x) golden vectors match the Python reference', () {
    expect(
      geoCanonicalJson(<String, Object?>{'b': 1, 'a': 'é中'}),
      '{"a":"é中","b":1}',
    );
    expect(
      geoCanonicalJson(<Object?>[
        <String, Object?>{
          'z': <Object?>[
            1,
            2,
            <String, Object?>{'q': null, 'p': true},
          ],
        },
        'x',
      ]),
      '[{"z":[1,2,{"p":true,"q":null}]},"x"]',
    );
    expect(
      geoCanonicalJson(<String, Object?>{
        'names': <String, Object?>{'cc:CN': '中国'},
        'translationQualityById': <String, Object?>{},
      }),
      '{"names":{"cc:CN":"中国"},"translationQualityById":{}}',
    );
    // Built via fromCharCode so the source stays printable ASCII.
    final ctrl = String.fromCharCode(1);
    expect(
      geoCanonicalJson(<String, Object?>{'k': 'a${ctrl}b'}),
      '{"k":"a\\u0001b"}',
    );
  });
}

void canonicalControlGroup() {
  test('C(x) escapes C0 controls like the Python encoder', () {
    for (var unit = 0; unit < 0x20; unit++) {
      if (unit == 0x08 ||
          unit == 0x09 ||
          unit == 0x0a ||
          unit == 0x0c ||
          unit == 0x0d) {
        continue;
      }
      final char = String.fromCharCode(unit);
      final hex = unit.toRadixString(16).padLeft(4, '0');
      expect(
        geoCanonicalJson(<String, Object?>{'k': char}),
        '{"k":"\\u$hex"}',
        reason: 'control U+${unit.toRadixString(16)}',
      );
    }
    expect(geoCanonicalJson(<String, Object?>{'k': '\b\f'}), '{"k":"\\b\\f"}');
  });
}

void canonicalLiteralGroup() {
  test('C(x) keeps DEL and astral characters literal, orders keys by code '
      'point', () {
    final del = String.fromCharCode(0x7f);
    expect(geoCanonicalJson(<String, Object?>{'d': del}), '{"d":"$del"}');
    final astral = String.fromCharCode(0x1f600);
    expect(geoCanonicalJson(<String, Object?>{'a': astral}), '{"a":"$astral"}');
    // U+FFFA sorts before U+10000 by code point; UTF-16 units would not.
    final high = String.fromCharCode(0xfffa);
    final astralId = String.fromCharCode(0x10000);
    expect(
      geoCanonicalJson(<String, Object?>{astralId: 2, high: 1}),
      '{"$high":1,"$astralId":2}',
    );
  });
}

void canonicalRejectionGroup() {
  test('C(x) rejects non-finite numbers and unsupported types', () {
    expect(() => geoCanonicalJson(double.nan), throwsFormatException);
    expect(() => geoCanonicalJson(double.infinity), throwsFormatException);
    expect(() => geoCanonicalJson(1.5), throwsFormatException);
    expect(() => geoCanonicalJson(Object()), throwsFormatException);
  });
}

void localeRevisionGoldenGroup() {
  test('locale revision golden vector with empty quality map', () {
    expect(
      geoLocaleRevision(<String, Object?>{'a': 'x'}),
      'l-b5835c13427e1c8d',
    );
  });
}

void publishedRevisionGroup() {
  test('revisions recomputed from real data equal the published values', () {
    final countries = loadDecodedData('countries.json');
    expect(geoCatalogRevision(countries['countries']), 'c-0d1490d60a530f8e');
    expect(geoCatalogRevision(countries['countries']), countries['revision']);

    final manifest = loadDecodedData('manifest.json');
    expect(geoManifestRevision(manifest['resources']), 'm-00f97c86c14ada75');
    expect(geoManifestRevision(manifest['resources']), manifest['revision']);
  });
}

void structureRevisionGroup() {
  test(
    'structure revisions recomputed from real data equal the file values',
    () {
      final expected = <String, String>{
        'CN': 's-618de1dd32b43463',
        'JP': 's-f6f89e0185926a48',
        'GB': 's-b6c4c44272f8f283',
        'US': 's-65edb4a623631538',
      };
      for (final entry in expected.entries) {
        final decoded = loadDecodedData('regions/${entry.key}.json');
        final computed = geoStructureRevision(decoded['nodes']);
        expect(computed, entry.value, reason: 'regions/${entry.key}.json');
        expect(
          computed,
          decoded['revision'],
          reason: 'revision field of regions/${entry.key}.json',
        );
      }
    },
  );
}

void localePackRevisionGroup() {
  test('locale pack revisions recomputed from real data equal the file '
      'values', () {
    final cases = <List<String>>[
      <String>['zh-Hans', 'CN'],
      <String>['zh-Hant', 'CN'],
      <String>['en', 'CN'],
      <String>['ja', 'JP'],
      <String>['zh-Hans', 'JP'],
    ];
    for (final path in cases) {
      final decoded = loadDecodedData('i18n/${path[0]}/${path[1]}.json');
      final coverage = decoded['coverage'] as Map<String, Object?>?;
      final quality = coverage == null
          ? null
          : coverage['translationQualityById'] as Map<String, Object?>?;
      final names = decoded['names'] as Map<String, Object?>;
      final computed = geoLocaleRevision(names, quality);
      expect(
        computed,
        decoded['revision'],
        reason: 'i18n/${path[0]}/${path[1]}.json',
      );
    }
  });
}

void catalogRevisionGroup() {
  test('catalog name pack revisions recomputed from real data', () {
    final decoded = loadDecodedData('catalog_i18n/zh-Hant.json');
    final coverage = decoded['coverage'] as Map<String, Object?>?;
    final quality =
        coverage!['translationQualityById'] as Map<String, Object?>?;
    final computed = geoLocaleRevision(
      decoded['names'] as Map<String, Object?>,
      quality,
    );
    expect(computed, 'l-a0944c216c266803');
    expect(computed, decoded['revision']);
  });
}

void revisionShapeGroup() {
  test('revision shape validation', () {
    expect(geoIsValidRevision('s-618de1dd32b43463'), isTrue);
    expect(geoIsValidRevision('x-618de1dd32b43463'), isFalse);
    expect(geoIsValidRevision('s-618DE1DD32B43463'), isFalse);
    expect(geoIsValidRevision('s-618d'), isFalse);
    expect(
      geoRevisionMatches('s-618de1dd32b43463', 's', [
        <String, Object?>{'a': 1},
      ]),
      isFalse,
    );
    expect(
      geoRevisionMatches(
        geoRevisionOf('s', <String, Object?>{'a': 1}),
        's',
        <String, Object?>{'a': 1},
      ),
      isTrue,
    );
    expect(() => geoRevisionOf('z', null), throwsArgumentError);
  });
}
