// SPDX-License-Identifier: BSD-3-Clause
// geo_regions production SDK — public library entry point.
//
// P1-04 implements the data layer here: models, strict parser, index,
// name resolution with quality policy and locale fallback. Runtime
// dependencies are the Flutter/Dart SDK only (PRD GR-12); networking,
// persistence and hashing are injected interfaces.
//
// Typical usage:
//
// ```dart
// // The host loads bytes (bundled asset, cache or network), verifies the
// // manifest SHA-256 chain, decodes JSON and hands the decoded value over:
// final structure = parseRegionStructure(decoded, expectedDatasetId: 'geo-regions-seed');
// final index = GeoRegionIndex.single(structure);
// final path = index.pathToRoot('iso3166-2:JP-13'); // [cc:JP, iso3166-2:JP-13]
//
// final pack = parseLocalePack(decodedPack, expectedStructure: structure);
// final resolver = GeoNameResolver(packs: {'zh-Hans': pack}, defaultLocale: 'en');
// final name = resolver.resolve(index.requireNode('cc:CN'), 'zh-CN');
//
// final draft = buildGeoSelection(index, 'iso3166-2:JP-13');
// // Host persists the draft as its own transaction (PROTOCOL.md §8):
// // submit to backend, then update the account cache and exit.
// validateGeoSelection(draft, index);
// ```
library geo_regions;

// Typed error taxonomy (CONSUMER_CONTRACT §2).
export 'src/errors.dart';

// Canonical serialization C(x) and content revisions (PROTOCOL.md §6).
export 'src/canonical.dart';
export 'src/revision.dart';
export 'src/sha256.dart';

// Immutable value models for the six protocol resources.
export 'src/models.dart';

// Strict parser and semantic validator aligned with tool/geo_data.py.
export 'src/parser.dart';

// Lookup index with root-inclusive paths and coverage introspection.
export 'src/index.dart';

// Substring search over names, aliases and IDs.
export 'src/search.dart';

// Locale aliasing, RFC 4647-style fallback, quality-gated name resolution.
export 'src/names.dart';

// Selection construction and semantic validation (PROTOCOL.md §8).
export 'src/selection.dart';

/// Protocol version accepted by this SDK build (PROTOCOL.md §3).
const String kGeoRegionsProtocolVersion = '1.0';
