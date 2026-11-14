// SPDX-License-Identifier: BSD-3-Clause
/// Reusable region picker with a default UI decoupled from the data entry
/// (P1-07, DEMO_UX state matrix).
///
/// [GeoRegionPicker] renders the DEMO_UX interaction core — search field,
/// root-inclusive breadcrumb, row list with loading/empty/error/offline
/// states, draft path with confirm/discard — over any [GeoRegionDataSource].
/// It never persists anything: confirming emits the draft [GeoSelection] to
/// the host, which owns the backend transaction, the account cache and the
/// navigation (PROTOCOL §8).
///
/// Accessibility: every control is reachable through semantics, status text
/// is exposed as live regions, row targets stay above the 44 px floor, and
/// stable-ID lines stay LTR inside RTL layouts (UX-03/10).
library;

// GR-12 keeps the main package free of third-party runtime dependencies, so
// the default UI builds on the Flutter SDK's own material library even where
// a newer Flutter deprecates that import in favor of a host-chosen package.
// Hosts on the replacement package can restyle everything through
// GeoPickerTheme and the row/badge builders.
// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';

import '../models.dart';
import 'geo_picker_data.dart';
import 'geo_picker_labels.dart';
import 'geo_picker_theme.dart';

part 'geo_picker_rendering.dart';

/// Optional row renderer; return `null` to keep the default row.
typedef GeoPickerRowBuilder = Widget? Function(
  BuildContext context,
  GeoPickerItem item,
  GeoPickerRowInfo info,
);

/// What the default row needs to know about the current state.
class GeoPickerRowInfo {
  /// Creates row info.
  const GeoPickerRowInfo({
    required this.enabled,
    required this.isDraftTarget,
    required this.onTap,
  });

  /// Whether the row can be activated at all (policy/search state).
  final bool enabled;

  /// Whether the row is the current draft target.
  final bool isDraftTarget;

  /// Activation callback; `null` when disabled.
  final VoidCallback? onTap;
}

enum _GeoStatus { loading, ready, error }

/// Default region picker UI over a [GeoRegionDataSource].
class GeoRegionPicker extends StatefulWidget {
  /// Creates a picker.
  ///
  /// [countryCode] pins browsing to one country (the host owns the country
  /// switcher, as in the demo); `null` lets the picker start from the
  /// country screen. [policy] governs what may be confirmed. [labels] and
  /// [theme] default to the ten-language table and the ambient Material
  /// theme. [rowBuilder] and [countryBadgeBuilder] override row rendering.
  const GeoRegionPicker({
    required this.dataSource,
    this.displayLocale = 'en',
    this.countryCode,
    this.policy = GeoSelectionPolicy.allowIntermediate,
    this.labels,
    this.theme,
    this.rowBuilder,
    this.countryBadgeBuilder,
    this.onConfirmed,
    this.onCountryChanged,
    this.expandBody = false,
    super.key,
  });

  /// Data entry; see [GeoRegionDataSource].
  final GeoRegionDataSource dataSource;

  /// UI locale for name resolution (e.g. `zh-CN`, `ar-SA`).
  final String displayLocale;

  /// Pinned country, or `null` for the standalone country screen.
  final String? countryCode;

  /// What the picker may confirm.
  final GeoSelectionPolicy policy;

  /// Copy overrides; defaults to the built-in ten-language table.
  final GeoPickerLabels? labels;

  /// Visual tokens; defaults to a derivation of the ambient theme.
  final GeoPickerTheme? theme;

  /// Row renderer override.
  final GeoPickerRowBuilder? rowBuilder;

  /// Availability badge override; return `null` for the default badge.
  final Widget? Function(String countryCode, GeoPickerAvailability value)?
  countryBadgeBuilder;

  /// Called with the draft selection after a successful confirm. The host
  /// submits it to its backend and only then commits and navigates (§8).
  final ValueChanged<GeoSelection>? onConfirmed;

  /// Standalone mode only: country the picker is browsing.
  final ValueChanged<String?>? onCountryChanged;

  /// When true the picker fills its height and scrolls its body internally;
  /// when false the body shrink-wraps for embedding in host scroll views.
  final bool expandBody;

  @override
  State<GeoRegionPicker> createState() => _GeoRegionPickerState();
}

class _GeoRegionPickerState extends State<GeoRegionPicker> {
  _GeoStatus _status = _GeoStatus.loading;
  Object? _error;
  bool _confirming = false;
  List<GeoPickerItem> _rows = const <GeoPickerItem>[];
  List<GeoPickerItem> _draft = const <GeoPickerItem>[];
  GeoSelection? _confirmed;
  GeoPickerItem? _confirmedTarget;
  final TextEditingController _search = TextEditingController();
  List<GeoPickerItem> _hits = const <GeoPickerItem>[];
  bool _searchBusy = false;
  int _generation = 0;
  Future<void> Function()? _retry;

