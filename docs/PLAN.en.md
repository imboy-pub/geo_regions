# geo_regions Two-Phase Execution Plan

Version: 1.0 · Date: 2026-11-13 · Persistent task ID: `geo-regions-v1`

Chinese: [PLAN.zh-CN.md](PLAN.zh-CN.md). Requirements: [PRD.en.md](PRD.en.md). Execution prompt: [ZCODE_START.zh-CN.md](../prompts/ZCODE_START.zh-CN.md). Machine-readable tasks: [tasks.json](../.plans/geo-regions-v1/tasks.json).

## 1. Execution principles

Target repository: `/Users/leeyi/project/imboy.pub/geo_regions`. Expected origin: `https://github.com/imboy-pub/geo_regions`. Inspect the actual `AGENTS.md`, Git status, worktrees and existing code before making changes. Recording this path does not mean the delivery environment has accessed the user's Mac. This ZIP is an importable baseline; it does not claim completion of the production SDK.

The first task is **P1-01: a runnable Demo with carefully designed UI/UX**. The name, BSD-3-Clause license and initial languages are already confirmed and must not become repeated approval requests. Start with the included small fixtures and draft contract. Finalize the contract in P1-02, then replace the prototype adapter with the real SDK. Do not wait for all data work before showing the Demo.

Keep ZCODE's current model and reasoning configuration unless instructed otherwise. Use at most two parallel workers by default, with one coordinator integrating changes, to avoid competing with existing long-running IMBoy work. A file has only one writer. The coordinator serializes changes to manifests, schemas, shared interfaces and pubspec files.

Reuse the persistent task ID across sessions; do not create a new date-based RUN_ID on every invocation. `.plans/geo-regions-v1/state.json` records evidence, branches, worktrees and checkpoints. A task remains completed only while its evidence matches the current inputs. All pending tasks genuinely remain to be implemented. Included prototypes, tools and seed data are inputs, not automatic proof that SDK tasks are complete.

## 2. Phases and dependencies

| Phase | Completion objective | Exit |
|---|---|---|
| Phase 1 | Independent Flutter package, ten-country seed governance, ten-locale resolution, optional UI, offline/on-demand tools and CI | Reviewable release candidate without IMBoy coupling |
| Phase 2 | IMBoy integration, legacy profile compatibility, save/navigation behavior and necessary adaptations across the three repositories | Actual acceptance evidence, rollout and rollback plan |

Dependency order: P1-01 → P1-02. P1-03, P1-04 and P1-06 may then run in parallel with isolated ownership. P1-05 depends on P1-04. P1-07 integrates data, loading and asset tooling. P1-08 closes the phase. Read-only discovery for P2-01 may begin after P1-02; remaining Phase 2 implementation follows the Phase 1 exit gate.

## 3. Phase 1 task cards

### P1-01 · First runnable Demo and UI/UX acceptance

- **Prerequisites:** Locate the repository and preserve existing changes. Use the supplied `demo/flutter` and `demo/web_preview`.
- **Steps:** Import the prototype → check/install Flutter → run bootstrap → format, analyze and run Widget tests → run on Web and one device or desktop class → fix issues against the UX specification.
- **Deliverables:** Runnable Flutter Demo, README, screenshots and interaction records covering two widths, light/dark mode and RTL. Keep fixtures explicitly identified; do not claim simulated remote requests actually occurred.
- **Tests:** In `demo/flutter`, run `dart format --output=none --set-exit-if-changed lib test`, `flutter analyze --fatal-infos`, `flutter test`, and `flutter build web --release`. First confirm platform-generation steps in the Demo README.
- **Acceptance:** Search → navigate → select → switch language while preserving IDs → retry → finish. No critical overflow at 390 px or 1280 px. RTL, enlarged text, keyboard and screen-reader states work. Passing the HTML reference does not substitute for Flutter compilation or layout acceptance.
- **Exit:** Evidence for AT-01/02/03/04. Missing devices are BLOCKED; complete available subchecks without falsely marking P1-01 complete. Objective acceptance does not require the user to approve every individual step.

### P1-02 · Finalize the data protocol and consumer contract

