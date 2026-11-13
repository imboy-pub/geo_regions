// SPDX-License-Identifier: BSD-3-Clause
/// Data repository orchestrating loading, caching, integrity and concurrency
/// for the active published set (P1-05; PRD §8, CONSUMER_CONTRACT §5).
///
/// The repository owns one immutable published set: a [GeoManifest] plus the
/// parsed resources loaded under it. Sources run cache (identity-keyed) →
/// bundled assets → remote; remote downloads are length- and SHA-256-verified
/// *before* any JSON decoding (AT-08). Generation tokens discard stale
/// commits (AT-07); atomic manifest swaps never mix releases (AT-10). Offline
/// without cache is a [GeoNetworkError] ("unavailable"), never empty children
/// (AT-11).
library;

import 'dart:async';
import 'dart:convert';

import '../errors.dart';
import '../index.dart';
import '../models.dart';
import '../names.dart';
import '../parser.dart';
import '../sha256.dart';
import 'contracts.dart';

/// Dataset-root-relative path of the countries catalog.
const String kGeoCatalogPath = 'countries.json';

/// Resource paths follow PROTOCOL.md §2; manifest entries never carry a
/// leading `data/` segment.
String geoStructurePath(String countryCode) => 'regions/$countryCode.json';

/// Path of a per-country locale pack.
String geoLocalePackPath(String locale, String countryCode) =>
    'i18n/$locale/$countryCode.json';

/// Path of a country-names pack.
String geoCatalogNamesPath(String locale) => 'catalog_i18n/$locale.json';

/// Orchestrates one published geo-regions set: load, cache, verify, parse.
class GeoRegionsRepository {
  /// Creates a repository pinned to [manifest].
  ///
  /// [store] persists verified resources; [bundledLoader] serves assets
  /// (offline first); [remoteLoader] REQUIRES [verifier] — strict remote
  /// mode fails fast otherwise (AT-09). [remoteBase] resolves entry paths
  /// into loader URIs; [datasetId] pins the namespace.
  GeoRegionsRepository({
    required GeoManifest manifest,
    GeoCacheStore? store,
    GeoResourceLoader? bundledLoader,
    GeoResourceLoader? remoteLoader,
    Uri? remoteBase,
    GeoHashVerifier? verifier,
    String? datasetId,
  }) : _store = store,
       _bundledLoader = bundledLoader,
       _remoteLoader = remoteLoader,
       _remoteBase = remoteBase,
       _verifier = verifier,
       _activeManifest = manifest,
       datasetId = datasetId ?? manifest.datasetId {
    if (datasetId != null && datasetId != manifest.datasetId) {
      throw GeoConfigurationError(
        'declared datasetId "$datasetId" does not match manifest dataset "${manifest.datasetId}"',
      );
    }
    if (remoteLoader != null && verifier == null) {
      throw const GeoConfigurationError(
        'strict remote mode requires a GeoHashVerifier: remote bytes must be '
        'length- and SHA-256-verified before any parsing (AT-09)',
      );
    }
  }

  final GeoCacheStore? _store;
  final GeoResourceLoader? _bundledLoader;
  final GeoResourceLoader? _remoteLoader;
  final Uri? _remoteBase;
  final GeoHashVerifier? _verifier;

  /// Dataset namespace every loaded resource must belong to.
  final String datasetId;

  GeoManifest _activeManifest;
  int _generation = 0;
  int _updateEpoch = 0;
  bool _disposed = false;
  bool _stale = false;
  bool _updating = false;
  String? _activeCountry;
  String? _activeLocale;
  GeoCountryCatalog? _catalog;
  GeoRegionIndex? _index;
  final Map<String, GeoRegionStructure> _structures =
      <String, GeoRegionStructure>{};
  final Map<String, Map<String, GeoLocalePack>> _packs =
      <String, Map<String, GeoLocalePack>>{};
  final Map<String, GeoCatalogNames> _catalogNames =
      <String, GeoCatalogNames>{};
  final Map<GeoCacheKey, Future<Object?>> _inflight =
      <GeoCacheKey, Future<Object?>>{};
  final List<void Function()> _listeners = <void Function()>[];

  /// The active published set; replaced only by an atomic [updateTo].
  GeoManifest get manifest => _activeManifest;

  /// Index of every committed structure, `null` before the first one.
  GeoRegionIndex? get index => _index;

  /// Committed countries catalog, `null` before the first load.
  GeoCountryCatalog? get catalog => _catalog;

