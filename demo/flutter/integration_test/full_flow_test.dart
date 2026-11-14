// SPDX-License-Identifier: BSD-3-Clause
// Runs in a real Chrome browser: search -> navigate -> select -> language
// switch keeps IDs -> offline error + retry -> confirm. Mirrors the P1-01
// acceptance flow from docs/DEMO_UX.md section 5.
import 'package:material_ui/material_ui.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:geo_regions_demo/main.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('full acceptance flow in a real browser', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1280, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(const GeoDemoApp());
    await tester.pumpAndSettle();

    // Search for a deep node by Chinese name.
    await tester.enterText(find.byKey(const ValueKey('region-search')), '南山');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-cn:440305')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
      'cc:CN / cn:44 / cn:4403 / cn:440305',
      reason: 'search + select must rebuild the full ancestor path',
    );

    // Switch display language; the stable-ID draft must not change.
    await tester.tap(find.byKey(const ValueKey('locale-picker')));
    await tester.pumpAndSettle();
    final english = find.byKey(const ValueKey('locale-en')).last;
    await tester.ensureVisible(english);
    await tester.pumpAndSettle();
    await tester.tap(english);
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
      'cc:CN / cn:44 / cn:4403 / cn:440305',
      reason: 'display language must not change selection identity',
    );

    // Simulated offline load failure for an uncached country, then recovery.
    await tester.tap(find.byKey(const ValueKey('airplane-toggle')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('country-JP')));
    await tester.pump(const Duration(milliseconds: 650));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('retry-button')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('airplane-toggle')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('retry-button')));
    await tester.pump(const Duration(milliseconds: 650));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('node-jp:13')), findsOneWidget);

    // Confirm the Chinese selection and inspect the persisted contract.
    await tester.tap(find.byKey(const ValueKey('country-CN')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-cn:44')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();
    final json = tester
        .widget<SelectableText>(find.byKey(const ValueKey('selection-json')))
        .data!;
    expect(json, contains('"datasetId": "geo-regions-ui-fixture"'));
    expect(json, contains('"pathIds"'));
    expect(tester.takeException(), isNull);

    // Screenshot artifact for human review (captured by the binding runner).
    await binding.takeScreenshot('p1-01-full-flow-desktop');
  });
}