- **Prerequisites:** P1-01. Treat the supplied protocol, schemas and data as the candidate baseline; do not reinvent existing standards.
- **Steps:** Review all six schema classes. Fix stable IDs, root-inclusive paths, locale aliases, revision/quality algorithms, childrenStatus and error categories. Add negative vectors that are valid JSON but invalid under the contract.
- **Deliverables:** `docs/PROTOCOL.md`, `schemas/`, consumer interfaces, compatibility/deprecation policy and strict-remote verifier prerequisites.
- **Tests:** `python3 tool/geo_data.py validate --schema` and `python3 -m unittest discover -s tests -v`. After implementing the Dart parser, compare both implementations against the same vectors.
- **Acceptance:** Reject duplicate keys, missing/cyclic parents, cross-country parents, dangling translated IDs, revision mismatches, path traversal and corrupted resources. Preserve valid source-quality metadata.
- **Exit:** No conflicting contract rules across GR-01/02/06/07/11. Format validation is not geographic fact validation.

### P1-03 · Ten-country review, ten-locale quality and expansion queue

- **Prerequisites:** P1-02. Inputs are `sources/`, the importer and coverage reports. Ordinary CI must not scrape live Internet data.
- **Steps:** Rebuild offline → verify commits/hashes/licenses → confirm each country's source profile and statistical levels → prioritize IMBoy's actual selection paths → review provisional names, Traditional Chinese gaps and ambiguous names → publish an explicit coverage profile.
- **Deliverables:** Reproducible structures for ten countries, 100 region-name packs, ten country-catalog name packs, source/quality reports and remaining work. Counts may change through expansion; the manifest is authoritative.
- **Tests:** `python3 tool/import_data.py --check`; full validation; compare structure hashes before/after adding a language; source-version diff and compatibility reports.
- **Acceptance:** Never invent translations to fill source gaps. Distinguish reviewed, qualified, provisional, native and missing names. Preserve the Chinese historical snapshot date and exceptional crosswalk evidence. Unknown children are not an administrative endpoint. File existence does not establish production coverage.
- **Parallelism:** Use [DATA_WORKPACKAGES.md](DATA_WORKPACKAGES.md). Workers write only their assigned staging areas; the coordinator integrates data and the manifest.
- **Exit:** Product claims match evidence. Unfinished global scope remains a public backlog. Release cannot pass while the core IMBoy selection paths remain unreviewed.

### P1-04 · SDK models, indexes and name resolution

- **Prerequisites:** P1-02. May run alongside P1-03/P1-06. Create the root Flutter package `geo_regions`; do not pass the Demo off as the production library.
- **Steps:** Implement parsers, models, root-inclusive selections, path validation, indexes, basic search, explicit locale aliases, quality filtering and language fallback.
- **Deliverables:** `lib/geo_regions.dart`, data-only entry points, model/name tests and API documentation. Depend only on Flutter SDK.
- **Tests:** Duplicate names, variable-depth trees, country-only selection, missing/insufficient-quality translations, separation of zh-CN and zh-Hant, different dataset IDs, revision mismatches, deleted nodes and parent migrations.
- **Acceptance:** Changing display language cannot change selection identity. Parsers return typed errors. Forward compatibility for unknown fields and rejection of unsupported major protocol versions follow one consistent rule.

### P1-05 · Loading, caching, integrity and concurrency

- **Prerequisites:** P1-04. Deterministic vectors may be used initially; final verification must include P1-03 data.
- **Steps:** Implement AssetBundle loading, injected remote loader/store/verifier, deduplication, cache indexing, resource state machines, generation tokens, atomic updates and fallback to a coherent previous release set.
- **Deliverables:** Data repository, fake adapters, strict-remote configuration checks, cache cleanup/quota interfaces and a real remote-adapter example.
- **Tests:** AT-06/07/08/09/10/11. Use controllable delays/reordering and a failing store. Verify SHA-256 before JSON decoding and persistent writes.
- **Acceptance:** No-network/no-cache produces explicit unavailable state. Bad downloads do not alter valid files. Old responses cannot overwrite current selections. Concurrent requests for the same resource result in one underlying load. Incompatible revisions never mix. Web entry points have no unconditional dart:io import.

### P1-06 · Offline asset generation and host CLI

- **Prerequisites:** P1-02. May run alongside P1-03/P1-04.
- **Steps:** Use the Python tools as golden reference and implement the package's Dart CLI (`bin/assets.dart` in this plan's proposed file layout). Resolve the installed package through package_config. Configure structures, country–locale pairs and catalogLocales separately. Generate exact pubspec asset entries and validation reports.
- **Deliverables:** Dart CLI, configuration schema/examples, fully offline, hybrid and online examples, pre-build preparation entry point and stale-configuration detection.
- **Tests:** Two distinct country–locale combinations; copied bytes match source hashes; real `flutter build web`/mobile resource inventories exclude unselected data; missing/corrupt resources, symlinks, unsafe output paths and failed reruns preserve existing valid output.
- **Acceptance:** Generate from an installed package, not a hardcoded checkout path. Adding a language does not require an SDK release. Unselected resources retain descriptors only, with no payload. Record compressed and uncompressed release sizes.

