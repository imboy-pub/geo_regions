// SPDX-License-Identifier: BSD-3-Clause
/// Shared fixtures: loaders for the repository's bundled `data/` files.
///
/// `data/` ships inside the package root, so tests read the real published
/// resources (golden vectors by definition) with `dart:io` — the library
/// itself stays web-compatible and IO-free.
library;

import 'dart:convert';
import 'dart:io';

import 'package:geo_regions/geo_regions.dart';

/// Decodes a JSON file under `data/` into a typed map.
Map<String, Object?> loadDecodedData(String relativePath) {
  final decoded = jsonDecode(File('data/$relativePath').readAsStringSync());
  if (decoded is! Map) {
    throw StateError('data/$relativePath did not decode to an object');
  }
  return <String, Object?>{
    for (final entry in decoded.entries)
      entry.key as String: entry.value as Object?,
  };
}

/// Loads and parses `data/regions/{countryCode}.json` (revision verified).
GeoRegionStructure loadStructure(String countryCode) =>
    parseRegionStructure(loadDecodedData('regions/$countryCode.json'));

/// Loads and parses `data/i18n/{locale}/{CC}.json` against [structure].
GeoLocalePack loadLocalePack(String locale, GeoRegionStructure structure) =>
    parseLocalePack(
      loadDecodedData('i18n/$locale/${structure.countryCode}.json'),
      expectedStructure: structure,
    );

/// Loads and parses `data/catalog_i18n/{locale}.json`.
GeoCatalogNames loadCatalogNames(String locale) =>
    parseCatalogNames(loadDecodedData('catalog_i18n/$locale.json'));

/// Loads and parses `data/countries.json`.
GeoCountryCatalog loadCountryCatalog() =>
    parseCountryCatalog(loadDecodedData('countries.json'));

/// Loads and parses `data/manifest.json`.
GeoManifest loadManifest() => parseManifest(loadDecodedData('manifest.json'));

/// Returns a deep copy of a decoded structure with [mutate] applied.
Map<String, Object?> mutateStructure(
  String countryCode,
  void Function(Map<String, Object?> decoded) mutate,
) {
  final decoded = loadDecodedData('regions/$countryCode.json');
  mutate(decoded);
  return decoded;
}

/// Copies a decoded JSON object into a fresh typed mutable map.
Map<String, Object?> copyJsonObject(Object? raw) => <String, Object?>{
  for (final entry in (raw as Map).entries) entry.key as String: entry.value,
};
