// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_data.dart';

late GeoRegionIndex _cn;
late GeoRegionIndex _jp;
late GeoRegionIndex _multi;

void main() {
  setUpAll(() {
    _cn = GeoRegionIndex.single(loadStructure('CN'));
    _jp = GeoRegionIndex.single(loadStructure('JP'));
    _multi = GeoRegionIndex(<GeoRegionStructure>[
      loadStructure('JP'),
      loadStructure('GB'),
    ]);
  });
  buildPathsGroup();
  countryOnlyGroup();
  displayIdentityGroup();
  deletedAndReparentedGroup();
  revisionAndDatasetGroup();
  shapeFailuresGroup();
  shapeBoundaryGroup();
  crossDatasetGroup();
}

GeoSelection _selection(
  String countryCode,
  List<String> pathIds, {
  String datasetId = 'geo-regions-seed',
  String? dataRevision,
}) => GeoSelection(
  protocolVersion: '1.0',
  datasetId: datasetId,
  countryCode: countryCode,
  dataRevision: dataRevision ?? _jp.structureOf('JP').revision,
  pathIds: pathIds,
);

void buildPathsGroup() {
  group('selection building', () {
    test('builds root-inclusive paths from the index', () {
      final draft = buildGeoSelection(_cn, 'cn-stat:440305');
      expect(draft.pathIds, <String>[
        'cc:CN',
        'iso3166-2:CN-GD',
        'cn-stat:4403',
        'cn-stat:440305',
      ]);
      expect(draft.countryCode, 'CN');
      expect(draft.datasetId, 'geo-regions-seed');
      expect(draft.dataRevision, 's-618de1dd32b43463');
      expect(() => validateGeoSelection(draft, _cn), returnsNormally);
    });

    test('multi-country indexes build per-country selections', () {
      final gb = buildGeoSelection(_multi, 'iso3166-2:GB-ABC');
      expect(gb.countryCode, 'GB');
      expect(gb.dataRevision, _multi.structureOf('GB').revision);
      expect(() => validateGeoSelection(gb, _multi), returnsNormally);
    });

    test('display snapshot must be parallel to the path', () {
      expect(
        () => buildGeoSelection(
          _cn,
          'cn-stat:440305',
          displaySnapshot: <String>['中国'],
        ),
        throwsA(isA<GeoConfigurationError>()),
      );
      expect(
        () => buildGeoSelection(
          _cn,
          'cn-stat:440305',
          displaySnapshot: <String>['中国', '广东省', '深圳市', '南山区'],
        ),
        returnsNormally,
      );
    });
  });
}

void countryOnlyGroup() {
  group('country-only selections', () {
    test('are single-element paths and validate', () {
      final draft = buildCountrySelection(_jp, 'JP');
      expect(draft.pathIds, <String>['cc:JP']);
      expect(() => validateGeoSelection(draft, _jp), returnsNormally);
      expect(
        () => buildCountrySelection(_jp, 'XX'),
        throwsA(isA<GeoNotFoundError>()),
      );
    });
  });
}

void displayIdentityGroup() {
  group('display language never changes selection identity', () {
    test('same identity under two display locales', () {
      final zh = buildGeoSelection(
        _jp,
        'iso3166-2:JP-13',
        displaySnapshot: <String>['日本', '東京都'],
        displayLocale: 'zh-Hans',
      );
      final ja = buildGeoSelection(
        _jp,
        'iso3166-2:JP-13',
        displaySnapshot: <String>['日本', '東京都'],
        displayLocale: 'ja',
      );
      expect(zh, ja);
      expect(zh.hashCode, ja.hashCode);
      final deeper = buildGeoSelection(_jp, 'cc:JP');
      expect(deeper == zh, isFalse);
      expect(parseSelection(zh.toMap()), zh);
      expect(zh.toJson(), contains('displayLocale'));
    });
  });
}

