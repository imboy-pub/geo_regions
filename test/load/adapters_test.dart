// SPDX-License-Identifier: BSD-3-Clause
/// Adapter tests: the bundled asset loader maps manifest-relative paths to
/// declared Flutter assets and keeps failure conditions typed.
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'fake_adapters.dart';
import 'fixture_bytes.dart';

void main() {
  group('GeoAssetBundleLoader', () {
    test('loads a declared asset under the configured prefix', () async {
      final jpBytes = dataBytes('regions/JP.json');
      final loader = GeoAssetBundleLoader(
        bundle: FakeAssetBundle(<String, ByteData>{
          'assets/geo_regions/regions/JP.json': byteDataOf(jpBytes),
        }),
      );
      final bytes = await loader.load(Uri(path: 'regions/JP.json'));
      expect(bytes.bytes, jpBytes);
      expect(bytes.contentLength, jpBytes.length);
    });

    test('custom prefix is honored', () async {
      final loader = GeoAssetBundleLoader(
        bundle: FakeAssetBundle(<String, ByteData>{
          'res/geo/countries.json': byteDataOf(dataBytes('countries.json')),
        }),
        assetPrefix: 'res/geo/',
      );
      final bytes = await loader.load(Uri(path: 'countries.json'));
      expect(bytes.length, dataBytes('countries.json').length);
    });

    test('missing asset surfaces as GeoNotFoundError', () async {
      final loader = GeoAssetBundleLoader(
        bundle: FakeAssetBundle(<String, ByteData>{}),
      );
      await expectLater(
        loader.load(Uri(path: 'regions/ZZ.json')),
        throwsA(
          isA<GeoNotFoundError>().having(
            (error) => error.message,
            'message',
            contains('assets/geo_regions/regions/ZZ.json'),
          ),
        ),
      );
    });

    test('traversal paths are rejected without touching the bundle', () async {
      final loader = GeoAssetBundleLoader(
        bundle: FakeAssetBundle(<String, ByteData>{}),
      );
      await expectLater(
        loader.load(Uri(path: 'regions/../manifest.json')),
        throwsA(isA<GeoNotFoundError>()),
      );
    });

    test('repository falls through from a missing asset to remote', () async {
      final jpBytes = dataBytes('regions/JP.json');
      final loader = servingLoader(<String, Uint8List>{
        'regions/JP.json': jpBytes,
      });
      final bundledLoader = GeoAssetBundleLoader(
        bundle: FakeAssetBundle(<String, ByteData>{
          'assets/geo_regions/regions/CN.json': byteDataOf(
            dataBytes('regions/SA.json'),
          ),
        }),
      );
      final repository = GeoRegionsRepository(
        manifest: realManifest,
        bundledLoader: bundledLoader,
        remoteLoader: loader,
        remoteBase: testBase(),
        verifier: FakeVerifier(),
      );
      final structure = await repository.loadStructure('JP');
      expect(structure.countryCode, 'JP');
      expect(loader.callsFor('regions/JP.json'), 1);
    });

    test('bundled-only repository loads offline', () async {
      final jpBytes = dataBytes('regions/JP.json');
      final repository = GeoRegionsRepository(
        manifest: manifestOf(<GeoManifestEntry>[realEntry('regions/JP.json')]),
        bundledLoader: GeoAssetBundleLoader(
          bundle: FakeAssetBundle(<String, ByteData>{
            'assets/geo_regions/regions/JP.json': byteDataOf(jpBytes),
          }),
        ),
      );
      final structure = await repository.loadStructure('JP');
      expect(structure.revision, realEntry('regions/JP.json').revision);
      expect(repository.isStale, isFalse);
    });

    test('bundled bytes failing the pinned identity are rejected', () async {
      final corrupted = flipOneByte(dataBytes('regions/JP.json'));
      final repository = GeoRegionsRepository(
        manifest: manifestOf(<GeoManifestEntry>[realEntry('regions/JP.json')]),
        bundledLoader: GeoAssetBundleLoader(
          bundle: FakeAssetBundle(<String, ByteData>{
            'assets/geo_regions/regions/JP.json': byteDataOf(corrupted),
          }),
        ),
      );
      await expectLater(
        repository.loadStructure('JP'),
        throwsA(isA<GeoIntegrityMismatchError>()),
      );
    });
  });
}
