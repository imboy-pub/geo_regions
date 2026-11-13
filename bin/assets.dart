// SPDX-License-Identifier: BSD-3-Clause
/// Offline asset generation and host-integration CLI (task P1-06).
///
/// Locates the installed geo_regions package through the *current working
/// directory's* `.dart_tool/package_config.json` (never a hard-coded repo or
/// pub-cache path), selects a resource subset from an assets config and
/// writes a host-ready bundle into `--out`:
///
/// * the selected payload files copied under their `data/` relative layout,
/// * a subset `manifest.json` (only bundled resources),
/// * a descriptor-only `registry.json` (all resources with `bundled` flags,
///   no unselected payloads),
/// * `assets.fragment.yaml` with precise per-file pubspec asset entries,
/// * an audit `report.json` with per-file SHA-256/bytes and gzip sizes,
/// * the `.geo_regions_generation` marker required for `--replace`.
///
/// Behaviour is aligned with the Python golden reference
/// `tool/geo_data.py::build_offline`; the runtime verification chain remains
/// the SDK repository's job — this tool only produces development/build-time
/// artifacts.
///
/// Exit codes: `0` success; `1` unexpected failure; `2` config, usage or
/// environment precondition error; `3` missing/stale/corrupt resource;
/// `4` unsafe or protected output. Shared infrastructure lives in
/// `bin/src_assets.dart`.
library;

import 'dart:convert';
import 'dart:io';

// The CLI imports the pure-Dart data-layer modules directly instead of the
// `package:geo_regions/geo_regions.dart` barrel: the barrel also exports the
// host loader stack (lib/src/load/), which depends on Flutter and therefore
// cannot compile on the plain VM this tool runs on. The imported modules
// (canonical/errors/parser/revision/sha256) have no Flutter dependency, so
// the CLI stays out of any host web compile graph.
import 'package:geo_regions/src/canonical.dart' show compareJsonKeys;
import 'package:geo_regions/src/errors.dart' show GeoParseFailureError;
import 'package:geo_regions/src/parser.dart' show parseManifest;
import 'package:geo_regions/src/revision.dart' show geoRevisionOf;
import 'package:geo_regions/src/sha256.dart' show geoSha256Hex;

import 'src_assets.dart';

final RegExp _countryPattern = RegExp(r'^[A-Z]{2}$');

/// Single-segment safety pattern for locale tags; it guarantees the tag is
/// one safe path component (no separators, no dot segments, no control
/// characters) while accepting BCP 47-style tags such as `zh-Hans` or `en`.
final RegExp _localePattern = RegExp(
  r'^[A-Za-z0-9]{2,8}(?:-[A-Za-z0-9]{1,8})*$',
);

void main(List<String> args) {
  try {
    final options = _parseArgs(args);
    if (options != null) {
      _generate(options);
    }
  } on CliError catch (error) {
    stderr.writeln('geo_regions:assets: ${error.message}');
    exit(error.code);
  } catch (error, stackTrace) {
    stderr.writeln('geo_regions:assets: unexpected failure: $error');
    stderr.writeln(stackTrace.toString());
    exit(kExitUnexpected);
  }
}

_Options? _parseArgs(List<String> args) {
  String? configPath;
  String? outputPath;
  var replace = false;
  var i = 0;
  while (i < args.length) {
    final arg = args[i];
    if (arg == '--help' || arg == '-h') {
      _printUsage(stdout);
      return null;
    } else if (arg == '--replace') {
      replace = true;
    } else if (arg == '--config' || arg.startsWith('--config=')) {
      configPath = _optionValue(args, arg, i, 'config');
      i++;
    } else if (arg == '--out' || arg.startsWith('--out=')) {
      outputPath = _optionValue(args, arg, i, 'out');
      i++;
    } else {
      throw CliError(kExitConfig, 'unknown argument: $arg (see --help)');
    }
    i++;
  }
  if (configPath == null) {
    throw CliError(kExitConfig, '--config <path> is required (see --help)');
  }
  if (outputPath == null) {
    throw CliError(kExitConfig, '--out <dir> is required (see --help)');
  }
  return _Options(
    configPath: configPath,
    outputPath: outputPath,
    replace: replace,
  );
}

