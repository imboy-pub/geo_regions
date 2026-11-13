# geo_regions Product Requirements

Version: 1.0 delivery baseline · Date: 2026-11-13 · Status: executable design baseline; production SDK implementation remains planned

Chinese counterpart: [PRD.zh-CN.md](PRD.zh-CN.md). Execution plan: [PLAN.en.md](PLAN.en.md). Contract: [PROTOCOL.md](PROTOCOL.md). Requirement identifiers are shared by both languages.

## 1. Confirmed decisions

The package name is **geo_regions**. Naming is no longer an approval gate. The product is an independent, commercially usable, contribution-friendly Flutter region-data SDK with an optional picker. IMBoy is its first integration, not a runtime dependency. The main package depends only on Flutter/Dart SDKs; HTTP, persistent storage, integrity implementations and business persistence are injected.

The project owns a complete resource system: country catalogs, region structures, localized names, provenance, versions, quality metadata, generators and validators. Developers obtain all data included in the published release and configure precisely which country structures and country–locale combinations ship offline. Other resources load on demand. Development availability and application bundling are separate requirements.

Global coverage remains the product goal. This delivery contains a ten-country seed batch. Ten countries, the administrative levels present upstream, or a successful fallback must never be reported as completed global coverage. Additional batches use the same contract and tools without core SDK changes.

Keep the repository's existing BSD-3-Clause license for original code. Preserve upstream licenses and notices for data. No account, key, IMBoy service, mandatory telemetry or fixed CDN is required. Permissive licensing still carries its stated obligations.[S01][S02][S03]

## 2. Delivery versus implementation

| Item | In this ZIP | After execution |
|---|---|---|
| PRD, contract and plan | Complete design and task materials | Updated with actual evidence |
| Data | Real ten-country source seed, ten locale sets, coverage/quality reports | Reviewed and published for explicitly supported coverage |
| Tools | Import, validation, manifest, diff, offline assets and extension tooling | Reproducible pipeline plus host-friendly Dart CLI |
| Demo | Flutter prototype and corresponding interactive HTML reference | Flutter runs in task one; later connects to the real SDK |
| Production SDK | Not claimed as implemented | Phase 1 |
| IMBoy changes | Separate integration design; no existing source modified | Phase 2 with regression evidence |
| CI/CD | Installable workflow files | Runs after push, with actual workflow URLs/results |

The first implementation task must deliver a usable, visually considered Demo. Documentation or backend-only work cannot substitute for it.

## 3. First data batch and locales

| Country | Code | Seed scope |
|---|---|---|
| China | CN | CLDR subdivisions plus a dated mainland statistical province/city/county source |
| Japan | JP | Available CLDR subdivisions, mainly prefectures |
| South Korea | KR | Available CLDR subdivisions, mainly first-level divisions |
| United States | US | CLDR states and included areas; no claim of complete counties/cities |
| United Kingdom | GB | Preserve the source's variable containment hierarchy |
| Germany | DE | Available CLDR subdivisions; no claim of complete municipalities |
| France | FR | Preserve available multi-level relations and source scope |
| Italy | IT | Preserve available multi-level administrative subdivisions |
| Russia | RU | Explicit CLDR source profile and temporal limitations |
| Saudi Arabia | SA | Available subdivisions and Arabic/RTL validation |

This is a replaceable initial batch chosen for this delivery, not an earlier user-specified immutable list. ISO-style identifiers and CLDR display/containment data are not geographic boundaries, proof of administrative currency or a sovereignty determination. Catalog/profile coverage for Hong Kong, Macao, Taiwan and other areas must be explicit. Missing deep data is not complete coverage. See [DATA_COVERAGE.md](DATA_COVERAGE.md).

| IMBoy UI locale | Resource locale | Language |
|---|---|---|
| zh-CN | zh-Hans | Simplified Chinese |
| zh-Hant | zh-Hant | Traditional Chinese |
| en-US | en | English |
| ja-JP | ja | Japanese |
| ko-KR | ko | Korean |
| ru-RU | ru | Russian |
| de-DE | de | German |
| fr-FR | fr | French |
| it-IT | it | Italian |
| ar-SA | ar | Arabic |

These are explicit project aliases. RFC 4647 lookup does not itself infer `zh-CN → zh-Hans`. Keep aliases, canonicalization and matching separate; script differences cannot be silently discarded.[S04][S05]

Ten-language support means supported resources, resolution, quality reporting, fallback and UI label integration. It does not mean every county has ten reviewed translations. Report coverage per country, locale and quality class. Copying English into ten directories must not count as translation.

