// SPDX-License-Identifier: BSD-3-Clause
/// Locale aliasing, RFC 4647-style fallback and quality-gated name
/// resolution (PROTOCOL.md §5, CONSUMER_CONTRACT §3–§4).
///
/// Resolution order (PRD §9): normalized request and explicit aliases →
/// RFC 4647-style lookup → host default locale → node source default name
/// (quality-gated) → stable ID. Missing translations stay missing; an empty
/// string never counts as a translation. The default name `node.name` passes
/// through the SAME quality filter as translations — filtering a provisional
/// translation and then serving the equally-provisional default name would
/// be a policy bypass and is forbidden.
library;

import 'errors.dart';
import 'models.dart';

/// Explicit project-level locale alias table (CONSUMER_CONTRACT §3).
///
/// Script aliases are configured, never inferred by truncation: `zh` never
/// silently resolves to `zh-Hans`, and `zh-Hans`/`zh-Hant` never mix.
const Map<String, String> kGeoLocaleAliases = <String, String>{
  'zh-CN': 'zh-Hans',
  'zh-Hant': 'zh-Hant',
  'en-US': 'en',
  'ja-JP': 'ja',
  'ko-KR': 'ko',
  'ru-RU': 'ru',
  'de-DE': 'de',
  'fr-FR': 'fr',
  'it-IT': 'it',
  'ar-SA': 'ar',
};

/// Quality values accepted by the default production profile.
const Set<String> kGeoAcceptedNameQualities = <String>{
  'approved-in-source',
  'contributed',
  'cldr-json-qualified',
  'source-native',
};

/// Quality values rejected unless the host explicitly opts in.
const Set<String> kGeoProvisionalNameQualities = <String>{
  'provisional',
  'unconfirmed',
};

/// Builds the ordered locale candidate chain for [requested].
///
/// The chain starts with the request verbatim, then its explicit alias (if
/// any), then RFC 4647-style truncations of each seed — with one project
/// restriction: truncation never removes a script subtag, so `zh-Hans`
/// never degrades to `zh` and `zh` never expands to `zh-Hans`.
List<String> geoLocaleCandidates(String requested) {
  final chain = <String>[];
  void add(String tag) {
    if (tag.isNotEmpty && !chain.contains(tag)) {
      chain.add(tag);
    }
  }

  add(requested);
  final alias = kGeoLocaleAliases[requested];
  if (alias != null) {
    add(alias);
  }
  for (final seed in List<String>.of(chain)) {
    var parts = seed.split('-');
    while (parts.length > 1) {
      if (_isScriptSubtag(parts.last)) {
        break;
      }
      parts = parts.sublist(0, parts.length - 1);
      add(parts.join('-'));
    }
  }
  return chain;
}

bool _isScriptSubtag(String subtag) =>
    subtag.length == 4 &&
    subtag.codeUnits.every(
      (unit) =>
          (unit >= 0x41 && unit <= 0x5a) || (unit >= 0x61 && unit <= 0x7a),
    );

/// Whether [quality] passes the production profile.
///
/// Unknown, missing and machine-candidate markers fail closed. When
/// [optInProvisional] is set, `provisional` and `unconfirmed` become
/// eligible; hosts must then label the displayed name as tentative.
bool geoIsQualityAccepted(String? quality, {bool optInProvisional = false}) {
  if (quality == null) {
    return false;
  }
  if (kGeoAcceptedNameQualities.contains(quality)) {
    return true;
  }
  return optInProvisional && kGeoProvisionalNameQualities.contains(quality);
}

/// Resolves display names for one country's nodes.
///
/// [packs] maps locale tag → locale pack for a single country; mixing packs
/// of different countries or structures is a host configuration error. The
/// packs' `compatibleStructureRevision` must already have been validated
/// against the structure during parsing ([parseLocalePack]).
class GeoNameResolver {
  /// Creates a resolver.
  ///
  /// [defaultLocale] is the host's fallback UI locale applied after the
  /// requested locale's own chain is exhausted.
  GeoNameResolver({
    Map<String, GeoLocalePack> packs = const <String, GeoLocalePack>{},
    this.defaultLocale,
    this.optInProvisional = false,
    this.catalogPacks = const <String, GeoCatalogNames>{},
  }) : _packs = packs {
    final countries = packs.values.map((pack) => pack.countryCode).toSet();
    if (countries.length > 1) {
      throw ArgumentError('a name resolver serves one country, got $countries');
    }
    final structures = packs.values
        .map((pack) => pack.compatibleStructureRevision)
        .toSet();
    if (structures.length > 1) {
      throw GeoIntegrityMismatchError(
        'locale packs target different structure revisions: $structures',
      );
    }
  }

  final Map<String, GeoLocalePack> _packs;

