// SPDX-License-Identifier: BSD-3-Clause
/// Injected host contracts for loading, caching and integrity (P1-05).
///
/// The runtime SDK depends only on the Flutter/Dart SDK (PRD GR-12), so
/// transport, persistence and remote hashing are host-supplied adapters
/// shaped exactly like CONSUMER_CONTRACT.md §5:
///
/// * [GeoResourceLoader] fetches bytes from a bundle, a CDN or a mirror.
/// * [GeoCacheStore] persists verified public resources between sessions.
/// * [GeoHashVerifier] proves remote bytes against the manifest identity.
/// * [GeoCacheKey] binds every cached payload to its full protocol identity
///   (datasetId / kind / country / locale / revision / sha256), so stale
///   releases can never impersonate the active set (PRD §8).
///
/// All interfaces are async on purpose: hosts may back them with files,
/// SharedPreferences, HTTP, IndexedDB or anything else. Implementations must
/// never block the UI thread.
library;

import 'dart:typed_data';

import '../errors.dart';
import '../models.dart';

/// Bytes of one protocol resource after Content-Encoding decoding.
///
/// [bytes] is the exact entity payload the integrity checks apply to; wire
/// compression is invisible here (PROTOCOL.md §7). [contentLength] is the
/// transport-reported decoded entity length when the loader knows it, or
/// `null`; it must never be the compressed wire length.
///
/// Callers hand ownership to the receiver and must not mutate the list
/// afterwards.
class GeoBytes {
  /// Creates a payload; [contentLength] is optional transport metadata.
  const GeoBytes(this.bytes, {this.contentLength});

  /// The decoded resource bytes.
  final Uint8List bytes;

  /// Transport-reported decoded length, when known.
  final int? contentLength;

  /// Number of bytes in [bytes].
  int get length => bytes.length;

  @override
  String toString() =>
      'GeoBytes(${bytes.length} bytes${contentLength == null ? '' : ', contentLength $contentLength'})';
}

/// Fetches raw resource bytes. Network/asset/custom mirror adapters.
abstract class GeoResourceLoader {
  /// Loads the resource identified by [resourceUri] and returns the decoded
  /// bytes.
  ///
  /// Distinct failure conditions must surface as distinct typed errors
  /// ([GeoNetworkError] for transport failures, [GeoNotFoundError] for
  /// missing resources); loaders never collapse failures into empty bytes.
  Future<GeoBytes> load(Uri resourceUri);
}

/// Persistent cache for verified public resources.
///
/// Keys already carry the full protocol identity, so a stale release can
/// never answer for the active manifest (PRD §8: "旧缓存不能冒充命中").
/// Implementations are responsible for atomic durable writes (crash between
/// write and rename must never leave a truncated payload readable under a
/// key), per CONSUMER_CONTRACT §5.
abstract class GeoCacheStore {
  /// Returns the cached bytes for [key], or `null` on a miss.
  Future<GeoBytes?> read(GeoCacheKey key);

  /// Persists [bytes] under [key], atomically replacing any previous value.
  Future<void> write(GeoCacheKey key, GeoBytes bytes);

  /// Removes [key]; a no-op when absent.
  Future<void> invalidate(GeoCacheKey key);

  /// Every key currently held; used for eviction and quota accounting.
  Future<List<GeoCacheKey>> keys();

  /// Total cached payload size in bytes (quota accounting, PRD §8).
  Future<int> totalSize();

  /// Drops every entry (quota enforcement or cache reset).
  Future<void> clear();
}

/// Proves remote bytes against the manifest identity.
///
/// Strict remote mode requires an injected verifier (AT-09): the SDK refuses
/// to construct a repository with a remote loader but no verifier, and never
/// silently skips verification. PRD §8 keeps cryptographic hashing behind
/// this injected interface instead of growing in-tree crypto.
abstract class GeoHashVerifier {
  /// Returns `true` only when [bytes] has exactly [expectedBytes] length and
  /// the SHA-256 digest [expectedSha256].
  Future<bool> verify(GeoBytes bytes, String expectedSha256, int expectedBytes);
}

/// Full protocol identity of one cached resource.
///
/// Equality covers every field: two keys are equal only when dataset, kind,
/// country, locale, revision and sha256 all agree, which is what makes
/// version-set isolation work (different revisions never collide, AT-08/10).
class GeoCacheKey {
  /// Creates a cache key.
  const GeoCacheKey({
    required this.datasetId,
    required this.kind,
    this.countryCode,
    this.locale,
    required this.revision,
    required this.sha256,
  });

  /// Builds the key for a manifest entry under [datasetId].
  factory GeoCacheKey.fromManifestEntry(
    String datasetId,
    GeoManifestEntry entry,
  ) => GeoCacheKey(
    datasetId: datasetId,
    kind: entry.kind,
    countryCode: entry.countryCode,
    locale: entry.locale,
    revision: entry.revision,
    sha256: entry.sha256,
  );

  /// Dataset namespace the resource belongs to.
  final String datasetId;

  /// Protocol resource kind.
  final GeoResourceKind kind;

  /// Country code for `structure`/`locale` resources.
  final String? countryCode;

  /// Locale tag for `locale`/`country-names` resources.
  final String? locale;

  /// Content-derived revision of the resource.
  final String revision;

  /// SHA-256 hex digest of the exact resource bytes.
  final String sha256;

  /// Stable string form for disk-backed stores and diagnostics.
  String toStorageKey() => <String>[
    'geo_regions',
    datasetId,
    kind.wireName,
    countryCode ?? '-',
    locale ?? '-',
    revision,
    sha256,
  ].join('/');

  @override
  bool operator ==(Object other) =>
      other is GeoCacheKey &&
      other.datasetId == datasetId &&
      other.kind == kind &&
      other.countryCode == countryCode &&
      other.locale == locale &&
      other.revision == revision &&
      other.sha256 == sha256;

  @override
  int get hashCode =>
      Object.hash(datasetId, kind, countryCode, locale, revision, sha256);

  @override
  String toString() => 'GeoCacheKey(${toStorageKey()})';
}
