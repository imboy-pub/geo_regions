// SPDX-License-Identifier: BSD-3-Clause
import 'dart:convert';
import 'package:flutter/material.dart';
import 'fixtures.dart';

void main() => runApp(const GeoDemoApp());

class GeoDemoApp extends StatefulWidget {
  const GeoDemoApp({super.key});
  @override
  State<GeoDemoApp> createState() => _GeoDemoAppState();
}

class _GeoDemoAppState extends State<GeoDemoApp> {
  String locale = 'zh-Hans';
  bool dark = false;
  @override
  Widget build(BuildContext context) {
    ThemeData theme(Brightness brightness) => ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6654D9), brightness: brightness),
      scaffoldBackgroundColor: brightness == Brightness.light ? const Color(0xFFF5F5F9) : const Color(0xFF14141D),
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(14)))),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(minimumSize: const Size(48, 48), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)))),
      textButtonTheme: TextButtonThemeData(style: TextButton.styleFrom(minimumSize: const Size(48, 48))),
    );
    return MaterialApp(
      title: 'geo_regions · Demo',
      debugShowCheckedModeBanner: false,
      // Demo copy is injected independently of Flutter framework localization.
      // Keep built-in MaterialLocalizations on a supported SDK default locale.
      // System menus/stock accessibility copy remain English in this prototype.
      locale: const Locale('en', 'US'),
      supportedLocales: const [Locale('en', 'US')],
      theme: theme(Brightness.light),
      darkTheme: theme(Brightness.dark),
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
      builder: (context, child) => Directionality(textDirection: locale == 'ar' ? TextDirection.rtl : TextDirection.ltr, child: child!),
      home: GeoPlayground(
        locale: locale,
        dark: dark,
        onLocale: (value) => setState(() => locale = value),
        onDark: (value) => setState(() => dark = value),
      ),
    );
  }
}

class GeoPlayground extends StatefulWidget {
  const GeoPlayground({super.key, required this.locale, required this.dark, required this.onLocale, required this.onDark});
  final String locale;
  final bool dark;
  final ValueChanged<String> onLocale;
  final ValueChanged<bool> onDark;
  @override
  State<GeoPlayground> createState() => _GeoPlaygroundState();
}

class _GeoPlaygroundState extends State<GeoPlayground> {
  final search = TextEditingController();
  String countryCode = 'CN';
  List<String> path = [];
  final Set<String> cached = {};
  bool airplane = false;
  bool loading = false;
  bool failed = false;
  int generation = 0;
  Map<String, Object?>? saved;

  String tr(String key) => label(widget.locale, key);
  DemoCountry get country => countries.firstWhere((c) => c.code == countryCode);
  List<String> get ids => [country.rootId, ...path];
  bool get dirty => saved == null ? countryCode != 'CN' || path.isNotEmpty : jsonEncode(saved!['pathIds']) != jsonEncode(ids);
  bool get canConfirm => !loading && !failed && (saved == null || dirty);
  DemoNode node(String id) => nodes.firstWhere((n) => n.id == id);
  bool get bundled => countryCode == 'CN';
  ColorScheme get colors => Theme.of(context).colorScheme;
  Color get offlineColor => widget.dark ? const Color(0xFF8BD6B5) : const Color(0xFF247E61);

  @override
  void dispose() {
    generation++;
    search.dispose();
    super.dispose();
  }

  Future<void> loadCountry(String code) async {
    final token = ++generation;
    setState(() {
      countryCode = code;
      path = [];
      search.clear();
      loading = true;
      failed = false;
    });
    final available = code == 'CN' || cached.contains(code);
    await Future<void>.delayed(Duration(milliseconds: available ? 60 : 550));
    if (!mounted || token != generation) return;
    setState(() {
      loading = false;
      failed = !available && airplane;
      if (!failed && code != 'CN') cached.add(code);
    });
  }

  void selectNode(DemoNode value) {
    final ancestors = <String>[value.id];
    var cursor = value;
    while (cursor.parentId != country.rootId) {
      cursor = node(cursor.parentId);
      ancestors.insert(0, cursor.id);
    }
    setState(() {
      path = ancestors;
      search.clear();
    });
  }