/// Reads the value of a `--flag value` / `--flag=value` pair; [index] points
/// at the flag itself.
String _optionValue(List<String> args, String arg, int index, String name) {
  final equals = arg.indexOf('=');
  if (equals >= 0) {
    final value = arg.substring(equals + 1);
    if (value.isEmpty) {
      throw CliError(kExitConfig, '--$name requires a value');
    }
    return value;
  }
  if (index + 1 >= args.length) {
    throw CliError(kExitConfig, '$arg requires a value');
  }
  return args[index + 1];
}

void _printUsage(IOSink sink) {
  sink.writeln(
    'Usage: dart run geo_regions:assets --config <path> --out <dir> [--replace]',
  );
  sink.writeln();
  sink.writeln(
    'Generates the offline geo_regions asset bundle for a host app.',
  );
  sink.writeln();
  sink.writeln('Options:');
  sink.writeln(
    '  --config <path>   Assets config JSON (config/assets.schema.json); required.',
  );
  sink.writeln('  --out <dir>       Output bundle directory; required.');
  sink.writeln(
    '  --replace         Replace an existing output that carries the',
  );
  sink.writeln('                    $kMarkerName marker.');
  sink.writeln('  -h, --help        Show this help.');
  sink.writeln();
  sink.writeln(
    'Exit codes: 0 success; 1 unexpected; 2 config/usage/environment;',
  );
  sink.writeln(
    '3 missing/stale/corrupt resource; 4 unsafe or protected output.',
  );
}

void _generate(_Options options) {
  final packageRoot = _resolvePackageRoot();
  final dataRoot = '$packageRoot/data';
  final config = _loadConfig(options.configPath);
  final plan = _buildPlan(dataRoot, config);
  final output = guardOutput(options.outputPath, packageRoot, options.replace);
  final staging = Directory(parentOf(output)).createTempSync('.geo-assets-');
  try {
    final report = _writeStagedBundle(staging, config, plan, options);
    swapIntoPlace(staging, output);
    _printSummary(output, report);
  } finally {
    if (staging.existsSync()) {
      staging.deleteSync(recursive: true);
    }
  }
}

/// Resolves the geo_regions package root from the current working
/// directory's package config; relative `rootUri` values resolve against the
/// package config file itself (package_config v2 spec).
String _resolvePackageRoot() {
  final configUri = Directory.current.uri.resolve(
    '.dart_tool/package_config.json',
  );
  final configFile = File.fromUri(configUri);
  if (!configFile.existsSync()) {
    throw CliError(
      kExitConfig,
      'package config not found: ${configFile.path}; run this CLI from a '
      'directory whose package graph resolves $kPackageName (after '
      '"dart pub get" / "flutter pub get")',
    );
  }
  final Object? decoded;
  try {
    decoded = jsonDecode(configFile.readAsStringSync());
  } on FormatException catch (error) {
    throw CliError(
      kExitConfig,
      'invalid JSON in ${configFile.path}: ${error.message}',
    );
  }
  if (decoded is! Map<String, Object?>) {
    throw CliError(kExitConfig, '${configFile.path}: JSON object required');
  }
  final packages = decoded['packages'];
  if (packages is! List) {
    throw CliError(
      kExitConfig,
      '${configFile.path}: "packages" array required',
    );
  }
  for (final item in packages) {
    if (item is Map<String, Object?> && item['name'] == kPackageName) {
      return _packageRootFromEntry(item, configUri);
    }
  }
  throw CliError(
    kExitConfig,
    '${configFile.path}: package "$kPackageName" is not resolved; add the '
    'dependency and run pub get',
  );
}

