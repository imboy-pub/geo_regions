// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions_demo/main.dart';

void main() {
  Future<void> mount(WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(const GeoDemoApp());
    await tester.pumpAndSettle();
  }

  testWidgets('locale change preserves selected IDs', (tester) async {
    await mount(tester);
    await tester.tap(find.byKey(const ValueKey('node-cn:44')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-cn:4403')));
    await tester.pumpAndSettle();
    final before = tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data;
    expect(before, 'cc:CN / cn:44 / cn:4403');
    await tester.tap(find.byKey(const ValueKey('locale-picker')));
    await tester.pumpAndSettle();
    final japanese = find.byKey(const ValueKey('locale-ja')).last;
    await tester.ensureVisible(japanese);
    await tester.pumpAndSettle();
    await tester.tap(japanese);
    await tester.pumpAndSettle();
    expect(tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data, before);
    expect(find.text('選択を確定'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('uncached offline country shows error and retry recovers', (tester) async {
    await mount(tester);
    await tester.tap(find.byKey(const ValueKey('airplane-toggle')));
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pump(const Duration(milliseconds: 650));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('retry-button')), findsOneWidget);
    expect(find.byKey(const ValueKey('node-jp:13')), findsNothing);
    await tester.tap(find.byKey(const ValueKey('airplane-toggle')));
    await tester.tap(find.byKey(const ValueKey('retry-button')));
    await tester.pump(const Duration(milliseconds: 650));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('node-jp:13')), findsOneWidget);
    expect(find.byKey(const ValueKey('retry-button')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('late country response cannot overwrite the latest country', (tester) async {
    await mount(tester);
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pump(const Duration(milliseconds: 20));
    await tester.tap(find.byKey(const ValueKey('country-CN')));
    // Advance past BOTH timers, including the stale 550 ms request.
    // pumpAndSettle alone may stop once the newer local request has settled.
    await tester.pump(const Duration(milliseconds: 650));
    await tester.pumpAndSettle();
    expect(tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data, 'cc:CN');
    expect(find.byKey(const ValueKey('node-cn:44')), findsOneWidget);
    expect(find.byKey(const ValueKey('node-jp:13')), findsNothing);
  });

  testWidgets('Arabic uses RTL and mobile controls remain usable', (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(const GeoDemoApp());
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('locale-picker')));
    await tester.pumpAndSettle();
    final arabic = find.byKey(const ValueKey('locale-ar')).last;
    await tester.ensureVisible(arabic);
    await tester.pumpAndSettle();
    await tester.tap(arabic);
    await tester.pumpAndSettle();
    expect(Directionality.of(tester.element(find.byKey(const ValueKey('region-search')))), TextDirection.rtl);
    expect(tester.takeException(), isNull);
  });

  testWidgets('French controls remain reachable at 200 percent text scale', (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(MaterialApp(
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(textScaler: TextScaler.linear(2)),
        child: child!,
      ),
      home: GeoPlayground(locale: 'fr', dark: false, onLocale: (_) {}, onDark: (_) {}),
    ));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('node-cn:44')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-cn:44')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();
    expect(tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data, 'cc:CN / cn:44');
    expect(find.byKey(const ValueKey('confirm-selection')).hitTestable(), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

}
