// SPDX-License-Identifier: BSD-3-Clause
// Demo widget tests over the production SDK and real generated assets.
//
// The demo mounts the repository built from `assets/geo_regions/` (hybrid
// subset) plus the simulated CDN (`assets/geo_cdn/`), so every assertion
// below uses the real `geo-regions-seed` IDs, revisions and quality rules.
// Kept from P1-01: locale/ID stability, offline error + retry, request
// races, RTL, 200% text, skeleton, localizations and the three viewports.
//
// Asset loading is preloaded once in setUpAll on the real event loop: the
// widget-test binding only delivers asset-channel replies during the first
// test of a process, so each test builds a FRESH harness from the preloaded
// bytes (fresh cache per test keeps offline/retry scenarios isolated).
import 'dart:convert';
import 'dart:typed_data';

// ignore_for_file: deprecated_member_use

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';
import 'package:geo_regions_demo/main.dart';
import 'package:geo_regions_demo/sdk_data.dart';

final Map<String, Uint8List> _bundledBytes = <String, Uint8List>{};
final Map<String, Uint8List> _cdnBytes = <String, Uint8List>{};
String _registryText = '';

/// Memory loader standing in for [GeoAssetBundleLoader] in tests.
class _MemoryLoader implements GeoResourceLoader {
  const _MemoryLoader(this.payloads);

  final Map<String, Uint8List> payloads;

  @override
  Future<GeoBytes> load(Uri resourceUri) async {
    final bytes = payloads[resourceUri.path];
    if (bytes == null) {
      throw GeoNotFoundError('test bundle: no payload for $resourceUri');
    }
    return GeoBytes(bytes, contentLength: bytes.length);
  }
}

DemoGeoHarness _freshHarness() {
  final manifest = demoManifestFromRegistry(jsonDecode(_registryText));
  final cdn = DemoCdnLoader(
    serve: (path) async {
      final bytes = _cdnBytes[path];
      if (bytes == null) {
        throw GeoNotFoundError('test CDN: no payload for $path');
      }
      return GeoBytes(bytes, contentLength: bytes.length);
    },
  );
  final repository = GeoRegionsRepository(
    manifest: manifest,
    bundledLoader: _MemoryLoader(_bundledBytes),
    remoteLoader: cdn,
    verifier: const DemoShaVerifier(),
    store: GeoMemoryCacheStore(),
  );
  return DemoGeoHarness(
    repository: repository,
    source: GeoRepositoryDataSource(
      repository,
      defaultLocale: 'en',
      bundledCountries: kDemoBundledCountries,
    ),
    cdn: cdn,
  );
}

