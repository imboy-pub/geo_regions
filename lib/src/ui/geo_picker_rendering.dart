// SPDX-License-Identifier: BSD-3-Clause
// Rendering half of the geo_region_picker library: search field, breadcrumb,
// body states, rows, footer and skeleton. Part of `geo_region_picker.dart`
// so the state machine and its widgets share one private surface.
part of 'geo_region_picker.dart';

/// Rendering half of the picker state: search field, breadcrumb, body
/// states, rows, footer and badges. Kept in this part so the state machine
/// file stays under the size budget; `this` is the picker [State].
extension _GeoPickerRender on _GeoRegionPickerState {
  Widget _header(GeoPickerTheme pickerTheme) {
    final cc = widget.countryCode ?? _draftCountryCode();
    if (cc == null) {
      return const SizedBox.shrink();
    }
    final value = widget.dataSource.availabilityOf(cc);
    final scheme = Theme.of(context).colorScheme;
    final overridden = widget.countryBadgeBuilder?.call(cc, value);
    if (overridden != null) {
      return Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Wrap(children: <Widget>[overridden]),
      );
    }
    final text = switch (value) {
      GeoPickerAvailability.bundled => _labels.bundled,
      GeoPickerAvailability.cached => _labels.cached,
      GeoPickerAvailability.remote => _labels.online,
      GeoPickerAvailability.unknown => '',
    };
    if (text.isEmpty) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Wrap(
        children: <Widget>[
          _badge(
            text,
            value == GeoPickerAvailability.remote
                ? scheme.primary
                : pickerTheme.offlineToneOf(scheme),
            key: const ValueKey('availability-badge'),
          ),
        ],
      ),
    );
  }

  String? _draftCountryCode() {
    for (final item in _draft) {
      final cc = item.countryCode;
      if (cc != null) {
        return cc;
      }
    }
    return null;
  }

  Widget _searchField() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: TextField(
        key: const ValueKey('region-search'),
        controller: _search,
        enabled: _status != _GeoStatus.loading,
        onChanged: (_) => _runSearch(),
        decoration: InputDecoration(
          hintText: _labels.searchHint,
          prefixIcon: const Icon(Icons.search),
          suffixIcon: _search.text.isEmpty
              ? null
              : IconButton(
                  tooltip: _labels.clearSearch,
                  key: const ValueKey('clear-search'),
                  onPressed: () {
                    _search.clear();
                    _runSearch();
                  },
                  icon: const Icon(Icons.close),
                ),
        ),
      ),
    );
  }

  Widget _breadcrumb() {
    if (_draft.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Text(_labels.countries, key: const ValueKey('breadcrumb-root')),
      );
    }
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Wrap(
        crossAxisAlignment: WrapCrossAlignment.center,
        children: <Widget>[
          for (var i = 0; i < _draft.length; i++) ...<Widget>[
            if (i > 0)
              Icon(
                Directionality.of(context) == TextDirection.rtl
                    ? Icons.chevron_left
                    : Icons.chevron_right,
                size: 16,
              ),
            TextButton(
              key: ValueKey('breadcrumb-${_draft[i].nodeId}'),
              onPressed: i == _draft.length - 1 ? null : () => _truncateTo(i),
              child: Text(_draft[i].label),
            ),
          ],
        ],
      ),
    );
  }

  Widget _bodyArea(GeoPickerTheme pickerTheme) {
    switch (_status) {
      case _GeoStatus.loading:
        return _LoadingSkeleton(_labels.loading);
      case _GeoStatus.error:
        return _errorPanel(pickerTheme);
      case _GeoStatus.ready:
        return _readyBody(pickerTheme);
    }
  }

  Widget _readyBody(GeoPickerTheme pickerTheme) {
    if (_searching) {
      return _searchResults(pickerTheme);
    }
    if (_rows.isEmpty && _draft.isNotEmpty) {
      return _coverageState(pickerTheme, _draft.last);
    }
    if (_rows.isEmpty) {
      return _statePanel(
        pickerTheme,
        icon: Icons.search_off_outlined,
        text: _labels.noResults,
        hint: _labels.noResultsHint,
        panelKey: const ValueKey('no-results'),
      );
    }
    return _rowList(_rows, pickerTheme);
  }

  Widget _searchResults(GeoPickerTheme pickerTheme) {
    if (_searchBusy) {
      return const Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    if (_hits.isEmpty) {
      return _statePanel(
        pickerTheme,
        icon: Icons.search_off_outlined,
        text: _labels.noResults,
        hint: _labels.noResultsHint,
        panelKey: const ValueKey('no-results'),
      );
    }
    return _rowList(_hits, pickerTheme, subtitleFromPath: true);
  }

  Widget _coverageState(GeoPickerTheme pickerTheme, GeoPickerItem target) {
    if (target.childrenStatus == GeoChildrenStatus.unknown) {
      return _statePanel(
        pickerTheme,
        icon: Icons.help_outline,
        text: _labels.coverageUnknown,
        panelKey: const ValueKey('coverage-unknown'),
        live: true,
      );
    }
    return _statePanel(
      pickerTheme,
      icon: Icons.task_alt,
      text: _labels.noChildRegions,
      panelKey: const ValueKey('no-child-regions'),
    );
  }

  Widget _rowList(
    List<GeoPickerItem> items,
    GeoPickerTheme pickerTheme, {
    bool subtitleFromPath = false,
  }) {
    final countryOnly = widget.policy == GeoSelectionPolicy.countryOnly;
    return ListView.builder(
      shrinkWrap: !widget.expandBody,
      physics: widget.expandBody ? null : const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(vertical: 4),
      itemCount: items.length,
      itemBuilder: (context, index) =>
          _row(items[index], pickerTheme, countryOnly, subtitleFromPath),
    );
  }

  Widget _row(
    GeoPickerItem item,
    GeoPickerTheme pickerTheme,
    bool countryOnly,
    bool subtitleFromPath,
  ) {
    final enabled = !countryOnly;
    final info = GeoPickerRowInfo(
      enabled: enabled,
      isDraftTarget: _draftIds.contains(item.nodeId),
      onTap: enabled ? () => _activate(item, subtitleFromPath) : null,
    );
    final custom = widget.rowBuilder?.call(context, item, info);
    if (custom != null) {
      return custom;
    }
    final scheme = Theme.of(context).colorScheme;
    final rowKey = '${item.isCountryRoot ? 'country' : 'node'}-${item.nodeId}';
    return ListTile(
      key: ValueKey(rowKey),
      enabled: enabled,
      minVerticalPadding: 14,
      onTap: info.onTap,
      shape: RoundedRectangleBorder(borderRadius: pickerTheme.cardRadius),
      leading: Icon(
        item.isCountryRoot ? Icons.public : Icons.location_on_outlined,
        color: info.isDraftTarget ? pickerTheme.accentOf(scheme) : null,
      ),
      title: Text(item.label),
      subtitle: _rowSubtitle(item, subtitleFromPath),
      trailing: _rowTrailing(item, countryOnly),
    );
  }

  Widget? _rowSubtitle(GeoPickerItem item, bool subtitleFromPath) {
    if (subtitleFromPath && item.pathLabels != null) {
      return Text(item.pathLabels!.join(' / '));
    }
    return null;
  }

  Widget _rowTrailing(GeoPickerItem item, bool countryOnly) {
    if (countryOnly) {
      return const Icon(Icons.lock_outline, size: 18);
    }
    if (item.hasChildren) {
      return Icon(
        Directionality.of(context) == TextDirection.rtl
            ? Icons.chevron_left
            : Icons.chevron_right,
        size: 19,
      );
    }
    return const Icon(Icons.add_location_alt_outlined, size: 19);
  }

  void _activate(GeoPickerItem item, bool fromSearch) {
    if (fromSearch) {
      _selectHit(item);
      return;
    }
    _enter(item);
  }

  Widget _errorPanel(GeoPickerTheme pickerTheme) {
    final error = _error;
    final code = error is Exception ? error.runtimeType.toString() : 'error';
    return _statePanel(
      pickerTheme,
      icon: Icons.cloud_off_outlined,
      text: _labels.error,
      panelKey: const ValueKey('picker-error'),
      live: true,
      code: code,
      action: FilledButton.tonalIcon(
        key: const ValueKey('retry-button'),
        onPressed: () {
          final retry = _retry;
          if (retry == null) {
            _bootstrap();
            return;
          }
          _update(() => _status = _GeoStatus.loading);
          retry();
        },
        icon: const Icon(Icons.refresh),
        label: Text(_labels.retry),
      ),
    );
  }

  Widget _statePanel(
    GeoPickerTheme pickerTheme, {
    required IconData icon,
    required String text,
    required ValueKey<String> panelKey,
    String? hint,
    String? code,
    bool live = false,
    Widget? action,
  }) {
    final scheme = Theme.of(context).colorScheme;
    return SizedBox(
      width: double.infinity,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 12),
        child: Column(
          children: <Widget>[
            Icon(icon, size: 36, color: pickerTheme.accentOf(scheme)),
            const SizedBox(height: 12),
            Semantics(
              liveRegion: live,
              child: Text(text, key: panelKey, textAlign: TextAlign.center),
            ),
            ..._statePanelDetails(scheme, hint: hint, code: code),
            if (action != null) ...<Widget>[const SizedBox(height: 16), action],
          ],
        ),
      ),
    );
  }

  List<Widget> _statePanelDetails(
    ColorScheme scheme, {
    required String? hint,
    required String? code,
  }) {
    final onSurfaceVariant = scheme.onSurfaceVariant;
    return <Widget>[
      if (hint != null) ...<Widget>[
        const SizedBox(height: 6),
        Text(
          hint,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 13, color: onSurfaceVariant),
        ),
      ],
      if (code != null) ...<Widget>[
        const SizedBox(height: 8),
        Directionality(
          textDirection: TextDirection.ltr,
          child: Text(
            code,
            style: TextStyle(
              fontSize: 11,
              fontFamily: 'monospace',
              color: onSurfaceVariant,
            ),
          ),
        ),
      ],
    ];
  }

  Widget _footer(GeoPickerTheme pickerTheme) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[_footerHeading(), _footerActions(pickerTheme)],
      ),
    );
  }

  Widget _footerHeading() {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Wrap(
          spacing: 8,
          runSpacing: 6,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: <Widget>[
            Icon(Icons.route_outlined, size: 17, color: scheme.primary),
            Text(
              _labels.draft,
              style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
            ),
            if (_dirty && _draft.isNotEmpty)
              _badge(_labels.unsaved, scheme.primary),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          _draftLabels().isEmpty
              ? _labels.countries
              : _draftLabels().join(' / '),
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        if (_draft.isNotEmpty) ...<Widget>[
          const SizedBox(height: 6),
          Directionality(
            textDirection: TextDirection.ltr,
            child: Text(
              _draftIds.join(' / '),
              key: const ValueKey('draft-id'),
              style: TextStyle(
                fontSize: 11,
                fontFamily: 'monospace',
                color: scheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ],
    );
  }

  Widget _footerActions(GeoPickerTheme pickerTheme) {
    return Wrap(
      spacing: 10,
      runSpacing: 8,
      children: <Widget>[
        FilledButton.icon(
          key: const ValueKey('confirm-selection'),
          onPressed: _canConfirm ? _confirm : null,
          icon: _confirming
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.check, size: 18),
          label: Text(_labels.confirm),
        ),
        if (_draft.isNotEmpty)
          TextButton.icon(
            key: const ValueKey('back-button'),
            onPressed: _canBack ? _back : null,
            icon: const Icon(Icons.arrow_upward, size: 17),
            label: Text(_labels.back),
          ),
        if (_dirty && _draft.isNotEmpty)
          TextButton(
            key: const ValueKey('discard-button'),
            onPressed: _discard,
            child: Text(_labels.discard),
          ),
      ],
    );
  }

  List<String> _draftLabels() => <String>[
    for (final item in _draft) item.label,
  ];

  bool get _canBack =>
      _draft.length > 1 || (_draft.length == 1 && widget.countryCode == null);

  Widget _badge(String text, Color color, {ValueKey<String>? key}) {
    return Container(
      key: key,
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
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

class _LoadingSkeleton extends StatelessWidget {
  const _LoadingSkeleton(this.loadingText);

  final String loadingText;

  @override
  Widget build(BuildContext context) {
    final block = Theme.of(context).colorScheme.surfaceContainerHighest;
    return Column(
      key: const ValueKey('loading-skeleton'),
      children: <Widget>[
        _loadingCaption(context),
        for (var i = 0; i < 6; i++) _skeletonRow(block),
      ],
    );
  }

  Widget _loadingCaption(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 4),
      child: SizedBox(
        height: 18,
        child: Center(
          child: Semantics(
            liveRegion: true,
            child: Text(
              loadingText,
              style: TextStyle(
                fontSize: 12,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _skeletonRow(Color block) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
      child: Row(
        children: <Widget>[
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: block,
              borderRadius: BorderRadius.circular(18),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Container(
                  height: 13,
                  margin: const EdgeInsets.only(right: 48),
                  decoration: BoxDecoration(
                    color: block,
                    borderRadius: BorderRadius.circular(6),
                  ),
                ),
                const SizedBox(height: 7),
                Container(
                  height: 10,
                  margin: const EdgeInsets.only(right: 96),
                  decoration: BoxDecoration(
                    color: block,
                    borderRadius: BorderRadius.circular(5),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

bool _listEquals(List<String> a, List<String> b) {
  if (a.length != b.length) {
    return false;
  }
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) {
      return false;
    }
  }
  return true;
}
