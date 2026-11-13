// SPDX-License-Identifier: BSD-3-Clause
/// Shared kit for the picker UI tests: a VM data loader over the repository's
/// real `data/` files (golden vectors, same policy as `test/test_data.dart`),
/// a scriptable fake [GeoRegionDataSource] for state-matrix tests, and a
/// pump harness. `dart:io` is test-only; the library under test stays
/// web-compatible.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import '../load/fake_adapters.dart';
import '../load/fixture_bytes.dart';
import '../test_data.dart' show loadDecodedData;

/// Serves manifest-relative paths from the repo's `data/` directory so
/// picker tests exercise the real published resources end to end.
class DataDirLoader implements GeoResourceLoader {
  @override
  Future<GeoBytes> load(Uri resourceUri) async {
    final path = resourceUri.path;
    if (path.contains('..')) {
      throw GeoNotFoundError('unsafe test path: $resourceUri');
    }
    final file = File('data/$path');
    if (!file.existsSync()) {
      throw GeoNotFoundError('no data file for $resourceUri');
    }
    final bytes = file.readAsBytesSync();
    return GeoBytes(bytes, contentLength: bytes.length);
  }
}

/// Repository over the real published set with everything served locally.
GeoRegionsRepository realRepository({GeoCacheStore? store}) {
  return GeoRegionsRepository(
    manifest: realManifest,
    bundledLoader: DataDirLoader(),
    store: store ?? GeoMemoryCacheStore(),
  );
}

/// Repository over a mutated real CN set: 广东省's source name is marked
/// provisional and every locale pack is re-linked to the recomputed
/// structure revision, so the unreviewed name cannot be served without the
/// host opt-in — and the `en` fallback pack drops the node entirely, leaving
/// the stable ID as the only honest display (AT-14).
GeoRegionsRepository provisionalRepository({GeoCacheStore? store}) {
  final structure = loadDecodedData('regions/CN.json');
  for (final node in structure['nodes']! as List<Object?>) {
    final map = node! as Map<String, Object?>;
    if (map['id'] == 'iso3166-2:CN-GD') {
      map['nameQuality'] = 'provisional';
    }
  }
  final nodes = structure['nodes'];
  final structureRevision = geoStructureRevision(nodes);
  structure['revision'] = structureRevision;
  final structureBytes = Uint8List.fromList(utf8.encode(jsonEncode(structure)));
  final payloads = <String, Uint8List>{'regions/CN.json': structureBytes};

  final entries = <GeoManifestEntry>[];
  for (final entry in realManifest.resources) {
    final packMatch = RegExp(r'^i18n/([^/]+)/CN\.json$').firstMatch(entry.path);
    if (entry.path == 'regions/CN.json') {
      entries.add(
        GeoManifestEntry(
          path: entry.path,
          kind: entry.kind,
          revision: structureRevision,
          sha256: geoSha256Hex(structureBytes),
          bytes: structureBytes.length,
          countryCode: 'CN',
        ),
      );
      continue;
    }
    if (packMatch != null) {
      final locale = packMatch.group(1)!;
      final pack = loadDecodedData(entry.path);
      pack['compatibleStructureRevision'] = structureRevision;
      final names = (pack['names']! as Map<Object?, Object?>)
          .cast<String, Object?>();
      if (locale == 'en') {
        names.remove('iso3166-2:CN-GD');
      }
      final coverage = pack['coverage'] as Map<Object?, Object?>?;
      final quality =
          (coverage?['translationQualityById'] as Map<Object?, Object?>?)
              ?.cast<String, Object?>();
      if (locale == 'en') {
        quality?.remove('iso3166-2:CN-GD');
      }
      pack['revision'] = geoLocaleRevision(names, quality);
      final bytes = Uint8List.fromList(utf8.encode(jsonEncode(pack)));
      payloads[entry.path] = bytes;
      entries.add(
        GeoManifestEntry(
          path: entry.path,
          kind: entry.kind,
          revision: pack['revision']! as String,
          sha256: geoSha256Hex(bytes),
          bytes: bytes.length,
          countryCode: 'CN',
          locale: locale,
          compatibleStructureRevision: structureRevision,
        ),
      );
      continue;
    }
    entries.add(entry);
  }
  final manifest = GeoManifest(
    protocolVersion: '1.0',
    datasetId: realManifest.datasetId,
    revision: realManifest.revision,
    resources: List<GeoManifestEntry>.unmodifiable(entries),
  );
  return GeoRegionsRepository(
    manifest: manifest,
    bundledLoader: FakeGeoLoader(payloads: payloads),
    store: store ?? GeoMemoryCacheStore(),
  );
}

/// [GeoRegionDataSource] whose behavior each test scripts.
class FakePickerDataSource implements GeoRegionDataSource {
  FakePickerDataSource({
    List<GeoPickerItem> countries = const <GeoPickerItem>[],
    Map<String, GeoPickerCountryContent> roots =
        const <String, GeoPickerCountryContent>{},
    Map<String, List<GeoPickerItem>> childrenByNode =
        const <String, List<GeoPickerItem>>{},
    List<GeoPickerItem> hits = const <GeoPickerItem>[],
  }) : countries = List<GeoPickerItem>.of(countries),
       roots = Map<String, GeoPickerCountryContent>.of(roots),
       childrenByNode = Map<String, List<GeoPickerItem>>.of(childrenByNode),
       hits = List<GeoPickerItem>.of(hits);

