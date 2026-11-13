// SPDX-License-Identifier: BSD-3-Clause
/// Substring search over names, aliases and IDs (P1-04 task card).
///
/// Results always carry the full root-inclusive path so same-named nodes
/// stay distinguishable: `南山区` under 鸡西 and `南山区` under 深圳 differ
/// by `pathIds` even though `name` is identical.
library;

import 'index.dart';
import 'models.dart';

/// Which attribute of a node matched a query.
enum GeoSearchField {
  /// Matched the source default name.
  name,

  /// Matched one of the node's explicit aliases.
  alias,

  /// Matched the node ID itself.
  id,
}

/// One search hit with its full root-inclusive path.
class GeoSearchResult {
  const GeoSearchResult({
    required this.node,
    required this.pathIds,
    required this.matchedField,
    required this.matchedValue,
  });

  /// The matched node.
  final GeoRegionNode node;

  /// Root-inclusive ID path `[cc:XX, …, node.id]`.
  final List<String> pathIds;

  /// Attribute that matched the query.
  final GeoSearchField matchedField;

  /// The matching attribute value (name, alias or the ID string).
  final String matchedValue;
}

/// Searches [index] for nodes whose name, alias or ID contains [query]
/// (case-insensitive substring), optionally restricted to [countryCode].
///
/// A query that is empty after trimming yields no results. [limit], when
/// positive, caps the number of returned hits; `null` means unbounded.
/// Matching precedence per node is name, then aliases, then ID; the first
/// hit wins for [GeoSearchResult.matchedField].
List<GeoSearchResult> geoSearch(
  GeoRegionIndex index,
  String query, {
  String? countryCode,
  int? limit,
}) {
  final needle = query.trim().toLowerCase();
  if (needle.isEmpty || (limit != null && limit <= 0)) {
    return const <GeoSearchResult>[];
  }
  final structures = countryCode == null
      ? [for (final structure in index.structures) structure.countryCode]
      : <String>[countryCode];
  final results = <GeoSearchResult>[];
  for (final code in structures) {
    final structure = index.structureOf(code);
    for (final node in structure.nodes) {
      final hit = _match(node, needle);
      if (hit != null) {
        results.add(
          GeoSearchResult(
            node: node,
            pathIds: index.pathToRoot(node.id),
            matchedField: hit.field,
            matchedValue: hit.value,
          ),
        );
        if (limit != null && results.length >= limit) {
          return List.unmodifiable(results);
        }
      }
    }
  }
  return List.unmodifiable(results);
}

class _Hit {
  const _Hit(this.field, this.value);

  final GeoSearchField field;
  final String value;
}

_Hit? _match(GeoRegionNode node, String needle) {
  if (node.name.toLowerCase().contains(needle)) {
    return _Hit(GeoSearchField.name, node.name);
  }
  for (final alias in node.aliases) {
    if (alias.toLowerCase().contains(needle)) {
      return _Hit(GeoSearchField.alias, alias);
    }
  }
  if (node.id.toLowerCase().contains(needle)) {
    return _Hit(GeoSearchField.id, node.id);
  }
  return null;
}
