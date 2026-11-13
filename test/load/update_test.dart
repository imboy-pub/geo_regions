// SPDX-License-Identifier: BSD-3-Clause
/// Atomic update tests (AT-10, GR-06): full verified staging, all-or-nothing
/// swap, stale-coherent fallback and foreign-dataset rejection.
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'fake_adapters.dart';
import 'fixture_bytes.dart';

GeoManifestEntry entry(String path) => realEntry(path);

/// Release 1: JP structure plus its zh-Hans pack.
GeoManifest set1() => manifestOf(<GeoManifestEntry>[
  entry('regions/JP.json'),
  entry('i18n/zh-Hans/JP.json'),
]);

/// Release 2: JP (unchanged revision) + SA + its zh-Hans pack.
GeoManifest set2() => manifestOf(<GeoManifestEntry>[
  entry('regions/JP.json'),
  entry('regions/SA.json'),
  entry('i18n/zh-Hans/SA.json'),
]);

Map<String, Uint8List> payloads12() => <String, Uint8List>{
  'regions/JP.json': dataBytes('regions/JP.json'),
  'i18n/zh-Hans/JP.json': dataBytes('i18n/zh-Hans/JP.json'),
  'regions/SA.json': dataBytes('regions/SA.json'),
  'i18n/zh-Hans/SA.json': dataBytes('i18n/zh-Hans/SA.json'),
};

GeoRegionsRepository repositoryWith({
  required GeoResourceLoader loader,
  GeoCacheStore? store,
  GeoManifest? manifest,
}) {
  return GeoRegionsRepository(
    manifest: manifest ?? set1(),
    store: store,
    remoteLoader: loader,
    remoteBase: testBase(),
    verifier: FakeVerifier(),
  );
}

void main() {
  atomicSwapGroup();
  failedUpdateGroup();
  guardGroup();
}

void atomicSwapGroup() {
  group('AT-10: update swaps a fully verified set', () {
    test('success path stages everything, then swaps atomically', () async {
      final store = GeoMemoryCacheStore();
      final loader = servingLoader(payloads12());
      final repository = repositoryWith(loader: loader, store: store);
      final candidate = set2();
      await repository.loadStructure('JP');
      expect(loader.callsFor('regions/JP.json'), 1);

      await repository.updateTo(candidate);

      expect(repository.manifest, same(candidate));
      expect(
        repository.structureFor('JP'),
        isNotNull,
        reason: 'unchanged revision: reused, not refetched',
      );
      expect(loader.callsFor('regions/JP.json'), 1);
      expect(loader.callsFor('regions/SA.json'), 1);
      expect(loader.callsFor('i18n/zh-Hans/SA.json'), 1);
      expect(repository.structureFor('SA'), isNotNull);
      expect(repository.isStale, isFalse);
      expect(await store.totalSize(), greaterThan(0));
    });

    test(
      'no cross-release mixing: content outside the new manifest is cleared',
      () async {
        final loader = servingLoader(payloads12());
        final repository = repositoryWith(loader: loader);
        final candidate = set2();
        await repository.loadStructure('JP');
        await repository.loadLocalePack('JP', 'zh-Hans');

        await repository.updateTo(candidate);

        expect(
          repository.packFor('JP', 'zh-Hans'),
          isNull,
          reason: 'packs not declared by the new manifest are not served',
        );
        expect(repository.structureFor('JP'), isNotNull);
        expect(
          repository.activeCountry,
          isNull,
          reason: 'active intent resets with the new set',
        );
      },
    );

    test(
      'failed update keeps the current set usable (stale coherent)',
      () async {
        final loader = servingLoader(payloads12());
        loader.fault = (Uri uri) => uri.toString().contains('regions/SA.json')
            ? const GeoNetworkError('offline')
            : null;
        final first = set1();
        final repository = repositoryWith(loader: loader, manifest: first);
        await repository.loadStructure('JP');

        await expectLater(
          repository.updateTo(set2()),
          throwsA(isA<GeoNetworkError>()),
        );

        expect(repository.manifest, same(first));
        expect(
          repository.isStale,
          isTrue,
          reason: 'explicit stale flag for offline fallback',
        );
        expect(
          repository.structureFor('SA'),
          isNull,
          reason: 'partially staged content must not leak into the active set',
        );

        // The previous complete set still serves offline without any request.
        final before = loader.callCount;
        final structure = await repository.loadStructure('JP');
        expect(structure.countryCode, 'JP');
        expect(loader.callCount, before);
      },
    );

    test('stale flag clears after a successful update', () async {
      final loader = servingLoader(payloads12());
      final repository = repositoryWith(loader: loader);
      await repository.loadStructure('JP');

      loader.fault = (Uri uri) =>
          uri.toString().contains('i18n/zh-Hans/SA.json')
          ? const GeoNetworkError('offline')
          : null;
      await expectLater(
        repository.updateTo(set2()),
        throwsA(isA<GeoNetworkError>()),
      );
      expect(repository.isStale, isTrue);

      loader.fault = null;
      await repository.updateTo(set2());
      expect(repository.isStale, isFalse);
    });

    test(
      'integrity failure during update leaves the old cache untouched',
      () async {
        final store = GeoMemoryCacheStore();
        final loader = servingLoader(payloads12());
        final first = set1();
        final repository = repositoryWith(
          loader: loader,
          store: store,
          manifest: first,
        );
        await repository.loadStructure('JP');
        final jpKey = store.writeLog.single;

        loader.serve(
          'regions/SA.json',
          flipOneByte(dataBytes('regions/SA.json')),
        );
        await expectLater(
          repository.updateTo(set2()),
          throwsA(isA<GeoIntegrityMismatchError>()),
        );

        final cached = await store.read(jpKey);
        expect(cached!.bytes, dataBytes('regions/JP.json'));
        expect(
          store.writeLog.where((key) => key.countryCode == 'SA'),
          isEmpty,
          reason: 'corrupt staged resource is never written',
        );
        expect(repository.manifest, same(first));
      },
    );
  });
}