  GeoPickerLabels get _labels =>
      widget.labels ?? GeoPickerLabels.forLocale(widget.displayLocale);
  bool get _searching => _search.text.trim().isNotEmpty;
  bool get _dirty =>
      _confirmed == null || !_listEquals(_draftIds, _confirmed!.pathIds);

  List<String> get _draftIds => <String>[
    for (final item in _draft) item.nodeId,
  ];

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void didUpdateWidget(GeoRegionPicker old) {
    super.didUpdateWidget(old);
    if (old.countryCode != widget.countryCode) {
      _bootstrap();
    } else if (old.displayLocale != widget.displayLocale) {
      _refreshLocale();
    }
  }

  @override
  void dispose() {
    _generation++;
    _search.dispose();
    super.dispose();
  }

  void _bootstrap() {
    final token = ++_generation;
    _search.clear();
    _hits = const <GeoPickerItem>[];
    _draft = const <GeoPickerItem>[];
    _confirmed = null;
    _confirmedTarget = null;
    setState(() {
      _status = _GeoStatus.loading;
      _error = null;
    });
    final pinned = widget.countryCode;
    if (pinned != null) {
      _openCountry(token, pinned);
    } else {
      _openCountries(token);
    }
  }

  Future<void> _openCountries(int token) async {
    _retry = () => _openCountries(++_generation);
    try {
      final rows = await widget.dataSource.loadCountries(widget.displayLocale);
      if (!_accept(token)) {
        return;
      }
      setState(() {
        _status = _GeoStatus.ready;
        _rows = rows;
      });
    } on Object catch (error) {
      _fail(token, error);
    }
  }

  Future<void> _openCountry(int token, String countryCode) async {
    _retry = () => _openCountry(++_generation, countryCode);
    try {
      final content = await widget.dataSource.openCountry(
        countryCode,
        widget.displayLocale,
      );
      if (!_accept(token)) {
        return;
      }
      setState(() {
        _status = _GeoStatus.ready;
        _draft = <GeoPickerItem>[content.root];
        _rows = content.children;
      });
    } on Object catch (error) {
      _fail(token, error);
    }
  }

  Future<void> _loadChildrenOf(GeoPickerItem item) async {
    final token = ++_generation;
    _retry = () => _loadChildrenOf(item);
    final cc = item.countryCode ?? _ccOf(item.nodeId);
    try {
      final rows = await widget.dataSource.loadChildren(
        cc,
        item.nodeId,
        widget.displayLocale,
      );
      if (!_accept(token)) {
        return;
      }
      setState(() {
        _status = _GeoStatus.ready;
        _rows = rows;
      });
    } on Object catch (error) {
      _fail(token, error);
    }
  }

  void _enter(GeoPickerItem item) {
    if (widget.policy == GeoSelectionPolicy.countryOnly) {
      setState(() {
        _status = _GeoStatus.ready;
        _draft = <GeoPickerItem>[item];
      });
      widget.onCountryChanged?.call(item.countryCode ?? _ccOf(item.nodeId));
      return;
    }
    widget.onCountryChanged?.call(item.countryCode ?? _ccOf(item.nodeId));
    setState(() {
      _status = _GeoStatus.ready;
      _draft = <GeoPickerItem>[..._draft, item];
      _rows = const <GeoPickerItem>[];
    });
    if (item.hasChildren) {
      _loadChildrenOf(item);
    }
  }

  void _back() {
    if (_draft.isEmpty) {
      return;
    }
    if (_draft.length == 1 && widget.countryCode == null) {
      widget.onCountryChanged?.call(null);
      final token = ++_generation;
      setState(() {
        _status = _GeoStatus.loading;
        _draft = const <GeoPickerItem>[];
      });
      _openCountries(token);
      return;
    }
    if (_draft.length == 1) {
      return;
    }
    setState(() => _draft = _draft.sublist(0, _draft.length - 1));
    _loadChildrenOf(_draft.last);
  }

  void _truncateTo(int depth) {
    if (depth >= _draft.length - 1) {
      return;
    }
    setState(() => _draft = _draft.sublist(0, depth + 1));
    _loadChildrenOf(_draft.last);
  }

  Future<void> _runSearch() async {
    final token = ++_generation;
    final query = _search.text.trim();
    _retry = _runSearch;
    if (query.isEmpty) {
      setState(() {
        _status = _GeoStatus.ready;
        _hits = const <GeoPickerItem>[];
        _searchBusy = false;
      });
      return;
    }
    setState(() => _searchBusy = true);
    try {
      final hits = await widget.dataSource.search(query, widget.displayLocale);
      if (!_accept(token)) {
        return;
      }
      setState(() {
        _status = _GeoStatus.ready;
        _searchBusy = false;
        _hits = hits;
      });
    } on Object catch (error) {
      _fail(token, error);
    }
  }

  void _selectHit(GeoPickerItem hit) {
    final labels = hit.pathLabels ?? const <String>[];
    final path = hit.pathIds;
    final ancestors = <GeoPickerItem>[
      for (var i = 0; i < path.length - 1; i++)
        _labelOnlyItem(path[i], labels.isEmpty ? path[i] : labels[i], hit),
    ];
    setState(() {
      _status = _GeoStatus.ready;
      _draft = <GeoPickerItem>[...ancestors, hit];
      _search.clear();
      _hits = const <GeoPickerItem>[];
    });
    if (hit.hasChildren) {
      _loadChildrenOf(hit);
    }
  }