  /// Country whose structure was last committed by [switchCountry].
  String? get activeCountry => _activeCountry;

  /// Locale last committed by [switchLocale].
  String? get activeLocale => _activeLocale;

  /// Whether the active set predates a failed update (stale coherent, PRD §8).
  bool get isStale => _stale;

  /// Whether [dispose] has run.
  bool get isDisposed => _disposed;

  /// Committed structure for [countryCode], `null` unless loaded (no I/O).
  GeoRegionStructure? structureFor(String countryCode) =>
      _structures[countryCode];

  /// Committed locale pack, `null` unless already loaded. Never triggers I/O.
  GeoLocalePack? packFor(String countryCode, String locale) =>
      _packs[countryCode]?[locale];

  /// Committed country-names pack, `null` unless already loaded.
  GeoCatalogNames? catalogNamesFor(String locale) => _catalogNames[locale];

  /// Builds a name resolver over the committed packs of [countryCode].
  GeoNameResolver resolverFor(
    String countryCode, {
    String? defaultLocale,
    bool optInProvisional = false,
  }) {
    return GeoNameResolver(
      packs: _packs[countryCode] ?? const <String, GeoLocalePack>{},
      defaultLocale: defaultLocale,
      optInProvisional: optInProvisional,
      catalogPacks: _catalogNames,
    );
  }

  /// Registers a change listener; silent after [dispose] (AT-07).
  void addListener(void Function() listener) => _listeners.add(listener);

  /// Removes a previously registered listener.
  void removeListener(void Function() listener) => _listeners.remove(listener);

  /// Loads the countries catalog from cache, assets or remote.
  Future<GeoCountryCatalog> loadCatalog() async {
    _ensureNotDisposed();
    final existing = _catalog;
    if (existing != null) {
      return existing;
    }
    final entry = _requireEntry(kGeoCatalogPath);
    return _ensureResource<GeoCountryCatalog>(entry, (bytes, decoded) async {
      final upd = _updateEpoch;
      final parsed = parseCountryCatalog(decoded, expectedDatasetId: datasetId);
      _crossCheckIdentity(entry, revision: parsed.revision);
      if (upd == _updateEpoch && !_disposed) {
        _catalog = parsed;
      }
      return parsed;
    });
  }

  /// Loads and commits the structure of [countryCode] (AT-06: only this
  /// country's resources are requested).
  Future<GeoRegionStructure> loadStructure(String countryCode) async {
    _ensureNotDisposed();
    final existing = _structures[countryCode];
    if (existing != null) {
      return existing;
    }
    final entry = _requireEntry(
      geoStructurePath(countryCode),
      expectCountry: countryCode,
    );
    return _ensureResource<GeoRegionStructure>(entry, (bytes, decoded) async {
      final upd = _updateEpoch;
      final parsed = parseRegionStructure(
        decoded,
        expectedDatasetId: datasetId,
      );
      _crossCheckIdentity(
        entry,
        revision: parsed.revision,
        countryCode: parsed.countryCode,
      );
      if (upd == _updateEpoch && !_disposed) {
        _structures[parsed.countryCode] = parsed;
        _rebuildIndex();
      }
      return parsed;
    });
  }

  /// Loads the locale pack of [locale] for [countryCode]; the structure is
  /// fetched only when not committed yet (GR-04, AT-06).
  Future<GeoLocalePack> loadLocalePack(
    String countryCode,
    String locale,
  ) async {
    _ensureNotDisposed();
    final existing = _packs[countryCode]?[locale];
    if (existing != null) {
      return existing;
    }
    final structure = await loadStructure(countryCode);
    final entry = _requireEntry(
      geoLocalePackPath(locale, countryCode),
      expectCountry: countryCode,
      expectLocale: locale,
    );
    return _ensureResource<GeoLocalePack>(entry, (bytes, decoded) async {
      final upd = _updateEpoch;
      final parsed = parseLocalePack(
        decoded,
        expectedStructure: structure,
        expectedDatasetId: datasetId,
      );
      _crossCheckIdentity(
        entry,
        revision: parsed.revision,
        countryCode: parsed.countryCode,
        locale: parsed.locale,
      );
      if (upd == _updateEpoch && !_disposed) {
        (_packs[parsed.countryCode] ??=
                <String, GeoLocalePack>{})[parsed.locale] =
            parsed;
      }
      return parsed;
    });
  }