void failedUpdateGroup() {
  group('AT-10 guards', () {
    test('foreign dataset manifests are rejected', () async {
      final repository = repositoryWith(loader: servingLoader(payloads12()));
      await expectLater(
        repository.updateTo(
          manifestOf(<GeoManifestEntry>[
            entry('regions/JP.json'),
          ], datasetId: 'other-ns'),
        ),
        throwsA(isA<GeoConfigurationError>()),
      );
    });

    test(
      'locale entries without a matching structure entry fail staging',
      () async {
        final loader = servingLoader(payloads12());
        final first = set1();
        final repository = repositoryWith(loader: loader, manifest: first);
        await repository.loadStructure('JP');
        final broken = manifestOf(<GeoManifestEntry>[
          entry('regions/JP.json'),
          entry('i18n/zh-Hans/SA.json'), // structure for SA missing
        ]);
        await expectLater(
          repository.updateTo(broken),
          throwsA(isA<GeoIntegrityMismatchError>()),
        );
        expect(repository.manifest, same(first));
        expect(repository.isStale, isTrue);
      },
    );
  });
}

void guardGroup() {
  group('update concurrency guard', () {
    test('a second update while one is in progress fails fast', () async {
      final loader = ManualGeoLoader();
      final repository = repositoryWith(loader: loader);
      final candidate = set2();

      final first = repository.updateTo(candidate);
      await expectLater(
        repository.updateTo(candidate),
        throwsA(isA<GeoConfigurationError>()),
      );

      loader.completeWhere(
        'regions/JP.json',
        GeoBytes(dataBytes('regions/JP.json')),
      );
      await pump();
      loader.completeWhere(
        'regions/SA.json',
        GeoBytes(dataBytes('regions/SA.json')),
      );
      await pump();
      loader.completeWhere(
        'i18n/zh-Hans/SA.json',
        GeoBytes(dataBytes('i18n/zh-Hans/SA.json')),
      );
      await pump();
      await first;
      expect(repository.manifest, same(candidate));
    });
  });
}
