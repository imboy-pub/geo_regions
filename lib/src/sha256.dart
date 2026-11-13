// SPDX-License-Identifier: BSD-3-Clause
/// Pure-Dart SHA-256 (FIPS 180-4) used for protocol revision computation.
///
/// Why an in-tree implementation: the package runtime depends only on the
/// Flutter/Dart SDK (PRD GR-12 forbids third-party runtime packages) while
/// PROTOCOL.md §6 requires SHA-256 over the canonical serialization C(x) for
/// every content revision. The PRD §8 prohibition on hand-rolled cryptography
/// targets remote-resource verification, where hashing stays behind the
/// injected `GeoHashVerifier` host interface (CONSUMER_CONTRACT §5); this
/// module is the data layer's digest primitive for revisions, not a
/// substitute for the injected verifier.
///
/// FIPS 180-4 test vectors are pinned in `test/sha256_test.dart`, including
/// the empty string and the classic multi-block vectors, plus a digest of a
/// real repository resource cross-checked against the manifest.
library;

import 'dart:convert';
import 'dart:typed_data';

/// Table of round constants from FIPS 180-4 §4.2.2.
const List<int> _roundConstants = <int>[
  0x428a2f98,
  0x71374491,
  0xb5c0fbcf,
  0xe9b5dba5,
  0x3956c25b,
  0x59f111f1,
  0x923f82a4,
  0xab1c5ed5,
  0xd807aa98,
  0x12835b01,
  0x243185be,
  0x550c7dc3,
  0x72be5d74,
  0x80deb1fe,
  0x9bdc06a7,
  0xc19bf174,
  0xe49b69c1,
  0xefbe4786,
  0x0fc19dc6,
  0x240ca1cc,
  0x2de92c6f,
  0x4a7484aa,
  0x5cb0a9dc,
  0x76f988da,
  0x983e5152,
  0xa831c66d,
  0xb00327c8,
  0xbf597fc7,
  0xc6e00bf3,
  0xd5a79147,
  0x06ca6351,
  0x14292967,
  0x27b70a85,
  0x2e1b2138,
  0x4d2c6dfc,
  0x53380d13,
  0x650a7354,
  0x766a0abb,
  0x81c2c92e,
  0x92722c85,
  0xa2bfe8a1,
  0xa81a664b,
  0xc24b8b70,
  0xc76c51a3,
  0xd192e819,
  0xd6990624,
  0xf40e3585,
  0x106aa070,
  0x19a4c116,
  0x1e376c08,
  0x2748774c,
  0x34b0bcb5,
  0x391c0cb3,
  0x4ed8aa4a,
  0x5b9cca4f,
  0x682e6ff3,
  0x748f82ee,
  0x78a5636f,
  0x84c87814,
  0x8cc70208,
  0x90befffa,
  0xa4506ceb,
  0xbef9a3f7,
  0xc67178f2,
];

/// Initial hash values from FIPS 180-4 §5.3.3.
const List<int> _initialHash = <int>[
  0x6a09e667,
  0xbb67ae85,
  0x3c6ef372,
  0xa54ff53a,
  0x510e527f,
  0x9b05688c,
  0x1f83d9ab,
  0x5be0cd19,
];

const int _mask32 = 0xffffffff;

int _rotr(int value, int bits) =>
    ((value >> bits) | (value << (32 - bits))) & _mask32;

/// Computes the SHA-256 digest of [bytes] and returns it as 64 lowercase hex
/// characters (FIPS 180-4).
String geoSha256Hex(List<int> bytes) {
  final state = Uint32List.fromList(_initialHash);
  final padded = _paddedCopy(bytes);
  final schedule = Uint32List(64);
  for (var offset = 0; offset < padded.length; offset += 64) {
    _compressBlock(padded, offset, schedule, state);
  }
  final buffer = StringBuffer();
  for (final word in state) {
    buffer.write(word.toRadixString(16).padLeft(8, '0'));
  }
  return buffer.toString();
}

/// Computes the SHA-256 digest of the UTF-8 encoding of [text].
String geoSha256HexOfString(String text) => geoSha256Hex(utf8.encode(text));

/// Returns a copy of [bytes] with the FIPS 180-4 §5.1.1 padding applied.
Uint8List _paddedCopy(List<int> bytes) {
  final bitLength = bytes.length * 8;
  final paddedLength = ((bytes.length + 8) ~/ 64 + 1) * 64;
  final padded = Uint8List(paddedLength)..setRange(0, bytes.length, bytes);
  padded[bytes.length] = 0x80;
  for (var i = 0; i < 8; i++) {
    padded[paddedLength - 1 - i] = (bitLength >> (8 * i)) & 0xff;
  }
  return padded;
}

/// Fills [schedule] with the 64-word message schedule of one block
/// (FIPS 180-4 §6.2.2 steps 1–2).
void _prepareSchedule(Uint8List padded, int offset, Uint32List schedule) {
  for (var t = 0; t < 16; t++) {
    final base = offset + 4 * t;
    schedule[t] =
        (padded[base] << 24) |
        (padded[base + 1] << 16) |
        (padded[base + 2] << 8) |
        padded[base + 3];
  }
  for (var t = 16; t < 64; t++) {
    final s0 =
        _rotr(schedule[t - 15], 7) ^
        _rotr(schedule[t - 15], 18) ^
        (schedule[t - 15] >> 3);
    final s1 =
        _rotr(schedule[t - 2], 17) ^
        _rotr(schedule[t - 2], 19) ^
        (schedule[t - 2] >> 10);
    schedule[t] = (schedule[t - 16] + s0 + schedule[t - 7] + s1) & _mask32;
  }
}

/// Runs the compression function over one 512-bit block, updating [state]
/// (FIPS 180-4 §6.2.2 steps 3–4).
void _compressBlock(
  Uint8List padded,
  int offset,
  Uint32List schedule,
  Uint32List state,
) {
  _prepareSchedule(padded, offset, schedule);
  var a = state[0];
  var b = state[1];
  var c = state[2];
  var d = state[3];
  var e = state[4];
  var f = state[5];
  var g = state[6];
  var h = state[7];
  for (var t = 0; t < 64; t++) {
    final bigS1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25);
    final choose = (e & f) ^ ((~e & _mask32) & g);
    final temp1 =
        (h + bigS1 + choose + _roundConstants[t] + schedule[t]) & _mask32;
    final bigS0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22);
    final majority = (a & b) ^ (a & c) ^ (b & c);
    final temp2 = (bigS0 + majority) & _mask32;
    h = g;
    g = f;
    f = e;
    e = (d + temp1) & _mask32;
    d = c;
    c = b;
    b = a;
    a = (temp1 + temp2) & _mask32;
  }
  _applyWorkingState(state, a, b, c, d, e, f, g, h);
}

/// Adds the working variables back into the chained state words.
void _applyWorkingState(
  Uint32List state,
  int a,
  int b,
  int c,
  int d,
  int e,
  int f,
  int g,
  int h,
) {
  state[0] = (state[0] + a) & _mask32;
  state[1] = (state[1] + b) & _mask32;
  state[2] = (state[2] + c) & _mask32;
  state[3] = (state[3] + d) & _mask32;
  state[4] = (state[4] + e) & _mask32;
  state[5] = (state[5] + f) & _mask32;
  state[6] = (state[6] + g) & _mask32;
  state[7] = (state[7] + h) & _mask32;
}
