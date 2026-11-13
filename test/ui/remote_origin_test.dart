// SPDX-License-Identifier: BSD-3-Clause
/// Real remote loading over actual HTTP, on the VM (P1-07, AT-06/AT-08/AT-09).
///
/// A `dart:io` HttpServer on a loopback port serves the repository's own
/// `data/` files with `Content-Type: application/json`. These tests run the
/// complete chain — download → length check → SHA-256 verification → parse →
/// cache — through an HTTP loader and the in-library digest, and the server
/// log proves that only the target country's resources are requested
/// (GR-04). 404, corrupted bytes and a closed server surface as distinct
/// typed errors.
///
/// This file deliberately contains no widget tests: the widget-test binding
/// installs an HttpOverrides fake (status 400 for everything), so any file
/// with a `testWidgets` cannot speak real HTTP. The widget-level rendering
/// of remotely sourced data lives in `remote_flow_test.dart`.
library;

import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import '../load/fixture_bytes.dart';

/// Serves `data/` over HTTP with tamper and 404 switches plus a request log.
class _RemoteOrigin {
  HttpServer? _server;
  int? _port;
  final Set<String> missing = <String>{};
  final Set<String> corrupt = <String>{};
  final List<String> requests = <String>[];

  Uri get base => Uri.parse('http://127.0.0.1:${_server?.port ?? 1}/');

  /// Starts (or restarts on the SAME port, so a repository pinned to the
  /// first URI can recover against the restarted origin).
  Future<void> start() async {
    _server = await HttpServer.bind(InternetAddress.loopbackIPv4, _port ?? 0);
    _port = _server!.port;
    _server!.listen((request) async {
      final path = request.uri.path.replaceFirst(RegExp(r'^/'), '');
      // ignore: avoid_print
      print(
        'SERVER REQUEST: method=${request.method} uri=${request.uri} path="$path"',
      );
      requests.add(path);
      try {
        if (missing.contains(path)) {
          request.response.statusCode = 404;
          await request.response.close();
          return;
        }
        final file = File('data/$path');
        if (!file.existsSync()) {
          request.response.statusCode = 404;
          await request.response.close();
          return;
        }
        final bytes = Uint8List.fromList(await file.readAsBytes());
        if (corrupt.contains(path) && bytes.isNotEmpty) {
          bytes[0] = bytes[0] ^ 0x5A;
        }
        request.response.headers.set(
          HttpHeaders.contentTypeHeader,
          'application/json; charset=utf-8',
        );
        request.response.contentLength = bytes.length;
        request.response.add(bytes);
        await request.response.close();
      } on Object {
        await request.response.close();
      }
    });
  }

  Future<void> stop() async {
    await _server?.close(force: true);
    _server = null;
  }
}

/// Minimal HTTP [GeoResourceLoader]; transport failures map to typed errors.
class _HttpLoader implements GeoResourceLoader {
  @override
  Future<GeoBytes> load(Uri uri) async {
    final HttpClientResponse response;
    try {
      final request = await HttpClient().getUrl(uri);
      response = await request.close().timeout(const Duration(seconds: 10));
    } on Object {
      throw GeoNetworkError('transport failure while fetching $uri');
    }
    if (response.statusCode == 404) {
      await response.drain<void>();
      throw GeoNotFoundError('HTTP 404 for $uri');
    }
    if (response.statusCode != 200) {
      await response.drain<void>();
      throw GeoNetworkError('HTTP ${response.statusCode} for $uri');
    }
    final body = await response.fold<List<int>>(
      <int>[],
      (accumulated, chunk) => accumulated..addAll(chunk),
    );
    return GeoBytes(
      Uint8List.fromList(body),
      contentLength: response.contentLength,
    );
  }
}

class _ShaVerifier implements GeoHashVerifier {
  const _ShaVerifier();

  @override
  Future<bool> verify(GeoBytes bytes, String sha256, int expectedBytes) async {
    return bytes.length == expectedBytes && geoSha256Hex(bytes.bytes) == sha256;
  }
}

GeoRegionsRepository _repository(_RemoteOrigin origin, {GeoCacheStore? store}) {
  return GeoRegionsRepository(
    manifest: realManifest,
    remoteLoader: _HttpLoader(),
    remoteBase: origin.base,
    verifier: const _ShaVerifier(),
    store: store ?? GeoMemoryCacheStore(),
  );
}

