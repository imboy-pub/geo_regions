// SPDX-License-Identifier: BSD-3-Clause
/// Strict parser and semantic validator for the six protocol resources.
///
/// Validation mirrors the Python golden reference `tool/geo_data.py::validate`
/// and the JSON Schemas in `schemas/` (strict `additionalProperties: false`).
/// Failures map to the typed taxonomy of CONSUMER_CONTRACT §2:
///
/// * wrong `protocolVersion` → [GeoUnsupportedVersionError]
/// * schema/shape violations, unknown fields, duplicate IDs, cycles,
///   cross-country parents, dangling translation IDs, unsafe or unsorted
///   manifest paths → [GeoParseFailureError]
/// * declared revision disagreeing with content, locale pack compatibility
///   label disagreeing with the referenced structure →
///   [GeoIntegrityMismatchError]
///
/// Byte-level duplicate JSON keys cannot be detected by `jsonDecode`; that
/// defense line is the host integrity chain, where SHA-256 verification runs
/// before any parsing. Node-ID duplication is always checked after parsing.
///
/// The Python reference additionally requires NFC-normalized text values;
/// reproducing that needs Unicode normalization tables which a
/// zero-dependency SDK does not carry. The publishing pipeline enforces NFC,
/// so this parser checks non-emptiness and control characters only.
library;

import 'dart:convert';

import 'canonical.dart';
import 'errors.dart';
import 'models.dart';
import 'validators.dart';

/// Decodes [text] as JSON, mapping syntax failures to [GeoParseFailureError].
///
/// Hosts verify bytes (length + SHA-256) before calling this; the parser
/// itself cannot see byte-level duplicate keys.
Object? parseJsonText(String text) {
  try {
    return jsonDecode(text);
  } on FormatException catch (error) {
    throw GeoParseFailureError('JSON decode failed: ${error.message}');
  }
}

/// Parses and validates a decoded `countries.json` value.
GeoCountryCatalog parseCountryCatalog(
  Object? decoded, {
  bool verifyRevision = true,
  String? expectedDatasetId,
}) {
  const what = 'countries';
  final map = asJsonObject(decoded, what);
  rejectUnknownFields(map, countriesFields, what);
  checkMetadata(map, what, expectedDatasetId: expectedDatasetId);
  final rawCountries = map['countries'];
  if (rawCountries is! List || rawCountries.isEmpty) {
    throw GeoParseFailureError('$what.countries: non-empty array required');
  }
  final entries = _parseCountryEntries(rawCountries, what);
  if (verifyRevision) {
    requireRevisionMatch(map['revision'] as String, 'c', rawCountries, what);
  }
  return GeoCountryCatalog(
    protocolVersion: kParserProtocolVersion,
    datasetId: map['datasetId'] as String,
    revision: map['revision'] as String,
    countries: List.unmodifiable(entries),
  );
}

List<GeoCountryEntry> _parseCountryEntries(List rawCountries, String what) {
  final entries = <GeoCountryEntry>[];
  final seen = <String>{};
  for (var i = 0; i < rawCountries.length; i++) {
    final row = asJsonObject(rawCountries[i], '$what.countries[$i]');
    rejectUnknownFields(row, countryEntryFields, '$what.countries[$i]');
    final code = row['code'];
    if (code is! String || !countryCodePattern.hasMatch(code)) {
      throw GeoParseFailureError(
        '$what.countries[$i].code: uppercase ISO alpha-2 required',
      );
    }
    if (!seen.add(code)) {
      throw GeoParseFailureError('$what: duplicate country $code');
    }
    final name = checkText(row['name'], 'country $code.name');
    final rootId = row['rootId'];
    if (rootId is! String || rootId != 'cc:$code') {
      throw GeoParseFailureError('$what: wrong country root for $code');
    }
    entries.add(GeoCountryEntry(code: code, name: name, rootId: rootId));
  }
  return entries;
}

