// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_data.dart';

void main() {
  errorCodesGroup();
  structureBasicsGroup();
  structureStrictFieldsGroup();
  structureTopologyGroup();
  structureParentLinksGroup();
  structureRevisionGroup();
  localePackGroup();
  localePackStrictGroup();
  localePackQualityGroup();
  countriesGroup();
  catalogNamesGroup();
  catalogCoverageGroup();
  manifestBasicsGroup();
  manifestStrictGroup();
  selectionParsingGroup();
  selectionRejectGroup();
  jsonTextGroup();
}

void errorCodesGroup() {
  group('typed error codes match CONSUMER_CONTRACT §2', () {
    test('every variant carries its stable code', () {
      expect(const GeoNetworkError('n').errorCode, 'network');
      expect(const GeoNotFoundError('n').errorCode, 'notFound');
      expect(
        const GeoUnsupportedVersionError('n').errorCode,
        'unsupportedVersion',
      );
      expect(
        const GeoIntegrityMismatchError('n').errorCode,
        'integrityMismatch',
      );
      expect(const GeoParseFailureError('n').errorCode, 'parseFailure');
      expect(const GeoUnknownCoverageError('n').errorCode, 'unknownCoverage');
      expect(const GeoConfigurationError('n').errorCode, 'configurationError');
      expect(
        const GeoParseFailureError('bad').toString(),
        'GeoParseFailureError(parseFailure): bad',
      );
    });
  });
}

void structureBasicsGroup() {
  group('structure parsing', () {
    test('accepts the real published structures', () {
      for (final code in <String>['CN', 'JP', 'GB', 'US']) {
        final structure = loadStructure(code);
        expect(structure.protocolVersion, '1.0');
        expect(structure.datasetId, 'geo-regions-seed');
        expect(structure.countryCode, code);
        expect(structure.nodes, isNotEmpty);
        expect(structure.revision, startsWith('s-'));
      }
    });

    test('rejects protocolVersion 1.1 with unsupportedVersion', () {
      final mutated = mutateStructure(
        'JP',
        (decoded) => decoded['protocolVersion'] = '1.1',
      );
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoUnsupportedVersionError>().having(
            (error) => error.message,
            'message',
            contains('protocolVersion'),
          ),
        ),
      );
    });

    test('rejects missing protocolVersion with unsupportedVersion', () {
      final mutated = mutateStructure(
        'JP',
        (decoded) => decoded.remove('protocolVersion'),
      );
      expect(
        () => parseRegionStructure(mutated),
        throwsA(isA<GeoUnsupportedVersionError>()),
      );
    });
  });
}

void structureStrictFieldsGroup() {
  group('structure parsing (strict fields)', () {
    test('rejects unknown top-level field (strict schema)', () {
      final mutated = mutateStructure(
        'JP',
        (decoded) => decoded['extraTop'] = 1,
      );
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('unknown field "extraTop"'),
          ),
        ),
      );
    });

    test('rejects unknown node field (strict schema)', () {
      final mutated = mutateStructure('JP', (decoded) {
        (decoded['nodes'] as List)[1]['surprise'] = 'x';
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(isA<GeoParseFailureError>()),
      );
    });

    test('rejects duplicate node IDs', () {
      final mutated = mutateStructure('JP', (decoded) {
        final nodes = decoded['nodes'] as List;
        nodes.add(copyJsonObject(nodes[1]));
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('duplicate ID'),
          ),
        ),
      );
    });
  });
}

void structureTopologyGroup() {
  group('structure parsing (topology)', () {
    test('rejects a second declared root (non-unique null parent)', () {
      final mutated = mutateStructure('JP', (decoded) {
        (decoded['nodes'] as List)[1]['parentId'] = null;
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('exactly one declared root'),
          ),
        ),
      );
    });

    test('rejects parent cycles', () {
      final mutated = mutateStructure('JP', (decoded) {
        final nodes = decoded['nodes'] as List;
        nodes[1]['parentId'] = 'iso3166-2:JP-02';
        nodes[2]['parentId'] = 'iso3166-2:JP-01';
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('parent cycle'),
          ),
        ),
      );
    });
  });
}

void structureParentLinksGroup() {
  group('structure parsing (parent links)', () {
    test('rejects cross-country parents', () {
      final mutated = mutateStructure('JP', (decoded) {
        (decoded['nodes'] as List)[1]['parentId'] = 'cc:CN';
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('cross-country parent'),
          ),
        ),
      );
    });

    test('rejects orphan parents', () {
      final mutated = mutateStructure('JP', (decoded) {
        (decoded['nodes'] as List)[1]['parentId'] = 'iso3166-2:JP-99';
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(isA<GeoParseFailureError>()),
      );
    });
  });
}