String _packageRootFromEntry(Map<String, Object?> entry, Uri configUri) {
  final rootUriText = entry['rootUri'];
  if (rootUriText is! String || rootUriText.isEmpty) {
    throw CliError(kExitConfig, 'package "$kPackageName": missing rootUri');
  }
  final resolved = configUri.resolveUri(Uri.parse(rootUriText));
  if (resolved.scheme != 'file') {
    throw CliError(
      kExitConfig,
      'package "$kPackageName" rootUri is not a file URI: $resolved',
    );
  }
  var rootPath = resolved.toFilePath();
  while (rootPath.endsWith('/') || rootPath.endsWith(r'\')) {
    rootPath = rootPath.substring(0, rootPath.length - 1);
  }
  if (!Directory(rootPath).existsSync()) {
    throw CliError(
      kExitConfig,
      'package "$kPackageName" root directory does not exist: $rootPath',
    );
  }
  return rootPath;
}

_Config _loadConfig(String path) {
  final file = File(path);
  if (!file.existsSync()) {
    throw CliError(kExitConfig, 'config file not found: $path');
  }
  final Object? decoded;
  try {
    decoded = jsonDecode(file.readAsStringSync());
  } on FormatException catch (error) {
    throw CliError(
      kExitConfig,
      'invalid JSON in config $path: ${error.message}',
    );
  }
  if (decoded is! Map<String, Object?>) {
    throw CliError(kExitConfig, 'config $path: JSON object required');
  }
  return _validateConfig(decoded, path);
}

/// Validates the decoded config against `config/assets.schema.json`
/// semantics (unknown fields rejected, `^[A-Z]{2}$` structure codes, locale
/// keys a subset of structures, unique arrays).
_Config _validateConfig(Map<String, Object?> decoded, String path) {
  const allowed = <String>{
    'profile',
    'structures',
    'locales',
    'catalogLocales',
  };
  for (final key in decoded.keys) {
    if (!allowed.contains(key)) {
      throw CliError(
        kExitConfig,
        'config $path: unknown field "$key" (allowed: ${allowed.toList()..sort()})',
      );
    }
  }
  for (final required in const ['structures', 'locales', 'catalogLocales']) {
    if (!decoded.containsKey(required)) {
      throw CliError(
        kExitConfig,
        'config $path: missing required field "$required"',
      );
    }
  }
  final profileValue = decoded['profile'];
  String? profile;
  if (profileValue != null) {
    if (profileValue is! String || profileValue.isEmpty) {
      throw CliError(kExitConfig, 'config.profile: non-empty string required');
    }
    profile = profileValue;
  }
  final structures = _validateCountryList(
    decoded['structures'],
    'config.structures',
    path,
  );
  return _Config(
    profile: profile,
    structures: structures,
    locales: _validateLocales(decoded['locales'], structures, path),
    catalogLocales: _validateLocaleList(
      decoded['catalogLocales'],
      'config.catalogLocales',
      path,
    ),
  );
}

List<String> _validateCountryList(Object? value, String field, String path) {
  if (value is! List) {
    throw CliError(kExitConfig, '$field: array required');
  }
  final seen = <String>{};
  final codes = <String>[];
  for (var i = 0; i < value.length; i++) {
    final item = value[i];
    if (item is! String || !_countryPattern.hasMatch(item)) {
      throw CliError(
        kExitConfig,
        '$field[$i]: ISO-style uppercase alpha-2 country code required, got $item',
      );
    }
    if (!seen.add(item)) {
      throw CliError(kExitConfig, '$field[$i]: duplicate country code $item');
    }
    codes.add(item);
  }
  return codes;
}

/// Validates `config.locales` and enforces that its keys are a subset of
/// [structures] (schema description: "Keys must be a subset of structures").
Map<String, List<String>> _validateLocales(
  Object? value,
  List<String> structures,
  String path,
) {
  if (value is! Map<String, Object?>) {
    throw CliError(kExitConfig, 'config.locales: object required');
  }
  final result = <String, List<String>>{};
  for (final entry in value.entries) {
    if (!structures.contains(entry.key)) {
      throw CliError(
        kExitConfig,
        'config.locales: key "${entry.key}" is not listed in config.structures',
      );
    }
    result[entry.key] = _validateLocaleList(
      entry.value,
      'config.locales["${entry.key}"]',
      path,
    );
  }
  return result;
}

List<String> _validateLocaleList(Object? value, String field, String path) {
  if (value is! List) {
    throw CliError(kExitConfig, '$field: array required');
  }
  final seen = <String>{};
  final tags = <String>[];
  for (var i = 0; i < value.length; i++) {
    final item = value[i];
    if (item is! String || item.length < 2) {
      throw CliError(
        kExitConfig,
        '$field[$i]: locale tag (min length 2) required, got $item',
      );
    }
    if (!_localePattern.hasMatch(item)) {
      throw CliError(
        kExitConfig,
        '$field[$i]: unsafe locale tag "$item" (single BCP 47-style segment required)',
      );
    }
    if (!seen.add(item)) {
      throw CliError(kExitConfig, '$field[$i]: duplicate locale $item');
    }
    tags.add(item);
  }
  return tags;
}

/// Loads the full data manifest and verifies every selected resource
/// (existence, SHA-256, byte count) plus the compatibility chain
/// (locale packs vs structure revision, catalog locales vs catalog revision).
_Plan _buildPlan(String dataRoot, _Config config) {
  final manifestFile = File('$dataRoot/$kManifestName');
  if (!manifestFile.existsSync()) {
    throw CliError(
      kExitResource,
      'package data manifest not found: ${manifestFile.path}',
    );
  }
  final raw = _decodeJsonObjectFile(manifestFile, 'package data manifest');
  try {
    parseManifest(raw);
  } on GeoParseFailureError catch (error) {
    throw CliError(
      kExitResource,
      'invalid package data manifest: ${error.message}',
    );
  }
  final rawEntries = <String, Map<String, Object?>>{};
  final fullRawResources = <Map<String, Object?>>[];
  for (final item in raw['resources'] as List<Object?>) {
    final entry = item as Map<String, Object?>;
    fullRawResources.add(entry);
    rawEntries[entry['path'] as String] = entry;
  }
  final selectedPaths = _selectedPaths(config);
  final missing = selectedPaths
      .where((path) => !rawEntries.containsKey(path))
      .toList();
  if (missing.isNotEmpty) {
    throw CliError(
      kExitResource,
      'selected resource missing: ${missing.join(', ')}',
    );
  }
  final fileBytes = _readAndVerifySelected(dataRoot, selectedPaths, rawEntries);
  final revisions = _checkCompatibility(dataRoot, config, rawEntries);
  return _Plan(
    protocolVersion: raw['protocolVersion'] as String,
    datasetId: raw['datasetId'] as String,
    fullRevision: raw['revision'] as String,
    fullRawResources: fullRawResources,
    selectedPaths: selectedPaths,
    rawEntries: rawEntries,
    fileBytes: fileBytes,
    structureRevisions: revisions.structureRevisions,
    catalogRevision: revisions.catalogRevision,
  );
}

List<String> _selectedPaths(_Config config) {
  final paths = <String>{'countries.json'};
  for (final code in config.structures) {
    paths.add('regions/$code.json');
  }
  for (final entry in config.locales.entries) {
    for (final tag in entry.value) {
      paths.add('i18n/$tag/${entry.key}.json');
    }
  }
  for (final tag in config.catalogLocales) {
    paths.add('catalog_i18n/$tag.json');
  }
  return paths.toList()..sort(compareJsonKeys);
}

/// Reads each selected file and verifies it against the manifest entry
/// (presence, SHA-256 over the full file bytes, byte count).
Map<String, List<int>> _readAndVerifySelected(
  String dataRoot,
  List<String> selectedPaths,
  Map<String, Map<String, Object?>> rawEntries,
) {
  final fileBytes = <String, List<int>>{};
  for (final path in selectedPaths) {
    final file = File('$dataRoot/$path');
    if (!file.existsSync()) {
      throw CliError(kExitResource, 'missing resource file: $path');
    }
    final bytes = file.readAsBytesSync();
    final entry = rawEntries[path]!;
    final digest = geoSha256Hex(bytes);
    if (entry['sha256'] != digest) {
      throw CliError(
        kExitResource,
        'corrupt resource (sha256 mismatch): $path '
        '(expected ${entry['sha256']}, got $digest)',
      );
    }
    if (entry['bytes'] != bytes.length) {
      throw CliError(
        kExitResource,
        'corrupt resource (byte count mismatch): $path '
        '(expected ${entry['bytes']}, got ${bytes.length})',
      );
    }
    fileBytes[path] = bytes;
  }
  return fileBytes;
}

/// The compatibility chain: every file's own revision must match its
/// manifest entry, locale packs must pin the exact current structure
/// revision and catalog packs the exact catalog revision ("stale config"
/// detection — never auto-repaired).
({Map<String, String> structureRevisions, String catalogRevision})
_checkCompatibility(
  String dataRoot,
  _Config config,
  Map<String, Map<String, Object?>> rawEntries,
) {
  final countries = _decodeJsonObjectFile(
    File('$dataRoot/countries.json'),
    'resource countries.json',
  );
  final catalogRevision = _consistentRevision(
    countries,
    'countries.json',
    rawEntries,
  );
  final structureRevisions = <String, String>{};
  for (final code in config.structures) {
    final path = 'regions/$code.json';
    final obj = _decodeJsonObjectFile(
      File('$dataRoot/$path'),
      'resource $path',
    );
    structureRevisions[code] = _consistentRevision(obj, path, rawEntries);
  }
  for (final entry in config.locales.entries) {
    for (final tag in entry.value) {
      final path = 'i18n/$tag/${entry.key}.json';
      final obj = _decodeJsonObjectFile(
        File('$dataRoot/$path'),
        'resource $path',
      );
      _consistentRevision(obj, path, rawEntries);
      final compatible = obj['compatibleStructureRevision'];
      final expected = structureRevisions[entry.key];
      if (compatible is! String || compatible != expected) {
        throw CliError(
          kExitResource,
          'stale config: $path pins structure revision $compatible but '
          'regions/${entry.key}.json is $expected; regenerate or update the config',
        );
      }
    }
  }
  for (final tag in config.catalogLocales) {
    final path = 'catalog_i18n/$tag.json';
    final obj = _decodeJsonObjectFile(
      File('$dataRoot/$path'),
      'resource $path',
    );
    _consistentRevision(obj, path, rawEntries);
    final compatible = obj['compatibleCatalogRevision'];
    if (compatible is! String || compatible != catalogRevision) {
      throw CliError(
        kExitResource,
        'stale config: $path pins catalog revision $compatible but '
        'countries.json is $catalogRevision; regenerate or update the config',
      );
    }
  }
  return (
    structureRevisions: structureRevisions,
    catalogRevision: catalogRevision,
  );
}

/// Returns the file's own revision and fails when it disagrees with the
/// manifest entry (a stale or hand-edited manifest).
String _consistentRevision(
  Map<String, Object?> obj,
  String path,
  Map<String, Map<String, Object?>> rawEntries,
) {
  final revision = obj['revision'];
  if (revision is! String || revision.isEmpty) {
    throw CliError(kExitResource, 'corrupt resource (missing revision): $path');
  }
  final declared = rawEntries[path]?['revision'];
  if (declared != revision) {
    throw CliError(
      kExitResource,
      'stale data manifest: $path is $revision but the manifest declares $declared',
    );
  }
  return revision;
}

Map<String, Object?> _decodeJsonObjectFile(File file, String description) {
  String text;
  try {
    text = file.readAsStringSync();
  } on IOException catch (error) {
    throw CliError(
      kExitResource,
      '$description: cannot read ${file.path}: $error',
    );
  }
  final Object? decoded;
  try {
    decoded = jsonDecode(text);
  } on FormatException catch (error) {
    throw CliError(
      kExitResource,
      '$description: invalid JSON in ${file.path}: ${error.message}',
    );
  }
  if (decoded is! Map<String, Object?>) {
    throw CliError(
      kExitResource,
      '$description: JSON object required in ${file.path}',
    );
  }
  return decoded;
}

/// Writes the staged bundle: payload copies, subset manifest, descriptor
/// registry, fragment, report and marker; self-checks the staged manifest.
Map<String, Object?> _writeStagedBundle(
  Directory staging,
  _Config config,
  _Plan plan,
  _Options options,
) {
  final generatedAt = DateTime.now().toUtc().toIso8601String();
  for (final path in plan.selectedPaths) {
    final target = File('${staging.path}/$path');
    target.parent.createSync(recursive: true);
    target.writeAsBytesSync(plan.fileBytes[path]!);
  }
  final selectedRaw = <Map<String, Object?>>[
    for (final path in plan.selectedPaths) plan.rawEntries[path]!,
  ];
  final subset = <String, Object?>{
    'protocolVersion': plan.protocolVersion,
    'datasetId': plan.datasetId,
    'revision': geoRevisionOf('m', selectedRaw),
    'resources': selectedRaw,
  };
  writeJsonFile('${staging.path}/$kManifestName', subset);
  writeJsonFile('${staging.path}/$kRegistryName', <String, Object?>{
    'protocolVersion': plan.protocolVersion,
    'datasetId': plan.datasetId,
    'revision': plan.fullRevision,
    'resources': <Map<String, Object?>>[
      for (final entry in plan.fullRawResources)
        <String, Object?>{
          ...entry,
          'bundled': plan.selectedPaths.contains(entry['path']),
        },
    ],
  });
  final fragmentPaths = <String>{
    ...plan.selectedPaths,
    kManifestName,
    kRegistryName,
  }.toList()..sort(compareJsonKeys);
  File('${staging.path}/assets.fragment.yaml')
      .writeAsStringSync(fragmentYaml(fragmentPaths));
  final report = _buildReport(config, plan, options, generatedAt);
  writeJsonFile('${staging.path}/report.json', report);
  File('${staging.path}/$kMarkerName').writeAsStringSync(
    'Generated by geo_regions assets CLI; safe replacement requires '
    '--replace and this marker.\ngeneratedAt: $generatedAt\n',
  );
  _selfCheckStagedManifest(staging);
  return report;
}

void _selfCheckStagedManifest(Directory staging) {
  final text = File('${staging.path}/$kManifestName').readAsStringSync();
  try {
    parseManifest(jsonDecode(text));
  } on GeoParseFailureError catch (error) {
    throw CliError(
      kExitUnexpected,
      'generated manifest failed self-check: ${error.message}',
    );
  }
}

Map<String, Object?> _buildReport(
  _Config config,
  _Plan plan,
  _Options options,
  String generatedAt,
) {
  final resources = <Map<String, Object?>>[];
  var uncompressedBytes = 0;
  var gzipBytes = 0;
  for (final path in plan.selectedPaths) {
    final bytes = plan.fileBytes[path]!;
    final compressed = gzip.encode(bytes).length;
    uncompressedBytes += bytes.length;
    gzipBytes += compressed;
    resources.add(<String, Object?>{
      'path': path,
      'bytes': bytes.length,
      'gzipBytes': compressed,
      'sha256': geoSha256Hex(bytes),
    });
  }
  return <String, Object?>{
    'profile': config.profile,
    'generatedAt': generatedAt,
    'datasetId': plan.datasetId,
    'configPath': options.configPath,
    'replace': options.replace,
    'structureRevisions': plan.structureRevisions,
    'catalogRevision': plan.catalogRevision,
    'resources': resources,
    'totals': <String, Object?>{
      'resourceFileCount': resources.length,
      'uncompressedBytes': uncompressedBytes,
      'gzipBytes': gzipBytes,
      'fragmentFileCount': plan.selectedPaths.length + 2,
    },
  };
}

void _printSummary(String output, Map<String, Object?> report) {
  final totals = report['totals'] as Map<String, Object?>;
  stdout.writeln(
    'geo_regions:assets: generated bundle with '
    '${totals['resourceFileCount']} resource file(s)',
  );
  stdout.writeln('  output: $output');
  stdout.writeln(
    '  uncompressed: ${totals['uncompressedBytes']} bytes; '
    'gzip estimate: ${totals['gzipBytes']} bytes',
  );
  stdout.writeln(
    '  fragment entries: ${totals['fragmentFileCount']} '
    '(merge into the host pubspec flutter.assets)',
  );
}

/// Parsed command-line options.
final class _Options {
  final String configPath;
  final String outputPath;
  final bool replace;

  const _Options({
    required this.configPath,
    required this.outputPath,
    required this.replace,
  });
}

/// Validated assets configuration (`config/assets.schema.json` semantics).
final class _Config {
  final String? profile;
  final List<String> structures;
  final Map<String, List<String>> locales;
  final List<String> catalogLocales;

  const _Config({
    required this.profile,
    required this.structures,
    required this.locales,
    required this.catalogLocales,
  });
}

/// Everything resolved from the package data needed to emit the bundle.
final class _Plan {
  final String protocolVersion;
  final String datasetId;
  final String fullRevision;
  final List<Map<String, Object?>> fullRawResources;
  final List<String> selectedPaths;
  final Map<String, Map<String, Object?>> rawEntries;
  final Map<String, List<int>> fileBytes;
  final Map<String, String> structureRevisions;
  final String catalogRevision;

  const _Plan({
    required this.protocolVersion,
    required this.datasetId,
    required this.fullRevision,
    required this.fullRawResources,
    required this.selectedPaths,
    required this.rawEntries,
    required this.fileBytes,
    required this.structureRevisions,
    required this.catalogRevision,
  });
}