/// Parses and validates a decoded `regions/{CC}.json` structure.
///
/// Enforces: strict node field set; unique IDs; exactly one `cc:{CC}` root
/// with `kind == country`; every parent present within the same country; no
/// cycles; every node reaching the root; `childrenStatus` within the
/// documented enum; and, when [verifyRevision] is set, the declared revision
/// matching the recomputed `s-` revision of the nodes payload.
GeoRegionStructure parseRegionStructure(
  Object? decoded, {
  bool verifyRevision = true,
  String? expectedDatasetId,
}) {
  const what = 'structure';
  final map = asJsonObject(decoded, what);
  rejectUnknownFields(map, structureFields, what);
  checkMetadata(map, what, expectedDatasetId: expectedDatasetId);
  final countryCode = requireCountryCode(
    map['countryCode'],
    '$what.countryCode',
  );
  final rawNodes = map['nodes'];
  if (rawNodes is! List || rawNodes.isEmpty) {
    throw GeoParseFailureError('$what.nodes: non-empty array required');
  }
  final nodes = _parseNodes(rawNodes, what);
  _validateStructureTopology(nodes, countryCode, what);
  if (verifyRevision) {
    requireRevisionMatch(
      map['revision'] as String,
      's',
      rawNodes,
      '$what ($countryCode)',
    );
  }
  return GeoRegionStructure(
    protocolVersion: kParserProtocolVersion,
    datasetId: map['datasetId'] as String,
    countryCode: countryCode,
    revision: map['revision'] as String,
    nodes: List.unmodifiable(nodes),
  );
}

List<GeoRegionNode> _parseNodes(List rawNodes, String what) {
  final nodes = <GeoRegionNode>[];
  final byId = <String, GeoRegionNode>{};
  for (var i = 0; i < rawNodes.length; i++) {
    final node = _parseNode(rawNodes[i], i, what);
    if (byId.containsKey(node.id)) {
      throw GeoParseFailureError('$what: duplicate ID ${node.id}');
    }
    byId[node.id] = node;
    nodes.add(node);
  }
  return nodes;
}

GeoRegionNode _parseNode(Object? raw, int index, String what) {
  final desc = '$what.nodes[$index]';
  final map = asJsonObject(raw, desc);
  rejectUnknownFields(map, nodeFields, desc);
  final id = checkText(map['id'], '$desc.id');
  final parentId = map['parentId'];
  if (parentId != null && parentId is! String) {
    throw GeoParseFailureError('$id.parentId: string or null required');
  }
  final kind = checkText(map['kind'], '$id.kind');
  final name = checkText(map['name'], '$id.name');
  final childrenStatus = _parseChildrenStatus(map['childrenStatus'], id);
  return GeoRegionNode(
    id: id,
    parentId: parentId as String?,
    kind: kind,
    name: name,
    childrenStatus: childrenStatus,
    code: optionalText(map['code'], '$id.code'),
    nameLocale: optionalLocale(map['nameLocale'], '$id.nameLocale'),
    nameQuality: optionalText(map['nameQuality'], '$id.nameQuality'),
    nativeLocale: optionalLocale(map['nativeLocale'], '$id.nativeLocale'),
    aliases: _parseAliases(map['aliases'], id),
  );
}

GeoChildrenStatus _parseChildrenStatus(Object? raw, String nodeId) {
  final status = raw is String ? GeoChildrenStatus.tryParseName(raw) : null;
  if (status == null) {
    throw GeoParseFailureError(
      '$nodeId: invalid childrenStatus (complete|partial|unknown)',
    );
  }
  return status;
}

List<String> _parseAliases(Object? raw, String nodeId) {
  if (raw == null) {
    return const <String>[];
  }
  if (raw is! List) {
    throw GeoParseFailureError('$nodeId.aliases: array required');
  }
  final aliases = <String>[];
  for (final alias in raw) {
    final value = checkText(alias, '$nodeId.alias');
    if (aliases.contains(value)) {
      throw GeoParseFailureError('$nodeId.aliases: duplicate alias');
    }
    aliases.add(value);
  }
  return List.unmodifiable(aliases);
}

void _validateStructureTopology(
  List<GeoRegionNode> nodes,
  String countryCode,
  String what,
) {
  final expectedRootId = 'cc:$countryCode';
  final byId = <String, GeoRegionNode>{for (final node in nodes) node.id: node};
  final nullParents = <String>[
    for (final node in nodes)
      if (node.parentId == null) node.id,
  ];
  if (nullParents.length != 1 || nullParents.single != expectedRootId) {
    throw GeoParseFailureError(
      '$what: exactly one declared root $expectedRootId required',
    );
  }
  if (byId[expectedRootId]!.kind != 'country') {
    throw GeoParseFailureError('$what: root kind must be country');
  }
  for (final node in nodes) {
    _walkToRoot(node, byId, expectedRootId);
  }
}

