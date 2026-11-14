// SPDX-License-Identifier: BSD-3-Clause
/// Immutable value models for the six protocol resources plus name
/// resolution results. All constructors are non-mutating; collection fields
/// are treated as read-only (parsers hand out unmodifiable views).
library;

import 'dart:convert';

/// `childrenStatus` enum from PROTOCOL.md §4.
///
/// `complete` means completeness within the declared coverage, not proof that
/// no finer real-world geography exists. An empty `unknown` node is not a
/// verified administrative leaf.
enum GeoChildrenStatus {
  /// All in-scope children are present.
  complete,

  /// Some in-scope children are present.
  partial,

  /// Whether children exist outside this snapshot is unknown.
  unknown;

  /// Parses the protocol spelling; returns `null` for anything else.
  static GeoChildrenStatus? tryParseName(String name) => switch (name) {
    'complete' => GeoChildrenStatus.complete,
    'partial' => GeoChildrenStatus.partial,
    'unknown' => GeoChildrenStatus.unknown,
    _ => null,
  };
}

/// Manifest resource kinds (PROTOCOL.md §2).
enum GeoResourceKind {
  /// `data/countries.json`.
  countries,

  /// `data/regions/{CC}.json`.
  structure,

  /// `data/i18n/{locale}/{CC}.json`.
  locale,

  /// `data/catalog_i18n/{locale}.json`.
  countryNames;

  /// The wire spelling used in manifests.
  String get wireName => switch (this) {
    GeoResourceKind.countries => 'countries',
    GeoResourceKind.structure => 'structure',
    GeoResourceKind.locale => 'locale',
    GeoResourceKind.countryNames => 'country-names',
  };

  /// Parses the manifest spelling; returns `null` for anything else.
  static GeoResourceKind? tryParseName(String name) => switch (name) {
    'countries' => GeoResourceKind.countries,
    'structure' => GeoResourceKind.structure,
    'locale' => GeoResourceKind.locale,
    'country-names' => GeoResourceKind.countryNames,
    _ => null,
  };
}

/// One node of a country structure (PROTOCOL.md §4).
///
/// [id] is a dataset-scoped opaque stable string; never parse labels out of
/// it. Equality is identity within a dataset: two nodes are equal when their
/// IDs are equal.
class GeoRegionNode {
  /// Creates an immutable region node.
  const GeoRegionNode({
    required this.id,
    required this.parentId,
    required this.kind,
    required this.name,
    required this.childrenStatus,
    this.code,
    this.nameLocale,
    this.nameQuality,
    this.nativeLocale,
    this.aliases = const <String>[],
  });

  /// Dataset-scoped opaque stable identifier, e.g. `iso3166-2:JP-13`.
  final String id;

  /// Parent ID; `null` only for the country root `cc:{CC}`.
  final String? parentId;

  /// Upstream node type (`country`, `subdivision`, statistical kinds...).
  final String kind;

  /// Optional source administrative or statistical code.
  final String? code;

  /// Source default display value; not necessarily native or reviewed.
  final String name;

  /// Explicitly known locale of the default name, when stated.
  final String? nameLocale;

  /// Source quality of the default name, when stated.
  final String? nameQuality;

  /// Locale of a source-evidenced native name.
  final String? nativeLocale;

  /// Explicit search aliases; never an implicit ID migration.
  final List<String> aliases;

  /// Declared child coverage within this snapshot.
  final GeoChildrenStatus childrenStatus;

  /// Whether this node is a country root (`parentId == null`).
  bool get isCountryRoot => parentId == null;

  @override
  bool operator ==(Object other) => other is GeoRegionNode && other.id == id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() => 'GeoRegionNode($id)';
}

/// A parsed `regions/{CC}.json` structure resource.
class GeoRegionStructure {
  /// Creates an immutable structure; [nodes] must be treated as read-only.
  const GeoRegionStructure({
    required this.protocolVersion,
    required this.datasetId,
    required this.countryCode,
    required this.revision,
    required this.nodes,
  });

  /// Protocol version; exactly `1.0` for this baseline.
  final String protocolVersion;

  /// Namespace of the dataset, e.g. `geo-regions-seed`.
  final String datasetId;

  /// ISO 3166-1 alpha-2 country code.
  final String countryCode;

  /// Content-derived structure revision `s-…`.
  final String revision;

  /// All nodes of the country in document order; first-free ordering.
  final List<GeoRegionNode> nodes;

  /// Number of nodes in this structure.
  int get nodeCount => nodes.length;

  @override
  String toString() =>
      'GeoRegionStructure($countryCode, $revision, $nodeCount nodes)';
}

/// One entry of `countries.json`.
class GeoCountryEntry {
  /// Creates an immutable catalog entry.
  const GeoCountryEntry({
    required this.code,
    required this.name,
    required this.rootId,
  });

  /// ISO 3166-1 alpha-2 code, e.g. `CN`.
  final String code;

  /// Source default display name.
  final String name;

  /// Structure root ID, always `cc:{code}`.
  final String rootId;

