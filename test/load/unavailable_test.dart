// SPDX-License-Identifier: BSD-3-Clause
/// Unavailability and coverage tests (AT-11): offline without cache is an
/// explicit typed failure (never empty children), and unknown-coverage nodes
/// refuse to impersonate leaves via the P1-04 index API.
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'fake_adapters.dart';
import 'fixture_bytes.dart';

void main() {
  offlineGroup();
  unknownCoverageGroup();
}

void offlineGroup() {
  group('AT-11: offline without cache is explicitly unavailable', () {
    test('no cache and no loaders fails with GeoNetworkError', () async {
      final repository = GeoRegionsRepository(
        manifest: realManifest,
        store: GeoMemoryCacheStore(),
      );
      await expectLater(
        repository.loadStructure('JP'),
        throwsA(
          isA<GeoNetworkError>().having(
            (error) => error.message,
            'message',
            contains('unavailable'),
          ),
        ),
      );
      expect(
        repository.index,
        isNull,
        reason: 'no empty-children placeholder state',
      );
      expect(repository.structureFor('JP'), isNull);
    });

    test(
      'remote transport failure surfaces as-is, then cache recovery works',
      () async {
        final store = GeoMemoryCacheStore();
        final loader =
            servingLoader(<String, Uint8List>{
                'regions/JP.json': dataBytes('regions/JP.json'),
              })
              ..fault = (Uri uri) => uri.toString().contains('regions/JP.json')
                  ? const GeoNetworkError('airplane mode')
                  : null;
        final repository = GeoRegionsRepository(
          manifest: realManifest,
          store: store,
          remoteLoader: loader,
          remoteBase: testBase(),
          verifier: FakeVerifier(),
        );

        await expectLater(
          repository.loadStructure('JP'),
          throwsA(isA<GeoNetworkError>()),
        );

        // A previously cached entry (e.g. written by an earlier session) makes
        // the same resource available offline.
        await store.write(
          GeoCacheKey.fromManifestEntry(
            'geo-regions-seed',
            realEntry('regions/JP.json'),
          ),
          GeoBytes(dataBytes('regions/JP.json')),
        );
        final structure = await repository.loadStructure('JP');
        expect(structure.countryCode, 'JP');
        expect(
          loader.callCount,
          1,
          reason: 'recovery came from cache, not the network',
        );
      },
    );

    test('not-declared resources never fall back to empty results', () async {
      final repository = GeoRegionsRepository(manifest: realManifest);
      await expectLater(
        repository.loadCatalogNames('zz-XX'),
        throwsA(isA<GeoNotFoundError>()),
      );
    });
  });
}

void unknownCoverageGroup() {
  group('AT-11: unknown coverage is not a leaf', () {
    test(
      'requireKnownCoverage throws for unknown nodes via the repository index',
      () async {
        final loader = servingLoader(<String, Uint8List>{
          'regions/JP.json': dataBytes('regions/JP.json'),
        });
        final repository = GeoRegionsRepository(
          manifest: realManifest,
          remoteLoader: loader,
          remoteBase: testBase(),
          verifier: FakeVerifier(),
        );
        final structure = await repository.loadStructure('JP');
        final unknownId = structure.nodes
            .firstWhere(
              (node) => node.childrenStatus == GeoChildrenStatus.unknown,
            )
            .id;

        final index = repository.index!;
        expect(index.coverageStatus(unknownId), GeoChildrenStatus.unknown);
        await expectLater(
          Future<void>.sync(() => index.requireKnownCoverage(unknownId)),
          throwsA(isA<GeoUnknownCoverageError>()),
        );
      },
    );

    test('complete nodes keep their leaf guarantee', () async {
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': dataBytes('regions/JP.json'),
      });
      final repository = GeoRegionsRepository(
        manifest: realManifest,
        remoteLoader: loader,
        remoteBase: testBase(),
        verifier: FakeVerifier(),
      );
      final structure = await repository.loadStructure('JP');
      final completeId = structure.nodes
          .firstWhere(
            (node) => node.childrenStatus == GeoChildrenStatus.complete,
          )
          .id;

      final index = repository.index!;
      Object? failure;
      try {
        index.requireKnownCoverage(completeId);
      } on GeoException catch (error) {
        failure = error;
      }
      expect(failure, isNull);
    });
  });
}
