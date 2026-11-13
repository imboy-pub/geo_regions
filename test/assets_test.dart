// SPDX-License-Identifier: BSD-3-Clause
/// Integration tests for the `bin/assets.dart` CLI (P1-06).
///
/// The CLI runs as a real subprocess (`dart run <repo>/bin/assets.dart`),
/// so every test exercises the actual exit-code contract, the artifact
/// files on disk and the package_config-based package root resolution.
/// The suite keeps the number of process-level CLI invocations at 10
/// (each `dart run` pays VM startup); later test groups reuse the artifacts
/// of the first successful run.
///
/// Temp directories are created with `Directory.systemTemp.createTemp` and
/// immediately resolved to their real path: on macOS `/var` is a symlink
/// and the CLI (by design) rejects output paths whose ancestor chain
/// contains a symlink.
@Timeout(Duration(minutes: 6))
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/src/revision.dart' show geoRevisionOf;
import 'package:geo_regions/src/sha256.dart' show geoSha256Hex;

void main() {
  tearDownAll(_deleteTempRoots);

  test('two country x locale combos produce the exact file set', () async {
    final bundle = await _primaryBundle();
    final files = _relativeFiles(bundle.outPath);
    expect(files, <String>{
      '.geo_regions_generation',
      'assets.fragment.yaml',
      'catalog_i18n/en.json',
      'countries.json',
      'i18n/en/CN.json',
      'i18n/ja/JP.json',
      'i18n/zh-Hans/CN.json',
      'manifest.json',
      'regions/CN.json',
      'regions/JP.json',
      'registry.json',
      'report.json',
    });
    // Unselected payloads must not land next to the selected ones.
    expect(File('${bundle.outPath}/regions/KR.json').existsSync(), isFalse);
    expect(
      File('${bundle.outPath}/i18n/zh-Hans/JP.json').existsSync(),
      isFalse,
    );
    expect(File('${bundle.outPath}/i18n/ja/CN.json').existsSync(), isFalse);
    expect(File('${bundle.outPath}/i18n/en/JP.json').existsSync(), isFalse);
    expect(
      File('${bundle.outPath}/catalog_i18n/ar.json').existsSync(),
      isFalse,
    );
  });

  test('copied payload bytes and manifest subset match the source', () async {
    final bundle = await _primaryBundle();
    final manifest = _decodeJsonFile(
      '${bundle.outPath}/manifest.json',
    ) as Map<String, Object?>;
    expect(manifest['protocolVersion'], '1.0');
    expect(manifest['datasetId'], 'geo-regions-seed');
    final resources = manifest['resources'] as List<Object?>;
    final paths = <String>[
      for (final entry in resources)
        (entry! as Map<String, Object?>)['path'] as String,
    ];
    expect(paths, <String>[
      'catalog_i18n/en.json',
      'countries.json',
      'i18n/en/CN.json',
      'i18n/ja/JP.json',
      'i18n/zh-Hans/CN.json',
      'regions/CN.json',
      'regions/JP.json',
    ]);
    for (final entry in resources) {
      final item = entry! as Map<String, Object?>;
      final path = item['path'] as String;
      final copied = File('${bundle.outPath}/$path').readAsBytesSync();
      final source = File('${_repoRoot!}/data/$path').readAsBytesSync();
      expect(copied, equals(source), reason: '$path bytes differ from source');
      expect(item['sha256'], geoSha256Hex(source), reason: path);
      expect(item['bytes'], source.length, reason: path);
    }
    expect(manifest['revision'], geoRevisionOf('m', resources));
  });

  test(
    'registry lists all 121 descriptors with correct bundled flags',
    () async {
      final bundle = await _primaryBundle();
      final registry = _decodeJsonFile(
        '${bundle.outPath}/registry.json',
      ) as Map<String, Object?>;
      expect(registry['protocolVersion'], '1.0');
      expect(registry['datasetId'], 'geo-regions-seed');
      final sourceManifest = _decodeJsonFile(
        '${_repoRoot!}/data/manifest.json',
      ) as Map<String, Object?>;
      expect(registry['revision'], sourceManifest['revision']);
      final resources = registry['resources'] as List<Object?>;
      expect(resources.length, 121);
      final bundled = <String, bool>{};
      for (final entry in resources) {
        final item = entry! as Map<String, Object?>;
        bundled[item['path'] as String] = item['bundled'] as bool;
      }
      expect(bundled.length, 121);
      expect(bundled['countries.json'], isTrue);
      expect(bundled['regions/CN.json'], isTrue);
      expect(bundled['regions/JP.json'], isTrue);
      expect(bundled['i18n/en/CN.json'], isTrue);
      expect(bundled['i18n/ja/JP.json'], isTrue);
      expect(bundled['i18n/zh-Hans/CN.json'], isTrue);
      expect(bundled['catalog_i18n/en.json'], isTrue);
      expect(bundled.values.where((flag) => flag).length, 7);
      expect(bundled['regions/KR.json'], isFalse);
      expect(bundled['i18n/ja/CN.json'], isFalse);
      expect(bundled['catalog_i18n/ar.json'], isFalse);
    },
  );

  test(
    'fragment lists precise per-file entries without directory lines',
    () async {
      final bundle = await _primaryBundle();
      final fragment = File('${bundle.outPath}/assets.fragment.yaml')
          .readAsStringSync();
      expect(fragment, startsWith('#'));
      expect(fragment, contains('flutter:\n  assets:'));
      final entries = _fragmentEntries(fragment);
      expect(entries, <String>[
        'packages/geo_regions/data/catalog_i18n/en.json',
        'packages/geo_regions/data/countries.json',
        'packages/geo_regions/data/i18n/en/CN.json',
        'packages/geo_regions/data/i18n/ja/JP.json',
        'packages/geo_regions/data/i18n/zh-Hans/CN.json',
        'packages/geo_regions/data/manifest.json',
        'packages/geo_regions/data/regions/CN.json',
        'packages/geo_regions/data/regions/JP.json',
        'packages/geo_regions/data/registry.json',
      ]);
      for (final entry in entries) {
        expect(
          entry.endsWith('.json'),
          isTrue,
          reason: 'directory line: $entry',
        );
      }
    },
  );

  test('report.json audit is coherent (gzip < uncompressed)', () async {
    final bundle = await _primaryBundle();
    final report = _decodeJsonFile(
      '${bundle.outPath}/report.json',
    ) as Map<String, Object?>;
    expect(report['profile'], 'cli-two-countries');
    expect(report['replace'], false);
    final generatedAt = DateTime.parse(report['generatedAt'] as String);
    expect(generatedAt.timeZoneOffset, Duration.zero, reason: 'UTC required');
    final structureRevisions =
        report['structureRevisions'] as Map<String, Object?>;
    expect(structureRevisions['CN'], _sourceRevision('regions/CN.json'));
    expect(structureRevisions['JP'], _sourceRevision('regions/JP.json'));
    expect(report['catalogRevision'], _sourceRevision('countries.json'));
    final resources = report['resources'] as List<Object?>;
    expect(resources.length, 7);
    var uncompressed = 0;
    var compressed = 0;
    for (final entry in resources) {
      final item = entry! as Map<String, Object?>;
      final path = item['path'] as String;
      final source = File('${_repoRoot!}/data/$path').readAsBytesSync();
      expect(item['bytes'], source.length, reason: path);
      expect(item['sha256'], geoSha256Hex(source), reason: path);
      expect(item['gzipBytes'], gzip.encode(source).length, reason: path);
      expect(
        item['gzipBytes'] as int,
        lessThan(item['bytes'] as int),
        reason: path,
      );
      uncompressed += item['bytes'] as int;
      compressed += item['gzipBytes'] as int;
    }
    final totals = report['totals'] as Map<String, Object?>;
    expect(totals['resourceFileCount'], 7);
    expect(totals['fragmentFileCount'], 9);
    expect(totals['uncompressedBytes'], uncompressed);
    expect(totals['gzipBytes'], compressed);
    expect(
      totals['gzipBytes'] as int,
      lessThan(totals['uncompressedBytes'] as int),
    );
  });

  test('missing resource: unknown country fails with exit 3', () async {
    final root = await _newTempRoot();
    final configPath = '${root.path}/missing.json';
    File(configPath).writeAsStringSync(
      json.encode(<String, Object?>{
        'profile': 'missing-test',
        'structures': <String>['CN', 'XX'],
        'locales': <String, Object?>{},
        'catalogLocales': <String>['en'],
      }),
    );
    final outPath = '${root.path}/missing-out';
    final proc = await _runCli(['--config', configPath, '--out', outPath]);
    expect(
      proc.exitCode,
      3,
      reason: 'stdout: ${proc.stdout}\nstderr: ${proc.stderr}',
    );
    expect(proc.stderr, contains('selected resource missing'));
    expect(proc.stderr, contains('regions/XX.json'));
    expect(
      Directory(outPath).existsSync(),
      isFalse,
      reason: 'no partial output',
    );
  });

  test('stale config detected through the resolved package, exit 3', () async {
    final root = await _newTempRoot();
    final fakePkg = '${root.path}/fakepkg';
    _copyRepoData(fakePkg);
    _tamperStaleLocale('$fakePkg/data');
    final fakeCwd = '${root.path}/host';
    Directory('$fakeCwd/.dart_tool').createSync(recursive: true);
    File('$fakeCwd/.dart_tool/package_config.json').writeAsStringSync(
      json.encode(<String, Object?>{
        'configVersion': 2,
        'packages': <Object?>[
          <String, Object?>{
            'name': 'geo_regions',
            'rootUri': Uri.file('$fakePkg/').toString(),
            'languageVersion': '3.9',
          },
        ],
      }),
    );
    final configPath = '${root.path}/stale.json';
    File(configPath).writeAsStringSync(
      json.encode(<String, Object?>{
        'profile': 'stale-test',
        'structures': <String>['JP'],
        'locales': <String, Object?>{
          'JP': <String>['ja'],
        },
        'catalogLocales': <String>['en'],
      }),
    );
    final outPath = '${root.path}/stale-out';
    final proc = await _runCli([
      '--config',
      configPath,
      '--out',
      outPath,
    ], workingDirectory: fakeCwd);
    expect(
      proc.exitCode,
      3,
      reason: 'stdout: ${proc.stdout}\nstderr: ${proc.stderr}',
    );
    expect(proc.stderr, contains('stale config'));
    expect(proc.stderr, contains('i18n/ja/JP.json'));
    expect(
      Directory(outPath).existsSync(),
      isFalse,
      reason: 'no partial output',
    );
    // The failure can only come from the resolved fake package: the repo
    // data is consistent and would have exited 0.
  });

  test('symlink ancestor in output path is rejected with exit 4', () async {
    final root = await _newTempRoot();
    Directory('${root.path}/real').createSync();
    Link('${root.path}/link').createSync('real');
    final configPath = await _writeSmallConfig(root, 'symlink.json');
    final proc = await _runCli([
      '--config',
      configPath,
      '--out',
      '${root.path}/link/out',
    ]);
    expect(proc.exitCode, 4, reason: 'stderr: ${proc.stderr}');
    expect(proc.stderr, contains('symlink'));
    expect(
      Directory('${root.path}/real/out').existsSync(),
      isFalse,
      reason: 'nothing created through the symlink',
    );
  });

  test(
    'output overlapping the package data tree is rejected with exit 4',
    () async {
      final root = await _newTempRoot();
      final configPath = await _writeSmallConfig(root, 'unsafe.json');
      final proc = await _runCli([
        '--config',
        configPath,
        '--out',
        '${_repoRoot!}/data',
      ]);
      expect(proc.exitCode, 4, reason: 'stderr: ${proc.stderr}');
      expect(proc.stderr, contains('unsafe output'));
    },
  );

  test(
    'replace protection: marker-gated --replace keeps old artifacts safe',
    () async {
      final root = await _newTempRoot();
      final configPath = await _writeSmallConfig(root, 'replace.json');
      final outPath = '${root.path}/bundle';
      // First generation succeeds.
      final first = await _runCli(['--config', configPath, '--out', outPath]);
      expect(first.exitCode, 0, reason: 'stderr: ${first.stderr}');
      final manifestBefore = File('$outPath/manifest.json').readAsBytesSync();
      var reportBefore = File('$outPath/report.json').readAsBytesSync();
      // Second run without --replace is rejected and changes nothing.
      final second = await _runCli(['--config', configPath, '--out', outPath]);
      expect(second.exitCode, 4, reason: 'stderr: ${second.stderr}');
      expect(second.stderr, contains('--replace'));
      expect(File('$outPath/manifest.json').readAsBytesSync(), manifestBefore);
      // --replace with the marker regenerates the bundle; the manifest is
      // content-derived and stays identical while the report's timestamp
      // moves, proving regeneration actually happened.
      final third = await _runCli([
        '--config',
        configPath,
        '--out',
        outPath,
        '--replace',
      ]);
      expect(third.exitCode, 0, reason: 'stderr: ${third.stderr}');
      expect(File('$outPath/.geo_regions_generation').existsSync(), isTrue);
      expect(File('$outPath/manifest.json').readAsBytesSync(), manifestBefore);
      expect(
        File('$outPath/report.json').readAsBytesSync(),
        isNot(reportBefore),
      );
      reportBefore = File('$outPath/report.json').readAsBytesSync();
      // --replace without the marker (marker deleted) is refused and keeps
      // the previous bundle untouched.
      File('$outPath/.geo_regions_generation').deleteSync();
      final fourth = await _runCli([
        '--config',
        configPath,
        '--out',
        outPath,
        '--replace',
      ]);
      expect(fourth.exitCode, 4, reason: 'stderr: ${fourth.stderr}');
      expect(fourth.stderr, contains('.geo_regions_generation'));
      expect(File('$outPath/manifest.json').readAsBytesSync(), manifestBefore);
      expect(File('$outPath/report.json').readAsBytesSync(), reportBefore);
    },
  );

  test('online-only config emits the descriptor-only minimal bundle', () async {
    final root = await _newTempRoot();
    final outPath = '${root.path}/online';
    final proc = await _runCli([
      '--config',
      '${_repoRoot!}/config/assets.online-only.json',
      '--out',
      outPath,
    ]);
    expect(
      proc.exitCode,
      0,
      reason: 'stdout: ${proc.stdout}\nstderr: ${proc.stderr}',
    );
    final files = _relativeFiles(outPath);
    expect(files, <String>{
      '.geo_regions_generation',
      'assets.fragment.yaml',
      'catalog_i18n/en.json',
      'countries.json',
      'manifest.json',
      'registry.json',
      'report.json',
    });
    expect(Directory('$outPath/regions').existsSync(), isFalse);
    expect(Directory('$outPath/i18n').existsSync(), isFalse);
    final manifest =
        _decodeJsonFile('$outPath/manifest.json') as Map<String, Object?>;
    final paths = <String>[
      for (final entry in manifest['resources'] as List<Object?>)
        (entry! as Map<String, Object?>)['path'] as String,
    ];
    expect(paths, <String>['catalog_i18n/en.json', 'countries.json']);
    final registry =
        _decodeJsonFile('$outPath/registry.json') as Map<String, Object?>;
    final bundled = <String>[];
    for (final entry in registry['resources'] as List<Object?>) {
      final item = entry! as Map<String, Object?>;
      if (item['bundled'] as bool) {
        bundled.add(item['path'] as String);
      }
    }
    expect(registry['resources'] as List<Object?>, hasLength(121));
    expect(bundled, <String>['catalog_i18n/en.json', 'countries.json']);
    final entries = _fragmentEntries(
      File('$outPath/assets.fragment.yaml').readAsStringSync(),
    );
    expect(entries, <String>[
      'packages/geo_regions/data/catalog_i18n/en.json',
      'packages/geo_regions/data/countries.json',
      'packages/geo_regions/data/manifest.json',
      'packages/geo_regions/data/registry.json',
    ]);
  });
}

