// SPDX-License-Identifier: BSD-3-Clause
/// Data plumbing between the picker UI and a geo_regions dataset (P1-07).
///
/// The default UI talks to [GeoRegionDataSource] — a deliberately small
/// interface returning display-ready rows. Hosts can implement it with the
/// bundled [GeoRepositoryDataSource] (backed by `GeoRegionsRepository`) or
/// with a fake for tests and previews; either way the widget never touches
/// the parser or the index directly.
///
/// The repository-backed source keeps the loading discipline of the load
/// layer: opening a country fetches only that country's structure and the
/// locale packs of the requested chain (GR-04/AT-06), search never triggers
/// new fetches, and every name passes the quality gate before display
/// (AT-14: unreviewed names are never shown, the stable ID is).
library;

import '../errors.dart';
import '../index.dart';
import '../models.dart';
import '../names.dart';
import '../search.dart';
import '../selection.dart';
import '../load/repository.dart';

/// How the rows of a country are currently served (badge semantics, DEMO_UX).
enum GeoPickerAvailability {
  /// Resource ships inside the host bundle; usable offline immediately.
  bundled,

  /// Resource was fetched before and is served from cache offline.
  cached,

  /// Resource must be fetched remotely; offline fails until cached.
  remote,

  /// Not known yet (e.g. country rows built without loading data).
  unknown,
}

/// What the picker may confirm (PROTOCOL.md §8 plus host depth policy).
enum GeoSelectionPolicy {
  /// Only the country root is confirmable; intermediate nodes cannot even
  /// be entered.
  countryOnly,

  /// Any node with known coverage is confirmable; an `unknown` empty node
  /// never impersonates a leaf (`requireKnownCoverage` semantics).
  allowIntermediate,

  /// Only declared leaves (complete coverage, no listed children) are
  /// confirmable. Country roots stay confirmable: PROTOCOL §8 declares
  /// country-only selections valid.
  requireLeafWithinDeclared,
}

/// Resolved display label plus the honesty flags the picker may render.
///
/// Hosts that opt in to provisional names (AT-14) need more than the text:
/// [isProvisional] marks tentatively-reviewed values and [isFallback] marks
/// values served outside the requested locale's own chain.
class GeoPickerLabelInfo {
  /// Creates label info.
  const GeoPickerLabelInfo({
    required this.text,
    this.isFallback = false,
    this.isProvisional = false,
  });

  /// Display text; the stable ID when nothing passed the quality policy.
  final String text;

  /// The value came from a fallback (default locale, default name or ID).
  final bool isFallback;

  /// The value carries `provisional`/`unconfirmed` quality (AT-14).
  final bool isProvisional;
}

/// One display row of the picker.
class GeoPickerItem {
  /// Creates a display row.
  const GeoPickerItem({
    required this.nodeId,
    required this.label,
    this.labelIsFallback = false,
    this.labelIsProvisional = false,
    this.countryCode,
    this.isCountryRoot = false,
    this.childrenStatus = GeoChildrenStatus.unknown,
    this.hasChildren = false,
    this.pathIds = const <String>[],
    this.pathLabels,
    this.availability = GeoPickerAvailability.unknown,
  });

  /// Stable node ID (`cc:XX` for country rows, deeper IDs below).
  final String nodeId;

  /// Display text; for the ID fallback this is the stable ID itself — the
  /// picker never shows an unreviewed name in its place (AT-14).
  final String label;

  /// Whether [label] came from a fallback (default locale, default name or
  /// ID); hosts may style it differently but must not hide it.
  final bool labelIsFallback;

  /// Whether [label] carries `provisional`/`unconfirmed` quality; hosts that
  /// opt in must label tentative names (AT-14).
  final bool labelIsProvisional;

  /// Country code; set for country rows and rows of an opened country.
  final String? countryCode;

  /// Whether this row is a country root.
  final bool isCountryRoot;

  /// Declared coverage of the node's children; [GeoChildrenStatus.unknown]
  /// means the snapshot does not know.
  final GeoChildrenStatus childrenStatus;

  /// Whether the snapshot lists children for this node.
  final bool hasChildren;

  /// Root-inclusive ID path; search hits carry the full path so same-named
  /// nodes stay distinguishable.
  final List<String> pathIds;

  /// Display labels parallel to [pathIds]; search hits carry them so the
  /// picker can rebuild the draft without extra loads.
  final List<String>? pathLabels;

  /// Availability badge value; meaningful on country rows.
  final GeoPickerAvailability availability;

