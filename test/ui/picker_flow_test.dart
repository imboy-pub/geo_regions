// SPDX-License-Identifier: BSD-3-Clause
/// Picker flows over the real published dataset (P1-07).
///
/// Every test drives the default UI through [GeoRepositoryDataSource] backed
/// by the repository's own `data/` files, so the deep paths, search
/// disambiguation, quality filtering and coverage wording below are real
/// data contracts, not fixture stand-ins.
library;

import 'dart:io';

// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_kit.dart';

final _zh = GeoPickerLabels.forLocale('zh-Hans');

GeoRepositoryDataSource _source({
  bool optInProvisional = false,
  GeoCacheStore? store,
}) {
  return GeoRepositoryDataSource(
    realRepository(store: store),
    defaultLocale: 'en',
    optInProvisional: optInProvisional,
    bundledCountries: const <String>{'CN'},
  );
}

void main() {
  group('AT-01 responsive layout', () {
    for (final size in const <Size>[
      Size(390, 844),
      Size(768, 1024),
      Size(1280, 900),
    ]) {
      testWidgets('no layout exception at ${size.width}x${size.height}', (
        tester,
      ) async {
        await pumpPicker(tester, picker: realPicker(_source()), size: size);
        await tester.pumpAndSettle();
        expect(
          tester.takeException(),
          isNull,
          reason: 'layout exception at ${size.width}x${size.height}',
        );
        expect(find.byKey(const ValueKey('region-search')), findsOneWidget);
        expect(find.byKey(const ValueKey('confirm-selection')), findsOneWidget);
        expect(
          find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
          findsOneWidget,
        );
      });
    }
  });

  group('AT-02 deep navigation over real IDs', () {
    testWidgets(
      '中国→广东→深圳 keeps the root-inclusive draft and back clears deeper levels',
      (tester) async {
        final selections = <GeoSelection>[];
        await pumpPicker(
          tester,
          picker: realPicker(_source(), onConfirmed: selections.add),
        );
        await tester.pumpAndSettle();

        String draftId() =>
            tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data!;
        expect(draftId(), 'cc:CN');

        await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
        await tester.pumpAndSettle();
        expect(draftId(), 'cc:CN / iso3166-2:CN-GD');

        await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
        await tester.pumpAndSettle();
        expect(draftId(), 'cc:CN / iso3166-2:CN-GD / cn-stat:4403');
        // 深圳市 lists its districts, so the rows continue…
        expect(
          find.byKey(const ValueKey('node-cn-stat:440305')),
          findsOneWidget,
        );

        // …and an unknown-coverage district shows the honest state — never
        // "deepest level reached" (AT-11).
        await tester.tap(find.byKey(const ValueKey('node-cn-stat:440305')));
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('coverage-unknown')), findsOneWidget);
        expect(find.text(_zh.coverageUnknown), findsOneWidget);

        // Back clears the deeper draft level (UX-01)…
        await tester.tap(find.byKey(const ValueKey('back-button')));
        await tester.pumpAndSettle();
        expect(draftId(), 'cc:CN / iso3166-2:CN-GD / cn-stat:4403');
        expect(find.byKey(const ValueKey('coverage-unknown')), findsNothing);

        // …and the breadcrumb truncates to the tapped ancestor.
        await tester.tap(find.byKey(const ValueKey('breadcrumb-cc:CN')));
        await tester.pumpAndSettle();
        expect(draftId(), 'cc:CN');
        expect(
          find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
          findsOneWidget,
        );
        expect(tester.takeException(), isNull);
      },
    );

    testWidgets('confirming 深圳市 emits the protocol selection draft', (
      tester,
    ) async {
      final selections = <GeoSelection>[];
      await pumpPicker(
        tester,
        picker: realPicker(_source(), onConfirmed: selections.add),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
      await tester.pumpAndSettle();

      await tester.ensureVisible(
        find.byKey(const ValueKey('confirm-selection')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('confirm-selection')));
      await tester.pumpAndSettle();
      expect(selections, hasLength(1));
      final selection = selections.single;
      expect(selection.datasetId, 'geo-regions-seed');
      expect(selection.countryCode, 'CN');
      expect(selection.pathIds, <String>[
        'cc:CN',
        'iso3166-2:CN-GD',
        'cn-stat:4403',
      ]);
      expect(selection.displaySnapshot, <String>['中国', '广东省', '深圳市']);
      expect(selection.displayLocale, 'zh-Hans');

      // The same draft cannot be confirmed twice (duplicate-submit guard).
      expect(
        tester
            .widget<FilledButton>(
              find.byKey(const ValueKey('confirm-selection')),
            )
            .onPressed,
        isNull,
      );
    });

    testWidgets('discard restores the last confirmed snapshot', (tester) async {
      final selections = <GeoSelection>[];
      await pumpPicker(
        tester,
        picker: realPicker(_source(), onConfirmed: selections.add),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
      await tester.pumpAndSettle();
      await tester.ensureVisible(
        find.byKey(const ValueKey('confirm-selection')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('confirm-selection')));
      await tester.pumpAndSettle();

      // Navigate deeper, then discard.
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:440305')));
      await tester.pumpAndSettle();
      String draftId() =>
          tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data!;
      expect(
        draftId(),
        'cc:CN / iso3166-2:CN-GD / cn-stat:4403 / cn-stat:440305',
      );

      await tester.ensureVisible(find.byKey(const ValueKey('discard-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('discard-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(FilledButton, _zh.discard));
      await tester.pumpAndSettle();
      expect(draftId(), 'cc:CN / iso3166-2:CN-GD / cn-stat:4403');
      expect(find.byKey(const ValueKey('node-cn-stat:440305')), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('unknown coverage cannot be confirmed (allowIntermediate)', (
      tester,
    ) async {
      await pumpPicker(tester, picker: realPicker(_source()));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:440305')));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FilledButton>(
              find.byKey(const ValueKey('confirm-selection')),
            )
            .onPressed,
        isNull,
        reason: 'cn-stat:440305 has unknown coverage; unknown is never a leaf',
      );
    });
  });

  group('AT-02 search disambiguation', () {
    testWidgets('同名节点 carry full disambiguation paths (南山区 under 深圳 and 鹤岗)', (
      tester,
    ) async {
      await pumpPicker(tester, picker: realPicker(_source()));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey('region-search')),
        '南山区',
      );
      await tester.pumpAndSettle();

      final subtitles = tester
          .widgetList<Text>(
            find.descendant(
              of: find.byType(ListTile),
              matching: find.byType(Text),
            ),
          )
          .where((text) => text.data != null && text.data!.contains(' / '))
          .map((text) => text.data!)
          .toSet();
      expect(subtitles, hasLength(2), reason: 'two distinct 南山区 paths');
      expect(
        subtitles,
        containsAll(<String>['中国 / 广东省 / 深圳市 / 南山区', '中国 / 黑龙江省 / 鹤岗市 / 南山区']),
      );

      // Selecting a hit rebuilds the full draft path.
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:230404')));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
        'cc:CN / iso3166-2:CN-HL / cn-stat:2304 / cn-stat:230404',
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('empty search shows its own state and clearing restores rows', (
      tester,
    ) async {
      await pumpPicker(tester, picker: realPicker(_source()));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byKey(const ValueKey('region-search')),
        '不存在的地区',
      );
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('no-results')), findsOneWidget);
      expect(find.text(_zh.noResults), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('clear-search')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('no-results')), findsNothing);
      expect(
        find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
        findsOneWidget,
      );
    });
  });

  group('AT-02 countryOnly policy', () {
    testWidgets('intermediate nodes cannot be entered; the country confirms', (
      tester,
    ) async {
      final selections = <GeoSelection>[];
      await pumpPicker(
        tester,
        picker: realPicker(
          _source(),
          policy: GeoSelectionPolicy.countryOnly,
          onConfirmed: selections.add,
        ),
      );
      await tester.pumpAndSettle();

      String draftId() =>
          tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data!;
      expect(draftId(), 'cc:CN');

      // Region rows are rendered but locked: tapping must not navigate.
      expect(
        tester
            .widget<ListTile>(
              find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
            )
            .enabled,
        isFalse,
      );
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
      await tester.pumpAndSettle();
      expect(draftId(), 'cc:CN', reason: 'countryOnly must not enter regions');
      expect(find.byKey(const ValueKey('node-cn-stat:4403')), findsNothing);

      await tester.ensureVisible(
        find.byKey(const ValueKey('confirm-selection')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('confirm-selection')));
      await tester.pumpAndSettle();
      expect(selections, hasLength(1));
      expect(selections.single.pathIds, <String>['cc:CN']);
      expect(selections.single.displaySnapshot, <String>['中国']);
    });
  });

  group('AT-03 locale switching and RTL', () {
    testWidgets('switching display locale keeps the draft IDs stable', (
      tester,
    ) async {
      await pumpPicker(tester, picker: _LocaleSwitchHost(_source()));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-iso3166-2:CN-GD')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('node-cn-stat:4403')));
      await tester.pumpAndSettle();
      final before = tester
          .widget<Text>(find.byKey(const ValueKey('draft-id')))
          .data;

      await tester.tap(find.byKey(const ValueKey('locale-toggle')));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('draft-id'))).data,
        before,
        reason: 'language switch must not change selection identity (UX-02)',
      );
      expect(before, 'cc:CN / iso3166-2:CN-GD / cn-stat:4403');
    });

    testWidgets('Arabic mirrors layout while ID lines stay LTR', (
      tester,
    ) async {
      await pumpPicker(
        tester,
        picker: realPicker(_source(), displayLocale: 'ar-SA'),
        direction: TextDirection.rtl,
      );
      await tester.pumpAndSettle();
      expect(
        Directionality.of(
          tester.element(find.byKey(const ValueKey('region-search'))),
        ),
        TextDirection.rtl,
      );
      final draftElement = tester.element(
        find.byKey(const ValueKey('draft-id')),
      );
      expect(
        draftElement
            .getInheritedWidgetOfExactType<Directionality>()!
            .textDirection,
        TextDirection.ltr,
        reason: 'stable ID line stays LTR inside an RTL layout (UX-03)',
      );
      expect(
        find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
        findsOneWidget,
      );
    });
  });

  group('AT-14 quality filtering', () {
    testWidgets('provisional source name: ID shown without opt-in, name with', (
      tester,
    ) async {
      // zh-Hans pack still carries a reviewed (source-native) name.
      await pumpPicker(
        tester,
        picker: realPicker(
          GeoRepositoryDataSource(provisionalRepository(), defaultLocale: 'en'),
          displayLocale: 'zh-Hans',
        ),
      );
      await tester.pumpAndSettle();
      final zhRow = tester.widget<ListTile>(
        find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
      );
      expect(rowLabelText(zhRow.title), '广东省');

      // ar: provisional translation filtered, en fallback pack drops the
      // node, provisional source name filtered → the stable ID is the only
      // honest display (AT-14: never show the unreviewed name).
      await pumpPicker(
        tester,
        picker: realPicker(
          GeoRepositoryDataSource(provisionalRepository(), defaultLocale: 'en'),
          id: 'ar-filtered',
          displayLocale: 'ar-SA',
        ),
      );
      await tester.pumpAndSettle();
      final idRow = tester.widget<ListTile>(
        find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
      );
      final idLabel = rowLabelText(idRow.title)!;
      // The stable-ID fallback carries the honesty badge in the defaults.
      expect(idLabel.startsWith('iso3166-2:CN-GD'), isTrue);
      expect(idLabel.contains('غير مترجم'), isTrue);

      // With the explicit opt-in the provisional translation may be served
      // (hosts must label it tentative).
      await pumpPicker(
        tester,
        picker: realPicker(
          GeoRepositoryDataSource(
            provisionalRepository(),
            defaultLocale: 'en',
            optInProvisional: true,
          ),
          id: 'ar-opted-in',
          displayLocale: 'ar-SA',
        ),
      );
      await tester.pumpAndSettle();
      final optedRow = tester.widget<ListTile>(
        find.byKey(const ValueKey('node-iso3166-2:CN-GD')),
      );
      final optedLabel = rowLabelText(optedRow.title)!;
      expect(optedLabel.startsWith('غوانغدونغ'), isTrue);
      // Opted-in provisional names must be labeled tentative (AT-14).
      expect(optedLabel.contains('مبدئي'), isTrue);
    });
  });

  group('AT-15 naming discipline', () {
    test('UI sources carry no host-product references and import no demo', () {
      for (final dir in const <String>['lib/src/ui', 'test/ui']) {
        for (final file in Directory(dir).listSync(recursive: true)) {
          if (file is! File || !file.path.endsWith('.dart')) {
            continue;
          }
          final content = file.readAsStringSync().toLowerCase();
          expect(
            content.contains(
              'imb'
              'oy',
            ),
            isFalse,
            reason: '${file.path} must not name the host product (GR/AT-15)',
          );
          expect(
            content.contains(
              'geo_'
              'regions_demo',
            ),
            isFalse,
            reason: '${file.path} must not import the demo package',
          );
        }
      }
    });
  });
}

/// Host that switches the picker's display locale in place, mirroring the
/// demo app's language menu (same picker state, new locale).
class _LocaleSwitchHost extends StatefulWidget {
  const _LocaleSwitchHost(this.source);

  final GeoRegionDataSource source;

  @override
  State<_LocaleSwitchHost> createState() => _LocaleSwitchHostState();
}

class _LocaleSwitchHostState extends State<_LocaleSwitchHost> {
  String _locale = 'zh-Hans';

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        TextButton(
          key: const ValueKey('locale-toggle'),
          onPressed: () => setState(() => _locale = 'ja'),
          child: Text(_locale),
        ),
        GeoRegionPicker(
          dataSource: widget.source,
          countryCode: 'CN',
          displayLocale: _locale,
        ),
      ],
    );
  }
}