  /// Loads the country-names pack of [locale], binding it to the catalog.
  Future<GeoCatalogNames> loadCatalogNames(String locale) async {
    _ensureNotDisposed();
    final existing = _catalogNames[locale];
    if (existing != null) {
      return existing;
    }
    final entry = _requireEntry(
      geoCatalogNamesPath(locale),
      expectLocale: locale,
    );
    final catalog = _catalog ?? await loadCatalog();
    return _ensureResource<GeoCatalogNames>(entry, (bytes, decoded) async {
      final upd = _updateEpoch;
      final parsed = parseCatalogNames(
        decoded,
        expectedCatalog: catalog,
        expectedDatasetId: datasetId,
      );
      _crossCheckIdentity(
        entry,
        revision: parsed.revision,
        locale: parsed.locale,
      );
      if (upd == _updateEpoch && !_disposed) {
        _catalogNames[parsed.locale] = parsed;
      }
      return parsed;
    });
  }

  /// Makes [countryCode] the active selection target.
  ///
  /// Bumps the generation token first; when the load completes and the token
  /// still matches, the country is committed and listeners notified. A later
  /// [switchCountry] invalidates the earlier commit, so a late response never
  /// overwrites the newest intent (AT-07). The structure still resolves for
  /// the caller, and its content stays in the additive identity-keyed cache.
  Future<GeoRegionStructure> switchCountry(String countryCode) async {
    _ensureNotDisposed();
    final generation = ++_generation;
    final structure = await loadStructure(countryCode);
    if (generation == _generation && !_disposed) {
      _activeCountry = countryCode;
      _notify();
    }
    return structure;
  }

  /// Makes [locale] active: loads catalog names plus the active country's
  /// pack, then commits atomically.
  Future<void> switchLocale(String locale) async {
    _ensureNotDisposed();
    final generation = ++_generation;
    await loadCatalogNames(locale);
    final country = _activeCountry;
    if (country != null) {
      await loadLocalePack(country, locale);
    }
    if (generation == _generation && !_disposed) {
      _activeLocale = locale;
      _notify();
    }
  }

  /// Atomically replaces the active set with [candidate] (AT-10).
  ///
  /// Every resource of the candidate is fetched, verified and parsed first;
  /// only a fully compatible staged set is swapped in. Any failure leaves
  /// the current set untouched and flags [isStale] (stale coherent, PRD §8).
  /// Cache writes of already-verified staged resources are kept: they are
  /// content-addressed and never mix into the active set.
  Future<void> updateTo(GeoManifest candidate) async {
    _ensureNotDisposed();
    if (candidate.datasetId != datasetId) {
      throw GeoConfigurationError(
        'cannot switch to manifest of dataset "${candidate.datasetId}"; '
        'repository is pinned to "$datasetId"',
      );
    }
    if (_updating) {
      throw const GeoConfigurationError(
        'an atomic update is already in progress',
      );
    }
    _updating = true;
    try {
      final staged = await _stageCandidate(candidate);
      // Bump epochs so pre-swap pipelines cannot commit into the new set.
      _generation++;
      _updateEpoch++;
      _activeManifest = candidate;
      _structures
        ..clear()
        ..addAll(staged.structures);
      _packs
        ..clear()
        ..addAll(staged.packs);
      _catalogNames
        ..clear()
        ..addAll(staged.catalogNames);
      _catalog = staged.catalog;
      _rebuildIndex();
      _stale = false;
      _activeCountry = null;
      _activeLocale = null;
      _notify();
    } on Object {
      _stale = true;
      _notify();
      rethrow;
    } finally {
      _updating = false;
    }
  }

  /// Evicts every cache entry of [targetDatasetId] (host quota hook, PRD §8).
  /// Returns the number of removed entries.
  Future<int> evictDataset(String targetDatasetId) async {
    final store = _store;
    if (store == null) {
      return 0;
    }
    var removed = 0;
    for (final key in await store.keys()) {
      if (key.datasetId == targetDatasetId) {
        await store.invalidate(key);
        removed++;
      }
    }
    return removed;
  }

  /// Disposes: bumps tokens, drops in-flight bookkeeping and clears state.
  /// Late responses commit nothing and notify nobody (AT-07); further loads
  /// throw [GeoConfigurationError].
  void dispose() {
    if (_disposed) {
      return;
    }
    _disposed = true;
    _generation++;
    _updateEpoch++;
    _inflight.clear();
    _structures.clear();
    _packs.clear();
    _catalogNames.clear();
    _catalog = null;
    _index = null;
  }

