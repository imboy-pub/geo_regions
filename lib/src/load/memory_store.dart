// SPDX-License-Identifier: BSD-3-Clause
/// In-memory [GeoCacheStore] for tests, examples and host prototyping (P1-05).
///
/// The store keeps verified payloads in a plain map and exposes fault
/// injection hooks so read/write failures are deterministically reproducible
/// (PRD §11: "可故障 store"). Real hosts swap in a file/IndexedDB backed
/// implementation with the same [GeoCacheStore] contract; atomic durable
/// writes stay that implementation's responsibility (CONSUMER_CONTRACT §5).
library;

import 'contracts.dart';

/// Volatile cache store with injectable failures and a write log.
///
/// * [readFault] / [writeFault] return the error object to throw for a key,
///   or `null` to proceed; they make cache corruption and I/O failures
///   deterministic in tests.
/// * [writeLog] records every successful write in order, letting tests
///   assert that bad downloads never reach the cache (AT-08).
class GeoMemoryCacheStore implements GeoCacheStore {
  /// Creates an empty store with optional fault hooks.
  GeoMemoryCacheStore({
    Object? Function(GeoCacheKey key)? readFault,
    Object? Function(GeoCacheKey key)? writeFault,
  }) : _readFault = readFault,
       _writeFault = writeFault;

  Object? Function(GeoCacheKey key)? _readFault;

  Object? Function(GeoCacheKey key)? _writeFault;

  /// Replaces the read-fault hook (return an error to throw, `null` to pass).
  set readFault(Object? Function(GeoCacheKey key)? hook) => _readFault = hook;

  /// Replaces the write-fault hook (return an error to throw, `null` to pass).
  set writeFault(Object? Function(GeoCacheKey key)? hook) => _writeFault = hook;

  final Map<GeoCacheKey, GeoBytes> _entries = <GeoCacheKey, GeoBytes>{};

  /// Chronological log of successful writes; cleared by [clear].
  final List<GeoCacheKey> writeLog = <GeoCacheKey>[];

  @override
  Future<GeoBytes?> read(GeoCacheKey key) async {
    final fault = _readFault?.call(key);
    if (fault != null) {
      throw fault;
    }
    return _entries[key];
  }

  @override
  Future<void> write(GeoCacheKey key, GeoBytes bytes) async {
    final fault = _writeFault?.call(key);
    if (fault != null) {
      throw fault;
    }
    _entries[key] = bytes;
    writeLog.add(key);
  }

  @override
  Future<void> invalidate(GeoCacheKey key) async {
    _entries.remove(key);
  }

  @override
  Future<List<GeoCacheKey>> keys() async => List.of(_entries.keys);

  @override
  Future<int> totalSize() async {
    var total = 0;
    for (final bytes in _entries.values) {
      total += bytes.length;
    }
    return total;
  }

  @override
  Future<void> clear() async {
    _entries.clear();
    writeLog.clear();
  }
}