/// Result of one CLI subprocess invocation.
final class _Proc {
  final int exitCode;
  final String stdout;
  final String stderr;

  const _Proc(this.exitCode, this.stdout, this.stderr);
}

/// A completed bundle generation plus its temp root.
final class _Bundle {
  final Directory root;
  final String outPath;

  const _Bundle(this.root, this.outPath);
}

String? _repoRoot;

/// Runs the CLI as a subprocess; defaults to the repository root as working
/// directory (package_config.json lives in `<repoRoot>/.dart_tool/`).
Future<_Proc> _runCli(List<String> args, {String? workingDirectory}) async {
  final result = await Process.run(
    'dart',
    <String>['run', '$_repoRoot/bin/assets.dart', ...args],
    workingDirectory: workingDirectory ?? _repoRoot,
    stdoutEncoding: utf8,
    stderrEncoding: utf8,
  );
  return _Proc(
    result.exitCode,
    result.stdout as String,
    result.stderr as String,
  );
}

final List<Directory> _tempRoots = <Directory>[];

/// Creates a temp root and immediately resolves it: macOS `/var` is a
/// symlink and the CLI rejects symlinked ancestor chains by design.
Future<Directory> _newTempRoot() async {
  final created = await Directory.systemTemp.createTemp('geo_assets_cli-');
  final resolved = Directory(created.resolveSymbolicLinksSync());
  _tempRoots.add(resolved);
  return resolved;
}

