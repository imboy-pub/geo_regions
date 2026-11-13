// SPDX-License-Identifier: BSD-3-Clause
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_data.dart';

void main() {
  test('FIPS 180-4 single-block vectors', () {
    expect(
      geoSha256HexOfString(''),
      'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    );
    expect(
      geoSha256HexOfString('abc'),
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    );
    expect(
      geoSha256Hex([0x61, 0x62, 0x63]),
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    );
  });

  test('FIPS 180-4 padding-boundary and multi-block vectors', () {
    expect(
      geoSha256HexOfString('a' * 55),
      '9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318',
    );
    expect(
      geoSha256HexOfString('a' * 64),
      'ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb',
    );
    expect(
      geoSha256HexOfString(
        'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq',
      ),
      '248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1',
    );
  });

  test('UTF-8 multibyte input', () {
    expect(
      geoSha256HexOfString('中文'),
      '72726d8818f693066ceb69afa364218b692e62ea92b385782363780f47529c21',
    );
  });

  test('digest matches the manifest SHA-256 of a real resource', () {
    final manifest = loadManifest();
    final entry = manifest.entryFor('catalog_i18n/ar.json');
    expect(entry, isNotNull);
    final bytes = File('data/catalog_i18n/ar.json').readAsBytesSync();
    expect(geoSha256Hex(bytes), entry!.sha256);
    expect(bytes.length, entry.bytes);
  });
}
