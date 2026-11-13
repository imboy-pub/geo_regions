// SPDX-License-Identifier: BSD-3-Clause
// geo_regions interactive demo — production SDK edition (P1-07).
//
// The demo keeps the P1-01 visual structure (brand hero, country strip,
// search, breadcrumb, confirmation snapshot) while its data layer now runs
// the real SDK: generated offline assets for the bundled subset, a simulated
// CDN for everything else, SHA-256 verification, memory cache, typed errors.
// All region browsing, selection, draft and confirmation semantics live in
// the reusable `GeoRegionPicker`; the demo only adds chrome around it.
//
// No fixture namespace remains: selections carry the real `geo-regions-seed`
// dataset identity and its content revisions (UX-12).
import 'dart:convert';

// The demo builds its chrome on the Flutter SDK's own material library so
// the SDK picker (which keeps GR-12: no third-party runtime dependencies and
// therefore no material_ui import) runs against one coherent widget set.
// ignore_for_file: deprecated_member_use

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart' show SemanticsBinding;
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:geo_regions/geo_regions.dart';

import 'demo_copy.dart';
import 'sdk_data.dart';

/// Demo theme: project purple seed, both brightnesses (DEMO_UX §2).
ThemeData demoTheme(Brightness brightness) {
  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF6654D9),
      brightness: brightness,
    ),
    scaffoldBackgroundColor: brightness == Brightness.light
        ? const Color(0xFFF5F5F9)
        : const Color(0xFF14141D),
    inputDecorationTheme: const InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(14)),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(48, 48),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(minimumSize: const Size(48, 48)),
    ),
  );
}

void main() {
  // ?semantics=1 forces the semantics tree on for a11y acceptance runs.
  if (Uri.base.queryParameters['semantics'] == '1') {
    WidgetsFlutterBinding.ensureInitialized();
    SemanticsBinding.instance.ensureSemantics();
  }
  runApp(const GeoDemoApp());
}

class GeoDemoApp extends StatefulWidget {
  const GeoDemoApp({super.key, this.harness});

  /// Prebuilt harness for widget tests (the widget-test binding only
  /// delivers asset-channel replies during the first test of a process, so
  /// later tests mount the app with a preloaded harness).
  final DemoGeoHarness? harness;

  @override
  State<GeoDemoApp> createState() => _GeoDemoAppState();
}

class _GeoDemoAppState extends State<GeoDemoApp> {
  String locale = 'zh-Hans';
  bool dark = false;
  Future<DemoGeoHarness>? _harness;

  // Web deep links such as ?locale=ar&dark=1 make acceptance screenshots
  // reproducible without in-app navigation. Unknown values fall back to the
  // defaults, so tests and mobile runs keep the original initial state.
  @override
  void initState() {
    super.initState();
    final params = Uri.base.queryParameters;
    final askedLocale = params['locale'];
    if (askedLocale != null && demoLocaleTags.containsKey(askedLocale)) {
      locale = askedLocale;
    }
    dark = params['dark'] == '1';
    final provided = widget.harness;
    _harness = provided != null
        ? Future<DemoGeoHarness>.value(provided)
        : buildDemoHarness();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'geo_regions · Demo',
      debugShowCheckedModeBanner: false,
      // Framework copy (Material/Cupertino system strings) follows the
      // selected demo language via flutter_localizations; picker copy comes
      // from the SDK's ten-language label table and demo chrome from
      // demoWord().
      locale: demoLocaleTags[locale] ?? const Locale('en', 'US'),
      supportedLocales: demoLocaleTags.values.toList(),
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: demoTheme(Brightness.light),
      darkTheme: demoTheme(Brightness.dark),
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
      builder: (context, child) => Directionality(
        textDirection: locale == 'ar' ? TextDirection.rtl : TextDirection.ltr,
        child: child!,
      ),
      home: FutureBuilder<DemoGeoHarness>(
        future: _harness,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          return GeoPlayground(
            harness: snapshot.data!,
            locale: locale,
            dark: dark,
            onLocale: (value) => setState(() => locale = value),
            onDark: (value) => setState(() => dark = value),
          );
        },
      ),
    );
  }
}

class GeoPlayground extends StatefulWidget {
  const GeoPlayground({
    super.key,
    required this.harness,
    required this.locale,
    required this.dark,
    required this.onLocale,
    required this.onDark,
  });