  void _ensureNotDisposed() {
    if (_disposed) {
      throw const GeoConfigurationError(
        'repository is disposed; no further loads',
      );
    }
  }

  void _notify() {
    if (_disposed) {
      return;
    }
    for (final listener in List.of(_listeners)) {
      listener();
    }
  }

  void _rebuildIndex() {
    _index = _structures.isEmpty ? null : GeoRegionIndex(_structures.values);
  }

  GeoManifestEntry _requireEntry(
    String path, {
    String? expectCountry,
    String? expectLocale,
  }) {
    final entry = _activeManifest.entryFor(path);
    if (entry == null) {
      throw GeoNotFoundError(
        'resource "$path" is not declared by the active manifest '
        '(revision ${_activeManifest.revision})',
      );
    }
    if (expectCountry != null && entry.countryCode != expectCountry) {
      throw GeoIntegrityMismatchError(
        'manifest entry "$path" declares country ${entry.countryCode}, expected $expectCountry',
      );
    }
    if (expectLocale != null && entry.locale != expectLocale) {
      throw GeoIntegrityMismatchError(
        'manifest entry "$path" declares locale ${entry.locale}, expected $expectLocale',
      );
    }
    return entry;
  }

  /// Deduped pipeline keyed by the entry's cache key: concurrent requests
  /// for the same identity share one in-flight future (GR-05, AT-07).
  Future<T> _ensureResource<T>(
    GeoManifestEntry entry,
    Future<T> Function(GeoBytes bytes, Object? decoded) build,
  ) {
    final key = GeoCacheKey.fromManifestEntry(datasetId, entry);
    return _ensure<T>(key, () async {
      final (bytes, decoded) = await _fetchAndDecode(entry);
      final parsed = await build(bytes, decoded);
      // Written only after verification + parse success (AT-08).
      await _writeCacheSafely(key, bytes);
      return parsed;
    });
  }

  Future<T> _ensure<T>(GeoCacheKey key, Future<T> Function() pipeline) {
    final existing = _inflight[key];
    if (existing != null) {
      return existing.then((value) => value as T);
    }
    final future = pipeline();
    _inflight[key] = future;
    future
        .whenComplete(() {
          if (identical(_inflight[key], future)) {
            _inflight.remove(key);
          }
        })
        .then((_) {}, onError: (Object _, StackTrace __) {});
    return future;
  }

  Future<(GeoBytes, Object?)> _fetchAndDecode(GeoManifestEntry entry) async {
    final bytes = await _obtainBytes(entry);
    return (bytes, _decodeJson(bytes, entry.path));
  }

  /// Source order: identity-keyed cache, bundled assets, then remote.
  Future<GeoBytes> _obtainBytes(GeoManifestEntry entry) async {
    final store = _store;
    if (store != null) {
      final cached = await store.read(
        GeoCacheKey.fromManifestEntry(datasetId, entry),
      );
      if (cached != null) {
        return _checkCachedLength(cached, entry);
      }
    }
    final bundled = _bundledLoader;
    if (bundled != null) {
      try {
        final bytes = await bundled.load(Uri(path: entry.path));
        _verifyOfflineBytes(bytes, entry);
        return bytes;
      } on GeoNotFoundError {
        // Not bundled: fall through to the remote source.
      }
    }
    final remote = _remoteLoader;
    if (remote != null) {
      final bytes = await remote.load(_remoteUri(entry));
      await _verifyRemoteBytes(bytes, entry);
      return bytes;
    }
    throw GeoNetworkError(
      'resource ${entry.path} is unavailable: no cache entry, no bundled asset '
      'and no remote loader configured',
    );
  }

  GeoBytes _checkCachedLength(GeoBytes cached, GeoManifestEntry entry) {
    if (cached.length != entry.bytes) {
      throw GeoIntegrityMismatchError(
        'cache entry for ${entry.path} holds ${cached.length} bytes, '
        'manifest declares ${entry.bytes}',
      );
    }
    return cached;
  }

  /// Digest check re-proves bundled bytes against the pinned identity.
  void _verifyOfflineBytes(GeoBytes bytes, GeoManifestEntry entry) {
    if (bytes.length != entry.bytes) {
      throw GeoIntegrityMismatchError(
        'bundled asset ${entry.path} has ${bytes.length} bytes, manifest declares ${entry.bytes}',
      );
    }
    if (geoSha256Hex(bytes.bytes) != entry.sha256) {
      throw GeoIntegrityMismatchError(
        'bundled asset ${entry.path} does not match its manifest SHA-256',
      );
    }
  }