void _deleteTempRoots() {
  for (final root in _tempRoots) {
    if (root.existsSync()) {
      root.deleteSync(recursive: true);
    }
  }
  _tempRoots.clear();
}

/// The first successful CLI run (memoized): two country x locale combos —
/// CN with zh-Hans/en and JP with ja — plus the `en` catalog locale.
Future<_Bundle> _primaryBundle() async {
  _repoRoot ??= _findRepoRoot();
  final root = await _newTempRoot();
  final configPath = '${root.path}/two-countries.json';
  File(configPath).writeAsStringSync(
    json.encode(<String, Object?>{
      'profile': 'cli-two-countries',
      'structures': <String>['CN', 'JP'],
      'locales': <String, Object?>{
        'CN': <String>['zh-Hans', 'en'],
        'JP': <String>['ja'],
      },
      'catalogLocales': <String>['en'],
    }),
  );
  final outPath = '${root.path}/bundle';
  final proc = await _runCli(['--config', configPath, '--out', outPath]);
  expect(
    proc.exitCode,
    0,
    reason: 'stdout: ${proc.stdout}\nstderr: ${proc.stderr}',
  );
  return _Bundle(root, outPath);
}

/// Minimal single-country config used by the guard/replace test groups.
Future<String> _writeSmallConfig(Directory root, String name) async {
  final configPath = '${root.path}/$name';
  File(configPath).writeAsStringSync(
    json.encode(<String, Object?>{
      'profile': 'cli-small',
      'structures': <String>['CN'],
      'locales': <String, Object?>{
        'CN': <String>['zh-Hans'],
      },
      'catalogLocales': <String>[],
    }),
  );
  return configPath;
}