void _walkToRoot(
  GeoRegionNode node,
  Map<String, GeoRegionNode> byId,
  String expectedRootId,
) {
  final seen = <String>{node.id};
  var parentId = node.parentId;
  while (parentId != null) {
    if (!seen.add(parentId)) {
      throw GeoParseFailureError('${node.id}: parent cycle at $parentId');
    }
    final ancestor = byId[parentId];
    if (ancestor == null) {
      throw GeoParseFailureError(
        '${node.id}: missing or cross-country parent $parentId',
      );
    }
    parentId = ancestor.parentId;
  }
  if (node.parentId != null && !seen.contains(expectedRootId)) {
    throw GeoParseFailureError('${node.id}: disconnected path');
  }
}

/// Parses and validates a decoded `i18n/{locale}/{CC}.json` locale pack.
///
/// When [expectedStructure] is given, the pack's [GeoLocalePack.names] keys
/// must be IDs of that exact structure (dangling IDs are rejected) and
/// [GeoLocalePack.compatibleStructureRevision] must equal the structure's
/// revision exactly.
GeoLocalePack parseLocalePack(
  Object? decoded, {
  GeoRegionStructure? expectedStructure,
  bool verifyRevision = true,
  String? expectedDatasetId,
}) {
  const what = 'locale pack';
  final map = asJsonObject(decoded, what);
  rejectUnknownFields(map, localeFields, what);
  checkMetadata(map, what, expectedDatasetId: expectedDatasetId);
  final countryCode = requireCountryCode(
    map['countryCode'],
    '$what.countryCode',
  );
  final locale = checkLocaleTag(map['locale'], '$what.locale');
  final compatible = requirePattern(
    map['compatibleStructureRevision'],
    structureRevisionPattern,
    '$what.compatibleStructureRevision',
  );
  final names = parseNamesMap(map['names'], what);
  final quality = parseQualityMap(map['coverage'], names, what);
  if (expectedStructure != null) {
    _checkPackAgainstStructure(
      countryCode,
      compatible,
      names,
      expectedStructure,
      what,
    );
  }
  if (verifyRevision) {
    requireRevisionMatch(
      map['revision'] as String,
      'l',
      localeRevisionPayload(map),
      '$what ($countryCode/$locale)',
    );
  }
  return GeoLocalePack(
    protocolVersion: kParserProtocolVersion,
    datasetId: map['datasetId'] as String,
    countryCode: countryCode,
    locale: locale,
    compatibleStructureRevision: compatible,
    revision: map['revision'] as String,
    names: Map.unmodifiable(names),
    qualityById: Map.unmodifiable(quality),
  );
}

/// Requires a pattern-matching string (same semantics as the optional
/// variant in validators.dart, but for mandatory fields).
String requirePattern(Object? raw, RegExp pattern, String what) {
  if (raw is! String || !pattern.hasMatch(raw)) {
    throw GeoParseFailureError('$what: must match ${pattern.pattern}');
  }
  return raw;
}

/// Raw locale-revision payload `{"names": …, "translationQualityById": …}`
/// mirroring `tool/geo_data.py::locale_revision`.
Object? localeRevisionPayload(Map<String, Object?> map) {
  return <String, Object?>{
    'names': map['names'],
    'translationQualityById': rawQuality(map['coverage']),
  };
}

void _checkPackAgainstStructure(
  String countryCode,
  String compatible,
  Map<String, String> names,
  GeoRegionStructure structure,
  String what,
) {
  if (countryCode != structure.countryCode) {
    throw GeoParseFailureError(
      '$what: country mismatch ($countryCode vs ${structure.countryCode})',
    );
  }
  if (compatible != structure.revision) {
    throw GeoIntegrityMismatchError(
      '$what: incompatible structure revision ($compatible != '
      '${structure.revision})',
    );
  }
  final validIds = <String>{for (final node in structure.nodes) node.id};
  final dangling = names.keys.where((id) => !validIds.contains(id)).toList()
    ..sort(compareJsonKeys);
  if (dangling.isNotEmpty) {
    throw GeoParseFailureError(
      '$what: dangling translation IDs ${dangling.take(3).toList()}',
    );
  }
}