  /// Remote verification before any decoding (AT-08/AT-09).
  Future<void> _verifyRemoteBytes(
    GeoBytes bytes,
    GeoManifestEntry entry,
  ) async {
    if (bytes.length != entry.bytes) {
      throw GeoIntegrityMismatchError(
        'download of ${entry.path} delivered ${bytes.length} bytes, '
        'manifest declares ${entry.bytes}',
      );
    }
    if (bytes.contentLength != null && bytes.contentLength != entry.bytes) {
      throw GeoIntegrityMismatchError(
        'transport content length ${bytes.contentLength} for ${entry.path} '
        'disagrees with manifest length ${entry.bytes}',
      );
    }
    final verifier = _verifier;
    if (verifier == null) {
      throw const GeoConfigurationError(
        'remote bytes reached verification without a verifier',
      );
    }
    if (!await verifier.verify(bytes, entry.sha256, entry.bytes)) {
      throw GeoIntegrityMismatchError(
        'SHA-256 of ${entry.path} does not match the manifest',
      );
    }
  }

  Uri _remoteUri(GeoManifestEntry entry) {
    final base = _remoteBase;
    final relative = Uri(path: entry.path);
    return base == null ? relative : base.resolveUri(relative);
  }

  Object? _decodeJson(GeoBytes bytes, String what) {
    final String text;
    try {
      text = utf8.decode(bytes.bytes);
    } on FormatException catch (error) {
      throw GeoParseFailureError(
        '$what: payload is not valid UTF-8 (${error.message})',
      );
    }
    return parseJsonText(text);
  }

  Future<void> _writeCacheSafely(GeoCacheKey key, GeoBytes bytes) async {
    final store = _store;
    if (store == null || _disposed) {
      return;
    }
    try {
      await store.write(key, bytes);
    } on Object {
      // Best-effort: a failed write must not fail an already verified load.
    }
  }

  void _crossCheckIdentity(
    GeoManifestEntry entry, {
    String? revision,
    String? countryCode,
    String? locale,
  }) {
    if (revision != null && revision != entry.revision) {
      throw GeoIntegrityMismatchError(
        'content of ${entry.path} declares revision $revision, manifest entry says ${entry.revision}',
      );
    }
    if (countryCode != null && countryCode != entry.countryCode) {
      throw GeoIntegrityMismatchError(
        'content of ${entry.path} declares country $countryCode, manifest entry says ${entry.countryCode}',
      );
    }
    if (locale != null && locale != entry.locale) {
      throw GeoIntegrityMismatchError(
        'content of ${entry.path} declares locale $locale, manifest entry says ${entry.locale}',
      );
    }
  }

  Future<_StagedSet> _stageCandidate(GeoManifest candidate) async {
    final catalog = await _stageCatalogOf(candidate);
    final structures = <String, GeoRegionStructure>{};
    for (final entry in candidate.resources) {
      if (entry.kind == GeoResourceKind.structure) {
        final structure = await _stageStructureOf(entry);
        structures[structure.countryCode] = structure;
      }
    }
    final packs = <String, Map<String, GeoLocalePack>>{};
    for (final entry in candidate.resources) {
      if (entry.kind != GeoResourceKind.locale) {
        continue;
      }
      final structure = structures[entry.countryCode];
      if (structure == null) {
        throw GeoIntegrityMismatchError(
          'locale entry ${entry.path} has no matching structure entry in the candidate manifest',
        );
      }
      final pack = await _stagePackOf(entry, structure);
      (packs[pack.countryCode] ??= <String, GeoLocalePack>{})[pack.locale] =
          pack;
    }
    final catalogNames = <String, GeoCatalogNames>{};
    for (final entry in candidate.resources) {
      if (entry.kind == GeoResourceKind.countryNames) {
        final names = await _stageCatalogNamesOf(entry, catalog);
        catalogNames[names.locale] = names;
      }
    }
    return _StagedSet(
      catalog: catalog,
      structures: structures,
      packs: packs,
      catalogNames: catalogNames,
    );
  }

