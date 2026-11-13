// SPDX-License-Identifier: BSD-3-Clause
/// Visual tokens for the default picker UI (P1-07).
///
/// [GeoPickerTheme] carries only what the picker needs to stay readable in
/// both Material themes and at 200% text scale (DEMO_UX UX-10/11): an accent,
/// an offline/success tone, a minimum interactive height and card shaping.
/// Everything else derives from the ambient `ThemeData`, so the picker adapts
/// to the host design system without a second source of truth.
library;

// GR-12 keeps the main package free of third-party runtime dependencies, so
// the default UI builds on the Flutter SDK's own material library even where
// a newer Flutter deprecates that import in favor of a host-chosen package.
// Hosts on the replacement package can restyle everything through
// [GeoPickerTheme] and the picker's row/badge builders.
// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';

/// Density and color overrides for [GeoRegionPicker]-family widgets.
class GeoPickerTheme {
  /// Creates tokens; every field is nullable so `null` means "derive from the
  /// ambient Material theme".
  const GeoPickerTheme({
    this.accent,
    this.offlineTone,
    this.rowMinHeight = 48,
    this.cardRadius = const BorderRadius.all(Radius.circular(14)),
    this.sectionSpacing = 12,
  });

  /// Derives a theme from the ambient [theme].
  factory GeoPickerTheme.fromTheme(ThemeData theme) {
    final scheme = theme.colorScheme;
    return GeoPickerTheme(
      accent: scheme.primary,
      offlineTone: scheme.brightness == Brightness.dark
          ? const Color(0xFF8BD6B5)
          : const Color(0xFF247E61),
    );
  }

  /// Primary accent for actions, selected rows and the search icon.
  final Color? accent;

  /// Tone of the bundled/cached availability badges and success states.
  final Color? offlineTone;

  /// Minimum interactive height of list rows; must stay at or above the
  /// 44 px touch-target floor (UX-10).
  final double rowMinHeight;

  /// Corner radius of the picker's inner cards and state panels.
  final BorderRadius cardRadius;

  /// Vertical gap between the picker's sections.
  final double sectionSpacing;

  /// Resolves [accent] against [scheme].
  Color accentOf(ColorScheme scheme) => accent ?? scheme.primary;

  /// Resolves [offlineTone] against [scheme].
  Color offlineToneOf(ColorScheme scheme) =>
      offlineTone ??
      (scheme.brightness == Brightness.dark
          ? const Color(0xFF8BD6B5)
          : const Color(0xFF247E61));
}
