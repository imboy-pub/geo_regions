// SPDX-License-Identifier: BSD-3-Clause
/// Unit tests for the injected contracts (CONSUMER_CONTRACT.md §5): cache
/// key identity, memory store semantics and injectable faults.
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'fixture_bytes.dart';

void main() {
  cacheKeyGroup();
  geoBytesGroup();
  memoryStoreGroup();
}

void cacheKeyGroup() {
  group('GeoCacheKey identity', () {
    final entry = realEntry('regions/JP.json');

    GeoCacheKey keyFromEntry() =>
        GeoCacheKey.fromManifestEntry('geo-regions-seed', entry);

    test('equality covers every identity field', () {
      expect(keyFromEntry(), keyFromEntry());
      expect(keyFromEntry().hashCode, keyFromEntry().hashCode);
      expect(
        keyFromEntry(),
        isNot(GeoCacheKey.fromManifestEntry('other-dataset', entry)),
      );
      expect(
        keyFromEntry(),
        isNot(copyKey(keyFromEntry(), revision: 's-ffffffffffffffff')),
      );
      expect(
        keyFromEntry(),
        isNot(
          copyKey(keyFromEntry(), sha256: 'ff${entry.sha256.substring(2)}'),
        ),
      );
      expect(
        keyFromEntry(),
        isNot(
          copyKey(
            keyFromEntry(),
            kind: GeoResourceKind.locale,
            locale: 'zh-Hans',
          ),
        ),
      );
    });

    test('fromManifestEntry mirrors the entry identity', () {
      final key = keyFromEntry();
      expect(key.datasetId, 'geo-regions-seed');
      expect(key.kind, GeoResourceKind.structure);
      expect(key.countryCode, 'JP');
      expect(key.locale, isNull);
      expect(key.revision, entry.revision);
      expect(key.sha256, entry.sha256);
    });

    test('storage key is stable and carries the identity', () {
      final key = keyFromEntry();
      final storage = key.toStorageKey();
      expect(storage, contains('geo_regions'));
      expect(storage, contains('geo-regions-seed'));
      expect(storage, contains('structure'));
      expect(storage, contains('JP'));
      expect(storage, contains(entry.revision));
      expect(storage, key.toStorageKey());
    });
  });
}

GeoCacheKey copyKey(
  GeoCacheKey key, {
  String? revision,
  String? sha256,
  GeoResourceKind? kind,
  String? locale,
}) {
  return GeoCacheKey(
    datasetId: key.datasetId,
    kind: kind ?? key.kind,
    countryCode: key.countryCode,
    locale: locale ?? key.locale,
    revision: revision ?? key.revision,
    sha256: sha256 ?? key.sha256,
  );
}

void geoBytesGroup() {
  group('GeoBytes', () {
    test('exposes length and optional transport content length', () {
      final bytes = GeoBytes(
        Uint8List.fromList(<int>[1, 2, 3]),
        contentLength: 3,
      );
      expect(bytes.length, 3);
      expect(bytes.contentLength, 3);
      expect(bytes.toString(), contains('3 bytes'));
      expect(GeoBytes(Uint8List(0)).contentLength, isNull);
    });
  });
}

void memoryStoreGroup() {
  group('GeoMemoryCacheStore', () {
    late GeoMemoryCacheStore store;
    late GeoCacheKey key;

    setUp(() {
      store = GeoMemoryCacheStore();
      key = GeoCacheKey(
        datasetId: 'geo-regions-seed',
        kind: GeoResourceKind.structure,
        countryCode: 'JP',
        revision: 's-1234567890abcdef',
        sha256: 'aa${'11' * 31}',
      );
    });

    test('write, read, invalidate round trip', () async {
      final payload = GeoBytes(Uint8List.fromList(<int>[9, 8, 7]));
      await store.write(key, payload);
      expect(await store.read(key), same(payload));
      expect(
        await store.read(
          GeoCacheKey(
            datasetId: key.datasetId,
            kind: key.kind,
            countryCode: key.countryCode,
            revision: key.revision,
            sha256: 'bb${'22' * 31}',
          ),
        ),
        isNull,
      );
      await store.invalidate(key);
      expect(await store.read(key), isNull);
      await store.invalidate(key); // no-op when absent
    });

    test('keys, totalSize and clear support quota accounting', () async {
      final payload = Uint8List.fromList(<int>[1, 2, 3, 4]);
      await store.write(key, GeoBytes(payload));
      final other = copyKey(key, revision: 's-ffffffffffffffff');
      await store.write(other, GeoBytes(payload));
      expect(await store.keys(), unorderedEquals(<GeoCacheKey>[key, other]));
      expect(await store.totalSize(), 8);
      await store.clear();
      expect(await store.keys(), isEmpty);
      expect(await store.totalSize(), 0);
      expect(store.writeLog, isEmpty);
    });

    test('write log records successful writes in order', () async {
      final second = copyKey(key, revision: 's-ffffffffffffffff');
      await store.write(key, GeoBytes(Uint8List(1)));
      await store.write(second, GeoBytes(Uint8List(2)));
      expect(store.writeLog, <GeoCacheKey>[key, second]);
    });

    test('read faults are injectable and deterministic', () async {
      store.readFault = (GeoCacheKey _) => const GeoNetworkError('disk broken');
      await expectLater(store.read(key), throwsA(isA<GeoNetworkError>()));
      store.readFault = null;
      expect(await store.read(key), isNull);
    });

    test('write faults leave the store and write log untouched', () async {
      store.writeFault = (GeoCacheKey _) => StateError('io failure');
      await expectLater(
        store.write(key, GeoBytes(Uint8List.fromList(<int>[1]))),
        throwsA(isA<StateError>()),
      );
      expect(store.writeLog, isEmpty);
      expect(await store.totalSize(), 0);
    });

    test('fault hooks can target a single key', () async {
      final other = copyKey(key, revision: 's-ffffffffffffffff');
      store.writeFault = (GeoCacheKey candidate) =>
          candidate == key ? const GeoNetworkError('quota exceeded') : null;
      await store.write(other, GeoBytes(Uint8List(2)));
      await expectLater(
        store.write(key, GeoBytes(Uint8List(1))),
        throwsA(isA<GeoNetworkError>()),
      );
      expect(store.writeLog, <GeoCacheKey>[other]);
    });
  });
}
