// SPDX-License-Identifier: BSD-3-Clause
/// Typed error taxonomy for geo_regions (CONSUMER_CONTRACT.md §2).
///
/// Hosts must be able to distinguish the seven failure classes below without
/// string matching. Conditions are never collapsed into "empty children" or a
/// generic runtime error. Every error carries a stable [GeoException.errorCode]
/// string matching the contract table:
///
/// | Class                          | errorCode            |
/// |--------------------------------|----------------------|
/// | [GeoNetworkError]              | `network`            |
/// | [GeoNotFoundError]             | `notFound`           |
/// | [GeoUnsupportedVersionError]   | `unsupportedVersion` |
/// | [GeoIntegrityMismatchError]    | `integrityMismatch`  |
/// | [GeoParseFailureError]         | `parseFailure`       |
/// | [GeoUnknownCoverageError]      | `unknownCoverage`    |
/// | [GeoConfigurationError]        | `configurationError` |
library;

/// Base type of every typed geo_regions failure.
///
/// The class is sealed: all variants live in this library, so hosts can use
/// exhaustive `switch` pattern matching over it.
sealed class GeoException implements Exception {
  /// Creates a typed error with a human-readable diagnostic [message].
  const GeoException(this.message);

  /// Human-readable diagnostic; never parsed for control flow.
  final String message;

  /// Stable machine-readable code from CONSUMER_CONTRACT.md §2.
  String get errorCode;

  @override
  String toString() => '$runtimeType($errorCode): $message';
}

/// Transport failure, timeout or connection loss while loading a resource.
///
/// Never conflated with "the region has no children".
final class GeoNetworkError extends GeoException {
  /// Creates a network failure diagnostic.
  const GeoNetworkError(super.message);

  @override
  String get errorCode => 'network';
}

/// A resource, country, node ID or selection target does not exist.
///
/// Covers HTTP 404, resources absent from the manifest, unknown node IDs in a
/// selection and selections that reference a different dataset namespace.
final class GeoNotFoundError extends GeoException {
  /// Creates a not-found diagnostic.
  const GeoNotFoundError(super.message);

  @override
  String get errorCode => 'notFound';
}

/// `protocolVersion` or a revision is outside the set this SDK supports.
///
/// The SDK accepts exactly the protocol versions it was built for; it never
/// "defaults to compatible" for future minors (CONSUMER_CONTRACT §6).
final class GeoUnsupportedVersionError extends GeoException {
  /// Creates an unsupported-version diagnostic.
  const GeoUnsupportedVersionError(super.message);

  @override
  String get errorCode => 'unsupportedVersion';
}

/// Content identity does not match: file length or SHA-256 mismatch, or a
/// revision label that disagrees with the payload it claims to describe.
///
/// Byte-length and SHA-256 checks happen in the host loader before any JSON
/// decoding; revision-vs-content checks happen in this SDK's parser.
final class GeoIntegrityMismatchError extends GeoException {
  /// Creates an integrity-mismatch diagnostic.
  const GeoIntegrityMismatchError(super.message);

  @override
  String get errorCode => 'integrityMismatch';
}

/// Bytes were transport- and integrity-valid but the JSON is syntactically or
/// semantically invalid: schema violations, duplicate IDs, cycles, cross
/// country parents, dangling translation IDs, malformed selections.
final class GeoParseFailureError extends GeoException {
  /// Creates a parse-failure diagnostic.
  const GeoParseFailureError(super.message);

  @override
  String get errorCode => 'parseFailure';
}

/// The coverage of a node is unknown (`childrenStatus: unknown`).
///
/// Such a node must not be presented as "has no child regions"; hosts that
/// need guaranteed completeness call [GeoRegionIndex.requireKnownCoverage]
/// before treating a node as a leaf.
final class GeoUnknownCoverageError extends GeoException {
  /// Creates an unknown-coverage diagnostic.
  const GeoUnknownCoverageError(super.message);

  @override
  String get errorCode => 'unknownCoverage';
}

/// The SDK was misconfigured by the embedding host.
///
/// Examples: strict remote mode without an injected verifier, an index mixing
/// structures from different datasets, a display snapshot that does not match
/// the selection path length.
final class GeoConfigurationError extends GeoException {
  /// Creates a configuration diagnostic.
  const GeoConfigurationError(super.message);

  @override
  String get errorCode => 'configurationError';
}
