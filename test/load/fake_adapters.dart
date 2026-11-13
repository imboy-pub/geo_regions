// SPDX-License-Identifier: BSD-3-Clause
/// Deterministic fake adapters for the loading pipeline tests: a loader with
/// controllable latency and ordering, a verifier with visible calls, and a
/// minimal asset bundle (PRD §11: failure, ordering and concurrency must be
/// reproducible with fakes).
library;

import 'dart:async';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart' show FlutterError;
import 'package:flutter/services.dart' show AssetBundle;
import 'package:geo_regions/geo_regions.dart';

import 'fixture_bytes.dart';

/// Fake [GeoResourceLoader] with a request log and fault injection.
///
/// Handlers map full URIs to payload factories; use [ManualGeoLoader] when a
/// test must control completion order explicitly.
class FakeGeoLoader implements GeoResourceLoader {
  FakeGeoLoader({
    Map<String, Uint8List> payloads = const <String, Uint8List>{},
    Uri? base,
  }) : _base = base,
       handlers = <String, GeoBytes Function(Uri uri)>{
         for (final entry in payloads.entries)
           uriFor(entry.key, base).toString(): (Uri uri) =>
               GeoBytes(entry.value, contentLength: entry.value.length),
       };

  final Uri? _base;
  final Map<String, GeoBytes Function(Uri uri)> handlers;

  /// Every URI ever requested, in order (AT-06 request-log assertions).
  final List<Uri> requests = <Uri>[];

  /// When set, the returned error object is thrown instead of serving.
  Object? Function(Uri uri)? fault;

  int get callCount => requests.length;

  int callsFor(String fragment) =>
      requests.where((uri) => uri.toString().contains(fragment)).length;

  /// Registers or replaces the payload served for a path.
  void serve(String path, Uint8List payload) {
    handlers[uriFor(path, _base).toString()] = (Uri uri) =>
        GeoBytes(payload, contentLength: payload.length);
  }

  @override
  Future<GeoBytes> load(Uri uri) async {
    requests.add(uri);
    final failure = fault?.call(uri);
    if (failure != null) {
      throw failure;
    }
    final handler = handlers[uri.toString()];
    if (handler == null) {
      throw GeoNotFoundError('fake loader: no handler for $uri');
    }
    return handler(uri);
  }
}

/// Manual-completion variant: every load parks in [pending] until a test
/// completes or fails it, giving full control over ordering (AT-07).
class ManualGeoLoader implements GeoResourceLoader {
  final List<Uri> requests = <Uri>[];

  final List<({Uri uri, Completer<GeoBytes> completer})> pending =
      <({Uri uri, Completer<GeoBytes> completer})>[];

  /// When set, the returned error object is thrown instead of parking.
  Object? Function(Uri uri)? fault;

  int callsFor(String fragment) =>
      requests.where((uri) => uri.toString().contains(fragment)).length;

  bool get hasPending => pending.isNotEmpty;

  @override
  Future<GeoBytes> load(Uri uri) async {
    requests.add(uri);
    final failure = fault?.call(uri);
    if (failure != null) {
      throw failure;
    }
    final completer = Completer<GeoBytes>();
    pending.add((uri: uri, completer: completer));
    return completer.future;
  }

  /// Completes the first pending load matching [fragment].
  void completeWhere(String fragment, GeoBytes bytes) {
    final index = pending.indexWhere(
      (entry) => entry.uri.toString().contains(fragment),
    );
    if (index < 0) {
      throw StateError('no pending load matching "$fragment"');
    }
    pending.removeAt(index).completer.complete(bytes);
  }

  /// Fails the first pending load matching [fragment].
  void failWhere(String fragment, Object error) {
    final index = pending.indexWhere(
      (entry) => entry.uri.toString().contains(fragment),
    );
    if (index < 0) {
      throw StateError('no pending load matching "$fragment"');
    }
    pending.removeAt(index).completer.completeError(error);
  }
}

/// Verifier that computes the real digest (deterministic), counts calls and
/// can be forced to reject.
class FakeVerifier implements GeoHashVerifier {
  int calls = 0;

  /// When `true`, the next verify call returns `false` once.
  bool failNext = false;

  @override
  Future<bool> verify(
    GeoBytes bytes,
    String expectedSha256,
    int expectedBytes,
  ) async {
    calls++;
    if (failNext) {
      failNext = false;
      return false;
    }
    return bytes.length == expectedBytes &&
        geoSha256Hex(bytes.bytes) == expectedSha256;
  }
}

/// Minimal in-memory [AssetBundle] for [GeoAssetBundleLoader] tests; missing
/// keys throw the same [FlutterError] the real binding throws. Only [load]
/// is exercised by the loader; every other member is unsupported.
class FakeAssetBundle implements AssetBundle {
  FakeAssetBundle(this.assets);

  final Map<String, ByteData> assets;

  @override
  Future<ByteData> load(String key) async {
    final data = assets[key];
    if (data == null) {
      throw FlutterError('Unable to load asset: "$key".');
    }
    return data;
  }

  @override
  Future<ui.ImmutableBuffer> loadBuffer(String key) {
    throw UnimplementedError('loadBuffer is not used by GeoAssetBundleLoader');
  }

  @override
  Future<String> loadString(String key, {bool cache = true}) {
    throw UnimplementedError('loadString is not used by GeoAssetBundleLoader');
  }

  @override
  Future<T> loadStructuredData<T>(
    String key,
    Future<T> Function(String value) parser,
  ) {
    throw UnimplementedError(
      'loadStructuredData is not used by GeoAssetBundleLoader',
    );
  }

  @override
  Future<T> loadStructuredBinaryData<T>(
    String key,
    FutureOr<T> Function(ByteData data) parser,
  ) {
    throw UnimplementedError(
      'loadStructuredBinaryData is not used by GeoAssetBundleLoader',
    );
  }

  @override
  void clear() {
    throw UnimplementedError('clear is not used by GeoAssetBundleLoader');
  }

  @override
  void evict(String key) {
    throw UnimplementedError('evict is not used by GeoAssetBundleLoader');
  }
}

/// Builds ByteData from bytes for asset fixtures.
ByteData byteDataOf(Uint8List bytes) => ByteData.sublistView(bytes);

/// Two zero delays: lets every microtask continuation of a freshly completed
/// future settle before assertions.
Future<void> pump() async {
  await Future<void>.delayed(Duration.zero);
  await Future<void>.delayed(Duration.zero);
}

/// Builds a repository wired to a fake remote stack over real payloads.
GeoRegionsRepository remoteRepository({
  required GeoResourceLoader loader,
  GeoCacheStore? store,
  GeoHashVerifier? verifier,
  Uri? base,
  GeoManifest? manifest,
}) {
  return GeoRegionsRepository(
    manifest: manifest ?? realManifest,
    store: store,
    remoteLoader: loader,
    remoteBase: base ?? testBase(),
    verifier: verifier,
  );
}

/// Fake loader serving the given real dataset payloads over [testBase()].
FakeGeoLoader servingLoader(Map<String, Uint8List> payloads, {Uri? base}) =>
    FakeGeoLoader(payloads: payloads, base: base ?? testBase());