/// Parses and validates a decoded `catalog_i18n/{locale}.json` pack.
///
/// When [expectedCatalog] is given, name keys must be exactly the catalog's
/// country codes (complete coverage required) and the compatibility revision
/// must match the catalog revision exactly.
GeoCatalogNames parseCatalogNames(
  Object? decoded, {
  GeoCountryCatalog? expectedCatalog,
  bool verifyRevision = true,
  String? expectedDatasetId,
}) {
  const what = 'country-names';
  final map = asJsonObject(decoded, what);
  rejectUnknownFields(map, catalogNamesFields, what);
  checkMetadata(map, what, expectedDatasetId: expectedDatasetId);
  final locale = checkLocaleTag(map['locale'], '$what.locale');
  final compatible = requirePattern(
    map['compatibleCatalogRevision'],
    catalogRevisionPattern,
    '$what.compatibleCatalogRevision',
  );
  final names = parseNamesMap(map['names'], what);
  final quality = parseQualityMap(map['coverage'], names, what);
  if (expectedCatalog != null) {
    _checkCatalogNamesAgainstCatalog(compatible, names, expectedCatalog, what);
  }
  if (verifyRevision) {
    requireRevisionMatch(
      map['revision'] as String,
      'l',
      localeRevisionPayload(map),
      what,
    );
  }
  return GeoCatalogNames(
    protocolVersion: kParserProtocolVersion,
    datasetId: map['datasetId'] as String,
    locale: locale,
    compatibleCatalogRevision: compatible,
    revision: map['revision'] as String,
    names: Map.unmodifiable(names),
    qualityById: Map.unmodifiable(quality),
  );
}

void _checkCatalogNamesAgainstCatalog(
  String compatible,
  Map<String, String> names,
  GeoCountryCatalog catalog,
  String what,
) {
  if (compatible != catalog.revision) {
    throw GeoIntegrityMismatchError(
      '$what: incompatible catalog revision ($compatible != '
      '${catalog.revision})',
    );
  }
  final codes = <String>{for (final entry in catalog.countries) entry.code};
  final unknown = names.keys.where((code) => !codes.contains(code)).toList()
    ..sort(compareJsonKeys);
  if (unknown.isNotEmpty) {
    throw GeoParseFailureError('$what: unknown country name key(s) $unknown');
  }
  final missing = codes.where((code) => !names.containsKey(code)).toList()
    ..sort();
  if (missing.isNotEmpty) {
    throw GeoParseFailureError(
      '$what: country-name coverage must be complete, missing $missing',
    );
  }
}

/// Parses and validates a decoded `manifest.json`.
///
/// Resource entries must be sorted by path (code-point order) with unique
/// paths; each path is checked against the traversal/encoding rules of
/// PROTOCOL.md §7. Full SHA-256 and byte-length verification of the
/// referenced files is the host loader's job (CONSUMER_CONTRACT §5).
GeoManifest parseManifest(Object? decoded, {bool verifyRevision = true}) {
  const what = 'manifest';
  final map = asJsonObject(decoded, what);
  rejectUnknownFields(map, manifestFields, what);
  checkMetadata(map, what);
  final rawResources = map['resources'];
  if (rawResources is! List) {
    throw GeoParseFailureError('$what.resources: array required');
  }
  final entries = <GeoManifestEntry>[];
  for (var i = 0; i < rawResources.length; i++) {
    entries.add(_parseManifestEntry(rawResources[i], i, what));
  }
  _checkManifestOrder(entries, what);
  if (verifyRevision) {
    requireRevisionMatch(map['revision'] as String, 'm', rawResources, what);
  }
  return GeoManifest(
    protocolVersion: kParserProtocolVersion,
    datasetId: map['datasetId'] as String,
    revision: map['revision'] as String,
    resources: List.unmodifiable(entries),
  );
}

GeoManifestEntry _parseManifestEntry(Object? raw, int index, String what) {
  final desc = '$what.resources[$index]';
  final map = asJsonObject(raw, desc);
  rejectUnknownFields(map, manifestEntryFields, desc);
  final path = checkText(map['path'], '$desc.path');
  _checkResourcePathSafety(path, desc);
  final kindRaw = map['kind'];
  final kind = kindRaw is String ? GeoResourceKind.tryParseName(kindRaw) : null;
  if (kind == null) {
    throw GeoParseFailureError('$desc.kind: invalid resource kind');
  }
  final revision = map['revision'];
  if (revision is! String || !resourceRevisionPattern.hasMatch(revision)) {
    throw GeoParseFailureError(
      '$desc.revision: must match ^[scl]-[a-f0-9]{16}\$',
    );
  }
  final sha256 = map['sha256'];
  if (sha256 is! String || !sha256Pattern.hasMatch(sha256)) {
    throw GeoParseFailureError('$desc.sha256: 64 lowercase hex required');
  }
  final bytes = map['bytes'];
  if (bytes is! int || bytes < 0) {
    throw GeoParseFailureError('$desc.bytes: non-negative integer required');
  }
  return GeoManifestEntry(
    path: path,
    kind: kind,
    revision: revision,
    sha256: sha256,
    bytes: bytes,
    countryCode: optionalPatternText(
      map['countryCode'],
      countryCodePattern,
      '$desc.countryCode',
    ),
    locale: optionalBoundedText(map['locale'], 2, 255, '$desc.locale'),
    compatibleStructureRevision: optionalPatternText(
      map['compatibleStructureRevision'],
      structureRevisionPattern,
      '$desc.compatibleStructureRevision',
    ),
    compatibleCatalogRevision: optionalPatternText(
      map['compatibleCatalogRevision'],
      catalogRevisionPattern,
      '$desc.compatibleCatalogRevision',
    ),
  );
}