  @override
  bool operator ==(Object other) =>
      other is GeoCountryEntry &&
      other.code == code &&
      other.name == name &&
      other.rootId == rootId;

  @override
  int get hashCode => Object.hash(code, name, rootId);

  @override
  String toString() => 'GeoCountryEntry($code)';
}

/// A parsed `countries.json` catalog resource.
class GeoCountryCatalog {
  /// Creates an immutable catalog; [countries] is read-only.
  const GeoCountryCatalog({
    required this.protocolVersion,
    required this.datasetId,
    required this.revision,
    required this.countries,
  });

  /// Protocol version; exactly `1.0` for this baseline.
  final String protocolVersion;

  /// Namespace of the dataset.
  final String datasetId;

  /// Content-derived catalog revision `c-…`.
  final String revision;

  /// Catalog entries.
  final List<GeoCountryEntry> countries;

  /// Looks up an entry by country code; `null` when absent.
  GeoCountryEntry? entryFor(String code) {
    for (final entry in countries) {
      if (entry.code == code) {
        return entry;
      }
    }
    return null;
  }

  @override
  String toString() =>
      'GeoCountryCatalog($datasetId, $revision, ${countries.length} countries)';
}

/// A parsed `i18n/{locale}/{CC}.json` region locale pack.
class GeoLocalePack {
  /// Creates an immutable locale pack; maps are read-only.
  const GeoLocalePack({
    required this.protocolVersion,
    required this.datasetId,
    required this.countryCode,
    required this.locale,
    required this.compatibleStructureRevision,
    required this.revision,
    required this.names,
    required this.qualityById,
  });

  /// Protocol version; exactly `1.0` for this baseline.
  final String protocolVersion;

  /// Namespace of the dataset.
  final String datasetId;

  /// Country whose structure this pack translates.
  final String countryCode;

  /// Locale tag of the translations.
  final String locale;

  /// Structure revision this pack was generated for; compatibility requires
  /// exact equality.
  final String compatibleStructureRevision;

  /// Content-derived locale revision `l-…`.
  final String revision;

  /// Node ID to translated name.
  final Map<String, String> names;

  /// Node ID to source quality marker; missing means unspecified (rejected
  /// by the production profile).
  final Map<String, String> qualityById;
}

/// A parsed `catalog_i18n/{locale}.json` country-names pack.
class GeoCatalogNames {
  /// Creates an immutable catalog names pack; maps are read-only.
  const GeoCatalogNames({
    required this.protocolVersion,
    required this.datasetId,
    required this.locale,
    required this.compatibleCatalogRevision,
    required this.revision,
    required this.names,
    required this.qualityById,
  });

  /// Protocol version; exactly `1.0` for this baseline.
  final String protocolVersion;

  /// Namespace of the dataset.
  final String datasetId;

  /// Locale tag of the country names.
  final String locale;

  /// Catalog revision this pack was generated for; exact equality required.
  final String compatibleCatalogRevision;

  /// Content-derived locale revision `l-…`.
  final String revision;

  /// Country code to localized country name (complete coverage required).
  final Map<String, String> names;

  /// Country code to source quality marker.
  final Map<String, String> qualityById;
}

/// One entry of `manifest.json`'s resource list (PROTOCOL.md §7).
class GeoManifestEntry {
  /// Creates an immutable manifest entry.
  const GeoManifestEntry({
    required this.path,
    required this.kind,
    required this.revision,
    required this.sha256,
    required this.bytes,
    this.countryCode,
    this.locale,
    this.compatibleStructureRevision,
    this.compatibleCatalogRevision,
  });

  /// Dataset-root-relative resource path; manifest paths never carry a
  /// leading `data/` prefix.
  final String path;

  /// Resource kind.
  final GeoResourceKind kind;

  /// Content-derived revision of the resource.
  final String revision;

  /// Full 64-hex SHA-256 of the actual file bytes.
  final String sha256;

  /// Byte length of the actual file after content decoding.
  final int bytes;

  /// Country code for `structure`/`locale` resources.
  final String? countryCode;

  /// Locale for `locale`/`country-names` resources.
  final String? locale;

  /// Compatibility link for `locale` resources.
  final String? compatibleStructureRevision;

  /// Compatibility link for `country-names` resources.
  final String? compatibleCatalogRevision;

  @override
  bool operator ==(Object other) =>
      other is GeoManifestEntry &&
      other.path == path &&
      other.kind == kind &&
      other.revision == revision &&
      other.sha256 == sha256 &&
      other.bytes == bytes &&
      other.countryCode == countryCode &&
      other.locale == locale &&
      other.compatibleStructureRevision == compatibleStructureRevision &&
      other.compatibleCatalogRevision == compatibleCatalogRevision;

  @override
  int get hashCode => Object.hash(
    path,
    kind,
    revision,
    sha256,
    bytes,
    countryCode,
    locale,
    compatibleStructureRevision,
    compatibleCatalogRevision,
  );

  @override
  String toString() => 'GeoManifestEntry($path)';
}