void _copyRepoData(String fakePkgRoot) {
  _repoRoot ??= _findRepoRoot();
  Directory(fakePkgRoot).createSync(recursive: true);
  Directory('${_repoRoot!}/data').listSync(recursive: true).forEach((entity) {
    if (entity is! File) {
      return;
    }
    final relative = entity.path.substring('${_repoRoot!}/data/'.length);
    final target = File('$fakePkgRoot/data/$relative');
    target.parent.createSync(recursive: true);
    entity.copySync(target.path);
  });
}

/// Turns the copied locale pack stale: pins a non-existent structure
/// revision, then refreshes its manifest entry (sha256/bytes) and the
/// manifest revision so only the stale pin is left to detect.
void _tamperStaleLocale(String dataRoot) {
  final localePath = '$dataRoot/i18n/ja/JP.json';
  final locale = _decodeJsonFile(localePath) as Map<String, Object?>;
  locale['compatibleStructureRevision'] = 's-ffffffffffffffff';
  final newBytes = utf8.encode(json.encode(locale));
  File(localePath).writeAsBytesSync(newBytes);
  final manifestPath = '$dataRoot/manifest.json';
  final manifest = _decodeJsonFile(manifestPath) as Map<String, Object?>;
  final resources = manifest['resources'] as List<Object?>;
  for (final entry in resources) {
    final item = entry! as Map<String, Object?>;
    if (item['path'] == 'i18n/ja/JP.json') {
      item['sha256'] = geoSha256Hex(newBytes);
      item['bytes'] = newBytes.length;
    }
  }
  manifest['revision'] = geoRevisionOf('m', resources);
  File(manifestPath).writeAsStringSync(json.encode(manifest));
}