  final DemoGeoHarness harness;
  final String locale;
  final bool dark;
  final ValueChanged<String> onLocale;
  final ValueChanged<bool> onDark;

  @override
  State<GeoPlayground> createState() => _GeoPlaygroundState();
}

class _GeoPlaygroundState extends State<GeoPlayground> {
  String countryCode = 'CN';
  GeoSelection? saved;
  List<GeoPickerItem>? countries;

  @override
  void initState() {
    super.initState();
    _refreshCountries();
  }

  @override
  void didUpdateWidget(GeoPlayground old) {
    super.didUpdateWidget(old);
    if (old.locale != widget.locale) {
      _refreshCountries();
    }
  }

  Future<void> _refreshCountries() async {
    final rows = await widget.harness.source.loadCountries(widget.locale);
    if (!mounted) {
      return;
    }
    setState(() => countries = rows);
  }

  void _openCountry(String code) {
    setState(() => countryCode = code);
    // Catalog data is already local; the refresh only re-reads the
    // availability knowledge the picker's loads just updated.
    _refreshCountries();
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 850;
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1216),
              child: Padding(
                padding: EdgeInsets.all(wide ? 32 : 18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    _topBar(),
                    SizedBox(height: wide ? 44 : 28),
                    _hero(wide),
                    const SizedBox(height: 24),
                    _controls(),
                    const SizedBox(height: 20),
                    if (wide)
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          SizedBox(width: 276, child: _countryPanel()),
                          const SizedBox(width: 24),
                          Expanded(child: _pickerColumn()),
                        ],
                      )
                    else ...<Widget>[
                      _countryStrip(),
                      const SizedBox(height: 16),
                      _pickerColumn(),
                    ],
                    const SizedBox(height: 24),
                    Center(
                      child: Text(
                        demoWord(widget.locale, 'preview'),
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 12,
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _topBar() {
    return SizedBox(
      width: double.infinity,
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 24,
        runSpacing: 12,
        children: <Widget>[_brandRow(), _settingsRow()],
      ),
    );
  }

  Widget _brandRow() {
    final colors = Theme.of(context).colorScheme;
    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 12,
      runSpacing: 8,
      children: <Widget>[
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: colors.primary,
            borderRadius: BorderRadius.circular(13),
          ),
          child: Icon(Icons.public, color: colors.onPrimary, size: 24),
        ),
        const Text(
          'geo_regions',
          style: TextStyle(
            fontSize: 21,
            fontWeight: FontWeight.w700,
            letterSpacing: -.5,
          ),
        ),
        _badge('SDK DEMO', colors.primary),
      ],
    );
  }

  Widget _settingsRow() {
    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 8,
      runSpacing: 8,
      children: <Widget>[
        Icon(
          Icons.translate,
          size: 20,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        Semantics(
          label: demoWord(widget.locale, 'language'),
          child: DropdownButton<String>(
            key: const ValueKey('locale-picker'),
            value: widget.locale,
            underline: const SizedBox.shrink(),
            items: <DropdownMenuItem<String>>[
              for (final key in demoLanguageNames.keys)
                DropdownMenuItem(
                  value: key,
                  child: Text(
                    demoLanguageNames[key]!,
                    key: ValueKey('locale-$key'),
                  ),
                ),
            ],
            onChanged: (value) {
              if (value != null) {
                widget.onLocale(value);
              }
            },
          ),
        ),
        Semantics(
          toggled: widget.dark,
          child: IconButton(
            tooltip: demoWord(widget.locale, 'dark'),
            onPressed: () => widget.onDark(!widget.dark),
            icon: Icon(
              widget.dark
                  ? Icons.light_mode_outlined
                  : Icons.dark_mode_outlined,
            ),
          ),
        ),
      ],
    );
  }

  Widget _hero(bool wide) {
    final colors = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          'GEO REGIONS / PLAYGROUND',
          style: TextStyle(
            color: colors.primary,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.6,
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          demoWord(widget.locale, 'heading'),
          style: TextStyle(
            fontSize: wide ? 40 : 29,
            fontWeight: FontWeight.w700,
            height: 1.25,
            letterSpacing: -1.0,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          demoWord(widget.locale, 'subtitle'),
          style: TextStyle(fontSize: 16, color: colors.onSurfaceVariant),
        ),
      ],
    );
  }

  Widget _controls() {
    final colors = Theme.of(context).colorScheme;
    final cdn = widget.harness.cdn;
    return Wrap(
      spacing: 12,
      runSpacing: 8,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: <Widget>[
        _badge('${widget.harness.datasetId}', colors.primary),
        _badge(
          '${countries?.length ?? 0} · ${demoWord(widget.locale, 'countries')}',
          colors.primary,
        ),
        _badge('CDN ${cdn.requests.length}', colors.onSurfaceVariant),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 280),
          child: MergeSemantics(
            child: Row(
              children: <Widget>[
                Switch(
                  key: const ValueKey('airplane-toggle'),
                  value: !cdn.online,
                  onChanged: (value) => setState(() => cdn.online = !value),
                ),
                const SizedBox(width: 8),
                Expanded(child: Text(demoWord(widget.locale, 'airplane'))),
              ],
            ),
          ),
        ),
        TextButton.icon(
          key: const ValueKey('simulate-failure'),
          onPressed: () => setState(() => cdn.failNext = true),
          icon: const Icon(Icons.cloud_off_outlined, size: 18),
          label: Text(demoWord(widget.locale, 'fail')),
        ),
      ],
    );
  }

  Widget _surface(Widget child) {
    final colors = Theme.of(context).colorScheme;
    return Material(
      color: colors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
        side: BorderSide(color: colors.outlineVariant),
      ),
      clipBehavior: Clip.antiAlias,
      child: child,
    );
  }

  Widget _countryPanel() {
    final rows = countries ?? const <GeoPickerItem>[];
    return _surface(
      Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.all(8),
              child: Text(
                demoWord(widget.locale, 'countries'),
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(height: 8),
            for (final row in rows)
              Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: _countryTile(row),
              ),
          ],
        ),
      ),
    );
  }

  Widget _countryTile(GeoPickerItem row) {
    final colors = Theme.of(context).colorScheme;
    final active = row.countryCode == countryCode;
    return Semantics(
      selected: active,
      child: Material(
        color: active ? colors.primaryContainer : colors.surface,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          key: ValueKey('country-${row.countryCode}'),
          borderRadius: BorderRadius.circular(12),
          onTap: () => _openCountry(row.countryCode!),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
            child: Row(
              children: <Widget>[
                Container(
                  width: 34,
                  height: 34,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: colors.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(9),
                  ),
                  child: Text(
                    row.countryCode ?? '',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    row.label,
                    style: TextStyle(
                      fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                    ),
                  ),
                ),
                Icon(
                  switch (row.availability) {
                    GeoPickerAvailability.bundled => Icons.offline_pin_outlined,
                    GeoPickerAvailability.cached => Icons.check_circle_outline,
                    _ => Icons.cloud_download_outlined,
                  },
                  size: 17,
                  color: active ? colors.primary : colors.onSurfaceVariant,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _countryStrip() {
    final rows = countries ?? const <GeoPickerItem>[];
    return SizedBox(
      height: 32 + MediaQuery.textScalerOf(context).scale(18),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: rows.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final row = rows[index];
          return ChoiceChip(
            key: ValueKey('country-${row.countryCode}'),
            selected: row.countryCode == countryCode,
            label: Text('${row.countryCode}  ${row.label}'),
            onSelected: (_) => _openCountry(row.countryCode!),
          );
        },
      ),
    );
  }

  Widget _pickerColumn() {
    return Column(
      children: <Widget>[
        _surface(
          Padding(
            padding: const EdgeInsets.all(20),
            child: GeoRegionPicker(
              dataSource: widget.harness.source,
              countryCode: countryCode,
              displayLocale: widget.locale,
              onConfirmed: (selection) => setState(() => saved = selection),
            ),
          ),
        ),
        if (saved != null) ...<Widget>[
          const SizedBox(height: 16),
          _snapshotCard(),
        ],
      ],
    );
  }

  Widget _snapshotCard() {
    final colors = Theme.of(context).colorScheme;
    return _surface(
      Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Icon(Icons.verified_outlined, color: colors.primary, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    demoWord(widget.locale, 'selected'),
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '${demoWord(widget.locale, 'dataset')}: ${saved!.datasetId} · ${saved!.dataRevision}',
              style: TextStyle(fontSize: 11, color: colors.onSurfaceVariant),
            ),
            const SizedBox(height: 12),
            Directionality(
              textDirection: TextDirection.ltr,
              child: SelectableText(
                const JsonEncoder.withIndent('  ').convert(saved!.toMap()),
                key: const ValueKey('selection-json'),
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: colors.onSurfaceVariant,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _badge(String text, Color color) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
