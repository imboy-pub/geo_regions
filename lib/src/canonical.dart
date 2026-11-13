// SPDX-License-Identifier: BSD-3-Clause
/// Canonical serialization C(x) from PROTOCOL.md §6.
///
/// C(x) is UTF-8 JSON with recursively sorted object keys, preserved array
/// order, literal Unicode (`ensure_ascii=false`), no extra whitespace
/// (`separators=(',', ':')`), no trailing newline and no non-finite numbers.
/// The Python reference lives in `tool/geo_data.py::canonical`; this Dart
/// implementation is aligned by cross-language golden vectors pinned in
/// `test/revision_test.dart` and by recomputing the revisions embedded in the
/// repository's own `data/` files.
///
/// Known, documented boundaries:
/// * Floating-point numbers are rejected with a [FormatException]. Protocol
///   payloads use integers, strings, booleans, null, arrays and objects only
///   (see `schemas/`), so accepting doubles would risk silently producing
///   digests that disagree with the Python reference. Non-finite numbers are
///   rejected for the same reason Python's `allow_nan=false` rejects them.
/// * `dart:convert`'s `jsonDecode` cannot detect byte-level duplicate object
///   keys. The duplicate-key defense line is the host integrity chain
///   (SHA-256 verification precedes parsing); node-ID duplicates are always
///   detected after parsing by [parseRegionStructure].
library;

import 'dart:convert';

/// Serializes [value] into the canonical form C(x) described in
/// PROTOCOL.md §6.
///
/// Throws [FormatException] when [value] contains a type that cannot appear
/// in protocol payloads (doubles, non-string map keys, other objects).
String geoCanonicalJson(Object? value) {
  final buffer = StringBuffer();
  _writeValue(buffer, value);
  return buffer.toString();
}

/// Returns the UTF-8 bytes of `geoCanonicalJson(value)`.
List<int> geoCanonicalJsonBytes(Object? value) =>
    utf8.encode(geoCanonicalJson(value));

void _writeValue(StringBuffer out, Object? value) {
  if (value == null) {
    out.write('null');
  } else if (value is bool) {
    out.write(value ? 'true' : 'false');
  } else if (value is int) {
    out.write(value.toString());
  } else if (value is String) {
    _writeString(out, value);
  } else if (value is List) {
    _writeList(out, value);
  } else if (value is Map) {
    _writeMap(out, value);
  } else if (value is double) {
    throw FormatException(
      'C(x) rejects floating-point numbers; protocol payloads are '
      'integer-only (${value.runtimeType}: $value)',
    );
  } else {
    throw FormatException(
      'C(x) cannot serialize value of type ${value.runtimeType}',
    );
  }
}

void _writeList(StringBuffer out, List value) {
  out.write('[');
  for (var i = 0; i < value.length; i++) {
    if (i > 0) {
      out.write(',');
    }
    _writeValue(out, value[i]);
  }
  out.write(']');
}

void _writeMap(StringBuffer out, Map value) {
  final keys = <String>[];
  for (final key in value.keys) {
    if (key is! String) {
      throw FormatException(
        'C(x) requires string object keys, got ${key.runtimeType}',
      );
    }
    keys.add(key);
  }
  keys.sort(compareJsonKeys);
  out.write('{');
  for (var i = 0; i < keys.length; i++) {
    if (i > 0) {
      out.write(',');
    }
    _writeString(out, keys[i]);
    out.write(':');
    _writeValue(out, value[keys[i]]);
  }
  out.write('}');
}

/// Escapes exactly what Python's JSON encoder escapes with
/// `ensure_ascii=false`: quote, backslash, and control characters below
/// U+0020 (short escapes for \b \t \n \f \r, lowercase `\u00xx` otherwise).
/// All other code units, including DEL and astral characters, stay literal.
void _writeString(StringBuffer out, String value) {
  out.write('"');
  for (var i = 0; i < value.length; i++) {
    final unit = value.codeUnitAt(i);
    switch (unit) {
      case 0x22:
        out.write(r'\"');
      case 0x5c:
        out.write(r'\\');
      case 0x08:
        out.write(r'\b');
      case 0x09:
        out.write(r'\t');
      case 0x0a:
        out.write(r'\n');
      case 0x0c:
        out.write(r'\f');
      case 0x0d:
        out.write(r'\r');
      default:
        if (unit < 0x20) {
          out.write('\\u${unit.toRadixString(16).padLeft(4, '0')}');
        } else {
          out.writeCharCode(unit);
        }
    }
  }
  out.write('"');
}

/// Compares two strings by Unicode code point, matching Python's default
/// `str` ordering used by `sort_keys=True`.
///
/// Comparing UTF-16 code units directly (Dart's `String.compareTo`) would
/// order astral characters before U+E000..U+FFFF; code-point comparison keeps
/// key ordering identical to the Python reference.
int compareJsonKeys(String a, String b) {
  final ai = a.runes.iterator;
  final bi = b.runes.iterator;
  while (ai.moveNext() && bi.moveNext()) {
    if (ai.current != bi.current) {
      return ai.current < bi.current ? -1 : 1;
    }
  }
  if (ai.moveNext()) {
    return 1;
  }
  if (bi.moveNext()) {
    return -1;
  }
  return 0;
}