void main() {
  test('strict remote mode without a verifier is a configuration error', () {
    final origin = _RemoteOrigin();
    expect(
      () => GeoRegionsRepository(
        manifest: realManifest,
        remoteLoader: _HttpLoader(),
        remoteBase: origin.base,
      ),
      throwsA(isA<GeoConfigurationError>()),
    );
  });

  test(
    'repository drives download→verify→parse→cache over real HTTP',
    () async {
      final origin = _RemoteOrigin();
      await origin.start();
      final store = GeoMemoryCacheStore();
      final source = GeoRepositoryDataSource(
        _repository(origin, store: store),
        defaultLocale: 'en',
      );
      addTearDown(origin.stop);

      // Opening Japan fetches exactly that country's resources — no catalog,
      // no other country, no extra locale packs (GR-04/AT-06), each exactly
      // once (deduplicated).
      final content = await source.openCountry('JP', 'zh-Hans');
      expect(content.root.nodeId, 'cc:JP');
      expect(origin.requests, <String>[
        'regions/JP.json',
        'i18n/zh-Hans/JP.json',
      ]);
      expect(store.writeLog.map((key) => key.countryCode), everyElement('JP'));

      // Reopening and navigating into the verified structure is free.
      await source.openCountry('JP', 'zh-Hans');
      await source.loadChildren('JP', 'iso3166-2:JP-13', 'zh-Hans');
      expect(origin.requests.length, 2);

      // Names resolve through the verified content.
      expect(content.children.first.nodeId, 'iso3166-2:JP-01');

      // The draft selection builds against the verified revision.
      final selection = await source.resolveSelection(
        <String>['cc:JP'],
        policy: GeoSelectionPolicy.allowIntermediate,
        displayLocale: 'zh-Hans',
      );
      expect(selection.datasetId, 'geo-regions-seed');
      expect(selection.pathIds, <String>['cc:JP']);
      expect(selection.displaySnapshot, <String>['日本']);
    },
  );

  test(
    '404 surfaces as notFound and recovers after the origin is fixed',
    () async {
      final origin = _RemoteOrigin();
      await origin.start();
      origin.missing.add('regions/KR.json');
      final source = GeoRepositoryDataSource(
        _repository(origin),
        defaultLocale: 'en',
      );
      addTearDown(origin.stop);

      await expectLater(
        source.openCountry('KR', 'zh-Hans'),
        throwsA(
          isA<GeoNotFoundError>().having(
            (error) => error.errorCode,
            'errorCode',
            'notFound',
          ),
        ),
      );

      origin.missing.clear();
      final content = await source.openCountry('KR', 'zh-Hans');
      expect(content.root.nodeId, 'cc:KR');
      expect(content.children.first.nodeId, 'iso3166-2:KR-11');
    },
  );

  test(
    'corrupted download fails verification and never reaches the cache',
    () async {
      final origin = _RemoteOrigin();
      await origin.start();
      origin.corrupt.add('regions/KR.json');
      final store = GeoMemoryCacheStore();
      final source = GeoRepositoryDataSource(
        _repository(origin, store: store),
        defaultLocale: 'en',
      );
      addTearDown(origin.stop);

      await expectLater(
        source.openCountry('KR', 'zh-Hans'),
        throwsA(
          isA<GeoIntegrityMismatchError>().having(
            (error) => error.errorCode,
            'errorCode',
            'integrityMismatch',
          ),
        ),
      );
      expect(store.writeLog, isEmpty, reason: 'AT-08: bad bytes never cache');

      // After the origin is fixed the same identity loads and caches cleanly.
      origin.corrupt.clear();
      final content = await source.openCountry('KR', 'zh-Hans');
      expect(content.root.nodeId, 'cc:KR');
      expect(store.writeLog, isNotEmpty);
    },
  );

  test('losing the server is a network failure; recovery restores', () async {
    final origin = _RemoteOrigin();
    await origin.start();
    final source = GeoRepositoryDataSource(
      _repository(origin),
      defaultLocale: 'en',
    );
    addTearDown(origin.stop);

    final jp = await source.openCountry('JP', 'zh-Hans');
    expect(jp.root.nodeId, 'cc:JP');

    // Already-verified structures keep resolving after the origin dies
    // (stale coherent, UX-05 at the repository level).
    await origin.stop();
    final deeper = await source.loadChildren(
      'JP',
      'iso3166-2:JP-13',
      'zh-Hans',
    );
    expect(deeper, isEmpty, reason: 'JP provinces list no children');

    // A never-loaded country now fails as a network error.
    await expectLater(
      source.openCountry('KR', 'zh-Hans'),
      throwsA(
        isA<GeoNetworkError>().having(
          (error) => error.errorCode,
          'errorCode',
          'network',
        ),
      ),
    );

    // The origin returns on the same port and the load recovers.
    await origin.start();
    final kr = await source.openCountry('KR', 'zh-Hans');
    expect(kr.root.nodeId, 'cc:KR');
  });
}
