// SPDX-License-Identifier: BSD-3-Clause
/// Widget-level remote flows with an in-memory remote loader (P1-07).
///
/// Real-socket VM tests live in `remote_origin_test.dart` (the widget-test
/// binding installs an HttpOverrides fake, so widget files cannot speak real
/// HTTP). Here the same integrity chain runs over in-memory "CDN" bytes:
/// remote loader + verifier + cache, rendered through the picker.
library;

import 'dart:typed_data';

// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import '../load/fake_adapters.dart';
import '../load/fixture_bytes.dart';
import 'test_kit.dart';

class _ShaVerifier implements GeoHashVerifier {
  const _ShaVerifier();

  @override
  Future<bool> verify(GeoBytes bytes, String sha256, int expectedBytes) async {
    return bytes.length == expectedBytes && geoSha256Hex(bytes.bytes) == sha256;
  }
}

void main() {
  testWidgets(
    'picker renders a remotely sourced country and its failure state',
    (tester) async {
      // In-memory stand-in for the CDN bytes: same protocol, same integrity
      // chain, no real sockets inside the fake-async widget zone.
      final remote = FakeGeoLoader(
        payloads: <String, Uint8List>{
          'regions/JP.json': dataBytes('regions/JP.json'),
          'i18n/zh-Hans/JP.json': dataBytes('i18n/zh-Hans/JP.json'),
        },
      );
      final store = GeoMemoryCacheStore();
      final source = GeoRepositoryDataSource(
        GeoRegionsRepository(
          manifest: realManifest,
          remoteLoader: remote,
          verifier: const _ShaVerifier(),
          store: store,
        ),
        defaultLocale: 'en',
      );
      final selections = <GeoSelection>[];
      await pumpPicker(
        tester,
        picker: GeoRegionPicker(
          dataSource: source,
          countryCode: 'JP',
          displayLocale: 'zh-Hans',
          onConfirmed: selections.add,
        ),
      );
      await tester.pumpAndSettle();

      // The remote country rendered through the verified payload.
      expect(
        find.byKey(const ValueKey('node-iso3166-2:JP-01')),
        findsOneWidget,
      );
      final tokyoRow = tester.widget<ListTile>(
        find.byKey(const ValueKey('node-iso3166-2:JP-13')),
      );
      // Default-name fallback carries the honesty badge, so assert on the
      // resolved label text instead of an exact Text widget.
      final tokyoLabel = rowLabelText(tokyoRow.title)!;
      expect(tokyoLabel.startsWith('Tokyo'), isTrue);
      // Default-name fallback rows carry the honesty badge in the defaults.
      expect(tokyoLabel.contains('未翻译'), isTrue);
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
        'cc:JP',
      );
      expect(store.writeLog.map((key) => key.countryCode), everyElement('JP'));

      // JP provinces are unknown coverage: entering one shows the honest
      // state, and the country root still confirms (PROTOCOL §8).
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:JP-13')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('coverage-unknown')), findsOneWidget);
      expect(
        tester
            .widget<FilledButton>(
              find.byKey(const ValueKey('confirm-selection')),
            )
            .onPressed,
        isNull,
      );

      await tester.tap(find.byKey(const ValueKey('back-button')));
      await tester.pumpAndSettle();
      await tester.ensureVisible(
        find.byKey(const ValueKey('confirm-selection')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('confirm-selection')));
      await tester.pumpAndSettle();
      expect(selections, hasLength(1));
      expect(selections.single.pathIds, <String>['cc:JP']);
      expect(selections.single.displaySnapshot, <String>['日本']);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('picker shows the typed notFound failure for a missing country', (
    tester,
  ) async {
    final remote = FakeGeoLoader(payloads: <String, Uint8List>{});
    final source = GeoRepositoryDataSource(
      GeoRegionsRepository(
        manifest: realManifest,
        remoteLoader: remote,
        verifier: const _ShaVerifier(),
        store: GeoMemoryCacheStore(),
      ),
      defaultLocale: 'en',
    );
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        countryCode: 'KR',
        displayLocale: 'zh-Hans',
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('picker-error')), findsOneWidget);
    expect(find.text('GeoNotFoundError'), findsOneWidget);
    expect(find.byKey(const ValueKey('retry-button')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
