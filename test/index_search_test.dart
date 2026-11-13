// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_data.dart';

void main() {
  pathGroup();
  pathDepthGroup();
  childrenCoverageGroup();
  sameNameGroup();
  searchByNameGroup();
  searchByIdGroup();
  searchOptionsGroup();
  indexGuardsGroup();
}

void pathGroup() {
  group('root-inclusive paths (real data)', () {
    test('CN Shenzhen Nanshan path is root-inclusive and four deep', () {
      final index = GeoRegionIndex.single(loadStructure('CN'));
      expect(index.pathToRoot('cn-stat:440305'), <String>[
        'cc:CN',
        'iso3166-2:CN-GD',
        'cn-stat:4403',
        'cn-stat:440305',
      ]);
      expect(
        index.pathNodesToRoot('cn-stat:440305').map((n) => n.name),
        contains('广东省'),
      );
    });

    test('JP Tokyo is exactly country plus prefecture', () {
      final index = GeoRegionIndex.single(loadStructure('JP'));
      expect(index.pathToRoot('iso3166-2:JP-13'), <String>[
        'cc:JP',
        'iso3166-2:JP-13',
      ]);
      expect(index.requireNode('iso3166-2:JP-13').name, 'Tokyo');
    });

    test('unknown IDs raise notFound, not empty paths', () {
      final index = GeoRegionIndex.single(loadStructure('JP'));
      expect(() => index.pathToRoot('nope'), throwsA(isA<GeoNotFoundError>()));
      expect(() => index.children('nope'), throwsA(isA<GeoNotFoundError>()));
      expect(() => index.requireNode('nope'), throwsA(isA<GeoNotFoundError>()));
    });
  });
}

void pathDepthGroup() {
  group('non-uniform structure depths (real data)', () {
    test('structures with different depths coexist (GB/US vs CN)', () {
      final index = GeoRegionIndex(<GeoRegionStructure>[
        loadStructure('GB'),
        loadStructure('US'),
      ]);
      // GB: country -> nation -> district for districts, two levels for the
      // nations themselves; US: country -> state; CN goes four levels deep.
      expect(index.pathToRoot('iso3166-2:GB-ABC'), hasLength(3));
      expect(index.pathToRoot('iso3166-2:GB-NIR'), <String>[
        'cc:GB',
        'iso3166-2:GB-NIR',
      ]);
      expect(index.pathToRoot('iso3166-2:US-AK'), <String>[
        'cc:US',
        'iso3166-2:US-AK',
      ]);
      expect(index.countryCodes, <String>['GB', 'US']);
      expect(
        GeoRegionIndex.single(loadStructure('CN')).pathToRoot('cn-stat:440305'),
        hasLength(4),
      );
    });
  });
}

void childrenCoverageGroup() {
  group('children and coverage', () {
    test('children of Shenzhen include Nanshan in document order', () {
      final index = GeoRegionIndex.single(loadStructure('CN'));
      final childIds = index.children('cn-stat:4403').map((n) => n.id).toList();
      expect(childIds, contains('cn-stat:440305'));
      expect(index.hasDeclaredChildren('cn-stat:4403'), isTrue);
      expect(index.coverageStatus('cn-stat:4403'), GeoChildrenStatus.complete);
    });

    test('unknown coverage is never a verified leaf', () {
      final index = GeoRegionIndex.single(loadStructure('JP'));
      expect(index.children('iso3166-2:JP-13'), isEmpty);
      expect(index.hasDeclaredChildren('iso3166-2:JP-13'), isFalse);
      expect(
        index.coverageStatus('iso3166-2:JP-13'),
        GeoChildrenStatus.unknown,
      );
      expect(
        () => index.requireKnownCoverage('iso3166-2:JP-13'),
        throwsA(
          isA<GeoUnknownCoverageError>().having(
            (error) => error.message,
            'message',
            contains('unknown'),
          ),
        ),
      );
      // A complete-status node passes the leaf guard.
      expect(() => index.requireKnownCoverage('cc:JP'), returnsNormally);
    });

    test('countryRoot resolves roots and rejects unknown countries', () {
      final index = GeoRegionIndex.single(loadStructure('JP'));
      expect(index.countryRoot('JP').id, 'cc:JP');
      expect(index.countryRoot('JP').isCountryRoot, isTrue);
      expect(() => index.countryRoot('XX'), throwsA(isA<GeoNotFoundError>()));
      expect(() => index.structureOf('XX'), throwsA(isA<GeoNotFoundError>()));
    });
  });
}

void sameNameGroup() {
  group('same-name nodes stay distinguishable', () {
    test('two distinct Nanshan districts share a name but not a path', () {
      final index = GeoRegionIndex.single(loadStructure('CN'));
      final jixi = index.requireNode('cn-stat:230404');
      final shenzhen = index.requireNode('cn-stat:440305');
      expect(jixi.name, '南山区');
      expect(shenzhen.name, '南山区');
      expect(jixi, isNot(shenzhen));
      expect(index.pathToRoot(jixi.id), <String>[
        'cc:CN',
        'iso3166-2:CN-HL',
        'cn-stat:2304',
        'cn-stat:230404',
      ]);
      expect(index.pathToRoot(shenzhen.id), <String>[
        'cc:CN',
        'iso3166-2:CN-GD',
        'cn-stat:4403',
        'cn-stat:440305',
      ]);
    });
  });
}