  Future<GeoCountryCatalog?> _stageCatalogOf(GeoManifest candidate) async {
    final entries = candidate.resources
        .where((entry) => entry.kind == GeoResourceKind.countries)
        .toList();
    if (entries.isEmpty) {
      return null;
    }
    if (entries.length > 1) {
      throw const GeoIntegrityMismatchError(
        'manifest declares more than one countries resource',
      );
    }
    final entry = entries.single;
    final existing = _catalog;
    if (existing != null && existing.revision == entry.revision) {
      return existing;
    }
    final key = GeoCacheKey.fromManifestEntry(datasetId, entry);
    return _ensure<GeoCountryCatalog>(key, () async {
      final (bytes, decoded) = await _fetchAndDecode(entry);
      final parsed = parseCountryCatalog(decoded, expectedDatasetId: datasetId);
      _crossCheckIdentity(entry, revision: parsed.revision);
      await _writeCacheSafely(key, bytes);
      return parsed;
    });
  }

  Future<GeoRegionStructure> _stageStructureOf(GeoManifestEntry entry) async {
    final countryCode = entry.countryCode;
    if (countryCode == null) {
      throw GeoIntegrityMismatchError(
        'structure entry ${entry.path} lacks countryCode',
      );
    }
    final existing = _structures[countryCode];
    if (existing != null && existing.revision == entry.revision) {
      return existing;
    }
    final key = GeoCacheKey.fromManifestEntry(datasetId, entry);
    return _ensure<GeoRegionStructure>(key, () async {
      final (bytes, decoded) = await _fetchAndDecode(entry);
      final parsed = parseRegionStructure(
        decoded,
        expectedDatasetId: datasetId,
      );
      _crossCheckIdentity(
        entry,
        revision: parsed.revision,
        countryCode: parsed.countryCode,
      );
      await _writeCacheSafely(key, bytes);
      return parsed;
    });
  }

  Future<GeoLocalePack> _stagePackOf(
    GeoManifestEntry entry,
    GeoRegionStructure structure,
  ) async {
    final countryCode = entry.countryCode;
    final locale = entry.locale;
    if (countryCode == null || locale == null) {
      throw GeoIntegrityMismatchError(
        'locale entry ${entry.path} lacks countryCode/locale',
      );
    }
    final existing = _packs[countryCode]?[locale];
    if (existing != null &&
        existing.revision == entry.revision &&
        existing.compatibleStructureRevision == structure.revision) {
      return existing;
    }
    final key = GeoCacheKey.fromManifestEntry(datasetId, entry);
    return _ensure<GeoLocalePack>(key, () async {
      final (bytes, decoded) = await _fetchAndDecode(entry);
      final parsed = parseLocalePack(
        decoded,
        expectedStructure: structure,
        expectedDatasetId: datasetId,
      );
      _crossCheckIdentity(
        entry,
        revision: parsed.revision,
        countryCode: parsed.countryCode,
        locale: parsed.locale,
      );
      await _writeCacheSafely(key, bytes);
      return parsed;
    });
  }

  Future<GeoCatalogNames> _stageCatalogNamesOf(
    GeoManifestEntry entry,
    GeoCountryCatalog? catalog,
  ) {
    final locale = entry.locale;
    if (locale == null) {
      throw GeoIntegrityMismatchError(
        'country-names entry ${entry.path} lacks locale',
      );
    }
    final existing = _catalogNames[locale];
    if (existing != null &&
        existing.revision == entry.revision &&
        (catalog == null ||
            existing.compatibleCatalogRevision == catalog.revision)) {
      return Future<GeoCatalogNames>.value(existing);
    }
    final key = GeoCacheKey.fromManifestEntry(datasetId, entry);
    return _ensure<GeoCatalogNames>(key, () async {
      final (bytes, decoded) = await _fetchAndDecode(entry);
      final parsed = parseCatalogNames(
        decoded,
        expectedCatalog: catalog,
        expectedDatasetId: datasetId,
      );
      _crossCheckIdentity(
        entry,
        revision: parsed.revision,
        locale: parsed.locale,
      );
      await _writeCacheSafely(key, bytes);
      return parsed;
    });
  }
}

/// Fully parsed candidate set held aside until the atomic swap.
class _StagedSet {
  const _StagedSet({
    required this.catalog,
    required this.structures,
    required this.packs,
    required this.catalogNames,
  });

  final GeoCountryCatalog? catalog;
  final Map<String, GeoRegionStructure> structures;
  final Map<String, Map<String, GeoLocalePack>> packs;
  final Map<String, GeoCatalogNames> catalogNames;
}