void structureRevisionGroup() {
  group('structure parsing (revisions)', () {
    test('rejects a declared revision that disagrees with content', () {
      final mutated = mutateStructure('JP', (decoded) {
        (decoded['nodes'] as List)[1]['name'] = 'Changed';
      });
      expect(
        () => parseRegionStructure(mutated),
        throwsA(
          isA<GeoIntegrityMismatchError>().having(
            (error) => error.message,
            'message',
            contains('revision does not match content'),
          ),
        ),
      );
      // The same input parses when revision verification is host-disabled.
      expect(
        () => parseRegionStructure(mutated, verifyRevision: false),
        returnsNormally,
      );
    });

    test('rejects datasetId mismatch against the expected namespace', () {
      expect(
        () => parseRegionStructure(
          loadDecodedData('regions/JP.json'),
          expectedDatasetId: 'other-dataset',
        ),
        throwsA(isA<GeoParseFailureError>()),
      );
    });

    test('rejects invalid childrenStatus values', () {
      final badStatus = mutateStructure('JP', (decoded) {
        (decoded['nodes'] as List)[1]['childrenStatus'] = 'maybe';
      });
      expect(
        () => parseRegionStructure(badStatus),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('childrenStatus'),
          ),
        ),
      );
    });
  });
}

void localePackGroup() {
  group('locale pack parsing', () {
    test('accepts the real published packs with structure linkage', () {
      final structure = loadStructure('JP');
      final pack = loadLocalePack('ja', structure);
      expect(pack.locale, 'ja');
      expect(pack.compatibleStructureRevision, structure.revision);
      expect(pack.names, isNotEmpty);
    });

    test('rejects dangling translation IDs', () {
      final structure = loadStructure('JP');
      final decoded = loadDecodedData('i18n/ja/JP.json');
      (decoded['names'] as Map)['bogus:node'] = 'どこか';
      expect(
        () => parseLocalePack(decoded, expectedStructure: structure),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('dangling translation'),
          ),
        ),
      );
    });
  });
}

void localePackStrictGroup() {
  group('locale pack parsing (strict)', () {
    test('rejects compatibleStructureRevision mismatch', () {
      final structure = loadStructure('JP');
      final decoded = loadDecodedData('i18n/ja/JP.json');
      decoded['compatibleStructureRevision'] = 's-0000000000000000';
      expect(
        () => parseLocalePack(decoded, expectedStructure: structure),
        throwsA(
          isA<GeoIntegrityMismatchError>().having(
            (error) => error.message,
            'message',
            contains('incompatible structure revision'),
          ),
        ),
      );
    });

    test('rejects malformed locale tags', () {
      final decoded = loadDecodedData('i18n/ja/JP.json');
      decoded['locale'] = 'j1';
      expect(
        () => parseLocalePack(decoded),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('BCP 47'),
          ),
        ),
      );
    });
  });
}

void localePackQualityGroup() {
  group('locale pack parsing (quality markers)', () {
    test('rejects quality markers for untranslated IDs', () {
      final decoded = loadDecodedData('i18n/ja/JP.json');
      final coverage = decoded['coverage'] as Map<String, Object?>;
      (coverage['translationQualityById'] as Map)['bogus:node'] =
          'approved-in-source';
      expect(
        () => parseLocalePack(decoded),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('unknown translation ID'),
          ),
        ),
      );
    });
  });
}

void countriesGroup() {
  group('countries parsing', () {
    test('accepts the real catalog', () {
      final catalog = loadCountryCatalog();
      expect(catalog.countries, hasLength(10));
      expect(catalog.revision, 'c-0d1490d60a530f8e');
    });

    test('rejects duplicate country codes', () {
      final decoded = loadDecodedData('countries.json');
      (decoded['countries'] as List).add(
        copyJsonObject((decoded['countries'] as List)[0]),
      );
      expect(
        () => parseCountryCatalog(decoded),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('duplicate country'),
          ),
        ),
      );
    });

    test('rejects wrong country roots', () {
      final decoded = loadDecodedData('countries.json');
      ((decoded['countries'] as List)[0] as Map)['rootId'] = 'cc:XX';
      expect(
        () => parseCountryCatalog(decoded),
        throwsA(isA<GeoParseFailureError>()),
      );
    });
  });
}

void catalogNamesGroup() {
  group('catalog names parsing', () {
    test('accepts the real packs', () {
      final catalog = loadCountryCatalog();
      final zhHant = loadCatalogNames('zh-Hant');
      expect(zhHant.names['CN'], '中國');
      expect(zhHant.compatibleCatalogRevision, catalog.revision);
    });

    test('rejects catalog names for unknown countries', () {
      final catalog = loadCountryCatalog();
      final decoded = loadDecodedData('catalog_i18n/zh-Hant.json');
      (decoded['names'] as Map)['XX'] = '不明';
      expect(
        () => parseCatalogNames(decoded, expectedCatalog: catalog),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('unknown country name key'),
          ),
        ),
      );
    });
  });
}

