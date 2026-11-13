// SPDX-License-Identifier: BSD-3-Clause
// Minimal geo_regions integration, README level (example/README.md).
//
// One screen: a GeoRegionPicker fed by a repository over the generated
// offline bundle, a selection-policy switch, a small label override, and
// the confirmed selection printed to the console and to a text card.
//
// The example builds its chrome on the Flutter SDK's own material library,
// exactly like the SDK picker (GR-12: the main package has no third-party
// runtime dependencies).
// ignore_for_file: deprecated_member_use

import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:geo_regions/geo_regions.dart';

void main() => runApp(const ExampleApp());

/// Step 4 of the README: resolve the release manifest from the registry
/// descriptor list, then wire repository → data source → picker.
Future<GeoRegionDataSource> buildDataSource() async {
  final registry = jsonDecode(
    await rootBundle.loadString('assets/geo_regions/registry.json'),
  ) as Map<Object?, Object?>;
  final manifest = GeoManifest(
    protocolVersion: registry['protocolVersion']! as String,
    datasetId: registry['datasetId']! as String,
    revision: registry['revision']! as String,
    resources: List<GeoManifestEntry>.unmodifiable(<GeoManifestEntry>[
      for (final raw in registry['resources']! as List<Object?>)
        _descriptor(raw! as Map<Object?, Object?>),
    ]),
  );
  final repository = GeoRegionsRepository(
    manifest: manifest,
    bundledLoader: const _BundleLoader(),
    // Strict remote mode would also need remoteLoader + verifier
    // (docs/SDK_INTEGRATION.md); this example stays offline-only, so
    // unbundled countries surface the typed unavailable error with retry.
    store: GeoMemoryCacheStore(),
  );
  return GeoRepositoryDataSource(
    repository,
    defaultLocale: 'en',
    bundledCountries: const <String>{'CN'},
  );
}

GeoManifestEntry _descriptor(Map<Object?, Object?> raw) => GeoManifestEntry(
  path: raw['path']! as String,
  kind: GeoResourceKind.tryParseName(raw['kind']! as String)!,
  revision: raw['revision']! as String,
  sha256: raw['sha256']! as String,
  bytes: raw['bytes']! as int,
  countryCode: raw['countryCode'] as String?,
  locale: raw['locale'] as String?,
  compatibleStructureRevision: raw['compatibleStructureRevision'] as String?,
  compatibleCatalogRevision: raw['compatibleCatalogRevision'] as String?,
);

/// Reads manifest-relative paths from this package's generated bundle.
class _BundleLoader implements GeoResourceLoader {
  const _BundleLoader();

  @override
  Future<GeoBytes> load(Uri resourceUri) async {
    final data = await rootBundle.load(
      'assets/geo_regions/${resourceUri.path}',
    );
    final bytes = Uint8List.fromList(
      data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
    );
    return GeoBytes(bytes, contentLength: bytes.length);
  }
}

class ExampleApp extends StatefulWidget {
  const ExampleApp({super.key});

  @override
  State<ExampleApp> createState() => _ExampleAppState();
}

class _ExampleAppState extends State<ExampleApp> {
  late Future<GeoRegionDataSource> _source = buildDataSource();
  GeoSelection? _selection;
  GeoSelectionPolicy _policy = GeoSelectionPolicy.allowIntermediate;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'geo_regions example',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF6654D9),
      ),
      home: Scaffold(
        appBar: AppBar(title: const Text('geo_regions example')),
        body: FutureBuilder<GeoRegionDataSource>(
          future: _source,
          builder: (context, snapshot) {
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            return ListView(
              padding: const EdgeInsets.all(16),
              children: <Widget>[
                _policySelector(),
                const SizedBox(height: 12),
                _pickerSection(snapshot.data!),
                if (_selection != null) ...<Widget>[
                  const Divider(height: 32),
                  _selectionCard(),
                ],
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _pickerSection(GeoRegionDataSource source) {
    return GeoRegionPicker(
      dataSource: source,
      displayLocale: 'en',
      policy: _policy,
      // Step 5: drop the picker in and handle the draft. The host owns the
      // backend transaction (PROTOCOL §8); this example just prints it.
      labels: GeoPickerLabels.forLocale('en')
          .copyWith(confirm: 'Pick this place'),
      onConfirmed: _onSelection,
    );
  }

  Widget _selectionCard() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          'Last selection (${_selection!.datasetId}, ${_selection!.dataRevision}):',
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Text(
          _selection!.pathIds.join(' / '),
          style: const TextStyle(fontFamily: 'monospace'),
        ),
      ],
    );
  }

  Widget _policySelector() {
    return SegmentedButton<GeoSelectionPolicy>(
      segments: const <ButtonSegment<GeoSelectionPolicy>>[
        ButtonSegment(
          value: GeoSelectionPolicy.countryOnly,
          label: const Text('Country only'),
        ),
        ButtonSegment(
          value: GeoSelectionPolicy.allowIntermediate,
          label: const Text('Allow intermediate'),
        ),
        ButtonSegment(
          value: GeoSelectionPolicy.requireLeafWithinDeclared,
          label: const Text('Declared leaf'),
        ),
      ],
      selected: <GeoSelectionPolicy>{_policy},
      onSelectionChanged: (selection) =>
          setState(() => _policy = selection.first),
    );
  }

  void _onSelection(GeoSelection selection) {
    // PROTOCOL §8: the picker emits a draft; the host submits it to its
    // backend and only then commits the account cache and exits.
    print('selection: ${selection.toJson()}');
    setState(() => _selection = selection);
  }
}
