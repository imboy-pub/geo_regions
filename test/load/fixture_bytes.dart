// SPDX-License-Identifier: BSD-3-Clause
/// Real-byte fixtures: the repository's bundled `data/` files are the golden
/// vectors for the loading pipeline (same policy as `test/test_data.dart`).
///
/// `dart:io` is fine here — tests run on the VM; the library under test stays
/// web-compatible and IO-free.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:geo_regions/geo_regions.dart';

/// Lazily-read memoized bytes of a dataset-root-relative data file.
final Map<String, Uint8List> _bytesCache = <String, Uint8List>{};

Uint8List dataBytes(String path) {
  final cached = _bytesCache[path];
  if (cached != null) {
    return cached;
  }
  final raw = Uint8List.fromList(File('data/$path').readAsBytesSync());
  _bytesCache[path] = raw;
  return raw;
}

/// The real published manifest (parsed, revision-verified).
final GeoManifest realManifest = parseManifest(
  jsonDecode(File('data/manifest.json').readAsStringSync()),
);

GeoManifestEntry realEntry(String path) => realManifest.entryFor(path)!;

/// A manifest built directly from entries (no wire round-trip), so tests can
/// pin identities — including deliberately broken ones.
GeoManifest manifestOf(
  List<GeoManifestEntry> entries, {
  String datasetId = 'geo-regions-seed',
}) {
  return GeoManifest(
    protocolVersion: '1.0',
    datasetId: datasetId,
    revision: 'm-test000000000000',
    resources: List.unmodifiable(entries),
  );
}

/// Copy of an entry with selected identity fields overridden.
GeoManifestEntry copyEntry(
  GeoManifestEntry entry, {
  String? revision,
  String? sha256,
  int? bytes,
}) {
  return GeoManifestEntry(
    path: entry.path,
    kind: entry.kind,
    revision: revision ?? entry.revision,
    sha256: sha256 ?? entry.sha256,
    bytes: bytes ?? entry.bytes,
    countryCode: entry.countryCode,
    locale: entry.locale,
    compatibleStructureRevision: entry.compatibleStructureRevision,
    compatibleCatalogRevision: entry.compatibleCatalogRevision,
  );
}

/// Entry whose sha256/bytes describe [payload] exactly (identity the fake
/// verifier will accept).
GeoManifestEntry syntheticEntry({
  required String path,
  required GeoResourceKind kind,
  required Uint8List payload,
  String? countryCode,
  String? locale,
  String? compatibleStructureRevision,
  String? compatibleCatalogRevision,
}) {
  return GeoManifestEntry(
    path: path,
    kind: kind,
    revision: kind == GeoResourceKind.structure
        ? 's-0000000000000000'
        : kind == GeoResourceKind.countries
        ? 'c-0000000000000000'
        : 'l-0000000000000000',
    sha256: geoSha256Hex(payload),
    bytes: payload.length,
    countryCode: countryCode,
    locale: locale,
    compatibleStructureRevision: compatibleStructureRevision,
    compatibleCatalogRevision: compatibleCatalogRevision,
  );
}

/// Same-length corruption: flips the last byte.
Uint8List flipOneByte(Uint8List bytes) {
  final copy = Uint8List.fromList(bytes);
  copy[copy.length - 1] ^= 0x2c;
  return copy;
}

/// Short read: drops the trailing [drop] bytes.
Uint8List shortBytes(Uint8List bytes, [int drop = 16]) =>
    Uint8List.fromList(bytes.sublist(0, bytes.length - drop));

/// Syntactically invalid JSON payload.
Uint8List invalidJsonBytes() =>
    Uint8List.fromList(utf8.encode('{"nodes": [not-json'));

/// The remote base used by loader-facing tests.
Uri testBase() => Uri.parse('https://cdn.example/geo/v1/');

/// URI the repository resolves for a manifest-relative [path].
Uri uriFor(String path, Uri? base) {
  final relative = Uri(path: path);
  return base == null ? relative : base.resolveUri(relative);
}
