// SPDX-License-Identifier: BSD-3-Clause
/// Loading pipeline tests: on-demand fetching (AT-06), strict remote
/// configuration (AT-09), bad-download containment (AT-08) and cache-key
/// version isolation (PRD §8).
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'fake_adapters.dart';
import 'fixture_bytes.dart';

GeoRegionsRepository repositoryWith({
  required FakeGeoLoader loader,
  GeoMemoryCacheStore? store,
  FakeVerifier? verifier,
  GeoManifest? manifest,
}) {
  return GeoRegionsRepository(
    manifest: manifest ?? realManifest,
    store: store,
    remoteLoader: loader,
    remoteBase: testBase(),
    verifier: verifier ?? FakeVerifier(),
  );
}

void main() {
  onDemandGroup();
  strictRemoteConfigGroup();
  integrityGroup();
  cacheIsolationGroup();
  evictionGroup();
}

void onDemandGroup() {
  group('AT-06: target country fetched on demand', () {
    test('structure load requests only the target country resource', () async {
      final store = GeoMemoryCacheStore();
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': dataBytes('regions/JP.json'),
      });
      final repository = repositoryWith(loader: loader, store: store);

      final structure = await repository.loadStructure('JP');

      expect(structure.countryCode, 'JP');
      expect(loader.requests, <Uri>[
        uriFor('regions/JP.json', testBase()),
      ], reason: 'no other country resource may be requested');
      expect(repository.structureFor('JP'), same(structure));
      expect(repository.index, isNotNull);
      expect(await store.totalSize(), greaterThan(0));
      expect(
        store.writeLog.where((key) => key.kind == GeoResourceKind.structure),
        isNotEmpty,
      );
    });

    test('locale pack fetch adds only the language resource, never structure again', () async {
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': dataBytes('regions/JP.json'),
        'i18n/zh-Hans/JP.json': dataBytes('i18n/zh-Hans/JP.json'),
      });
      final repository = repositoryWith(loader: loader);

      await repository.loadStructure('JP');
      expect(loader.callsFor('regions/JP.json'), 1);

      final pack = await repository.loadLocalePack('JP', 'zh-Hans');
      expect(pack.locale, 'zh-Hans');
      expect(loader.callsFor('i18n/zh-Hans/JP.json'), 1);
      expect(
        loader.callsFor('regions/JP.json'),
        1,
        reason: 'GR-04: structure is already cached',
      );
      expect(repository.packFor('JP', 'zh-Hans'), same(pack));
    });

    test('committed resources are re-served without any I/O', () async {
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': dataBytes('regions/JP.json'),
      });
      final repository = repositoryWith(loader: loader);

      final first = await repository.loadStructure('JP');
      final second = await repository.loadStructure('JP');

      expect(second, same(first));
      expect(loader.callCount, 1);
    });

    test('exact-identity cache hit serves without the loader', () async {
      final store = GeoMemoryCacheStore();
      final entry = realEntry('regions/JP.json');
      await store.write(
        GeoCacheKey.fromManifestEntry('geo-regions-seed', entry),
        GeoBytes(dataBytes('regions/JP.json')),
      );
      final loader = servingLoader(<String, Uint8List>{});
      final repository = repositoryWith(loader: loader, store: store);

      final structure = await repository.loadStructure('JP');

      expect(structure.revision, entry.revision);
      expect(loader.callCount, 0);
    });
  });
}

void strictRemoteConfigGroup() {
  group('AT-09: strict remote mode requires a verifier', () {
    test('remote loader without verifier fails fast at construction', () {
      expect(
        () => GeoRegionsRepository(
          manifest: realManifest,
          remoteLoader: servingLoader(<String, Uint8List>{}),
          remoteBase: testBase(),
        ),
        throwsA(isA<GeoConfigurationError>()),
      );
    });

    test('remote loader with verifier constructs', () {
      expect(
        () => GeoRegionsRepository(
          manifest: realManifest,
          remoteLoader: servingLoader(<String, Uint8List>{}),
          remoteBase: testBase(),
          verifier: FakeVerifier(),
        ),
        returnsNormally,
      );
    });

    test('cache-only and bundled-only repositories need no verifier', () {
      expect(
        () => GeoRegionsRepository(
          manifest: realManifest,
          store: GeoMemoryCacheStore(),
        ),
        returnsNormally,
      );
    });
  });
}