/// A parsed `manifest.json`.
class GeoManifest {
  /// Creates an immutable manifest; [resources] is read-only and sorted by
  /// path with unique paths (enforced during parsing).
  const GeoManifest({
    required this.protocolVersion,
    required this.datasetId,
    required this.revision,
    required this.resources,
  });

  /// Protocol version; exactly `1.0` for this baseline.
  final String protocolVersion;

  /// Namespace of the dataset.
  final String datasetId;

  /// Content-derived manifest revision `m-…`.
  final String revision;

  /// Resource entries sorted by path.
  final List<GeoManifestEntry> resources;

  /// Looks up an entry by resource path; `null` when absent.
  GeoManifestEntry? entryFor(String path) {
    for (final entry in resources) {
      if (entry.path == path) {
        return entry;
      }
    }
    return null;
  }
}

/// A selection value (PROTOCOL.md §8).
///
/// Equality and [hashCode] deliberately cover the identity fields only
/// (protocolVersion, datasetId, countryCode, dataRevision, pathIds).
/// `displaySnapshot` and `displayLocale` are display conveniences: changing
/// the display language must never change selection identity.
class GeoSelection {
  /// Creates a selection value.
  const GeoSelection({
    required this.protocolVersion,
    required this.datasetId,
    required this.countryCode,
    required this.dataRevision,
    required this.pathIds,
    this.displaySnapshot,
    this.displayLocale,
  });

  /// Protocol version; exactly `1.0` for this baseline.
  final String protocolVersion;

  /// Namespace of the dataset the path IDs belong to.
  final String datasetId;

  /// ISO 3166-1 alpha-2 country code.
  final String countryCode;

  /// Structure revision the path was validated against.
  final String dataRevision;

  /// Root-inclusive ID path starting at `cc:{CC}`; country-only selections
  /// have exactly one element.
  final List<String> pathIds;

  /// Optional display labels parallel to [pathIds].
  final List<String>? displaySnapshot;

  /// Optional locale the snapshot was rendered in.
  final String? displayLocale;

  @override
  bool operator ==(Object other) =>
      other is GeoSelection &&
      other.protocolVersion == protocolVersion &&
      other.datasetId == datasetId &&
      other.countryCode == countryCode &&
      other.dataRevision == dataRevision &&
      _listEquals(other.pathIds, pathIds);

  @override
  int get hashCode => Object.hash(
    protocolVersion,
    datasetId,
    countryCode,
    dataRevision,
    Object.hashAll(pathIds),
  );

  static bool _listEquals(List<String> a, List<String> b) {
    if (a.length != b.length) {
      return false;
    }
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) {
        return false;
      }
    }
    return true;
  }

  /// Serializes to the protocol JSON object shape (schema-conformant).
  Map<String, Object?> toMap() => <String, Object?>{
    'protocolVersion': protocolVersion,
    'datasetId': datasetId,
    'countryCode': countryCode,
    'dataRevision': dataRevision,
    'pathIds': List<String>.of(pathIds),
    if (displaySnapshot != null)
      'displaySnapshot': List<String>.of(displaySnapshot!),
    if (displayLocale != null) 'displayLocale': displayLocale,
  };

  /// Serializes to a JSON string in the protocol shape.
  String toJson() => jsonEncode(toMap());

  @override
  String toString() => 'GeoSelection($countryCode, $pathIds)';
}

/// Where a [ResolvedName] came from.
enum GeoNameSource {
  /// A translation from a locale pack for the requested locale chain.
  translation,

  /// A translation from a locale pack for the host default locale.
  defaultLocaleTranslation,

  /// The node's source default name (quality-gated like translations).
  defaultName,

  /// No acceptable name; the stable ID is the display fallback.
  idFallback,
}

/// Result of name resolution (PROTOCOL.md §5, CONSUMER_CONTRACT §3).
///
/// `text == null` with [isFallback] and [source] == [GeoNameSource.idFallback]
/// means no name passed the quality policy; hosts display the stable ID and
/// state that the name is unavailable instead of inventing one.
class ResolvedName {
  /// Creates a resolution result.
  const ResolvedName({
    required this.nodeId,
    required this.requestedLocale,
    required this.source,
    this.resolvedLocale,
    this.quality,
    this.text,
  });

  /// The node the name was resolved for.
  final String nodeId;

  /// Locale the caller asked for, verbatim.
  final String requestedLocale;

  /// Locale actually served, when a locale-specific value was used.
  final String? resolvedLocale;

  /// Source quality marker of the served value, when known.
  final String? quality;

  /// Whether the served value is a fallback (default locale, default name or
  /// ID). `false` only when the requested locale's own chain matched.
  bool get isFallback => source != GeoNameSource.translation;

  /// Whether the served value carries a tentatively-reviewed quality
  /// (`provisional`/`unconfirmed`). Hosts that opt in to serving these
  /// (AT-14) must label them as tentative in the UI.
  bool get isTentative =>
      quality == 'provisional' || quality == 'unconfirmed';

  /// Display text; `null` only for the ID fallback.
  final String? text;

  /// Which resolution stage produced this value.
  final GeoNameSource source;
}