void searchByNameGroup() {
  group('search', () {
    test('name search returns results carrying full paths', () {
      final index = GeoRegionIndex.single(loadStructure('CN'));
      final results = geoSearch(index, '广东');
      expect(results, isNotEmpty);
      final guangdong = results.firstWhere(
        (r) => r.node.id == 'iso3166-2:CN-GD',
      );
      expect(guangdong.matchedField, GeoSearchField.name);
      expect(guangdong.pathIds, <String>['cc:CN', 'iso3166-2:CN-GD']);
    });

    test('same-name search hits remain distinguishable by path', () {
      final index = GeoRegionIndex.single(loadStructure('CN'));
      final results = geoSearch(index, '南山区');
      final pathsById = <String, List<String>>{};
      for (final result in results) {
        pathsById[result.node.id] = result.pathIds;
      }
      expect(pathsById.containsKey('cn-stat:230404'), isTrue);
      expect(pathsById.containsKey('cn-stat:440305'), isTrue);
      expect(
        pathsById['cn-stat:230404'],
        isNot(equals(pathsById['cn-stat:440305'])),
      );
      expect(pathsById['cn-stat:440305']!.last, 'cn-stat:440305');
    });

    test('name search is case-insensitive for ASCII', () {
      final index = GeoRegionIndex.single(loadStructure('JP'));
      final results = geoSearch(index, 'tokyo');
      final tokyo = results.firstWhere((r) => r.node.id == 'iso3166-2:JP-13');
      expect(tokyo.matchedField, GeoSearchField.name);
    });
  });
}

void searchByIdGroup() {
  group('search by ID and alias', () {
    test('ID substring search flags the id field', () {
      final index = GeoRegionIndex.single(loadStructure('CN'));
      final results = geoSearch(index, '4403');
      final ids = results.map((r) => r.node.id).toSet();
      expect(ids, contains('cn-stat:4403'));
      expect(ids, contains('cn-stat:440305'));
      expect(results.every((r) => r.matchedField == GeoSearchField.id), isTrue);
    });

    test('alias search flags the alias field', () {
      final withAlias = parseRegionStructure(
        _withAlias(),
        verifyRevision: false,
      );
      final index = GeoRegionIndex(<GeoRegionStructure>[withAlias]);
      final aliasHit = geoSearch(index, 'Edo');
      expect(aliasHit.map((r) => r.node.id), contains('iso3166-2:JP-13'));
      expect(aliasHit.first.matchedField, GeoSearchField.alias);
    });
  });
}

void searchOptionsGroup() {
  group('search options', () {
    test('country scoping, limits and empty queries', () {
      final multi = GeoRegionIndex(<GeoRegionStructure>[
        loadStructure('JP'),
        loadStructure('US'),
      ]);
      expect(
        geoSearch(
          multi,
          'a',
          countryCode: 'JP',
        ).every((r) => r.pathIds.first == 'cc:JP'),
        isTrue,
      );
      expect(geoSearch(multi, 'Alaska', limit: 1), hasLength(1));
      expect(geoSearch(multi, '   '), isEmpty);
      expect(geoSearch(multi, 'Alaska', limit: 0), isEmpty);
    });
  });
}

void indexGuardsGroup() {
  group('index construction guards', () {
    test('rejects node IDs reused across countries', () {
      final clone = parseRegionStructure(_jpClone(), verifyRevision: false);
      expect(
        () => GeoRegionIndex(<GeoRegionStructure>[loadStructure('JP'), clone]),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('ID reused across countries'),
          ),
        ),
      );
    });

    test('rejects mixing datasets in one index', () {
      final other = parseRegionStructure(
        _jpAsDataset('geo-regions-other'),
        verifyRevision: false,
      );
      expect(
        () => GeoRegionIndex(<GeoRegionStructure>[loadStructure('JP'), other]),
        throwsA(isA<GeoConfigurationError>()),
      );
    });

    test('rejects duplicate country structures', () {
      final structures = <GeoRegionStructure>[
        loadStructure('JP'),
        loadStructure('JP'),
      ];
      expect(
        () => GeoRegionIndex(structures),
        throwsA(isA<GeoConfigurationError>()),
      );
    });
  });
}

Map<String, Object?> _withAlias() {
  final decoded = loadDecodedData('regions/JP.json');
  for (final node in decoded['nodes'] as List) {
    if ((node as Map)['id'] == 'iso3166-2:JP-13') {
      node['aliases'] = <String>['Edo'];
    }
  }
  return decoded;
}

Map<String, Object?> _jpClone() => _jpAsDataset('geo-regions-seed', 'QQ');

Map<String, Object?> _jpAsDataset(String datasetId, [String? countryCode]) {
  final decoded = loadDecodedData('regions/JP.json');
  decoded['datasetId'] = datasetId;
  if (countryCode != null) {
    decoded['countryCode'] = countryCode;
    for (final node in decoded['nodes'] as List) {
      final map = node as Map;
      if (map['id'] == 'cc:JP') {
        map['id'] = 'cc:$countryCode';
      }
      if (map['parentId'] == 'cc:JP') {
        map['parentId'] = 'cc:$countryCode';
      }
    }
  }
  return decoded;
}
