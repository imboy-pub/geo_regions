// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

void main() {
  test('accepts exactly protocol 1.0', () {
    expect(kGeoRegionsProtocolVersion, '1.0');
  });
}