void _checkResourcePathSafety(String path, String desc) {
  if (path.contains('\\')) {
    throw GeoParseFailureError('$desc: backslash in resource path');
  }
  if (path.contains('%') ||
      path.codeUnits.any((unit) => unit < 32 || unit == 127)) {
    throw GeoParseFailureError(
      '$desc: encoded or control-character resource path',
    );
  }
  if (path.isEmpty || path.startsWith('/')) {
    throw GeoParseFailureError('$desc: absolute/empty resource path');
  }
  if (path
      .split('/')
      .any((part) => part.isEmpty || part == '.' || part == '..')) {
    throw GeoParseFailureError('$desc: path traversal in resource path');
  }
  if (path.contains(':') || path.contains('?') || path.contains('#')) {
    throw GeoParseFailureError('$desc: non-file resource path');
  }
}

void _checkManifestOrder(List<GeoManifestEntry> entries, String what) {
  final seen = <String>{};
  for (var i = 0; i < entries.length; i++) {
    final path = entries[i].path;
    if (!seen.add(path)) {
      throw GeoParseFailureError('$what: duplicate manifest path $path');
    }
    if (i > 0 && compareJsonKeys(entries[i - 1].path, path) > 0) {
      throw GeoParseFailureError(
        '$what: resources must be sorted by path '
        '("${entries[i - 1].path}" before "$path")',
      );
    }
  }
}

/// Parses a decoded selection JSON object (shape only, per
/// `schemas/selection.schema.json`). Country, revision and parent edges are
/// validated against a live structure with [validateGeoSelection] in
/// `selection.dart`.
GeoSelection parseSelection(Object? decoded) {
  const what = 'selection';
  final map = asJsonObject(decoded, what);
  rejectUnknownFields(map, selectionFields, what);
  final version = map['protocolVersion'];
  if (version != kParserProtocolVersion) {
    throw GeoUnsupportedVersionError(
      '$what: unsupported protocolVersion "$version"; '
      'this SDK accepts exactly "1.0"',
    );
  }
  final datasetId = checkText(map['datasetId'], '$what.datasetId');
  final countryCode = requireCountryCode(
    map['countryCode'],
    '$what.countryCode',
  );
  final dataRevision = requirePattern(
    map['dataRevision'],
    structureRevisionPattern,
    '$what.dataRevision',
  );
  final pathIds = _parseSelectionPath(map['pathIds'], what);
  final snapshot = _parseSnapshot(map['displaySnapshot'], what);
  final displayLocale = optionalBoundedText(
    map['displayLocale'],
    2,
    255,
    '$what.displayLocale',
  );
  return GeoSelection(
    protocolVersion: kParserProtocolVersion,
    datasetId: datasetId,
    countryCode: countryCode,
    dataRevision: dataRevision,
    pathIds: pathIds,
    displaySnapshot: snapshot,
    displayLocale: displayLocale,
  );
}

List<String> _parseSelectionPath(Object? raw, String what) {
  if (raw is! List || raw.isEmpty) {
    throw GeoParseFailureError('$what.pathIds: non-empty array required');
  }
  final ids = <String>[];
  for (final item in raw) {
    if (item is! String || item.isEmpty) {
      throw GeoParseFailureError('$what.pathIds: non-empty strings required');
    }
    if (ids.contains(item)) {
      throw GeoParseFailureError('$what.pathIds: duplicate path ID $item');
    }
    ids.add(item);
  }
  return List.unmodifiable(ids);
}

List<String>? _parseSnapshot(Object? raw, String what) {
  if (raw == null) {
    return null;
  }
  if (raw is! List) {
    throw GeoParseFailureError('$what.displaySnapshot: array required');
  }
  final values = <String>[];
  for (final item in raw) {
    if (item is! String) {
      throw GeoParseFailureError('$what.displaySnapshot: strings required');
    }
    values.add(item);
  }
  return List.unmodifiable(values);
}