  GeoPickerItem _labelOnlyItem(String id, String label, GeoPickerItem like) {
    return GeoPickerItem(
      nodeId: id,
      label: label,
      countryCode: like.countryCode ?? _ccOf(id),
      isCountryRoot: id.startsWith('cc:'),
      hasChildren: true,
    );
  }

  Future<void> _confirm() async {
    if (!_canConfirm) {
      return;
    }
    final token = _generation;
    setState(() => _confirming = true);
    _retry = _confirm;
    try {
      final selection = await widget.dataSource.resolveSelection(
        _draftIds,
        policy: widget.policy,
        displayLocale: widget.displayLocale,
      );
      if (!_accept(token)) {
        return;
      }
      setState(() {
        _confirming = false;
        _confirmed = selection;
        _confirmedTarget = _draft.last;
      });
      widget.onConfirmed?.call(selection);
    } on Object catch (error) {
      _fail(token, error);
    }
  }

  Future<void> _discard() async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(_labels.discardTitle),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(_labels.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(_labels.discard),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted) {
      return;
    }
    final confirmed = _confirmed;
    final target = _confirmedTarget;
    if (confirmed == null) {
      _bootstrap();
      return;
    }
    final ids = confirmed.pathIds;
    final snapshot = confirmed.displaySnapshot ?? const <String>[];
    final rebuilt = <GeoPickerItem>[
      for (var i = 0; i < ids.length; i++)
        if (i == ids.length - 1 && target != null)
          target
        else
          GeoPickerItem(
            nodeId: ids[i],
            label: i < snapshot.length ? snapshot[i] : ids[i],
            countryCode: _ccOf(ids.first),
            isCountryRoot: i == 0,
            hasChildren: i < ids.length - 1,
          ),
    ];
    setState(() {
      _draft = rebuilt;
      _confirmed = confirmed;
      _confirmedTarget = target;
    });
    _loadChildrenOf(rebuilt.last);
  }

  Future<void> _refreshLocale() async {
    final token = ++_generation;
    try {
      final ids = _draftIds;
      if (ids.isEmpty) {
        await _openCountries(token);
        return;
      }
      final labels = await widget.dataSource.resolveLabels(
        ids,
        widget.displayLocale,
      );
      if (!_accept(token)) {
        return;
      }
      setState(() {
        _draft = <GeoPickerItem>[
          for (final item in _draft)
            labels.containsKey(item.nodeId)
                ? item.copyWith(
                    label: labels[item.nodeId]!.text,
                    labelIsFallback: labels[item.nodeId]!.isFallback,
                    labelIsProvisional: labels[item.nodeId]!.isProvisional,
                  )
                : item,
        ];
      });
      if (_draft.isNotEmpty) {
        await _loadChildrenOf(_draft.last);
      }
      if (_searching) {
        await _runSearch();
      }
    } on Object catch (error) {
      _fail(token, error);
    }
  }

  bool get _canConfirm {
    if (_status != _GeoStatus.ready || _confirming || _draft.isEmpty) {
      return false;
    }
    if (!_dirty) {
      return false;
    }
    return _policyAllows(_draft.last);
  }

  bool _policyAllows(GeoPickerItem target) => switch (widget.policy) {
    GeoSelectionPolicy.countryOnly => _draft.length == 1,
    GeoSelectionPolicy.allowIntermediate =>
      target.isCountryRoot ||
          target.childrenStatus != GeoChildrenStatus.unknown,
    GeoSelectionPolicy.requireLeafWithinDeclared =>
      target.isCountryRoot ||
          (target.childrenStatus == GeoChildrenStatus.complete &&
              !target.hasChildren),
  };

  bool _accept(int token) {
    if (token != _generation) {
      return false;
    }
    return true;
  }

  void _fail(int token, Object error) {
    if (token != _generation) {
      return;
    }
    setState(() {
      _status = _GeoStatus.error;
      _error = error;
      _searchBusy = false;
      _confirming = false;
    });
  }

  String _ccOf(String nodeId) => nodeId.substring(3);

  /// setState wrapper for the rendering extension (protected member lint).
  void _update(VoidCallback fn) => setState(fn);

  @override
  Widget build(BuildContext context) {
    final pickerTheme =
        widget.theme ?? GeoPickerTheme.fromTheme(Theme.of(context));
    return Column(
      mainAxisSize: widget.expandBody ? MainAxisSize.max : MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        _header(pickerTheme),
        _searchField(),
        _breadcrumb(),
        const Divider(height: 1),
        if (widget.expandBody)
          Expanded(child: _bodyArea(pickerTheme))
        else
          _bodyArea(pickerTheme),
        const Divider(height: 1),
        _footer(pickerTheme),
      ],
    );
  }
}
