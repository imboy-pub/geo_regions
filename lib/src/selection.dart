// SPDX-License-Identifier: BSD-3-Clause
/// Selection construction and semantic validation (PROTOCOL.md §8).
///
/// Identity is `pathIds`, never label text joined with spaces. Validation
/// replays every parent edge against the live structure; deleted IDs raise
/// [GeoNotFoundError] and reparented IDs raise [GeoIntegrityMismatchError].
/// The SDK never guesses a mapping for a moved or retired node — hosts need
/// an explicit migration record. Display language is display-only: changing
/// it never changes selection identity.
library;

import 'errors.dart';
import 'index.dart';
import 'models.dart';

/// Builds a selection for [nodeId] from [index].
///
/// The resulting `pathIds` are the root-inclusive path `[cc:XX, …, nodeId]`.
/// [displaySnapshot] must be parallel to the path (same length) and
/// [displayLocale] states which locale rendered it; both are conveniences
/// that do not participate in equality.
GeoSelection buildGeoSelection(
  GeoRegionIndex index,
  String nodeId, {
  List<String>? displaySnapshot,
  String? displayLocale,
}) {
  final pathIds = index.pathToRoot(nodeId);
  _checkSnapshot(displaySnapshot, pathIds);
  final countryCode = pathIds.first.substring('cc:'.length);
  final structure = index.structureOf(countryCode);
  return GeoSelection(
    protocolVersion: kSelectionProtocolVersion,
    datasetId: structure.datasetId,
    countryCode: countryCode,
    dataRevision: structure.revision,
    pathIds: pathIds,
    displaySnapshot: displaySnapshot,
    displayLocale: displayLocale,
  );
}

/// Builds a country-only (single-element path) selection for [countryCode].
GeoSelection buildCountrySelection(
  GeoRegionIndex index,
  String countryCode, {
  List<String>? displaySnapshot,
  String? displayLocale,
}) {
  final root = index.countryRoot(countryCode);
  final pathIds = <String>[root.id];
  _checkSnapshot(displaySnapshot, pathIds);
  final structure = index.structureOf(countryCode);
  return GeoSelection(
    protocolVersion: kSelectionProtocolVersion,
    datasetId: structure.datasetId,
    countryCode: countryCode,
    dataRevision: structure.revision,
    pathIds: List.unmodifiable(pathIds),
    displaySnapshot: displaySnapshot,
    displayLocale: displayLocale,
  );
}

void _checkSnapshot(List<String>? displaySnapshot, List<String> pathIds) {
  if (displaySnapshot != null && displaySnapshot.length != pathIds.length) {
    throw GeoConfigurationError(
      'displaySnapshot must correspond to the complete path '
      '(${displaySnapshot.length} labels vs ${pathIds.length} IDs)',
    );
  }
}

/// Protocol version stamped on selections built by this SDK.
const String kSelectionProtocolVersion = '1.0';

/// Validates [selection] against [index] and throws on any mismatch.
///
/// Checks, in order: supported protocol version ([GeoUnsupportedVersionError]);
/// known country ([GeoNotFoundError]); same dataset namespace
/// ([GeoNotFoundError] — a different `datasetId` is a different namespace and
/// the IDs are not transferable); exact `dataRevision`
/// ([GeoIntegrityMismatchError] — compatibility is exact equality, never
/// "close in time"); path shape: non-empty, unique IDs, first element
/// `cc:{countryCode}` ([GeoParseFailureError]); every ID known
/// ([GeoNotFoundError]); every adjacent parent edge real and root parent
/// null ([GeoIntegrityMismatchError]); display snapshot parallel to the
/// path ([GeoParseFailureError]). Country-only single-element paths are
/// valid.
void validateGeoSelection(GeoSelection selection, GeoRegionIndex index) {
  if (selection.protocolVersion != kSelectionProtocolVersion) {
    throw GeoUnsupportedVersionError(
      'selection: unsupported protocolVersion '
      '"${selection.protocolVersion}"; this SDK accepts exactly "1.0"',
    );
  }
  final structure = index.structureOf(selection.countryCode);
  if (selection.datasetId != structure.datasetId) {
    throw GeoNotFoundError(
      'selection: dataset mismatch (${selection.datasetId} vs index '
      '${structure.datasetId}); a different datasetId is a different ID '
      'namespace',
    );
  }
  if (selection.dataRevision != structure.revision) {
    throw GeoIntegrityMismatchError(
      'selection: stale structure revision (${selection.dataRevision} != '
      '${structure.revision})',
    );
  }
  _validatePathShape(selection);
  _validatePathEdges(selection, index);
  final snapshot = selection.displaySnapshot;
  if (snapshot != null && snapshot.length != selection.pathIds.length) {
    throw GeoParseFailureError(
      'selection: snapshot must correspond to the complete path',
    );
  }
}

void _validatePathShape(GeoSelection selection) {
  final path = selection.pathIds;
  if (path.isEmpty) {
    throw GeoParseFailureError('selection: nonempty string path required');
  }
  if (path.toSet().length != path.length) {
    throw GeoParseFailureError('selection: duplicate path ID');
  }
  if (path.first != 'cc:${selection.countryCode}') {
    throw GeoParseFailureError(
      'selection: path must include country root first',
    );
  }
}

void _validatePathEdges(GeoSelection selection, GeoRegionIndex index) {
  String? expectedParent;
  for (final nodeId in selection.pathIds) {
    final node = index.requireNode(nodeId);
    if (node.parentId != expectedParent) {
      throw GeoIntegrityMismatchError(
        'selection: missing or incorrect parent edge at $nodeId '
        '(expected parent ${expectedParent ?? 'null'}, found '
        '${node.parentId ?? 'null'})',
      );
    }
    expectedParent = nodeId;
  }
}