  List<GeoPickerItem> countries;
  Map<String, GeoPickerCountryContent> roots;
  Map<String, List<GeoPickerItem>> childrenByNode;
  List<GeoPickerItem> hits;

  /// When set, the next call of the named operation fails with this error.
  Object? failureOnNext;
  String? failureOnNextOp;

  /// When set, the next call of the named operation delays before serving.
  Duration delayOnNext = Duration.zero;
  String? delayOnNextOp;

  final List<String> calls = <String>[];

  GeoPickerItem item(String id, String label) => GeoPickerItem(
    nodeId: id,
    label: label,
    countryCode: id.startsWith('cc:') ? id.substring(3) : 'ZZ',
    isCountryRoot: id.startsWith('cc:'),
    hasChildren: childrenByNode[id]?.isNotEmpty ?? false,
    pathIds: <String>[id],
  );

  Future<T> _gate<T>(String op, Future<T> Function() serve) async {
    calls.add(op);
    if (failureOnNextOp == op && failureOnNext != null) {
      failureOnNextOp = null;
      throw failureOnNext!;
    }
    if (delayOnNextOp == op) {
      delayOnNextOp = null;
      await Future<void>.delayed(delayOnNext);
    }
    return serve();
  }

  @override
  Future<List<GeoPickerItem>> loadCountries(String locale) =>
      _gate('loadCountries', () async => countries);

  @override
  Future<GeoPickerCountryContent> openCountry(
    String countryCode,
    String locale,
  ) => _gate<GeoPickerCountryContent>('openCountry:$countryCode', () async {
    final content = roots[countryCode];
    if (content == null) {
      throw GeoNotFoundError('fake source has no country $countryCode');
    }
    return content;
  });

  @override
  Future<List<GeoPickerItem>> loadChildren(
    String countryCode,
    String nodeId,
    String locale,
  ) => _gate('loadChildren:$nodeId', () async {
    final rows = childrenByNode[nodeId];
    if (rows == null) {
      throw GeoNotFoundError('fake source has no children of $nodeId');
    }
    return rows;
  });

  @override
  Future<List<GeoPickerItem>> search(String query, String locale) =>
      _gate('search', () async => hits);

  @override
  Future<GeoSelection> resolveSelection(
    List<String> pathIds, {
    required GeoSelectionPolicy policy,
    String? displayLocale,
  }) async {
    if (failureOnNextOp == 'resolveSelection' && failureOnNext != null) {
      failureOnNextOp = null;
      throw failureOnNext!;
    }
    return GeoSelection(
      protocolVersion: '1.0',
      datasetId: 'fake-dataset',
      countryCode: pathIds.first.substring(3),
      dataRevision: 's-fake000000000000',
      pathIds: List.unmodifiable(pathIds),
      displaySnapshot: <String>[for (final id in pathIds) '名:$id'],
      displayLocale: displayLocale,
    );
  }

  @override
  Future<Map<String, String>> resolveLabels(
    List<String> nodeIds,
    String locale,
  ) async => <String, String>{for (final id in nodeIds) id: '名:$id'};

  @override
  GeoPickerAvailability availabilityOf(String countryCode) =>
      countryCode == 'CN' || countryCode == 'ZZ'
      ? GeoPickerAvailability.bundled
      : GeoPickerAvailability.remote;
}

/// Pumps [picker] inside a scaffold; [direction], [textScale] and [size]
/// mirror the DEMO_UX acceptance conditions (RTL, 200% text, viewports).
Future<void> pumpPicker(
  WidgetTester tester, {
  required Widget picker,
  TextDirection direction = TextDirection.ltr,
  double textScale = 1.0,
  Size size = const Size(800, 1200),
  ThemeMode themeMode = ThemeMode.light,
}) async {
  await tester.binding.setSurfaceSize(size);
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      themeMode: themeMode,
      theme: ThemeData(useMaterial3: true, brightness: Brightness.light),
      darkTheme: ThemeData(useMaterial3: true, brightness: Brightness.dark),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context)
            .copyWith(textScaler: TextScaler.linear(textScale)),
        child: Directionality(textDirection: direction, child: child!),
      ),
      home: Scaffold(body: SingleChildScrollView(child: picker)),
    ),
  );
}

/// Creates a pinned [GeoRepositoryDataSource]-backed picker for [countryCode].
///
/// [id] distinguishes consecutive mounts in one test: pumpWidget reuses the
/// State of a same-type, same-key widget, so a fresh data source needs a
/// fresh key to actually remount.
GeoRegionPicker realPicker(
  GeoRegionDataSource source, {
  Object id = 'primary',
  String? countryCode = 'CN',
  String displayLocale = 'zh-Hans',
  GeoSelectionPolicy policy = GeoSelectionPolicy.allowIntermediate,
  GeoPickerLabels? labels,
  ValueChanged<GeoSelection>? onConfirmed,
  ValueChanged<String?>? onCountryChanged,
}) {
  return GeoRegionPicker(
    key: ValueKey('picker-$id-$countryCode-$policy'),
    dataSource: source,
    countryCode: countryCode,
    displayLocale: displayLocale,
    policy: policy,
    labels: labels,
    onConfirmed: onConfirmed,
    onCountryChanged: onCountryChanged,
  );
}