  void confirm() {
    if (!canConfirm) return;
    setState(() {
      saved = <String, Object?>{
        'datasetId': 'geo-regions-ui-fixture',
        'countryCode': countryCode,
        'pathIds': List<String>.of(ids),
        'dataRevision': 'fixture-1',
      };
    });
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(tr('selected')), duration: const Duration(seconds: 2)));
  }

  Future<void> discard() async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(tr('discardTitle')),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(tr('cancel'))),
          FilledButton(onPressed: () => Navigator.of(context).pop(true), child: Text(tr('discard'))),
        ],
      ),
    );
    if (accepted != true || !mounted) return;
    generation++;
    setState(() {
      countryCode = saved?['countryCode'] as String? ?? 'CN';
      path = saved == null ? [] : (saved!['pathIds'] as List<String>).skip(1).toList();
      search.clear();
      loading = false;
      failed = false;
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: LayoutBuilder(builder: (context, constraints) {
        final wide = constraints.maxWidth >= 850;
        return SingleChildScrollView(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1216),
              child: Padding(
                padding: EdgeInsets.all(wide ? 32 : 18),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  topBar(),
                  SizedBox(height: wide ? 48 : 32),
                  Text('GEO REGIONS / PLAYGROUND', style: TextStyle(color: colors.primary, fontWeight: FontWeight.w700, letterSpacing: 1.6, fontSize: 11)),
                  const SizedBox(height: 12),
                  Text(tr('heading'), style: TextStyle(fontSize: wide ? 40 : 29, fontWeight: FontWeight.w700, height: 1.25, letterSpacing: -1.0)),
                  const SizedBox(height: 10),
                  Text(tr('subtitle'), style: TextStyle(fontSize: 16, color: colors.onSurfaceVariant)),
                  const SizedBox(height: 28),
                  controls(),
                  const SizedBox(height: 24),
                  if (wide)
                    Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      SizedBox(width: 276, child: countryPanel()),
                      const SizedBox(width: 24),
                      Expanded(child: selectionPanel()),
                    ])
                  else ...[
                    countryStrip(),
                    const SizedBox(height: 16),
                    selectionPanel(),
                  ],
                  const SizedBox(height: 24),
                  Center(child: Text(tr('preview'), textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: colors.onSurfaceVariant))),
                  const SizedBox(height: 16),
                ]),
              ),
            ),
          ),
        );
      }),
    ),
  );

  Widget topBar() => SizedBox(
    width: double.infinity,
    child: Wrap(
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 24,
      runSpacing: 12,
      children: [
        Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 12, runSpacing: 8, children: [
          Container(width: 40, height: 40, decoration: BoxDecoration(color: colors.primary, borderRadius: BorderRadius.circular(13)), child: Icon(Icons.public, color: colors.onPrimary, size: 24)),
          const Text('geo_regions', style: TextStyle(fontSize: 21, fontWeight: FontWeight.w700, letterSpacing: -.5)),
          badge('DEMO', colors.primary),
        ]),
        Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 8, runSpacing: 8, children: [
          Icon(Icons.translate, size: 20, color: colors.onSurfaceVariant),
          Semantics(label: tr('language'), child: DropdownButton<String>(
            key: const ValueKey('locale-picker'),
            value: widget.locale,
            underline: const SizedBox.shrink(),
            items: locales.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value, key: ValueKey('locale-${e.key}')))).toList(),
            onChanged: (value) { if (value != null) widget.onLocale(value); },
          )),
          Semantics(toggled: widget.dark, child: IconButton(tooltip: tr('dark'), onPressed: () => widget.onDark(!widget.dark), icon: Icon(widget.dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined))),
        ]),
      ],
    ),
  );

  Widget controls() => Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
    badge('10 ${tr('countries')}', colors.primary),
    badge('10 ${tr('language')}', colors.primary),
    ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 280),
      child: MergeSemantics(child: Row(children: [
        Switch(key: const ValueKey('airplane-toggle'), value: airplane, onChanged: (v) => setState(() => airplane = v)),
        const SizedBox(width: 8),
        Expanded(child: Text(tr('airplane'))),
      ])),
    ),
    TextButton.icon(
      key: const ValueKey('simulate-failure'),
      onPressed: () { generation++; setState(() { loading = false; failed = true; }); },
      icon: const Icon(Icons.cloud_off_outlined, size: 18),
      label: Text(tr('fail')),
    ),
  ]);

  Widget surface(Widget child) => Container(
    decoration: BoxDecoration(color: colors.surface, borderRadius: BorderRadius.circular(22), border: Border.all(color: colors.outlineVariant)),
    clipBehavior: Clip.antiAlias,
    child: child,
  );

  Widget countryPanel() => surface(Padding(
    padding: const EdgeInsets.all(16),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(padding: const EdgeInsets.all(8), child: Text(tr('countries'), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600))),
      const SizedBox(height: 8),
      ...countries.map((c) => Padding(padding: const EdgeInsets.only(bottom: 5), child: countryTile(c))),
    ]),
  ));

  Widget countryTile(DemoCountry value) {
    final active = value.code == countryCode;
    return Semantics(selected: active, child: Material(
      color: active ? colors.primaryContainer : colors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        key: ValueKey('country-${value.code}'),
        borderRadius: BorderRadius.circular(12),
        onTap: () => loadCountry(value.code),
        child: Padding(padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10), child: Row(children: [
          Container(width: 34, height: 34, alignment: Alignment.center, decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(9)), child: Text(value.code, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700))),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(value.name(widget.locale), style: TextStyle(fontWeight: active ? FontWeight.w700 : FontWeight.w500)),
            Text(value.nativeName, style: TextStyle(fontSize: 11, color: colors.onSurfaceVariant)),
          ])),
          Icon(value.code == 'CN' ? Icons.offline_pin_outlined : cached.contains(value.code) ? Icons.check_circle_outline : Icons.cloud_download_outlined, size: 17, color: active ? colors.primary : colors.onSurfaceVariant),
        ])),
      ),
    ));
  }

  Widget countryStrip() => SizedBox(height: 32 + MediaQuery.textScalerOf(context).scale(18), child: ListView.separated(
    scrollDirection: Axis.horizontal,
    itemCount: countries.length,
    separatorBuilder: (_, i) => const SizedBox(width: 8),
    itemBuilder: (context, index) {
      final c = countries[index];
      return ChoiceChip(key: ValueKey('country-${c.code}'), selected: countryCode == c.code, label: Text('${c.code}  ${c.name(widget.locale)}'), onSelected: (_) => loadCountry(c.code));
    },
  ));

  Widget selectionPanel() => Column(children: [
    surface(Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(padding: const EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
          Text(tr('choose'), style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w700)),
          badge(tr(bundled ? 'offline' : cached.contains(countryCode) ? 'cached' : 'online'), bundled ? offlineColor : colors.primary),
          badge(tr('sample'), colors.onSurfaceVariant),
        ]),
        const SizedBox(height: 18),
        TextField(
          key: const ValueKey('region-search'),
          controller: search,
          enabled: !loading && !failed,
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(hintText: tr('search'), prefixIcon: const Icon(Icons.search), suffixIcon: search.text.isEmpty ? null : IconButton(tooltip: tr('clear'), onPressed: () => setState(search.clear), icon: const Icon(Icons.close))),
        ),
        const SizedBox(height: 12),
        Wrap(crossAxisAlignment: WrapCrossAlignment.center, children: [
          TextButton(onPressed: loading || failed ? null : () => setState(() { path = []; search.clear(); }), child: Text(country.name(widget.locale))),
          for (var i = 0; i < path.length; i++) ...[
            Icon(widget.locale == 'ar' ? Icons.chevron_left : Icons.chevron_right, size: 16),
            TextButton(onPressed: () => setState(() { path = path.take(i + 1).toList(); search.clear(); }), child: Text(node(path[i]).name(widget.locale))),
          ],
        ]),
      ])),
      Divider(height: 1, color: colors.outlineVariant),
      AnimatedSize(duration: const Duration(milliseconds: 180), alignment: Alignment.topCenter, child: Padding(padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12), child: regionBody())),
      Divider(height: 1, color: colors.outlineVariant),
      Padding(padding: const EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 8, runSpacing: 8, children: [
          Icon(Icons.route_outlined, size: 17, color: colors.primary),
          Text(tr('draft'), style: TextStyle(fontSize: 12, color: colors.onSurfaceVariant)),
          if (dirty) badge(tr('unsaved'), colors.primary),
        ]),
        const SizedBox(height: 10),
        Text([country.name(widget.locale), ...path.map((id) => node(id).name(widget.locale))].join(' / '), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        Directionality(textDirection: TextDirection.ltr, child: Text(ids.join(' / '), key: const ValueKey('draft-id'), style: TextStyle(fontSize: 11, color: colors.onSurfaceVariant))),
        const SizedBox(height: 20),
        Wrap(spacing: 10, runSpacing: 8, children: [
          FilledButton.icon(key: const ValueKey('confirm-selection'), onPressed: canConfirm ? confirm : null, icon: const Icon(Icons.check, size: 18), label: Text(tr('confirm'))),
          if (path.isNotEmpty) TextButton.icon(onPressed: loading || failed ? null : () => setState(() { path.removeLast(); search.clear(); }), icon: const Icon(Icons.arrow_upward, size: 17), label: Text(tr('back'))),
          if (dirty) TextButton(onPressed: discard, child: Text(tr('discard'))),
        ]),
      ])),
    ])),
    if (saved != null) ...[
      const SizedBox(height: 16),
      surface(Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [Icon(Icons.verified_outlined, color: offlineColor, size: 20), const SizedBox(width: 8), Expanded(child: Text(tr('selected'), style: const TextStyle(fontWeight: FontWeight.w600)))]),
        const SizedBox(height: 12),
        Directionality(textDirection: TextDirection.ltr, child: SelectableText(const JsonEncoder.withIndent('  ').convert(saved), key: const ValueKey('selection-json'), style: TextStyle(fontFamily: 'monospace', fontSize: 12, color: colors.onSurfaceVariant))),
      ]))),
    ],
  ]);

  Widget regionBody() {
    if (loading) return statePanel(Icons.hourglass_top, tr('loading'), null, progress: true);
    if (failed) return statePanel(Icons.cloud_off_outlined, tr('error'), FilledButton.tonalIcon(key: const ValueKey('retry-button'), onPressed: () => loadCountry(countryCode), icon: const Icon(Icons.refresh), label: Text(tr('retry'))));
    final query = search.text.trim().toLowerCase();
    final currentParent = path.isEmpty ? country.rootId : path.last;
    final visible = nodes.where((n) => n.countryCode == countryCode && (query.isEmpty ? n.parentId == currentParent : '${n.name(widget.locale)} ${n.nativeName} ${n.id} ${n.names.values.join(' ')}'.toLowerCase().contains(query))).toList();
    if (visible.isEmpty) return statePanel(query.isEmpty ? Icons.task_alt : Icons.search_off_outlined, tr(query.isEmpty ? 'deepest' : 'empty'), query.isEmpty ? null : Text(tr('emptyHint'), textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: colors.onSurfaceVariant)));
    return Column(children: visible.map((n) => ListTile(
      key: ValueKey('node-${n.id}'),
      minVerticalPadding: 14,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      leading: CircleAvatar(backgroundColor: colors.surfaceContainerHighest, foregroundColor: colors.primary, radius: 18, child: const Icon(Icons.location_on_outlined, size: 18)),
      title: Text(n.name(widget.locale), style: const TextStyle(fontWeight: FontWeight.w500)),
      subtitle: Text(n.id, style: TextStyle(fontSize: 11, color: colors.onSurfaceVariant)),
      trailing: Icon(nodes.any((child) => child.parentId == n.id) ? (widget.locale == 'ar' ? Icons.chevron_left : Icons.chevron_right) : Icons.add_location_alt_outlined, size: 19),
      onTap: () => selectNode(n),
    )).toList());
  }

  Widget statePanel(IconData icon, String title, Widget? action, {bool progress = false}) => SizedBox(
    width: double.infinity,
    child: Padding(padding: const EdgeInsets.symmetric(vertical: 42, horizontal: 12), child: Column(children: [
      if (progress) const SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 2)) else Icon(icon, size: 38, color: colors.primary),
      const SizedBox(height: 16),
      Semantics(liveRegion: true, child: Text(title, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w500))),
      if (action != null) ...[const SizedBox(height: 16), action],
    ])),
  );

  Widget badge(String text, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
    decoration: BoxDecoration(color: colors.surfaceContainerHighest, borderRadius: BorderRadius.circular(8)),
    child: Text(text, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: color)),
  );
}