### P1-07 · Reusable picker and real Demo

- **Prerequisites:** P1-03/04/05/06. Reuse the P1-01 design.
- **Steps:** Replace the fixture adapter with the SDK. Separate default UI from data APIs. Provide labels, themes, builders and selection policies. Demonstrate real local files, HTTP failures and cache recovery.
- **Deliverables:** Reusable widget, real `example/`, lightweight integration instructions and the full state matrix.
- **Tests:** AT-01–11 and AT-14/15, including a real remote-resource integrity check and offline browser access after restart. Request logs prove that only intended resources were fetched.
- **Acceptance:** Default UI contains no IMBoy references. Arabic RTL and 200% text scale work. Unknown coverage does not display “last level reached.” Retry and save states recover correctly.

### P1-08 · CI, platform acceptance and release candidate

Set `config/readiness.json` → `productionSdkExpected: true`; `tool/check_readiness.py` must reject missing production pubspec/lib/test. Current protocol 1.0 schemas remain strict; unsupported fields/versions are explicit errors, not an implied promise of arbitrary forward compatibility.

- **Prerequisites:** P1-03/04/05/06/07. Baseline CI starts with the initial import; it is not postponed until this task.
- **Steps:** Complete package analyze/test/build gates. Run source and data validation. Record minimum-supported Flutter and IMBoy 3.41.x compatibility evidence. Run package dry-run, offline bundle inspection and license-distribution checks.
- **Deliverables:** Actual workflow URLs, test summary, changelog, bundle/performance report, draft release, and installation/upgrade/rollback instructions.
- **Acceptance:** The required summary gate does not become pending indefinitely because of path filtering. Data-only PRs do not unnecessarily start Flutter. Once SDK implementation is claimed, missing SDK files must not produce a green result. Critical SKIP results prevent completion. Data tags cannot overwrite different bytes under the same version.
- **Publishing boundary:** This plan authorizes local development and reviewable materials; it does not automatically authorize public pub.dev publication, main-branch merging or production changes. Record missing release setup/access once and continue independent work.

## 4. Phase 2 task cards

### P2-01 · Inspect the real IMBoy baseline

- **Prerequisites:** Read-only discovery may run after P1-02. Implementation requires P1-08.
- **Inputs:** Actual `imboyapp`/`imboy`/`imboyadmin` paths, AGENTS files, worktrees, origins and current commits. Directory names do not prove remote repository names.
- **Deliverables:** Interface/file/test inventory, legacy region samples, existing-test reuse matrix and a conflict map of ongoing tasks.
- **Verified reference:** Flutter main `2cee59317de36e2f70420f46dc881b1117b034c9`, queried on 2026-11-13, already includes PR #68's path and save/navigation fixes. Recheck at execution time and avoid reimplementing the fix.
- **Acceptance:** Identify legacy string/cache behavior, backend fields that can actually be stored, and admin display points. List missing repositories. Do not invent migration endpoints without reading the source.

### P2-02 · Host adapters and account isolation

- **Prerequisites:** P1-08 and P2-01.
- **Deliverables:** Loader/store/verifier adapters reusing existing HTTP/cache infrastructure, locale aliases, labels, bundled-CN and on-demand-other-country configuration.
- **Acceptance:** Do not add a duplicate networking framework for this feature. Web storage works. Two accounts do not share their selections. Public data bytes may be reused while profile data remains isolated. Structure/name combinations obey configuration.

### P2-03 · Profile contract and migration

- **Prerequisites:** P1-08 and P2-01. May run alongside P2-02 with separate backend file ownership.
- **Steps:** Choose compatible fields/JSON structure based on the real API. Preserve the legacy string. Validate dataset/country/path/revision server-side rather than trusting display names. Migrate old data only when a unique, trustworthy mapping exists.
- **Deliverables:** Compatibility contract, minimal necessary backend/admin changes, idempotent migration, rollback script/instructions and old/new-client interoperability tests.
- **Acceptance:** Do not guess ambiguous names, names with spaces, obsolete codes or deleted/merged regions. Mark unresolved values and retain their original text. Reruns preserve data. Old clients still read their expected string.

### P2-04 · Replace the data source and preserve save/navigation

- **Prerequisites:** P2-02/03.
- **Deliverables:** Preserve IMBoy's iOS-style `SetRegionPage`, provider and `MorePage` integration while moving internal identity/name handling to SDK paths and resolution.
- **Acceptance:** Select deeply → navigate up → re-enter → restore the complete path. Commit persistent profile changes only after server success. Remain on the page with retry on failure. Return consistently to MorePage after success. Repeated taps trigger one save. Language changes do not falsely set hasChanged.
- **Tests:** Reuse existing Widget regressions and AT-MF06. Add meaningful loader/cache coverage separate from Widget fakes.