  /// Returns a copy with display fields replaced (identity fields — IDs,
  /// coverage, paths — never change; a locale switch must not change what
  /// the draft points at, only how it is spelled, UX-02).
  GeoPickerItem copyWith({
    String? label,
    bool? labelIsFallback,
    bool? labelIsProvisional,
  }) {
    return GeoPickerItem(
      nodeId: nodeId,
      label: label ?? this.label,
      labelIsFallback: labelIsFallback ?? this.labelIsFallback,
      labelIsProvisional: labelIsProvisional ?? this.labelIsProvisional,
      countryCode: countryCode,
      isCountryRoot: isCountryRoot,
      childrenStatus: childrenStatus,
      hasChildren: hasChildren,
      pathIds: pathIds,
      pathLabels: pathLabels,
      availability: availability,
    );
  }
}

/// Root item plus first-level rows of one opened country.
class GeoPickerCountryContent {
  /// Creates the content of an opened country.
  const GeoPickerCountryContent({required this.root, required this.children});

  /// The country root row (`cc:XX`).
  final GeoPickerItem root;

  /// Declared first-level rows below the root.
  final List<GeoPickerItem> children;
}

/// Minimal data interface consumed by the default picker UI.
abstract class GeoRegionDataSource {
  /// Country rows for the picker's standalone first screen.
  Future<List<GeoPickerItem>> loadCountries(String locale);

  /// Opens [countryCode]: its root row and declared children.
  Future<GeoPickerCountryContent> openCountry(
    String countryCode,
    String locale,
  );

  /// Children rows of [nodeId] inside [countryCode] (both already opened).
  Future<List<GeoPickerItem>> loadChildren(
    String countryCode,
    String nodeId,
    String locale,
  );

  /// Search hits over names, aliases and IDs with full disambiguation paths.
  /// Implementations define the scope; the repository-backed source searches
  /// the catalog plus every structure already opened in this session and
  /// never fetches new resources for a search.
  Future<List<GeoPickerItem>> search(String query, String locale);

  /// Builds the draft selection for [pathIds], enforcing [policy]. Throws a
  /// typed [GeoException] on invalid paths or policy violations; the host
  /// submits the returned draft as its own transaction (PROTOCOL §8).
  Future<GeoSelection> resolveSelection(
    List<String> pathIds, {
    required GeoSelectionPolicy policy,
    String? displayLocale,
  });

  /// Display labels for [nodeIds] in [locale]; lets the picker re-render a
  /// kept draft after a language switch without changing its IDs (UX-02).
  /// The value carries the honesty flags alongside the text so a locale
  /// switch cannot leave stale fallback/provisional marks behind (AT-14).
  Future<Map<String, GeoPickerLabelInfo>> resolveLabels(
    List<String> nodeIds,
    String locale,
  );

  /// Availability badge value for [countryCode].
  GeoPickerAvailability availabilityOf(String countryCode);
}

/// [GeoRegionDataSource] over a [GeoRegionsRepository].
///
/// Names resolve through [GeoNameResolver] with the project locale chain and
/// quality policy; a pack that the active manifest does not declare (e.g. a
/// locale missing from a hybrid bundle) is remembered as missing instead of
/// being re-requested on every row build.
class GeoRepositoryDataSource implements GeoRegionDataSource {
  /// Upper bound of node search hits per query.
  static const int _searchLimit = 50;

  /// Creates a source over [repository].
  ///
  /// [defaultLocale] is the host fallback locale for name resolution;
  /// [optInProvisional] must stay `false` unless the host labels tentative
  /// names (AT-14). [bundledCountries] declares which countries the host
  /// bundled offline (drives the availability badge; the integrity chain
  /// itself is the repository's job).
  GeoRepositoryDataSource(
    this.repository, {
    this.defaultLocale,
    this.optInProvisional = false,
    Set<String> bundledCountries = const <String>{},
  }) : _bundled = Set<String>.of(bundledCountries);

  /// The repository this source reads from.
  final GeoRegionsRepository repository;

  /// Host default locale for name resolution.
  final String? defaultLocale;

  /// Whether provisional/unconfirmed names may be served (must be labeled).
  final bool optInProvisional;

  final Set<String> _bundled;
  final Set<String> _loadedCountries = <String>{};
  final Set<String> _missingPacks = <String>{};
  final Set<String> _missingCatalogLocales = <String>{};

  @override
  GeoPickerAvailability availabilityOf(String countryCode) {
    if (_bundled.contains(countryCode)) {
      return GeoPickerAvailability.bundled;
    }
    if (_loadedCountries.contains(countryCode)) {
      return GeoPickerAvailability.cached;
    }
    return GeoPickerAvailability.remote;
  }

