// SPDX-License-Identifier: BSD-3-Clause
/// Content revisions derived from C(x) (PROTOCOL.md §6).
///
/// A revision is `'<prefix>-' + first 16 hex chars of SHA-256(C(payload))`
/// with the prefix identifying the resource kind: `s-` structure,
/// `c-` catalog, `l-` locale pack, `m-` manifest. Quality-only changes alter
/// revisions even when spelling does not; short revisions never replace the
/// full 64-hex SHA-256 integrity hashes carried by the manifest.
library;

import 'canonical.dart';
import 'sha256.dart';

/// Valid revision prefixes per PROTOCOL.md §6.
const Set<String> geoRevisionPrefixes = <String>{'s', 'c', 'l', 'm'};

final RegExp _revisionPattern = RegExp(r'^[sclm]-[a-f0-9]{16}$');

/// Computes the revision of [payload] for the given one-letter [prefix].
///
/// [prefix] must be one of [geoRevisionPrefixes]; anything else throws an
/// [ArgumentError].
String geoRevisionOf(String prefix, Object? payload) {
  if (!geoRevisionPrefixes.contains(prefix)) {
    throw ArgumentError.value(
      prefix,
      'prefix',
      'revision prefix must be one of $geoRevisionPrefixes',
    );
  }
  final digest = geoSha256Hex(geoCanonicalJsonBytes(payload));
  return '$prefix-${digest.substring(0, 16)}';
}

/// Computes the structure revision `s-…` of a decoded `nodes` array.
String geoStructureRevision(Object? nodes) => geoRevisionOf('s', nodes);

/// Computes the catalog revision `c-…` of a decoded `countries` array.
String geoCatalogRevision(Object? countries) => geoRevisionOf('c', countries);

/// Computes the locale revision `l-…` of a decoded locale payload.
///
/// Mirrors `tool/geo_data.py::locale_revision`: the hashed object is
/// `{"names": names, "translationQualityById": quality}` with an empty map
/// when no quality information exists. Absent quality therefore still changes
/// nothing relative to the reference implementation.
String geoLocaleRevision(
  Map<String, Object?> names, [
  Map<String, Object?>? translationQualityById,
]) => geoRevisionOf('l', <String, Object?>{
  'names': names,
  'translationQualityById': translationQualityById ?? const <String, Object?>{},
});

/// Computes the manifest revision `m-…` of a decoded `resources` array.
String geoManifestRevision(Object? resources) => geoRevisionOf('m', resources);

/// Whether [value] matches the revision shape `^[sclm]-[a-f0-9]{16}$`.
bool geoIsValidRevision(String value) => _revisionPattern.hasMatch(value);

/// Whether [revision] equals the revision computed from [payload] under
/// [prefix]. Compatibility checks require exact equality, never "close in
/// time" (PROTOCOL.md §6).
bool geoRevisionMatches(String revision, String prefix, Object? payload) =>
    revision == geoRevisionOf(prefix, payload);
