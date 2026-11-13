# geo_regions example — five-step integration

A minimal runnable host: one `GeoRegionPicker` over a repository backed by a
generated offline bundle. Everything below runs from this directory.

## 1. Add the dependency

`example/pubspec.yaml` already shows it — in your own app:

```yaml
dependencies:
  flutter:
    sdk: flutter
  geo_regions:
    path: /absolute/path/to/geo_regions   # or a hosted/git ref once published
```

then `flutter pub get`.

## 2. Generate the offline bundle

Pick which countries/languages ship inside the app (config axes are
independent; see [docs/ASSETS_CLI.md](../docs/ASSETS_CLI.md)):

```bash
dart run geo_regions:assets --config config/assets.hybrid-cn.json \
  --out example/assets/geo_regions/
```

`--replace` re-runs into an existing directory. This example vendors the
bundle at `example/assets/geo_regions/` (already generated).

## 3. Declare the assets

Merge the generated fragment entries into your **existing** `flutter:` block.
The fragment lists `packages/geo_regions/data/...` for in-package data; this
example vendors the files locally, so the prefix is rewritten to
`assets/geo_regions/` (see `example/pubspec.yaml`). Never declare a whole
directory — the CLI emits exact per-file entries on purpose.

## 4. Build the repository and data source

Resolve the release manifest (the registry descriptor list in the bundle),
then wire the repository. `lib/main.dart` shows the whole step:

```dart
final manifest = /* GeoManifest from assets/geo_regions/registry.json */;
final repository = GeoRegionsRepository(
  manifest: manifest,
  bundledLoader: GeoAssetBundleLoader(assetPrefix: 'assets/geo_regions/'),
  store: GeoMemoryCacheStore(),
);
final dataSource = GeoRepositoryDataSource(
  repository,
  defaultLocale: 'en',
  bundledCountries: {'CN'},
);
```

Strict remote mode (countries fetched from a CDN) additionally injects a
`GeoResourceLoader` remote loader, a `Uri remoteBase`, and a `GeoHashVerifier`
— see [docs/SDK_INTEGRATION.md](../docs/SDK_INTEGRATION.md).

## 5. Place the picker

```dart
GeoRegionPicker(
  dataSource: dataSource,
  displayLocale: 'en',                       // any of the ten primary locales
  policy: GeoSelectionPolicy.allowIntermediate, // or countryOnly / requireLeaf…
  labels: GeoPickerLabels.forLocale('en').copyWith(confirm: 'Pick this place'),
  onConfirmed: (selection) {
    // Draft selection (PROTOCOL §8): submit to your backend, and only after
    // success commit the account cache and navigate back.
    print(selection.toJson());
  },
)
```

## Run

```bash
flutter pub get
flutter run
```

The bundle ships China offline (with zh-Hans/zh-Hant/en names) plus the
country catalog in ten languages. Other countries are declared by the pinned
manifest but not bundled, so opening one surfaces the typed
unavailable/network error with retry — wire a remote loader + verifier to
serve them (see step 4 link). Unknown-coverage levels always read
"Coverage of this level is unknown in this dataset", never "deepest level".

## Selection contract

`onConfirmed` receives the draft `GeoSelection`
(`datasetId`, `countryCode`, `dataRevision`, root-inclusive `pathIds`,
optional display snapshot). Persist the IDs, not the labels: they are stable
across display languages.