### P2-05 · End-to-end and cross-platform regression

- **Prerequisites:** P2-04.
- **Deliverables:** Evidence for ten-locale switching, Arabic RTL, offline/recovery, cache corruption, account switching and old/new profile formats; actual results for Flutter Web, Android/iOS and existing supported desktop platforms.
- **Acceptance:** The same user has consistent values across clients. Backend persistence and admin display work. Existing path/navigation regressions remain green. Missing devices or login information produce BLOCKED, not PASSED.
- **Device policy:** Follow each repository's AGENTS instructions. Do not modify protected native-platform files to bypass required build/test procedures.

### P2-06 · Rollout, documentation and handoff

- **Prerequisites:** P2-05.
- **Deliverables:** Configuration flag, fallback to legacy region reads, compatibility window, source-update process and final acceptance table.
- **Acceptance:** Rollback does not require deleting new data. Migration can resume/re-enter. Code and data releases remain identifiable. Every GR requirement has PASS or an explicitly accepted scope statement. Critical failures prevent completion.
- **Handoff:** Provide reviewable diffs, commits or draft-PR materials. Do not perform public publication, production operations or merging without explicit authorization.

## 5. Acceptance matrix

| Test ID | Main scenario | Requirements |
|---|---|---|
| AT-01 | Responsive Demo, keyboard and screen reader | GR-09 |
| AT-02 | Deep paths, duplicate names, country-only selection | GR-01/08/10 |
| AT-03 | Ten-locale switching preserves IDs; RTL | GR-02/07/09 |
| AT-04 | Separate loading/empty/error/offline/retry states | GR-05/09 |
| AT-05 | Adding a language preserves structure hashes | GR-02/11 |
| AT-06 | Fetch selected country only; locale switch fetches names only | GR-04 |
| AT-07 | Deduplication and reordered responses | GR-05 |
| AT-08 | Hash corruption, short reads and invalid JSON preserve cache | GR-06 |
| AT-09 | Strict remote mode rejects missing verifier | GR-06/12 |
| AT-10 | Atomic updates and coherent previous-release fallback | GR-05/06 |
| AT-11 | No-cache offline and unknown children do not imply a leaf | GR-05/10 |
| AT-12 | Compiled output contains selected payloads only | GR-03/13 |
| AT-13 | Pinned sources, licenses, offline rebuild and diff | GR-11/15 |
| AT-14 | Provisional filtering and evidenced Traditional Chinese fallback | GR-07 |
| AT-15 | SDK has no IMBoy/third-party runtime coupling | GR-12/16 |
| AT-16 | Save success/failure/repeated taps/navigation to MorePage | GR-14 |
| AT-17 | Ambiguous legacy migration, idempotency and old-client compatibility | GR-01/14 |
| AT-18 | Real Web/native cache behavior and account isolation | GR-13/14 |
| AT-19 | CI gates, data-only PRs and reconstructible draft releases | GR-15 |
| AT-20 | Reject different bytes under one version; rollback | GR-06/15 |

## 6. Evidence, status and resumption

For each task retain input commits/source hashes, changed files, executed commands, exit codes, report paths, output hashes, tested scope and PASS/FAIL/SKIP/BLOCKED results. `.plans/geo-regions-v1/evidence/<task>/` contains necessary evidence only, without secrets, large SDK caches or device credentials.

Task states are pending / in_progress / blocked / completed. Verify prerequisites before starting. Completion requires command results and usable evidence. A new session reads state and Git differences, then rechecks tasks affected by changed inputs; a completed label alone is insufficient. Status tooling manages records, not code review or automatic proof of passing tests.

When ZCODE provides a native task panel, use its actual task/update_plan/TodoWrite capability to show these IDs, states and next steps, keeping state.json synchronized. Tool names vary by version. If no such capability exists, state that fact and provide the terminal task list; do not fabricate calls. Progress and resumable checkpoints must exist outside the chat transcript.

## 7. Initial execution commands

```bash
cd /Users/leeyi/project/imboy.pub/geo_regions
python3 tool/plan_status.py init
python3 tool/plan_status.py status
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 -m unittest discover -s tests -v
```

Import the package safely according to README first. Schema-validation dependencies are in `tool/requirements-ci.txt`. Then execute P1-01. These commands validate delivery inputs; they do not prove completion of the later production SDK.
