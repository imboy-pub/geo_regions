// SPDX-License-Identifier: BSD-3-Clause
// Demo data layer: wires the production geo_regions SDK to the two asset
// bundles generated before build (see pubspec.yaml regeneration notes).
//
// - `assets/geo_regions/` is the hybrid-CN offline subset (config/
//   assets.hybrid-cn.json): countries catalog, catalog names in ten
//   languages, the CN structure and its zh-Hans/zh-Hant/en packs, plus the
//   subset manifest and the full registry descriptor list.
// - `assets/geo_cdn/` stands in for the CDN: the complete dataset. The demo
//   pretends these bytes arrive over the network; the repository still
//   length-checks and SHA-256-verifies every byte against the pinned
//   manifest before decoding (AT-08/09), so "simulated online" exercises
//   the real integrity chain.
//
// The demo manifest is resolved from the registry descriptor list exactly
// like a host would resolve its release manifest: every resource of the
// pinned release (bundled or not) must be declared, or loading refuses with
// a typed notFound error. No fixture namespace remains (UX-12).
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:geo_regions/geo_regions.dart';

const String kDemoBundledPrefix = 'assets/geo_regions/';
const String kDemoCdnPrefix = 'assets/geo_cdn/';

/// Countries the demo bundles offline (mirrors the hybrid config profile).
const Set<String> kDemoBundledCountries = <String>{'CN'};

/// Simulated latency of the "CDN" so loading skeletons and request races
/// are observable without real sockets.
const Duration kDemoCdnLatency = Duration(milliseconds: 250);

/// Builds a [GeoManifest] from a decoded registry descriptor list (the
/// CLI's `registry.json`): the full release descriptor set, `bundled` flags
/// stripped — a host-resolved manifest, not a parsed subset manifest.
GeoManifest demoManifestFromRegistry(Object? decoded) {
  final map = decoded! as Map<Object?, Object?>;
  return GeoManifest(
    protocolVersion: map['protocolVersion']! as String,
    datasetId: map['datasetId']! as String,
    revision: map['revision']! as String,
    resources: List<GeoManifestEntry>.unmodifiable(<GeoManifestEntry>[
      for (final raw in map['resources']! as List<Object?>)
        _entryFromDescriptor(raw! as Map<Object?, Object?>),
    ]),
  );
}

GeoManifestEntry _entryFromDescriptor(Map<Object?, Object?> raw) {
  return GeoManifestEntry(
    path: raw['path']! as String,
    kind: GeoResourceKind.tryParseName(raw['kind']! as String)!,
    revision: raw['revision']! as String,
    sha256: raw['sha256']! as String,
    bytes: raw['bytes']! as int,
    countryCode: raw['countryCode'] as String?,
    locale: raw['locale'] as String?,
    compatibleStructureRevision: raw['compatibleStructureRevision'] as String?,
    compatibleCatalogRevision: raw['compatibleCatalogRevision'] as String?,
  );
}

Future<GeoManifest> loadDemoManifest() async {
  final text = await rootBundle.loadString(
    '${kDemoBundledPrefix}registry.json',
  );
  return demoManifestFromRegistry(jsonDecode(text));
}

/// The demo's simulated CDN [GeoResourceLoader].
///
/// * Serves manifest-relative paths from [serve] — by default the second
///   asset bundle, but tests may plug in preloaded bytes because the
///   widget-test binding only delivers asset-channel replies during the
///   first test of a process.
/// * [online] models the offline switch: `false` fails with a typed
///   [GeoNetworkError] — the picker shows error + retry, never empty rows.
/// * [failNext] models a one-shot transport failure for the failure button.
/// * [requests] is the request log: the acceptance run asserts that opening
///   a country only requests that country's resources (GR-04/AT-06).
class DemoCdnLoader implements GeoResourceLoader {
  DemoCdnLoader({Future<GeoBytes> Function(String path)? serve})
    : serve =
          serve ??
          ((String path) async {
            final data = await rootBundle.load('$kDemoCdnPrefix$path');
            return GeoBytes(
              Uint8List.fromList(
                data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
              ),
              contentLength: data.lengthInBytes,
            );
          });

  /// Payload provider for one manifest-relative path.
  final Future<GeoBytes> Function(String path) serve;

  bool online = true;
  bool failNext = false;
  final List<String> requests = <String>[];

  @override
  Future<GeoBytes> load(Uri resourceUri) async {
    final path = resourceUri.path;
    requests.add(path);
    if (!online) {
      throw const GeoNetworkError('demo: offline switch is on');
    }
    if (failNext) {
      failNext = false;
      throw const GeoNetworkError('demo: simulated transport failure');
    }
    await Future<void>.delayed(kDemoCdnLatency);
    return serve(path);
  }
}

/// Demo verifier: the SDK ships the SHA-256 implementation, so strict
/// remote mode is exercised with the real digest (AT-09).
class DemoShaVerifier implements GeoHashVerifier {
  const DemoShaVerifier();

  @override
  Future<bool> verify(GeoBytes bytes, String sha256, int expectedBytes) async {
    return bytes.length == expectedBytes && geoSha256Hex(bytes.bytes) == sha256;
  }
}

/// Assembled demo data layer.
class DemoGeoHarness {
  DemoGeoHarness({
    required this.repository,
    required this.source,
    required this.cdn,
  });

  final GeoRegionsRepository repository;
  final GeoRepositoryDataSource source;
  final DemoCdnLoader cdn;

  /// Dataset identity surfaced in the demo header (UX-12: the demo shows
  /// the real namespace, never a fixture one).
  String get datasetId => repository.datasetId;
}

/// Builds the demo harness: registry manifest, bundled subset loader,
/// simulated CDN loader with real verification, and a memory cache so
/// previously loaded countries keep working offline (UX-05).
Future<DemoGeoHarness> buildDemoHarness() async {
  final manifest = await loadDemoManifest();
  final cdn = DemoCdnLoader();
  final repository = GeoRegionsRepository(
    manifest: manifest,
    bundledLoader: GeoAssetBundleLoader(assetPrefix: kDemoBundledPrefix),
    remoteLoader: cdn,
    verifier: const DemoShaVerifier(),
    store: GeoMemoryCacheStore(),
  );
  final source = GeoRepositoryDataSource(
    repository,
    defaultLocale: 'en',
    bundledCountries: kDemoBundledCountries,
  );
  return DemoGeoHarness(repository: repository, source: source, cdn: cdn);
}
