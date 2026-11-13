# Changelog

All notable changes to the `geo_regions` package and dataset are recorded here.
Data releases use `data-vYYYY.MM.DD[.N]` tags and are independent of code
versions (PROTOCOL.md §10). Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0-wip.1] - 2026-11-14

### Added (task geo-regions-v1, Phase 1)

- Data protocol 1.0 baseline: six frozen JSON Schemas, deterministic
  content revisions (C(x) canonical serialization, SHA-256), and the
  ten-country research-seed dataset (4,143 nodes, 100 locale packs,
  36 pinned sources) with full offline reproducibility.
- Dart SDK data layer: typed errors, immutable models, strict parser
  with semantic validators, root-inclusive index, search with
  disambiguation, quality-gated name resolution (explicit alias table,
  RFC 4647 fallback without script truncation), selection contract.
- Loading layer: injected loader/store/verifier contracts, bundled
  asset loader, repository orchestration with SHA-256-before-decode
  integrity, request dedupe, generation tokens, atomic collection
  switching with stale-coherent fallback, strict-remote verifier
  prerequisite, cache eviction hook.
- Reusable `GeoRegionPicker` UI: three selection policies, ten-locale
  labels, theme/builders, accessible state matrix (loading/error/
  offline/unknown-coverage distinct states).
- `dart run geo_regions:assets` CLI: offline subset generation with
  config schema, stale-config rejection, per-file pubspec fragment,
  registry descriptor, gzip/uncompressed audit report.
- Demo app consuming the production SDK; example app; integration
  documentation (`docs/SDK_INTEGRATION.md`, `docs/ASSETS_CLI.md`,
  `docs/CONSUMER_CONTRACT.md`).
- CI: data gates, scoped Flutter gates (pinned 3.50.0), required-gate
  job, immutable data-tag release workflow.

### Known limits

- Dataset maturity is `research-seed`; individual name quality is
  reported per ID (`humanReviewVerified: false`). Production mode
  intentionally rejects this seed until review batches land
  (DP-01/02/09 backlog in `docs/DATA_WORKPACKAGES.md`).
- Global coverage beyond the ten seed countries is an explicit backlog,
  not a completed claim.
