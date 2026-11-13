// SPDX-License-Identifier: BSD-3-Clause
/// Internal validation primitives shared by the resource parsers.
///
/// This library is an implementation detail of `parser.dart`; it is not
/// exported from the public `geo_regions.dart` surface. It carries the
/// schema-level patterns, the strict 1.0 field sets and the low-level
/// semantic checks aligned with `tool/geo_data.py` and `schemas/`.
library;

import 'errors.dart';
import 'revision.dart';

/// Protocol version literal used by parsers when constructing models.
const String kParserProtocolVersion = '1.0';

/// Uppercase ISO 3166-1 alpha-2 country code.
final RegExp countryCodePattern = RegExp(r'^[A-Z]{2}$');

/// Any resource revision label `^[sclm]-[a-f0-9]{16}$`.
final RegExp anyRevisionPattern = RegExp(r'^[sclm]-[a-f0-9]{16}$');

/// Structure revision label `^s-[a-f0-9]{16}$`.
final RegExp structureRevisionPattern = RegExp(r'^s-[a-f0-9]{16}$');

/// Catalog revision label `^c-[a-f0-9]{16}$`.
final RegExp catalogRevisionPattern = RegExp(r'^c-[a-f0-9]{16}$');

/// Manifest-entry revision label `^[scl]-[a-f0-9]{16}$`.
final RegExp resourceRevisionPattern = RegExp(r'^[scl]-[a-f0-9]{16}$');

/// Full 64 lowercase hex SHA-256.
final RegExp sha256Pattern = RegExp(r'^[a-f0-9]{64}$');

/// Ordinary BCP 47 tag syntax, ported verbatim from `tool/geo_data.py`.
/// It is a syntax check only; no IANA registry or grandfathered claims.
final RegExp bcp47Pattern = RegExp(
  r'^(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4}|[A-Za-z]{5,8})'
  r'(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?'
  r'(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*'
  r'(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*'
  r'(?:-x(?:-[A-Za-z0-9]{1,8})+)?$',
);

/// Allowed fields on a region node (structure.schema.json).
const Set<String> nodeFields = <String>{
  'id',
  'parentId',
  'kind',
  'code',
  'name',
  'nativeLocale',
  'childrenStatus',
  'aliases',
  'nameLocale',
  'nameQuality',
};

/// Allowed top-level fields of a structure resource.
const Set<String> structureFields = <String>{
  'protocolVersion',
  'datasetId',
  'revision',
  'coverage',
  'sourceRefs',
  'countryCode',
  'nodes',
};

/// Allowed top-level fields of a region locale pack.
const Set<String> localeFields = <String>{
  'protocolVersion',
  'datasetId',
  'revision',
  'coverage',
  'sourceRefs',
  'countryCode',
  'locale',
  'compatibleStructureRevision',
  'names',
};

/// Allowed top-level fields of a catalog names pack.
const Set<String> catalogNamesFields = <String>{
  'protocolVersion',
  'datasetId',
  'revision',
  'coverage',
  'sourceRefs',
  'locale',
  'compatibleCatalogRevision',
  'names',
};

/// Allowed top-level fields of the country catalog.
const Set<String> countriesFields = <String>{
  'protocolVersion',
  'datasetId',
  'revision',
  'coverage',
  'sourceRefs',
  'countries',
};

/// Allowed top-level fields of the manifest.
const Set<String> manifestFields = <String>{
  'protocolVersion',
  'datasetId',
  'revision',
  'resources',
};

/// Allowed fields on one manifest resource entry.
const Set<String> manifestEntryFields = <String>{
  'path',
  'kind',
  'revision',
  'sha256',
  'bytes',
  'countryCode',
  'locale',
  'compatibleStructureRevision',
  'compatibleCatalogRevision',
};

/// Allowed fields on one country catalog entry.
const Set<String> countryEntryFields = <String>{'code', 'name', 'rootId'};

/// Allowed fields on a selection value.
const Set<String> selectionFields = <String>{
  'protocolVersion',
  'datasetId',
  'countryCode',
  'dataRevision',
  'pathIds',
  'displaySnapshot',
  'displayLocale',
};

/// Coerces a decoded JSON value into a typed object map, throwing
/// [GeoParseFailureError] for non-objects or non-string keys.
Map<String, Object?> asJsonObject(Object? decoded, String what) {
  if (decoded is! Map) {
    throw GeoParseFailureError('$what: JSON object required');
  }
  final map = <String, Object?>{};
  for (final entry in decoded.entries) {
    if (entry.key is! String) {
      throw GeoParseFailureError('$what: string object keys required');
    }
    map[entry.key as String] = entry.value;
  }
  return map;
}

/// Throws [GeoParseFailureError] for fields outside the strict 1.0 schema.
void rejectUnknownFields(
  Map<String, Object?> map,
  Set<String> allowed,
  String what,
) {
  for (final key in map.keys) {
    if (!allowed.contains(key)) {
      throw GeoParseFailureError(
        '$what: unknown field "$key" rejected by strict 1.0 schema',
      );
    }
  }
}