  @override
  Future<List<GeoPickerItem>> loadCountries(String locale) async {
    final catalog = await repository.loadCatalog();
    await _ensureCatalogNames(locale);
    final resolver = repository.resolverFor(
      '__catalog__',
      defaultLocale: defaultLocale,
      optInProvisional: optInProvisional,
    );
    final items = <GeoPickerItem>[];
    for (final entry in catalog.countries) {
      final resolved = resolver.resolveCatalogName(entry, locale);
      items.add(
        GeoPickerItem(
          nodeId: entry.rootId,
          label: resolved.text ?? entry.code,
          labelIsFallback: resolved.isFallback,
          labelIsProvisional: resolved.isTentative,
          countryCode: entry.code,
          isCountryRoot: true,
          hasChildren: true,
          pathIds: <String>[entry.rootId],
          availability: availabilityOf(entry.code),
        ),
      );
    }
    return items;
  }

  @override
  Future<GeoPickerCountryContent> openCountry(
    String countryCode,
    String locale,
  ) async {
    final children = await loadChildren(countryCode, 'cc:$countryCode', locale);
    final resolver = _resolverOf(countryCode);
    final root = repository.index!.requireNode('cc:$countryCode');
    return GeoPickerCountryContent(
      root: _nodeItem(root, resolver, locale, countryCode),
      children: children,
    );
  }

  @override
  Future<List<GeoPickerItem>> loadChildren(
    String countryCode,
    String nodeId,
    String locale,
  ) async {
    final structure = await repository.loadStructure(countryCode);
    await _ensurePacks(countryCode, locale);
    _loadedCountries.add(structure.countryCode);
    final resolver = _resolverOf(countryCode);
    return <GeoPickerItem>[
      for (final node in repository.index!.children(nodeId))
        _nodeItem(node, resolver, locale, countryCode),
    ];
  }

  @override
  Future<List<GeoPickerItem>> search(String query, String locale) async {
    final index = repository.index;
    if (index == null) {
      return const <GeoPickerItem>[];
    }
    final results = <GeoPickerItem>[];
    final catalogHits = await _catalogSearchHits(index, query, locale);
    results.addAll(catalogHits);
    for (final hit in geoSearch(index, query, limit: _searchLimit)) {
      results.add(_searchItem(index, hit, locale));
    }
    return results;
  }

  @override
  Future<GeoSelection> resolveSelection(
    List<String> pathIds, {
    required GeoSelectionPolicy policy,
    String? displayLocale,
  }) async {
    if (pathIds.isEmpty) {
      throw const GeoParseFailureError('selection path is empty');
    }
    if (policy == GeoSelectionPolicy.countryOnly && pathIds.length != 1) {
      throw GeoParseFailureError(
        'policy countryOnly allows single-element paths, got ${pathIds.length}',
      );
    }
    if (pathIds.length > 1) {
      _enforceDepthPolicy(pathIds.last, policy);
    }
    final index = repository.index!;
    final labels = await _displaySnapshot(index, pathIds, displayLocale);
    return buildGeoSelection(
      index,
      pathIds.last,
      displaySnapshot: labels,
      displayLocale: displayLocale,
    );
  }

  /// `requireKnownCoverage` semantics: unknown coverage and non-leaves are
  /// rejected for the strict policies (AT-11: unknown is never an endpoint).
  void _enforceDepthPolicy(String targetId, GeoSelectionPolicy policy) {
    final index = repository.index!;
    index.requireKnownCoverage(targetId);
    if (policy == GeoSelectionPolicy.requireLeafWithinDeclared) {
      if (index.coverageStatus(targetId) != GeoChildrenStatus.complete ||
          index.hasDeclaredChildren(targetId)) {
        throw GeoParseFailureError(
          'policy requireLeafWithinDeclared: $targetId is not a declared leaf',
        );
      }
    }
  }

  @override
  Future<Map<String, GeoPickerLabelInfo>> resolveLabels(
    List<String> nodeIds,
    String locale,
  ) async {
    if (nodeIds.isEmpty) {
      return const <String, GeoPickerLabelInfo>{};
    }
    final countryCode = nodeIds.first.substring(3);
    await repository.loadStructure(countryCode);
    await _ensurePacks(countryCode, locale);
    final resolver = _resolverOf(countryCode);
    final index = repository.index!;
    return <String, GeoPickerLabelInfo>{
      for (final id in nodeIds)
        id: _labelInfo(resolver.resolve(index.requireNode(id), locale), id),
    };
  }

  GeoPickerLabelInfo _labelInfo(ResolvedName resolved, String nodeId) {
    return GeoPickerLabelInfo(
      text: resolved.text ?? nodeId,
      isFallback: resolved.isFallback,
      isProvisional: resolved.isTentative,
    );
  }