Object? _decodeJsonFile(String path) =>
    jsonDecode(File(path).readAsStringSync());

/// The revision of a repo data resource, read straight from the source file.
String _sourceRevision(String path) {
  final obj =
      _decodeJsonFile('${_repoRoot!}/data/$path') as Map<String, Object?>;
  return obj['revision'] as String;
}

/// All files under [dirPath] as relative POSIX-ish paths.
Set<String> _relativeFiles(String dirPath) {
  return Directory(dirPath)
      .listSync(recursive: true)
      .whereType<File>()
      .map((file) => file.path.substring(dirPath.length + 1))
      .toSet();
}

/// Extracts the `- "…"` asset entries of a generated fragment.
List<String> _fragmentEntries(String fragment) {
  return fragment
      .split('\n')
      .where((line) => line.trimLeft().startsWith('- '))
      .map((line) => line.trim().substring(2).replaceAll('"', ''))
      .toList();
}

/// Locates the repository root (data/ + .dart_tool present), tolerating a
/// working directory set elsewhere by the test runner.
String _findRepoRoot() {
  var dir = Directory.current;
  while (true) {
    if (File('${dir.path}/data/manifest.json').existsSync() &&
        File('${dir.path}/.dart_tool/package_config.json').existsSync()) {
      return dir.resolveSymbolicLinksSync();
    }
    final parent = dir.parent;
    if (parent.path == dir.path) {
      throw StateError(
        'repository root (data/ + .dart_tool/) not found above '
        '${Directory.current.path}',
      );
    }
    dir = parent;
  }
}