/// Checks the metadata block shared by every resource: protocol version,
/// datasetId, revision shape, coverage object and sourceRefs.
void checkMetadata(
  Map<String, Object?> map,
  String what, {
  String? expectedDatasetId,
}) {
  final version = map['protocolVersion'];
  if (version != kParserProtocolVersion) {
    throw GeoUnsupportedVersionError(
      '$what: unsupported protocolVersion "$version"; '
      'this SDK accepts exactly "1.0"',
    );
  }
  final datasetId = checkText(map['datasetId'], '$what.datasetId');
  if (expectedDatasetId != null && datasetId != expectedDatasetId) {
    throw GeoParseFailureError(
      '$what: datasetId mismatch ($datasetId != $expectedDatasetId)',
    );
  }
  final revision = map['revision'];
  if (revision is! String || !anyRevisionPattern.hasMatch(revision)) {
    throw GeoParseFailureError(
      '$what.revision: must match ^[sclm]-[a-f0-9]{16}\$',
    );
  }
  final coverage = map['coverage'];
  if (coverage != null && coverage is! Map) {
    throw GeoParseFailureError('$what.coverage: object required');
  }
  _checkSourceRefs(map['sourceRefs'], what);
}

void _checkSourceRefs(Object? raw, String what) {
  if (raw == null) {
    return;
  }
  if (raw is! List) {
    throw GeoParseFailureError('$what.sourceRefs: array required');
  }
  final seen = <String>{};
  for (final ref in raw) {
    final value = checkText(ref, '$what.sourceRefs');
    if (!seen.add(value)) {
      throw GeoParseFailureError('$what.sourceRefs: duplicate reference');
    }
  }
}

/// Requires an uppercase ISO alpha-2 country code.
String requireCountryCode(Object? raw, String what) {
  if (raw is! String || !countryCodePattern.hasMatch(raw)) {
    throw GeoParseFailureError('$what: uppercase ISO alpha-2 required');
  }
  return raw;
}

/// Requires a non-empty, control-character-free string.
String checkText(Object? value, String what) {
  if (value is! String || value.trim().isEmpty) {
    throw GeoParseFailureError('$what: non-empty string required');
  }
  if (value.codeUnits.any((unit) => unit < 0x20)) {
    throw GeoParseFailureError('$what: control character not allowed');
  }
  return value;
}

/// Like [checkText] but tolerates `null` (optional field).
String? optionalText(Object? value, String what) {
  if (value == null) {
    return null;
  }
  return checkText(value, what);
}

/// Requires a BCP 47 tag when the value is present.
String? optionalLocale(Object? value, String what) {
  if (value == null) {
    return null;
  }
  return checkLocaleTag(value, what);
}

/// Requires an ordinary BCP 47 tag of length 2..255.
String checkLocaleTag(Object? value, String what) {
  final tag = checkText(value, what);
  if (tag.length < 2 || tag.length > 255) {
    throw GeoParseFailureError('$what: length must be within 2..255');
  }
  if (!bcp47Pattern.hasMatch(tag)) {
    throw GeoParseFailureError('$what: invalid ordinary BCP 47 tag "$tag"');
  }
  return tag;
}

/// Requires a bounded-length string when the value is present.
String? optionalBoundedText(
  Object? value,
  int minLength,
  int maxLength,
  String what,
) {
  if (value == null) {
    return null;
  }
  if (value is! String ||
      value.length < minLength ||
      value.length > maxLength) {
    throw GeoParseFailureError(
      '$what: string of length $minLength..$maxLength required',
    );
  }
  return value;
}

/// Requires a pattern-matching string when the value is present.
String? optionalPatternText(Object? value, RegExp pattern, String what) {
  if (value == null) {
    return null;
  }
  if (value is! String || !pattern.hasMatch(value)) {
    throw GeoParseFailureError('$what: pattern ${pattern.pattern} required');
  }
  return value;
}

/// Parses the `names` object of a locale/catalog pack.
Map<String, String> parseNamesMap(Object? raw, String what) {
  if (raw is! Map) {
    throw GeoParseFailureError('$what.names: object required');
  }
  final names = <String, String>{};
  for (final entry in raw.entries) {
    if (entry.key is! String) {
      throw GeoParseFailureError('$what.names: string keys required');
    }
    names[entry.key as String] = checkText(
      entry.value,
      '$what.names.${entry.key}',
    );
  }
  return names;
}

/// Parses `coverage.translationQualityById`; markers for untranslated IDs
/// are rejected.
Map<String, String> parseQualityMap(
  Object? coverageRaw,
  Map<String, String> names,
  String what,
) {
  final raw = rawQuality(coverageRaw);
  if (raw is! Map) {
    throw GeoParseFailureError(
      '$what.coverage.translationQualityById: object required',
    );
  }
  final quality = <String, String>{};
  for (final entry in raw.entries) {
    if (entry.key is! String) {
      throw GeoParseFailureError(
        '$what.coverage.translationQualityById: string keys required',
      );
    }
    final key = entry.key as String;
    if (!names.containsKey(key)) {
      throw GeoParseFailureError(
        '$what.coverage.translationQualityById: unknown translation ID $key',
      );
    }
    quality[key] = checkText(
      entry.value,
      '$what.coverage.translationQualityById.$key',
    );
  }
  return quality;
}

/// Raw `translationQualityById` value for revision payloads, matching the
/// Python reference's `coverage.get('translationQualityById', {})`.
Object? rawQuality(Object? coverageRaw) {
  if (coverageRaw is! Map) {
    return const <String, Object?>{};
  }
  return coverageRaw['translationQualityById'] ?? const <String, Object?>{};
}

/// Throws [GeoIntegrityMismatchError] when the declared revision disagrees
/// with the recomputed revision of [payload].
void requireRevisionMatch(
  String declared,
  String prefix,
  Object? payload,
  String what,
) {
  final computed = geoRevisionOf(prefix, payload);
  if (declared != computed) {
    throw GeoIntegrityMismatchError(
      '$what: revision does not match content '
      '(declared $declared, computed $computed)',
    );
  }
}