void main() {
  setUpAll(() async {
    // Real-async preload of the bundle bytes the demo serves. The registry
    // descriptor list enumerates the full release; each payload lives in
    // exactly one of the two demo bundles.
    _registryText = await rootBundle.loadString(
      '${kDemoBundledPrefix}registry.json',
    );
    final manifest = demoManifestFromRegistry(jsonDecode(_registryText));
    for (final entry in manifest.resources) {
      for (final prefix in const [kDemoBundledPrefix, kDemoCdnPrefix]) {
        try {
          final data = await rootBundle.load('$prefix${entry.path}');
          final bytes = Uint8List.fromList(
            data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
          );
          (prefix == kDemoBundledPrefix
                  ? _bundledBytes
                  : _cdnBytes)[entry.path] =
              bytes;
          break;
        } on FlutterError {
          // Not in this bundle; try the next one.
        }
      }
    }
  });

  Future<void> mount(WidgetTester tester, DemoGeoHarness harness) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(GeoDemoApp(harness: harness));
    await tester.pumpAndSettle();
  }

  String draftId(WidgetTester tester) =>
      tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data!;

  testWidgets('locale change preserves selected IDs over real data', (
    tester,
  ) async {
    await mount(tester, _freshHarness());
    await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
    await tester.pumpAndSettle();
    final before = draftId(tester);
    expect(before, 'cc:CN / iso3166-2:CN-GD / cn-stat:4403');

    await tester.tap(find.byKey(const ValueKey('locale-picker')));
    await tester.pumpAndSettle();
    final japanese = find.byKey(const ValueKey('locale-ja')).last;
    await tester.ensureVisible(japanese);
    await tester.pumpAndSettle();
    await tester.tap(japanese);
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    expect(draftId(tester), before);
    expect(find.text('選択を確定'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('uncached offline country shows error and retry recovers', (
    tester,
  ) async {
    final harness = _freshHarness();
    await mount(tester, harness);
    await tester.tap(find.byKey(const ValueKey('airplane-toggle')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('picker-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('retry-button')), findsOneWidget);
    expect(find.byKey(const ValueKey('node-iso3166-2:JP-01')), findsNothing);

    await tester.tap(find.byKey(const ValueKey('airplane-toggle')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('retry-button')));
    // Advance past the simulated CDN latency; a plain pumpAndSettle stops
    // early because the skeleton schedules no frames.
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('node-iso3166-2:JP-01')), findsOneWidget);
    expect(find.byKey(const ValueKey('retry-button')), findsNothing);
    expect(harness.cdn.requests, contains('regions/JP.json'));
    expect(tester.takeException(), isNull);
  });

  testWidgets('late country response cannot overwrite the latest country', (
    tester,
  ) async {
    final harness = _freshHarness();
    await mount(tester, harness);
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pump(const Duration(milliseconds: 80));
    await tester.tap(find.byKey(const ValueKey('country-CN')));
    // JP's simulated CDN latency is 250 ms; advance past it so the late
    // response actually arrives, then settle the newer CN intent.
    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();
    expect(draftId(tester), 'cc:CN');
    expect(find.byKey(const ValueKey('node-iso3166-2:CN-GD')), findsOneWidget);
    expect(find.byKey(const ValueKey('node-iso3166-2:JP-01')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Arabic uses RTL and mobile controls remain usable', (
    tester,
  ) async {
    final harness = _freshHarness();
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(GeoDemoApp(harness: harness));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('locale-picker')));
    await tester.pumpAndSettle();
    final arabic = find.byKey(const ValueKey('locale-ar')).last;
    await tester.ensureVisible(arabic);
    await tester.pumpAndSettle();
    await tester.tap(arabic);
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    expect(
      Directionality.of(
        tester.element(find.byKey(const ValueKey('region-search'))),
      ),
      TextDirection.rtl,
    );
    expect(find.byKey(const ValueKey('country-CN')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('French controls remain reachable at 200 percent text scale', (
    tester,
  ) async {
    final harness = _freshHarness();
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(2)),
          child: child!,
        ),
        home: GeoPlayground(
          harness: harness,
          locale: 'fr',
          dark: false,
          onLocale: (_) {},
          onDark: (_) {},
        ),
      ),
    );
    // The fr locale pack for CN is not bundled: the picker fetches it via
    // the simulated CDN with latency. Advance the fake clock past it — the
    // static skeleton schedules no frames, so pumpAndSettle alone would
    // stop too early.
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();
    expect(draftId(tester), 'cc:CN / iso3166-2:CN-GD');
    expect(
      find.byKey(const ValueKey('confirm-selection')).hitTestable(),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('loading shows skeleton placeholders instead of region rows', (
    tester,
  ) async {
    await mount(tester, _freshHarness());
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pump();
    expect(find.byKey(const ValueKey('loading-skeleton')), findsOneWidget);
    expect(find.byKey(const ValueKey('node-iso3166-2:JP-01')), findsNothing);
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('loading-skeleton')), findsNothing);
    expect(find.byKey(const ValueKey('node-iso3166-2:JP-01')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('framework Material localizations follow the selected language', (
    tester,
  ) async {
    await mount(tester, _freshHarness());
    expect(
      Localizations.localeOf(tester.element(find.byType(GeoPlayground)))
          .languageCode,
      'zh',
    );
    await tester.tap(find.byKey(const ValueKey('locale-picker')));
    await tester.pumpAndSettle();
    final arabic = find.byKey(const ValueKey('locale-ar')).last;
    await tester.ensureVisible(arabic);
    await tester.pumpAndSettle();
    await tester.tap(arabic);
    await tester.pumpAndSettle();
    expect(
      Localizations.localeOf(tester.element(find.byType(GeoPlayground)))
          .languageCode,
      'ar',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('no layout overflow at 390, 768 and 1280 widths', (tester) async {
    for (final size in const [
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      await tester.binding.setSurfaceSize(size);
      await tester.pumpWidget(GeoDemoApp(harness: _freshHarness()));
      await tester.pumpAndSettle();
      expect(
        tester.takeException(),
        isNull,
        reason: 'layout exception at ${size.width}x${size.height}',
      );
      expect(
        find.byKey(const ValueKey('region-search')),
        findsOneWidget,
        reason: 'search visible at ${size.width}x${size.height}',
      );
      expect(
        find.byKey(const ValueKey('confirm-selection')),
        findsOneWidget,
        reason: 'confirm visible at ${size.width}x${size.height}',
      );
      await tester.binding.setSurfaceSize(null);
    }
  });

  testWidgets('confirmed selection carries the real dataset identity', (
    tester,
  ) async {
    await mount(tester, _freshHarness());
    await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();

    final json = tester
        .widget<SelectableText>(find.byKey(const ValueKey('selection-json')))
        .data!;
    expect(json, contains('"datasetId": "geo-regions-seed"'));
    expect(json, contains('"countryCode": "CN"'));
    expect(json, contains('"pathIds"'));
    expect(json, contains('"cc:CN"'));
    expect(json, contains('"dataRevision"'));
    expect(
      json,
      contains('s-'),
      reason: 'real content revision, not fixture-1',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'unknown coverage says so instead of claiming the deepest level',
    (tester) async {
      await mount(tester, _freshHarness());
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:440305')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('coverage-unknown')), findsOneWidget);
      expect(find.text('数据范围未知'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('opening a country only requests that country over the CDN', (
    tester,
  ) async {
    final harness = _freshHarness();
    await mount(tester, harness);
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();
    expect(harness.cdn.requests, <String>[
      'regions/JP.json',
      'i18n/zh-Hans/JP.json',
    ]);
    expect(
      harness.cdn.requests.where((path) => path.contains('regions/CN')),
      isEmpty,
      reason: 'GR-04: the bundled country must not be re-fetched',
    );
    expect(tester.takeException(), isNull);
  });
}
