// SPDX-License-Identifier: BSD-3-Clause
/// Picker state matrix over a scriptable fake data source (P1-07, AT-04).
///
/// The DEMO_UX states — loading skeleton, loaded rows, failure with retry,
/// empty search, unknown coverage — are separated here with controllable
/// delays and failures, independent of any network or dataset.
library;

// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_kit.dart';

final _zh = GeoPickerLabels.forLocale('zh-Hans');

FakePickerDataSource _fake() {
  final source = FakePickerDataSource();
  source.childrenByNode['cc:ZZ'] = <GeoPickerItem>[
    source.item('iso:ZZ-1', 'Region One'),
    source.item('iso:ZZ-2', 'Region Two'),
  ];
  source.roots['ZZ'] = GeoPickerCountryContent(
    root: source.item('cc:ZZ', 'Zedland'),
    children: List<GeoPickerItem>.of(source.childrenByNode['cc:ZZ']!),
  );
  source.countries = <GeoPickerItem>[
    source.item('cc:ZZ', 'Zedland'),
    source.item('cc:YY', 'Whyland'),
  ];
  return source;
}

void main() {
  testWidgets('loading shows the skeleton, then rows arrive', (tester) async {
    final source = _fake()
      ..delayOnNextOp = 'loadCountries'
      ..delayOnNext = const Duration(seconds: 2);
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(dataSource: source, displayLocale: 'zh-Hans'),
    );
    expect(find.byKey(const ValueKey('loading-skeleton')), findsOneWidget);
    expect(find.text(_zh.loading), findsOneWidget);
    expect(find.byKey(const ValueKey('country-cc:ZZ')), findsNothing);

    await tester.pump(const Duration(seconds: 2));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('loading-skeleton')), findsNothing);
    expect(find.byKey(const ValueKey('country-cc:ZZ')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('load failure and retry are separated from empty results', (
    tester,
  ) async {
    final source = _fake()
      ..failureOnNextOp = 'loadCountries'
      ..failureOnNext = const GeoNetworkError('simulated transport failure');
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(dataSource: source, displayLocale: 'zh-Hans'),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('picker-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('retry-button')), findsOneWidget);
    expect(find.text('GeoNetworkError'), findsOneWidget);
    expect(find.byKey(const ValueKey('no-results')), findsNothing);

    source.failureOnNext = null;
    await tester.tap(find.byKey(const ValueKey('retry-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('picker-error')), findsNothing);
    expect(find.byKey(const ValueKey('country-cc:ZZ')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('openCountry failure recovers through retry', (tester) async {
    final source = _fake()
      ..failureOnNextOp = 'openCountry:ZZ'
      ..failureOnNext = const GeoNotFoundError('country not served');
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        countryCode: 'ZZ',
        displayLocale: 'zh-Hans',
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('retry-button')), findsOneWidget);

    source.failureOnNext = null;
    await tester.tap(find.byKey(const ValueKey('retry-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('node-iso:ZZ-1')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('search failure and recovery keep the browse rows intact', (
    tester,
  ) async {
    final source = _fake();
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        countryCode: 'ZZ',
        displayLocale: 'zh-Hans',
      ),
    );
    await tester.pumpAndSettle();
    source
      ..failureOnNextOp = 'search'
      ..failureOnNext = const GeoNetworkError('search transport failure');
    await tester.enterText(
      find.byKey(const ValueKey('region-search')),
      'Region',
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('picker-error')), findsOneWidget);

    source.failureOnNext = null;
    await tester.tap(find.byKey(const ValueKey('retry-button')));
    await tester.pumpAndSettle();
    // The retried search completes with no fake hits; clearing restores rows.
    expect(find.byKey(const ValueKey('no-results')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('clear-search')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('node-iso:ZZ-1')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('search hits carry disambiguation and empty stays distinct', (
    tester,
  ) async {
    final source = _fake();
    final hit = source.item('iso:ZZ-1', 'Region One');
    source.hits = <GeoPickerItem>[
      GeoPickerItem(
        nodeId: hit.nodeId,
        label: hit.label,
        countryCode: 'ZZ',
        hasChildren: false,
        childrenStatus: GeoChildrenStatus.complete,
        pathIds: const <String>['cc:ZZ', 'iso:ZZ-1'],
        pathLabels: const <String>['Zedland', 'Region One'],
      ),
    ];
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        countryCode: 'ZZ',
        displayLocale: 'zh-Hans',
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('region-search')), 'One');
    await tester.pumpAndSettle();
    expect(find.text('Zedland / Region One'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('node-iso:ZZ-1')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
      'cc:ZZ / iso:ZZ-1',
    );

    source.hits = const <GeoPickerItem>[];
    await tester.enterText(
      find.byKey(const ValueKey('region-search')),
      'no match at all',
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('no-results')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('requireLeafWithinDeclared confirms only declared leaves', (
    tester,
  ) async {
    final source = _fake();
    final leaf = source.item('leaf:9', 'Declared Leaf');
    source.childrenByNode['cc:ZZ'] = <GeoPickerItem>[
      GeoPickerItem(
        nodeId: leaf.nodeId,
        label: leaf.label,
        countryCode: 'ZZ',
        childrenStatus: GeoChildrenStatus.complete,
        hasChildren: false,
        pathIds: const <String>['cc:ZZ', 'leaf:9'],
      ),
      GeoPickerItem(
        nodeId: 'iso:ZZ-1',
        label: 'Region One',
        countryCode: 'ZZ',
        childrenStatus: GeoChildrenStatus.complete,
        hasChildren: true,
        pathIds: const <String>['cc:ZZ', 'iso:ZZ-1'],
      ),
      GeoPickerItem(
        nodeId: 'iso:ZZ-u',
        label: 'Unknown Level',
        countryCode: 'ZZ',
        childrenStatus: GeoChildrenStatus.unknown,
        hasChildren: false,
        pathIds: const <String>['cc:ZZ', 'iso:ZZ-u'],
      ),
    ];
    source.roots['ZZ'] = GeoPickerCountryContent(
      root: source.roots['ZZ']!.root,
      children: List<GeoPickerItem>.of(source.childrenByNode['cc:ZZ']!),
    );
    final selections = <GeoSelection>[];
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        countryCode: 'ZZ',
        policy: GeoSelectionPolicy.requireLeafWithinDeclared,
        displayLocale: 'zh-Hans',
        onConfirmed: selections.add,
      ),
    );
    await tester.pumpAndSettle();

    FilledButton confirmButton() => tester.widget<FilledButton>(
      find.byKey(const ValueKey('confirm-selection')),
    );

    // The declared leaf is immediately confirmable.
    expect(confirmButton().onPressed, isNotNull);
    await tester.tap(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();
    expect(selections.single.pathIds, <String>['cc:ZZ']);

    // An intermediate node is not a leaf: confirm disabled; the fake serves
    // no children under it.
    source.childrenByNode['iso:ZZ-1'] = <GeoPickerItem>[];
    await tester.tap(find.byKey(const ValueKey('node-iso:ZZ-1')));
    await tester.pumpAndSettle();
    expect(confirmButton().onPressed, isNull);
    expect(find.byKey(const ValueKey('no-child-regions')), findsOneWidget);

    // Back out, then try the unknown-coverage node: it never impersonates a
    // leaf either.
    await tester.tap(find.byKey(const ValueKey('back-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-iso:ZZ-u')));
    await tester.pumpAndSettle();
    expect(confirmButton().onPressed, isNull);
    expect(find.byKey(const ValueKey('coverage-unknown')), findsOneWidget);
    expect(selections, hasLength(1));
  });

  testWidgets('standalone navigation reports country changes and back', (
    tester,
  ) async {
    final source = _fake();
    final visited = <String?>[];
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        displayLocale: 'zh-Hans',
        onCountryChanged: visited.add,
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('back-button')), findsNothing);

    await tester.tap(find.byKey(const ValueKey('country-cc:ZZ')));
    await tester.pumpAndSettle();
    expect(visited, <String?>['ZZ']);
    expect(find.byKey(const ValueKey('node-iso:ZZ-1')), findsOneWidget);
    expect(find.byKey(const ValueKey('back-button')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('back-button')));
    await tester.pumpAndSettle();
    expect(visited.last, isNull);
    expect(find.byKey(const ValueKey('country-cc:YY')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('availability badges follow the data source', (tester) async {
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: _fake(),
        countryCode: 'ZZ',
        displayLocale: 'zh-Hans',
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text(_zh.bundled), findsOneWidget);

    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: _fake(),
        countryCode: 'YY',
        displayLocale: 'zh-Hans',
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text(_zh.online), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('200 percent text scale keeps the controls usable', (
    tester,
  ) async {
    final source = _fake();
    await pumpPicker(
      tester,
      picker: GeoRegionPicker(
        dataSource: source,
        countryCode: 'ZZ',
        displayLocale: 'fr-FR',
      ),
      textScale: 2.0,
      size: const Size(390, 844),
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('node-iso:ZZ-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('node-iso:ZZ-1')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
      'cc:ZZ / iso:ZZ-1',
    );
    await tester.ensureVisible(find.byKey(const ValueKey('confirm-selection')));
    await tester.pumpAndSettle();
    expect(
      find.byKey(const ValueKey('confirm-selection')).hitTestable(),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