void integrityGroup() {
  group('AT-08: bad downloads never pollute cache or state', () {
    test('SHA-256 mismatch is rejected and nothing is written', () async {
      final store = GeoMemoryCacheStore();
      final verifier = FakeVerifier();
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': flipOneByte(dataBytes('regions/JP.json')),
      });
      final repository = repositoryWith(
        loader: loader,
        store: store,
        verifier: verifier,
      );

      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );

      expect(verifier.calls, 1, reason: 'hash check must run before decoding');
      expect(store.writeLog, isEmpty);
      expect(await store.totalSize(), 0);
      expect(repository.structureFor('JP'), isNull);
      expect(repository.index, isNull);
    });

    test('short read is rejected before hashing', () async {
      final verifier = FakeVerifier();
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': shortBytes(dataBytes('regions/JP.json')),
      });
      final repository = repositoryWith(loader: loader, verifier: verifier);

      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );
      expect(verifier.calls, 0, reason: 'length pre-check happens first');
    });

    test('invalid JSON fails parse without polluting the cache', () async {
      final store = GeoMemoryCacheStore();
      final payload = invalidJsonBytes();
      final entry = syntheticEntry(
        path: 'regions/JP.json',
        kind: GeoResourceKind.structure,
        payload: payload,
        countryCode: 'JP',
      );
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': payload,
      });
      final repository = repositoryWith(
        loader: loader,
        store: store,
        manifest: manifestOf(<GeoManifestEntry>[entry]),
      );

      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoParseFailureError>()),
      );
      expect(
        store.writeLog,
        isEmpty,
        reason: 'parse happens before the cache write',
      );
      expect(await store.totalSize(), 0);
    });

    test(
      'content disagreeing with the manifest identity is rejected',
      () async {
        final store = GeoMemoryCacheStore();
        final realBytes = dataBytes('regions/JP.json');
        final entry = copyEntry(
          realEntry('regions/JP.json'),
          revision: 's-0000000000000000',
        );
        final loader = servingLoader(<String, Uint8List>{
          'regions/JP.json': realBytes,
        });
        final repository = repositoryWith(
          loader: loader,
          store: store,
          manifest: manifestOf(<GeoManifestEntry>[entry]),
        );

        await expectLater(
          repository.loadStructure('JP'),
          throwsA(isA<GeoIntegrityMismatchError>()),
        );
        expect(store.writeLog, isEmpty);
      },
    );

    test(
      'failed download leaves the previous revision cache entry intact',
      () async {
        final store = GeoMemoryCacheStore();
        final realBytes = dataBytes('regions/JP.json');
        // A previous release lives under its own (older) revision key.
        final oldEntry = copyEntry(
          realEntry('regions/JP.json'),
          revision: 's-0000000000000000',
        );
        final oldKey = GeoCacheKey.fromManifestEntry(
          'geo-regions-seed',
          oldEntry,
        );
        await store.write(oldKey, GeoBytes(realBytes));

        final loader = servingLoader(<String, Uint8List>{
          'regions/JP.json': flipOneByte(realBytes),
        });
        final repository = repositoryWith(loader: loader, store: store);

        await expectLater(
          repository.loadStructure('JP'),
          throwsA(isA<GeoIntegrityMismatchError>()),
        );

        final cached = await store.read(oldKey);
        expect(cached, isNotNull);
        expect(
          cached!.bytes,
          realBytes,
          reason: 'old cache entry must remain byte-identical',
        );
        expect(
          store.writeLog,
          <GeoCacheKey>[oldKey],
          reason: 'corrupt download must not be written; only the pre-seeded entry exists',
        );
      },
    );

    test('corrupted cache entry with wrong length is detected', () async {
      final store = GeoMemoryCacheStore();
      final entry = realEntry('regions/JP.json');
      await store.write(
        GeoCacheKey.fromManifestEntry('geo-regions-seed', entry),
        GeoBytes(shortBytes(dataBytes('regions/JP.json'))),
      );
      final loader = servingLoader(<String, Uint8List>{});
      final repository = repositoryWith(loader: loader, store: store);

      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );
      expect(loader.callCount, 0);
    });

    test('verifier rejection surfaces as integrity mismatch', () async {
      final verifier = FakeVerifier()..failNext = true;
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': dataBytes('regions/JP.json'),
      });
      final repository = repositoryWith(loader: loader, verifier: verifier);

      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );
      expect(repository.structureFor('JP'), isNull);
    });
  });
}

void cacheIsolationGroup() {
  group('cache-key version isolation', () {
    test('cache written under another revision never answers', () async {
      final store = GeoMemoryCacheStore();
      final entry = realEntry('regions/JP.json');
      // Same resource identity except the revision — must not count as a hit.
      await store.write(
        copyKeyOf(entry, revision: 's-0000000000000000'),
        GeoBytes(dataBytes('regions/JP.json')),
      );
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': dataBytes('regions/JP.json'),
      });
      final repository = repositoryWith(loader: loader, store: store);

      final structure = await repository.loadStructure('JP');

      expect(structure.revision, entry.revision);
      expect(loader.callCount, 1, reason: 'stale-revision cache is not a hit');
    });

    test('resources outside the manifest are not found', () async {
      final loader = servingLoader(<String, Uint8List>{});
      final repository = repositoryWith(loader: loader);
      await expectLater(
        repository.loadStructure('ZZ'),
        throwsA(isA<GeoNotFoundError>()),
      );
      await expectLater(
        repository.loadLocalePack('JP', 'zz-XX'),
        throwsA(isA<GeoNotFoundError>()),
      );
    });
  });
}

GeoCacheKey copyKeyOf(GeoManifestEntry entry, {String? revision}) {
  return GeoCacheKey(
    datasetId: 'geo-regions-seed',
    kind: entry.kind,
    countryCode: entry.countryCode,
    locale: entry.locale,
    revision: revision ?? entry.revision,
    sha256: entry.sha256,
  );
}

void evictionGroup() {
  group('cache eviction hook', () {
    test('evictDataset removes only the pinned dataset entries', () async {
      final store = GeoMemoryCacheStore();
      final repository = repositoryWith(
        loader: servingLoader(<String, Uint8List>{
          'regions/JP.json': dataBytes('regions/JP.json'),
        }),
        store: store,
      );
      await repository.loadStructure('JP');
      final foreignEntry = realEntry('regions/JP.json');
      await store.write(
        GeoCacheKey(
          datasetId: 'other-ns',
          kind: foreignEntry.kind,
          countryCode: foreignEntry.countryCode,
          revision: foreignEntry.revision,
          sha256: foreignEntry.sha256,
        ),
        GeoBytes(Uint8List.fromList(<int>[1])),
      );

      final removed = await repository.evictDataset('geo-regions-seed');

      expect(removed, 1);
      expect(await store.keys(), hasLength(1));
      expect((await store.keys()).single.datasetId, 'other-ns');
      expect(await repository.evictDataset('nothing-here'), 0);
    });
  });
}