## 4. Users and responsibility boundaries

Consumers may use only data APIs or the default picker. They may operate fully offline, use a public mirror, private service or compatible custom dataset. Hosts own accounts, profile saves, business validation, routing, theme, UI internationalization and backend compatibility.

The picker accepts `GeoPickerLabels`, theming and builders. Core code must not depend on IMBoy's Riverpod, slang, `UserRepoLocal` or `MorePage`. Region names are separate from interface labels such as Search, Done and Retry.

Out of scope: maps, GPS, reverse geocoding, postal-address validation, phone codes, boundary polygons, automatic pinyin and a claim of all administrative levels in every language being reviewed at once.

## 5. Requirements and acceptance contracts

| ID | Requirement | Required evidence |
|---|---|---|
| GR-01 | One structure per country; variable finite depth; stable IDs | Duplicate names are safe; complete root-to-node paths; country-only selection |
| GR-02 | Separate catalog, catalog names, structure and region names | Adding a locale changes no structure bytes or revisions |
| GR-03 | Independent country–locale offline selection | Build samples contain only the selected structures and translations |
| GR-04 | On-demand network access | Opening JP requests no unrelated country structures; locale switches reuse the same structure revision |
| GR-05 | Cache, deduplication and concurrency safety | One concurrent load per resource; stale responses cannot overwrite current state; no updates after disposal |
| GR-06 | Integrity and compatibility | Check byte length/SHA-256 before parsing; failures preserve valid cache; incompatible resources never mix |
| GR-07 | Observable quality-aware fallback | Return requested/resolved locale, source quality and fallback status; draft is not reviewed |
| GR-08 | Query and search | ID, parent/child, name and alias search; results carry full disambiguating paths |
| GR-09 | Usable UI | Demo first; responsive layout, keyboard, RTL, dark mode, enlarged text and recovery |
| GR-10 | Configurable selection policy | Country-only, intermediate selection, business depth and supported-leaf rules tested separately |
| GR-11 | Data governance | Pinned upstream revision/hash/license/date/coverage; offline reproducibility |
| GR-12 | Dependency discipline | No third-party runtime dependencies in the main package; no unconditional dart:io in Web entry points |
| GR-13 | Platforms and bundle size | Platform-specific strategies; actual artifact proves unselected resources are absent |
| GR-14 | IMBoy compatibility | Save to server before cache commit/navigation; keep selection on failure; suppress duplicate submissions |
| GR-15 | Repeatable release | Automated PR gates and reconstructible data; independent code/data versions; actual CI evidence after push |
| GR-16 | Replaceable infrastructure | Mirror and fully offline examples work without accounts, API keys or telemetry |

## 6. Protocol principles

Geo Regions Data Protocol 1.0 is a project contract built on existing standards, not a new Internet standard. Use ISO country identifiers, BCP 47, RFC 8259 UTF-8 JSON, JSON Schema 2020-12, standard URIs/HTTPS and HTTP cache semantics.[S04]–[S10]

Identity is `(datasetId, countryCode, nodeId)`. A selection includes `pathIds` and `dataRevision`. Its first path element is the country root `cc:XX`; country-only selection still has one element. Display names and space-delimited strings are not identity. Retirements, mergers and code changes require migration records; never silently assign an old ID to a different entity.

`childrenStatus` describes completeness within declared coverage, not an inference from a failed request or an empty array. Unknown coverage must not satisfy a strict leaf rule. The host either permits a supported intermediate level or blocks submission with a clear explanation. Statistical source depth is not necessarily legal administrative rank.

Manifests contain relative paths, resource kinds, revisions, SHA-256, sizes and compatibility links. Hash verification proves content integrity, not name correctness or independent authenticity when the manifest is also replaced. Remote deployments require a trusted manifest channel. Signatures may be added later, but SHA-256 alone must not be described as signature verification.

## 7. Full development data and selective application assets

1. Ship published `data/` as ordinary package files; do not declare the full directory in the library's Flutter assets.
2. The included Python tools support repository development now. Phase 1 adds `dart run geo_regions:assets`, resolving the installed package root instead of hardcoding a pub-cache path.
3. Hosts explicitly declare generated assets. Flutter directory declarations do not recursively include every subdirectory: generate exact entries or a deliberately flat indexed layout.[S06]
4. `pub get` is not an arbitrary generation hook. Run resource preparation before local and CI builds; reject missing/stale generated output.
5. The bundled manifest lists files actually bundled. A full registry may describe remote resources without including their bytes.
6. Run `pub publish --dry-run` and measure compressed/uncompressed payloads. If future global data exceeds service limits, resolve packaging and the product promise explicitly; do not silently replace full published data availability with a manual data-hunting step.[S02]