void catalogCoverageGroup() {
  group('catalog names parsing (coverage)', () {
    test('rejects incomplete catalog-name coverage', () {
      final catalog = loadCountryCatalog();
      final decoded = loadDecodedData('catalog_i18n/zh-Hant.json');
      (decoded['names'] as Map).remove('SA');
      final coverage = decoded['coverage'] as Map;
      (coverage['translationQualityById'] as Map).remove('SA');
      expect(
        () => parseCatalogNames(decoded, expectedCatalog: catalog),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('coverage must be complete'),
          ),
        ),
      );
    });

    test('rejects compatibleCatalogRevision mismatch', () {
      final catalog = loadCountryCatalog();
      final decoded = loadDecodedData('catalog_i18n/zh-Hant.json');
      decoded['compatibleCatalogRevision'] = 'c-0000000000000000';
      expect(
        () => parseCatalogNames(decoded, expectedCatalog: catalog),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );
    });
  });
}

void manifestBasicsGroup() {
  group('manifest parsing', () {
    test('accepts the real manifest', () {
      final manifest = loadManifest();
      expect(manifest.revision, 'm-00f97c86c14ada75');
      expect(manifest.resources.first.path, 'catalog_i18n/ar.json');
    });

    test('rejects unsorted resources', () {
      final decoded = loadDecodedData('manifest.json');
      decoded['resources'] = (decoded['resources'] as List).reversed.toList();
      expect(
        () => parseManifest(decoded),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('sorted by path'),
          ),
        ),
      );
    });

    test('rejects duplicate resource paths', () {
      final decoded = loadDecodedData('manifest.json');
      final resources = decoded['resources'] as List;
      resources[1] = copyJsonObject(resources[0]);
      expect(
        () => parseManifest(decoded),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('duplicate manifest path'),
          ),
        ),
      );
    });
  });
}

void manifestStrictGroup() {
  group('manifest parsing (strict)', () {
    test('rejects path traversal in resource paths', () {
      final decoded = loadDecodedData('manifest.json');
      ((decoded['resources'] as List)[0] as Map)['path'] = '../outside.json';
      expect(
        () => parseManifest(decoded),
        throwsA(
          isA<GeoParseFailureError>().having(
            (error) => error.message,
            'message',
            contains('traversal'),
          ),
        ),
      );
    });

    test('rejects malformed sha256 and bytes fields', () {
      final decoded = loadDecodedData('manifest.json');
      ((decoded['resources'] as List)[0] as Map)['sha256'] = 'XYZ';
      expect(
        () => parseManifest(decoded),
        throwsA(isA<GeoParseFailureError>()),
      );

      final decoded2 = loadDecodedData('manifest.json');
      ((decoded2['resources'] as List)[0] as Map)['bytes'] = -1;
      expect(
        () => parseManifest(decoded2),
        throwsA(isA<GeoParseFailureError>()),
      );
    });
  });
}

void selectionParsingGroup() {
  group('selection parsing', () {
    test('round-trips a valid selection', () {
      final selection = GeoSelection(
        protocolVersion: '1.0',
        datasetId: 'geo-regions-seed',
        countryCode: 'JP',
        dataRevision: 's-f6f89e0185926a48',
        pathIds: <String>['cc:JP', 'iso3166-2:JP-13'],
        displaySnapshot: <String>['日本', '東京都'],
        displayLocale: 'zh-Hans',
      );
      final parsed = parseSelection(selection.toMap());
      expect(parsed, selection);
      expect(parsed.displayLocale, 'zh-Hans');
    });

    test('rejects protocolVersion 1.1', () {
      expect(
        () => parseSelection(<String, Object?>{
          'protocolVersion': '1.1',
          'datasetId': 'd',
          'countryCode': 'JP',
          'dataRevision': 's-f6f89e0185926a48',
          'pathIds': <String>['cc:JP'],
        }),
        throwsA(isA<GeoUnsupportedVersionError>()),
      );
    });
  });
}

void selectionRejectGroup() {
  group('selection parsing (rejections)', () {
    test('rejects unknown fields and duplicate path IDs', () {
      expect(
        () => parseSelection(<String, Object?>{
          'protocolVersion': '1.0',
          'datasetId': 'd',
          'countryCode': 'JP',
          'dataRevision': 's-f6f89e0185926a48',
          'pathIds': <String>['cc:JP'],
          'mystery': true,
        }),
        throwsA(isA<GeoParseFailureError>()),
      );
      expect(
        () => parseSelection(<String, Object?>{
          'protocolVersion': '1.0',
          'datasetId': 'd',
          'countryCode': 'JP',
          'dataRevision': 's-f6f89e0185926a48',
          'pathIds': <String>['cc:JP', 'cc:JP'],
        }),
        throwsA(isA<GeoParseFailureError>()),
      );
    });
  });
}

void jsonTextGroup() {
  group('parseJsonText', () {
    test('maps JSON syntax failures to parseFailure', () {
      expect(
        () => parseJsonText('{oops'),
        throwsA(isA<GeoParseFailureError>()),
      );
      expect(parseJsonText('{"a":1}'), <String, Object?>{'a': 1});
    });
  });
}