  /// Host default locale consulted after the requested chain.
  final String? defaultLocale;

  /// Whether provisional/unconfirmed names may be served (must be labeled).
  final bool optInProvisional;

  /// Optional catalog-name packs for [resolveCatalogName].
  final Map<String, GeoCatalogNames> catalogPacks;

  /// Resolves the display name of [node] for [requestedLocale].
  ResolvedName resolve(GeoRegionNode node, String requestedLocale) {
    for (final candidate in geoLocaleCandidates(requestedLocale)) {
      final resolved = _fromPacks(
        node,
        candidate,
        requestedLocale,
        GeoNameSource.translation,
      );
      if (resolved != null) {
        return resolved;
      }
    }
    if (defaultLocale != null && defaultLocale != requestedLocale) {
      for (final candidate in geoLocaleCandidates(defaultLocale!)) {
        final resolved = _fromPacks(
          node,
          candidate,
          requestedLocale,
          GeoNameSource.defaultLocaleTranslation,
        );
        if (resolved != null) {
          return resolved;
        }
      }
    }
    if (geoIsQualityAccepted(
      node.nameQuality,
      optInProvisional: optInProvisional,
    )) {
      return ResolvedName(
        nodeId: node.id,
        requestedLocale: requestedLocale,
        resolvedLocale: node.nameLocale,
        quality: node.nameQuality,
        text: node.name,
        source: GeoNameSource.defaultName,
      );
    }
    return ResolvedName(
      nodeId: node.id,
      requestedLocale: requestedLocale,
      source: GeoNameSource.idFallback,
    );
  }

  ResolvedName? _fromPacks(
    GeoRegionNode node,
    String candidate,
    String requestedLocale,
    GeoNameSource source,
  ) {
    final pack = _lookupPack(candidate);
    if (pack == null) {
      return null;
    }
    final text = pack.names[node.id];
    if (text == null || text.isEmpty) {
      return null;
    }
    final quality = pack.qualityById[node.id];
    if (!geoIsQualityAccepted(quality, optInProvisional: optInProvisional)) {
      return null;
    }
    return ResolvedName(
      nodeId: node.id,
      requestedLocale: requestedLocale,
      resolvedLocale: pack.locale,
      quality: quality,
      text: text,
      source: source,
    );
  }

  GeoLocalePack? _lookupPack(String locale) {
    final exact = _packs[locale];
    if (exact != null) {
      return exact;
    }
    for (final entry in _packs.entries) {
      if (entry.key.toLowerCase() == locale.toLowerCase()) {
        return entry.value;
      }
    }
    return null;
  }

  /// Resolves a country list entry's name for [requestedLocale].
  ///
  /// Catalog packs are consulted through the same candidate chain and
  /// quality policy. The catalog's source-default `entry.name` carries no
  /// quality metadata, so it is only served as a labeled fallback, mirroring
  /// `countries.json`, which publishes no per-name quality markers.
  ResolvedName resolveCatalogName(
    GeoCountryEntry entry,
    String requestedLocale,
  ) {
    final requestedChain = geoLocaleCandidates(requestedLocale);
    final defaultChain =
        (defaultLocale == null || defaultLocale == requestedLocale)
        ? const <String>[]
        : geoLocaleCandidates(defaultLocale!);
    for (var i = 0; i < requestedChain.length + defaultChain.length; i++) {
      final fromRequestedChain = i < requestedChain.length;
      final candidate = fromRequestedChain
          ? requestedChain[i]
          : defaultChain[i - requestedChain.length];
      final pack = _lookupCatalogPack(candidate);
      if (pack == null) {
        continue;
      }
      final text = pack.names[entry.code];
      if (text == null || text.isEmpty) {
        continue;
      }
      final quality = pack.qualityById[entry.code];
      if (!geoIsQualityAccepted(quality, optInProvisional: optInProvisional)) {
        continue;
      }
      return ResolvedName(
        nodeId: entry.rootId,
        requestedLocale: requestedLocale,
        resolvedLocale: pack.locale,
        quality: quality,
        text: text,
        source: fromRequestedChain
            ? GeoNameSource.translation
            : GeoNameSource.defaultLocaleTranslation,
      );
    }
    return ResolvedName(
      nodeId: entry.rootId,
      requestedLocale: requestedLocale,
      resolvedLocale: null,
      quality: null,
      text: entry.name,
      source: GeoNameSource.defaultName,
    );
  }

  GeoCatalogNames? _lookupCatalogPack(String locale) {
    final exact = catalogPacks[locale];
    if (exact != null) {
      return exact;
    }
    for (final entry in catalogPacks.entries) {
      if (entry.key.toLowerCase() == locale.toLowerCase()) {
        return entry.value;
      }
    }
    return null;
  }
}