## 8. Loading and caching

V1 resolves an immutable release set. Bundled or cached bytes matching that set are eligible; otherwise the loader fetches them. Cache identity includes dataset, kind, country, locale, revision and hash. Old bytes with a different manifest expectation are not a cache hit.

Validate an entire compatible update before atomically switching the active manifest. Interrupted downloads preserve current selection and references. Offline fallback may use the previous coherent release, explicitly marked stale, but may not mix its structure with a different release's names. Store adapters must provide failure-safe atomic writes.

Hosts choose quota, eviction, expiry and cleanup. Public data cache may be shared; account-specific selections may not. Cancellation is best effort, with generation tokens preventing stale commits even when transport cancellation is unavailable.

Strict remote mode fails configuration when no reliable SHA-256 verifier is provided. Do not implement new cryptography to advertise zero dependencies. Build-time validation of bundled files and runtime validation of downloaded files are distinct controls.

## 9. Internationalization and quality

Resolution order: normalized request and explicit aliases → RFC 4647-style matching among available resources → configured default locale → source default name → stable ID. Hosts may configure the fallback chain; actual resolution is returned. Missing and tentative names can be explained without exposing technical stack traces.

Preserve source draft metadata by ID. `approved-in-source` is not project review; qualified JSON export is not necessarily the same as an individually approved XML value. Production defaults allow only approved-in-source, contributed, cldr-json-qualified and source-native quality values. Provisional, unconfirmed, candidate and unknown values are excluded. The same rule applies to node.nameQuality/nameLocale, so falling back to node.name cannot bypass filtering. An explicitly labeled seed preview may include tentative values. Source-native Chinese is not a translation into the other nine languages. Traditional Chinese gaps remain work items; unreviewed conversion must not masquerade as a sourced translation.

Adding a locale changes language/catalog-name resources and registration only; existing structure hashes remain unchanged. Adding a country is isolated from existing country files. Both operations produce provenance, license, coverage and diff evidence.

## 10. UI/UX acceptance

Use [DEMO_UX.md](DEMO_UX.md) for the first milestone. A person should understand the country, current depth, whether selection is allowed, and resource availability at a glance.

Require a narrow single-column and wide two-panel layout, complete breadcrumbs, visible current selection, clearable search, loading skeleton, no-results state, offline-without-cache state, failed-download retry and offline/cache badges. Saving suppresses duplicates. Status uses text as well as color. Target at least 44 logical-pixel tap areas. At 200% text scale, key actions remain reachable. Arabic mirrors appropriate layout through Directionality while IDs/codes retain readable ordering. Keyboard and accessibility semantics cover the whole flow.

Screenshots support design review but do not replace interaction tests. An HTML reference does not establish Flutter compilation, native rendering or device-test success.

## 11. Performance and testability

Measure release builds with recorded hardware and dataset size. Warm queries avoid repeated JSON decoding; report p50/p95 for first parsing and search. Initial search results target p95 below 150 ms on the nominated baseline device. This is an acceptance budget, not a measurement from this delivery.

Inject loader, store, clock and verifier to reproduce corruption, reorderings, concurrency and version mismatches deterministically. Widget fixtures test UI; separate repository tests must exercise parsing/cache behavior. Replacing initialization in a Widget fake does not prove the real data pipeline works.

## 12. Two-phase completion

**Phase 1: independent library.** Demo first; then contract, reviewed scope/licensing, real SDK, optional UI, Dart asset CLI, offline/remote examples, quality policy, tests, artifact inspection and CI. Ten-country supported depth is explicit and ten locales resolve/fallback. Incomplete coverage stays in an executable queue. Publishing is separate: prepare a draft rather than silently publishing to pub.dev.

**Phase 2: IMBoy integration.** Reuse existing code and protected worktrees, or use a registered isolated task worktree. Preserve legacy values; verify real backend support for IDs, caching, navigation, language switching, Flutter Web and devices. Change backend/admin only when the inspected API/display contract requires it.

Critical SKIP/BLOCKED items prevent completion. Missing devices, credentials or release configuration do not prevent independent work, but the blocked checks must never be counted as passed.

## 13. Evidence

Sources were checked on 2026-11-13. Full links are in [REFERENCES.md](REFERENCES.md); actual source versions, hashes and observation dates are in `sources/` and [DATA_SOURCES.md](DATA_SOURCES.md). GR, AT and P1/P2 identifiers connect requirements, tests and tasks in the plan.
