// SPDX-License-Identifier: BSD-3-Clause
/// In-memory lookup index over one or more parsed country structures.
///
/// The index is the SDK's query surface: ID lookup, parent/child traversal,
/// root-inclusive paths and coverage introspection. Paths always include the
/// country root (`cc:XX`), so same-named nodes in different branches remain
/// distinguishable and persisted selections can be revalidated exactly.
library;

import 'errors.dart';
import 'models.dart';

class _IndexData {
  const _IndexData(
    this.byId,
    this.childrenById,
    this.structuresByCountry,
    this.datasetId,
  );

  final Map<String, GeoRegionNode> byId;
  final Map<String, List<GeoRegionNode>> childrenById;
  final Map<String, GeoRegionStructure> structuresByCountry;
  final String datasetId;
}

/// Lookup index over the structures it was built from.
///
/// All structures must belong to one dataset; node IDs are unique across the
/// index (mirroring the Python reference's cross-country ID-uniqueness gate).
class GeoRegionIndex {
  GeoRegionIndex(Iterable<GeoRegionStructure> structures)
    : this._(_build(structures));

  /// Creates a single-country index.
  GeoRegionIndex.single(GeoRegionStructure structure) : this([structure]);

  GeoRegionIndex._(_IndexData data)
    : _byId = data.byId,
      _childrenById = data.childrenById,
      _structuresByCountry = data.structuresByCountry,
      datasetId = data.datasetId;

  final Map<String, GeoRegionNode> _byId;
  final Map<String, List<GeoRegionNode>> _childrenById;
  final Map<String, GeoRegionStructure> _structuresByCountry;

  /// Dataset namespace shared by every indexed structure.
  final String datasetId;

  static _IndexData _build(Iterable<GeoRegionStructure> structures) {
    final byId = <String, GeoRegionNode>{};
    final childrenById = <String, List<GeoRegionNode>>{};
    final structuresByCountry = <String, GeoRegionStructure>{};
    var datasetId = '';
    for (final structure in structures) {
      if (datasetId.isEmpty) {
        datasetId = structure.datasetId;
      } else if (structure.datasetId != datasetId) {
        throw GeoConfigurationError(
          'an index cannot mix datasets (${structure.datasetId} vs '
          '$datasetId); different datasetIds are different namespaces',
        );
      }
      if (structuresByCountry.containsKey(structure.countryCode)) {
        throw GeoConfigurationError(
          'duplicate structure for country ${structure.countryCode}',
        );
      }
      structuresByCountry[structure.countryCode] = structure;
      for (final node in structure.nodes) {
        if (byId.containsKey(node.id)) {
          throw GeoParseFailureError('ID reused across countries: ${node.id}');
        }
        byId[node.id] = node;
        childrenById.putIfAbsent(node.parentId ?? '', () => []).add(node);
      }
    }
    if (datasetId.isEmpty) {
      throw GeoConfigurationError('an index requires at least one structure');
    }
    return _IndexData(byId, childrenById, structuresByCountry, datasetId);
  }

  /// Country codes present in this index, in insertion order.
  List<String> get countryCodes => List.unmodifiable(_structuresByCountry.keys);

  /// Structures in this index, in insertion order.
  List<GeoRegionStructure> get structures =>
      List.unmodifiable(_structuresByCountry.values);

  /// Whether [id] resolves to a node in this index.
  bool containsNodeId(String id) => _byId.containsKey(id);

  /// Node for [id], or `null` when unknown.
  GeoRegionNode? nodeById(String id) => _byId[id];

  /// Node for [id]; throws [GeoNotFoundError] when unknown.
  GeoRegionNode requireNode(String id) {
    final node = _byId[id];
    if (node == null) {
      throw GeoNotFoundError('unknown node ID $id in dataset $datasetId');
    }
    return node;
  }

  /// Country root node for [countryCode]; throws [GeoNotFoundError] when the
  /// country is not indexed.
  GeoRegionNode countryRoot(String countryCode) {
    final structure = _structuresByCountry[countryCode];
    if (structure == null) {
      throw GeoNotFoundError(
        'country $countryCode is not present in dataset $datasetId',
      );
    }
    return requireNode('cc:$countryCode');
  }

  /// Structure for [countryCode]; throws [GeoNotFoundError] when absent.
  GeoRegionStructure structureOf(String countryCode) {
    final structure = _structuresByCountry[countryCode];
    if (structure == null) {
      throw GeoNotFoundError(
        'country $countryCode is not present in dataset $datasetId',
      );
    }
    return structure;
  }

  /// Child nodes of [id] in document order; throws [GeoNotFoundError] for
  /// unknown IDs. An empty result means "no children listed here" — pair it
  /// with [coverageStatus] before claiming leafness.
  List<GeoRegionNode> children(String id) {
    requireNode(id);
    return List.unmodifiable(_childrenById[id] ?? const <GeoRegionNode>[]);
  }

  /// Whether [id] has any child nodes listed in the structure.
  bool hasDeclaredChildren(String id) => children(id).isNotEmpty;

  /// Declared coverage of [id]'s child list. `GeoChildrenStatus.unknown`
  /// means the snapshot does not know whether children exist; it does NOT
  /// mean the node is an administrative leaf.
  GeoChildrenStatus coverageStatus(String id) => requireNode(id).childrenStatus;

  /// Guards leaf-style treatment of [id].
  ///
  /// Throws [GeoUnknownCoverageError] when the node's coverage is unknown,
  /// forcing hosts to pick an explicit level policy instead of silently
  /// presenting "no child regions".
  void requireKnownCoverage(String id) {
    final status = coverageStatus(id);
    if (status == GeoChildrenStatus.unknown) {
      throw GeoUnknownCoverageError(
        'coverage of $id is unknown within this snapshot; an empty child '
        'list is not a verified administrative leaf',
      );
    }
  }

  /// Root-inclusive ID path to [id]: `[cc:XX, …, id]`.
  ///
  /// Throws [GeoNotFoundError] for unknown IDs.
  List<String> pathToRoot(String id) =>
      List.unmodifiable(pathNodesToRoot(id).map((node) => node.id));

  /// Root-inclusive node path to [id]: `[cc:XX node, …, id node]`.
  ///
  /// Throws [GeoNotFoundError] for unknown IDs.
  List<GeoRegionNode> pathNodesToRoot(String id) {
    var node = requireNode(id);
    final path = <GeoRegionNode>[node];
    while (!node.isCountryRoot) {
      node = requireNode(node.parentId!);
      path.add(node);
    }
    return path.reversed.toList(growable: false);
  }
}