  Future<List<String>> _displaySnapshot(
    GeoRegionIndex index,
    List<String> pathIds,
    String? displayLocale,
  ) async {
    if (displayLocale == null) {
      return const <String>[];
    }
    final countryCode = pathIds.first.substring(3);
    await _ensurePacks(countryCode, displayLocale);
    final resolver = _resolverOf(countryCode);
    return <String>[
      for (final id in pathIds)
        resolver.resolve(index.requireNode(id), displayLocale).text ?? id,
    ];
  }

  GeoNameResolver _resolverOf(String countryCode) => repository.resolverFor(
    countryCode,
    defaultLocale: defaultLocale,
    optInProvisional: optInProvisional,
  );

  GeoPickerItem _nodeItem(
    GeoRegionNode node,
    GeoNameResolver resolver,
    String locale,
    String countryCode,
  ) {
    final resolved = resolver.resolve(node, locale);
    return GeoPickerItem(
      nodeId: node.id,
      label: resolved.text ?? node.id,
      labelIsFallback: resolved.isFallback,
      labelIsProvisional: resolved.isTentative,
      countryCode: countryCode,
      isCountryRoot: node.isCountryRoot,
      childrenStatus: node.childrenStatus,
      hasChildren: repository.index!.hasDeclaredChildren(node.id),
      pathIds: repository.index!.pathToRoot(node.id),
    );
  }

  GeoPickerItem _searchItem(
    GeoRegionIndex index,
    GeoSearchResult hit,
    String locale,
  ) {
    final countryCode = hit.pathIds.first.substring(3);
    final resolver = _resolverOf(countryCode);
    final labels = <String>[
      for (final id in hit.pathIds)
        resolver.resolve(index.requireNode(id), locale).text ?? id,
    ];
    final resolved = resolver.resolve(hit.node, locale);
    return GeoPickerItem(
      nodeId: hit.node.id,
      label: labels.last,
      labelIsFallback: resolved.isFallback,
      labelIsProvisional: resolved.isTentative,
      countryCode: countryCode,
      isCountryRoot: hit.node.isCountryRoot,
      childrenStatus: hit.node.childrenStatus,
      hasChildren: index.hasDeclaredChildren(hit.node.id),
      pathIds: hit.pathIds,
      pathLabels: labels,
    );
  }

  Future<List<GeoPickerItem>> _catalogSearchHits(
    GeoRegionIndex index,
    String query,
    String locale,
  ) async {
    final catalog = repository.catalog;
    if (catalog == null) {
      return const <GeoPickerItem>[];
    }
    await _ensureCatalogNames(locale);
    final resolver = repository.resolverFor(
      '__catalog__',
      defaultLocale: defaultLocale,
      optInProvisional: optInProvisional,
    );
    final needle = query.trim().toLowerCase();
    if (needle.isEmpty) {
      return const <GeoPickerItem>[];
    }
    final hits = <GeoPickerItem>[];
    for (final entry in catalog.countries) {
      final resolved = resolver.resolveCatalogName(entry, locale);
      final text = resolved.text ?? entry.name;
      final hay =
          '${text.toLowerCase()} ${entry.name.toLowerCase()} '
          '${entry.code.toLowerCase()}';
      if (!hay.contains(needle)) {
        continue;
      }
      hits.add(
        GeoPickerItem(
          nodeId: entry.rootId,
          label: text,
          labelIsFallback: resolved.isFallback,
          labelIsProvisional: resolved.isTentative,
          countryCode: entry.code,
          isCountryRoot: true,
          hasChildren: true,
          pathIds: <String>[entry.rootId],
        ),
      );
    }
    return hits;
  }

  /// Loads every declared pack of the requested locale chain; packs the
  /// manifest does not declare are remembered, not re-requested (GR-04).
  Future<void> _ensurePacks(String countryCode, String locale) async {
    for (final candidate in geoLocaleCandidates(locale)) {
      if (repository.packFor(countryCode, candidate) != null) {
        return;
      }
      final key = '$countryCode/$candidate';
      if (_missingPacks.contains(key)) {
        continue;
      }
      try {
        await repository.loadLocalePack(countryCode, candidate);
        return;
      } on GeoNotFoundError {
        _missingPacks.add(key);
      }
    }
    if (defaultLocale != null) {
      await _ensurePacks(countryCode, defaultLocale!);
    }
  }

  Future<void> _ensureCatalogNames(String locale) async {
    for (final candidate in geoLocaleCandidates(locale)) {
      if (repository.catalogNamesFor(candidate) != null) {
        return;
      }
      if (_missingCatalogLocales.contains(candidate)) {
        continue;
      }
      try {
        await repository.loadCatalogNames(candidate);
        return;
      } on GeoNotFoundError {
        _missingCatalogLocales.add(candidate);
      }
    }
    if (defaultLocale != null) {
      await _ensureCatalogNames(defaultLocale!);
    }
  }
}