void deletedAndReparentedGroup() {
  group('selection validation failures (IDs and edges)', () {
    test('deleted IDs raise notFound and never guess a mapping', () {
      final broken = _selection('JP', <String>[
        'cc:JP',
        'iso3166-2:JP-13',
        'iso3166-2:JP-99',
      ]);
      expect(
        () => validateGeoSelection(broken, _jp),
        throwsA(
          isA<GeoNotFoundError>().having(
            (error) => error.message,
            'message',
            contains('iso3166-2:JP-99'),
          ),
        ),
      );
    });

    test('reparented or skipped levels fail on the parent edge', () {
      // Break a real edge: pretend Nanshan hangs directly off the CN root.
      final wrongEdge = _selection('CN', <String>[
        'cc:CN',
        'cn-stat:440305',
      ], dataRevision: _cn.structureOf('CN').revision);
      expect(
        () => validateGeoSelection(wrongEdge, _cn),
        throwsA(
          isA<GeoIntegrityMismatchError>().having(
            (error) => error.message,
            'message',
            contains('parent edge'),
          ),
        ),
      );

      final skipped = _selection('CN', <String>[
        'cc:CN',
        'iso3166-2:CN-GD',
        'cn-stat:440305',
      ], dataRevision: _cn.structureOf('CN').revision);
      expect(
        () => validateGeoSelection(skipped, _cn),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );
    });
  });
}

void revisionAndDatasetGroup() {
  group('selection validation failures (revision and namespace)', () {
    test('stale dataRevision is rejected', () {
      final stale = _selection('JP', <String>[
        'cc:JP',
      ], dataRevision: 's-0000000000000000');
      expect(
        () => validateGeoSelection(stale, _jp),
        throwsA(
          isA<GeoIntegrityMismatchError>().having(
            (error) => error.message,
            'message',
            contains('stale structure revision'),
          ),
        ),
      );
    });

    test('a different datasetId is a different ID namespace', () {
      final foreign = _selection('JP', <String>[
        'cc:JP',
      ], datasetId: 'geo-regions-other');
      expect(
        () => validateGeoSelection(foreign, _jp),
        throwsA(
          isA<GeoNotFoundError>().having(
            (error) => error.message,
            'message',
            contains('dataset mismatch'),
          ),
        ),
      );
    });
  });
}

void shapeFailuresGroup() {
  group('selection validation failures (shape)', () {
    test('path shape errors: wrong root first, duplicates', () {
      final wrongRoot = _selection('JP', <String>['iso3166-2:JP-13']);
      expect(
        () => validateGeoSelection(wrongRoot, _jp),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('country root first'),
          ),
        ),
      );
      final duplicated = _selection('JP', <String>[
        'cc:JP',
        'iso3166-2:JP-13',
        'cc:JP',
      ]);
      expect(
        () => validateGeoSelection(duplicated, _jp),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('duplicate path ID'),
          ),
        ),
      );
    });

    test('unsupported selection protocol versions are rejected', () {
      const future = GeoSelection(
        protocolVersion: '1.1',
        datasetId: 'geo-regions-seed',
        countryCode: 'JP',
        dataRevision: 's-f6f89e0185926a48',
        pathIds: <String>['cc:JP'],
      );
      expect(
        () => validateGeoSelection(future, _jp),
        throwsA(isA<GeoUnsupportedVersionError>()),
      );
    });
  });
}

void shapeBoundaryGroup() {
  group('selection validation failures (boundaries)', () {
    test('unknown countries and mismatched snapshot lengths are rejected', () {
      final unknownCountry = _selection('XX', <String>['cc:XX']);
      expect(
        () => validateGeoSelection(unknownCountry, _jp),
        throwsA(isA<GeoNotFoundError>()),
      );
      final skewed = GeoSelection(
        protocolVersion: '1.0',
        datasetId: 'geo-regions-seed',
        countryCode: 'JP',
        dataRevision: _jp.structureOf('JP').revision,
        pathIds: <String>['cc:JP', 'iso3166-2:JP-13'],
        displaySnapshot: <String>['日本'],
      );
      expect(
        () => validateGeoSelection(skewed, _jp),
        throwsA(isA<GeoParseFailureError>()),
      );
    });
  });
}

void crossDatasetGroup() {
  group('cross-dataset namespaces', () {
    test('IDs from one dataset never validate against another', () {
      final jpDecoded = loadDecodedData('regions/JP.json');
      jpDecoded['datasetId'] = 'geo-regions-ui-fixture';
      jpDecoded['revision'] = 's-1111111111111111';
      final fixture = parseRegionStructure(jpDecoded, verifyRevision: false);
      final fixtureIndex = GeoRegionIndex.single(fixture);
      // Same path shape, different namespace: not transferable.
      final fromReal = buildCountrySelection(_jp, 'JP');
      expect(
        () => validateGeoSelection(fromReal, fixtureIndex),
        throwsA(isA<GeoNotFoundError>()),
      );
      final fromFixture = buildCountrySelection(fixtureIndex, 'JP');
      expect(
        () => validateGeoSelection(fromFixture, _jp),
        throwsA(isA<GeoNotFoundError>()),
      );
    });
  });
}
