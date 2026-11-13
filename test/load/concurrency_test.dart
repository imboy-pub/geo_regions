// SPDX-License-Identifier: BSD-3-Clause
/// Concurrency and generation-token tests (AT-07, GR-05): request
/// deduplication, out-of-order responses and dispose semantics.
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'fake_adapters.dart';
import 'fixture_bytes.dart';

GeoRegionsRepository manualRepository({
  required ManualGeoLoader loader,
  GeoMemoryCacheStore? store,
  GeoManifest? manifest,
}) {
  return GeoRegionsRepository(
    manifest: manifest ?? realManifest,
    store: store,
    remoteLoader: loader,
    remoteBase: testBase(),
    verifier: FakeVerifier(),
  );
}

final Map<String, Uint8List> manualPayloads = <String, Uint8List>{
  'regions/JP.json': dataBytes('regions/JP.json'),
  'regions/CN.json': dataBytes('regions/CN.json'),
  'i18n/zh-Hans/JP.json': dataBytes('i18n/zh-Hans/JP.json'),
  'i18n/en/JP.json': dataBytes('i18n/en/JP.json'),
  'countries.json': dataBytes('countries.json'),
  'catalog_i18n/en.json': dataBytes('catalog_i18n/en.json'),
  'catalog_i18n/zh-Hans.json': dataBytes('catalog_i18n/zh-Hans.json'),
};

GeoBytes payloadOf(String path) => GeoBytes(manualPayloads[path]!);

void main() {
  dedupeGroup();
  outOfOrderGroup();
  disposeGroup();
}

void dedupeGroup() {
  group('AT-07/GR-05: same-key requests share one in-flight load', () {
    test(
      'two concurrent structure loads hit the loader exactly once',
      () async {
        final loader = ManualGeoLoader();
        final repository = manualRepository(loader: loader);

        final first = repository.loadStructure('JP');
        final second = repository.loadStructure('JP');

        expect(loader.hasPending, isTrue);
        expect(loader.callsFor('regions/JP.json'), 1);

        loader.completeWhere('regions/JP.json', payloadOf('regions/JP.json'));
        final structures = await Future.wait(<Future<GeoRegionStructure>>[
          first,
          second,
        ]);

        expect(structures[0], same(structures[1]));
        expect(loader.callsFor('regions/JP.json'), 1);
      },
    );

    test(
      'a request joining mid-flight does not re-trigger the loader',
      () async {
        final loader = ManualGeoLoader();
        final repository = manualRepository(loader: loader);

        final first = repository.loadStructure('JP');
        loader.completeWhere('regions/JP.json', payloadOf('regions/JP.json'));
        final second = repository.loadStructure('JP');

        expect(await first, same(await second));
        expect(loader.callsFor('regions/JP.json'), 1);
      },
    );

    test('failed loads are not memoized: the retry refetches', () async {
      final loader = ManualGeoLoader();
      final repository = manualRepository(loader: loader);

      final failing = repository.loadStructure('JP');
      loader.failWhere(
        'regions/JP.json',
        const GeoNetworkError('connection lost'),
      );
      await expectLater(failing, throwsA(isA<GeoNetworkError>()));

      final retry = repository.loadStructure('JP');
      expect(loader.callsFor('regions/JP.json'), 2);
      loader.completeWhere('regions/JP.json', payloadOf('regions/JP.json'));
      expect((await retry).countryCode, 'JP');
    });
  });
}

void outOfOrderGroup() {
  group('AT-07: late responses never overwrite the newest intent', () {
    test(
      'fast country switch: stale response keeps the new selection',
      () async {
        final loader = ManualGeoLoader();
        final repository = manualRepository(loader: loader);
        final events = <String>[];
        repository.addListener(() => events.add('changed'));

        final staleSwitch = repository.switchCountry('JP');
        final freshSwitch = repository.switchCountry('CN');

        // The fresh (later) intent completes first.
        loader.completeWhere('regions/CN.json', payloadOf('regions/CN.json'));
        await pump();
        expect(repository.activeCountry, 'CN');
        expect(events, <String>['changed']);

        // The stale (earlier) intent arrives afterwards and must not commit.
        loader.completeWhere('regions/JP.json', payloadOf('regions/JP.json'));
        await pump();
        await staleSwitch;
        await freshSwitch;

        expect(repository.activeCountry, 'CN');
        expect(events, <String>[
          'changed',
        ], reason: 'stale commit must not notify');
        expect(
          repository.structureFor('JP'),
          isNotNull,
          reason: 'content cache stays additive and identity-keyed',
        );
        expect(repository.structureFor('CN'), isNotNull);
      },
    );

    test('fast locale switch: stale locale keeps the newest', () async {
      final loader = ManualGeoLoader();
      final repository = manualRepository(loader: loader);

      final countrySwitch = repository.switchCountry('JP');
      loader.completeWhere('regions/JP.json', payloadOf('regions/JP.json'));
      await pump();
      await countrySwitch;

      final staleLocale = repository.switchLocale('en');
      final freshLocale = repository.switchLocale('zh-Hans');

      loader.completeWhere('countries.json', payloadOf('countries.json'));
      await pump();
      loader.completeWhere(
        'catalog_i18n/zh-Hans.json',
        payloadOf('catalog_i18n/zh-Hans.json'),
      );
      await pump();
      loader.completeWhere(
        'i18n/zh-Hans/JP.json',
        payloadOf('i18n/zh-Hans/JP.json'),
      );
      await pump();

      expect(repository.activeLocale, 'zh-Hans');

      loader.completeWhere(
        'catalog_i18n/en.json',
        payloadOf('catalog_i18n/en.json'),
      );
      await pump();
      loader.completeWhere('i18n/en/JP.json', payloadOf('i18n/en/JP.json'));
      await pump();
      await staleLocale;
      await freshLocale;

      expect(
        repository.activeLocale,
        'zh-Hans',
        reason: 'stale locale commit dropped',
      );
      expect(repository.packFor('JP', 'zh-Hans'), isNotNull);
    });
  });
}

void disposeGroup() {
  group('dispose semantics', () {
    test('late response after dispose commits and notifies nothing', () async {
      final loader = ManualGeoLoader();
      final store = GeoMemoryCacheStore();
      final repository = manualRepository(loader: loader, store: store);
      final events = <String>[];
      repository.addListener(() => events.add('changed'));

      final pending = repository.switchCountry('JP');
      await pump(); // let the load reach the manual loader's pending queue
      repository.dispose();

      loader.completeWhere('regions/JP.json', payloadOf('regions/JP.json'));
      await pump();
      await pending;

      expect(repository.isDisposed, isTrue);
      expect(repository.activeCountry, isNull);
      expect(
        events,
        isEmpty,
        reason: 'callbacks are silently dropped after dispose',
      );
      expect(store.writeLog, isEmpty, reason: 'no cache writes after dispose');
      expect(await store.totalSize(), 0);
    });

    test('loads after dispose fail with a configuration error', () async {
      final repository = manualRepository(loader: ManualGeoLoader());
      repository.dispose();
      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoConfigurationError>()),
      );
      repository.dispose(); // idempotent
    });
  });
}
