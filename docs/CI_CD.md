# CI/CD 方案 / CI/CD configuration

版本 / Version: 2026-11-13

## 1. 当前交付状态 / What is delivered

本包包含可提交到 `imboy-pub/geo_regions` 的 GitHub Actions 配置，**没有在本次会话中推送仓库、启用仓库设置、运行在线 Actions 或发布任何 Release/pub.dev 包**。本地工具的验证记录与将来 GitHub 的运行记录必须分开。

The bundle contains GitHub Actions configuration ready to commit to `imboy-pub/geo_regions`. This delivery does not imply that a repository push, repository-setting change, hosted Actions run or release/publication has occurred. Local evidence and hosted CI evidence are separate.

只保留两条工作流 / Two workflows:

| 文件 / File | 触发 / Trigger | 结果 / Result |
|---|---|---|
| `.github/workflows/ci.yml` | PR、main push、手动、可复用调用 / PR, main push, manual, reusable call | 数据和工具验证；按变更范围执行 Flutter；稳定 Required gate / Data/tool checks, scoped Flutter checks, stable required gate |
| `.github/workflows/release-data.yml` | `data-v*` tag push，或手动指定已存在 tag / data tag push or an existing tag | 重新运行完整 CI，再创建数据 ZIP + SHA-256 的草稿 Release / Full verification followed by a draft data release |

## 2. CI 为什么高效 / Why the CI is small

数据验证在一个 Linux job 内运行：来源重现、JSON Schema、图结构与语言兼容、Manifest、Python 边界测试、浏览器参考原型的纯逻辑测试、离线子集生成。没有 Android/iOS 构建矩阵，没有每个国家单独启动一个 runner，没有每次 PR 自动抓取上游数据。

One Linux job runs source reproducibility, schema/graph/language checks, manifest checks, Python boundary tests, the design reference's pure logic tests and an offline subset build. There is no mobile build matrix, per-country runner matrix or automatic upstream refresh on every PR.

`tool/ci_scope.py` 根据真实 Git diff 决定是否启动 Flutter job。Dart、lib/test、示例、Flutter Demo、pubspec、分析配置、工作流、`schemas/`、`config/data_policy.json` 或 `tool/import_data.py` 变化触发 Flutter，因为后三类会影响协议、locale 匹配或生成字段。仅数据内容、与协议无关的工具和文档变更可以只走快速数据关卡。找不到可靠比较基线时保守执行全部。Release 重用 CI 时强制 Flutter 关卡。

`tool/ci_scope.py` uses a real Git diff. Flutter code, package metadata, examples, the demo, workflows, schemas, locale policy and importer changes trigger Flutter checks. Schema, `config/data_policy.json` and `tool/import_data.py` changes can affect the consumed contract or generated fields. Data-content changes, unrelated tools and documentation use the inexpensive gate. An unavailable base selects a full run. Release verification forces Flutter checks.

同一 PR 的旧运行自动取消；main 与 Release 运行不会被新提交取消。依赖下载使用 Python/Flutter 缓存，证据保留 7 天。固定一个 Flutter 版本，避免无需要的大矩阵。

Older runs of the same PR are cancelled. Main and release runs are not. Python and Flutter dependency downloads use caches, and evidence artifacts are retained for seven days. One pinned Flutter version avoids an unnecessary version matrix.

## 3. 必须通过的内容 / Required checks

数据 job 执行以下实命令 / Commands in the data job:

```bash
python3 -m pip install -r tool/requirements-ci.txt
python3 tool/check_readiness.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema --report build/reports/data-validation.json
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
node demo/web_preview/test_logic.cjs
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py offline --config config/offline.example.json --out build/offline-assets
```

Node 只用于不依赖浏览器的参考原型行为测试，由 GitHub 托管 runner 提供。它不代替 Dart、Widget 或真实浏览器验证。

The runner's Node runtime is used only for the design reference's browser-independent behavior tests. Those checks do not replace Dart, Widget or browser tests.

Flutter job 固定 `3.41.5`：先按 `demo/flutter/bootstrap.sh` 创建 Web 平台文件，再 format 检查、analyze、Widget tests、Web release build。该固定版本已通过 Flutter 官方 GitHub tag 核对，commit 为 `2c9eb20739dfec95e2c74bd3dfa4601b0a8a36aa`。

The Flutter job uses `3.41.5`, bootstraps Web platform files, and runs formatting checks, analysis, Widget tests and a release Web build. The official Flutter tag resolves to commit `2c9eb20739dfec95e2c74bd3dfa4601b0a8a36aa`.

```bash
bash demo/flutter/bootstrap.sh
cd demo/flutter
dart format --output=none --set-exit-if-changed lib test
flutter analyze --fatal-infos
flutter test
flutter build web --release
```

当前 `config/readiness.json` 显式标记 `productionSdkExpected: false`。P1-08 必须改为 `true`，每次 CI 的 `tool/check_readiness.py` 随后要求根包 pubspec、`lib/geo_regions.dart` 和真实测试文件都存在，缺失直接失败；不能通过删掉源码获得绿灯。根目录真正出现 `pubspec.yaml` 后，还会对生产库执行 get、format、analyze、test、publish dry-run。在根包尚未实现时日志明确说明只验收 Demo；这不是“生产 SDK 已完成”的证明。

The seed explicitly sets `productionSdkExpected: false` in `config/readiness.json`. P1-08 must switch it to true. The readiness guard then requires the root manifest, public library and tests on every CI run; removing the implementation cannot silently turn the package checks green. Once a root package exists, CI also runs get, format, analysis, tests and a publication dry run for that package. Until then, the log explicitly identifies the delivered demo as the only Flutter implementation being verified.

`Required gate` 始终运行，要求 data 成功且所有被选中的 Flutter 检查成功。不会把整个工作流放进 `paths-ignore`，防止必需状态检查因为完全未触发而一直等待。数据-only PR 的 Flutter job 明确 skipped，而 Required gate 能确认这种跳过符合范围规则。

The final required gate always runs and requires successful data checks plus successful selected Flutter checks. Workflow-level path skipping is avoided so a required check is not left permanently pending.

## 4. CI 安全和版本固定 / Security and version pins

所有 PR job 只读仓库；只有草稿 Release 的最后一个 job 具有 `contents: write`。不使用 `pull_request_target` 运行外部 PR，不给外部 PR 发布凭据，不保存长期 pub.dev token。上下文传入 shell 时先放环境变量，再带引号读取。

PR jobs have read-only repository permissions. Only the final draft-release job gets `contents: write`. The workflow does not execute external PR code under `pull_request_target`, expose publishing credentials to PRs or store long-lived pub.dev tokens. Shell inputs are passed through quoted environment variables.

直接使用的 Actions 已通过官方仓库 API 校验到完整 SHA / Verified direct action pins:

| Action | 已选版本 / Version | 完整 SHA / Commit |
|---|---|---|
| `actions/checkout` | `v4.2.2` | `11bd71901bbe5b1630ceea73d27597364c9af683` |
| `actions/setup-python` | `v5.6.0` | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| `actions/upload-artifact` | `v4.6.2` | `ea165f8d65b6e75b540449e92b4886f43607fa02` |
| `subosito/flutter-action` | `v2.23.0` | `1a449444c387b1966244ae4d4f8c696479add0b2` |

这组选择不是“永远最新”的承诺。Dependabot 每月提出 Actions 和 Python 开发依赖更新 PR，更新仍须经过真实 CI；不会自动合并。第三方复合 Action 的内部依赖与 runner 镜像属于另外的供应链边界，完整 SHA 并不替代审查。

Pins are not a claim to always track the newest version. Monthly Dependabot PRs propose updates without automatic merging. Composite-action internals and the runner image remain separate dependency boundaries.

## 5. 数据 CD / Data release flow

使用 `data-vYYYY.MM.DD` 或 `data-vYYYY.MM.DD.N` 表示独立数据发布。示例 `data-v2026.11.13.1`。维护者先提交并检查版本，再推送同名不可变 tag，或对已有 tag 触发手动工作流。

Use a separate date-based data tag, for example `data-v2026.11.13.1`. Commit and verify the intended revision before creating the tag. The manual workflow accepts an existing tag.

流程先把 tag 解析为完整 commit SHA，验证和打包都 checkout 同一 SHA，避免两次解析可变 tag 对应不同代码。重新运行完整 CI 后，`tool/package_release.py` 生成确定性 ZIP 与 SHA-256，BUILD.json 记录 testedCommit；公开动作前再解析远端轻量/annotated tag 确认仍指向该 SHA，最后用 GitHub CLI 创建 **draft** Release。已有 Release 直接失败，不覆盖附件、不移动 tag。修正数据应创建新 revision 和新 tag。

The workflow resolves the tag once to a full commit, uses that same SHA for verification and packaging, and records it as testedCommit in BUILD.json. After full CI it builds the deterministic ZIP/checksum, checks the remote lightweight or annotated tag still points to the tested commit, then creates a draft release with GitHub CLI. Existing releases are not overwritten and tags are never moved. Corrections require new revisions and a new tag.

草稿的说明默认称研究种子，包含真实覆盖与许可边界。公开发布以及 CDN 配置是单独的维护者操作；公共 CDN 必须使用版本目录，不能把已发布路径替换为不同内容。发布前的 tag 检查只证明检查时未移动；防止管理员之后强制移动 tag 仍需要仓库 tag ruleset。数据源 URL 可配置，不强制依赖 IMBoy 域名。

Draft notes identify the research-seed coverage and licensing limits. Public publication and CDN setup are separate operations. Serve immutable versioned paths and allow host-configured resource origins. A point-in-time tag check cannot stop a later administrator mutation; enforce a tag ruleset for that guarantee.

本配置不把 HTTP cache headers、CORS、CDN 域名或 GitHub Pages 视作已部署完成。发布后应从实际托管 URL 检查 SHA-256、Content-Type、CORS 和缓存头。

This configuration does not claim that HTTP cache headers, CORS, a CDN domain or GitHub Pages has already been deployed. Verify those properties against the actual hosting origin.

数据 Release ZIP 另含完整 sources/raw、源锁、crosswalk、覆盖报告、importer、Schema、数据配置与必要开发校验器，可直接 `python3 tool/import_data.py --check` 离线重建。它不含 Flutter Demo 和执行计划；本次完整开发交付 ZIP 才同时包含这些材料。

The data-release ZIP includes raw snapshots, lock, crosswalk, coverage evidence, importer, schemas, data policy and validation tools. It reproduces offline with `python3 tool/import_data.py --check`. The Flutter demo and execution plans belong to the full development handoff ZIP instead.

## 6. pub.dev 后续自动发布 / Later pub.dev automation

本轮尚无已实现的根 Flutter 库，所以没有启动自动发布。Dart 官方文档说明，首次创建 package 需手动 `dart pub publish`，自动发布用于已有包；后续可在 pub.dev Admin 配置仓库 `imboy-pub/geo_regions` 与 `v{{version}}` tag pattern，并使用 GitHub OIDC，避免长期 token。

There is no implemented root package to publish yet. Dart's documentation requires manual publication for a package's first version; automated publication is for existing packages. Later configure the repository and `v{{version}}` pattern on pub.dev and use GitHub OIDC instead of a long-lived token.

激活前置条件 / Activation prerequisites:

- 根包名称确为 `geo_regions`，真实 package 名称可用性和 publisher 权限已确认。/ Confirm package name availability and publisher rights.
- SDK 及示例关卡通过，许可证/署名/publish 大小/选定 assets 验证通过。/ Pass SDK/demo checks, license/notice/size/asset-selection checks.
- `pubspec.yaml` 版本、CHANGELOG 与 tag 对齐。/ Align package version, changelog and tag.
- 首个版本已人工发布成功；只给匹配版本 tag 的发布 job 配置 `id-token: write`。/ Complete the first manual publication; grant OIDC only to matching tag publication jobs.
- 对版本 tag 配置维护者可用的规则；按所用 GitHub 计划和实际权限实施。/ Configure tag rules using features available to the repository.

不要把仅用于 Dart 包的通用发布 workflow 直接当作已验收的 Flutter 发布方案；Flutter SDK 安装、依赖解析、pub dry-run 和远端实际权限仍需现场验证。

Do not treat a generic Dart publication workflow as a verified Flutter release pipeline without checking Flutter SDK setup, dependency resolution, dry-run output and actual publisher permissions.

## 7. 首次启用步骤 / First activation

1. 通过交付包安装器的 dry-run 核对目标 `/Users/leeyi/project/imboy.pub/geo_regions`，保留现有 LICENSE、未提交修改和所有 worktree。/ Review the installer dry run and preserve existing work.
2. 在任务分支提交 `.github`、工具、数据和 Demo；ZCODE 第一节点先实际运行 Flutter 并修复 format/analyze/test。/ Commit on the task branch; run and fix the first Flutter milestone locally.
3. 创建 PR 或 push main 触发第一次在线 CI，保留运行 URL。/ Trigger the first hosted CI and retain its run URL.
4. 仓库 Settings 中允许所需 Actions；若组织策略阻止第三方 Flutter Action，使用经组织批准的安装方式。/ Confirm Actions policy, using an approved Flutter installer if necessary.
5. 第一次结果出现后，把实际显示的 `Required gate` 状态检查加入 main 规则。仅靠 YAML 不能启用分支保护。/ Add the observed gate name to main rules after its first run; YAML alone cannot enable branch protection.
6. 仅在准备数据发布时推送数据 tag 或手动运行草稿 Release；检查附件和来源说明。/ Create a data tag only when a release is intended; inspect the draft artifacts.

## 8. 本轮验证范围 / Evidence limits

本地已运行数据重建、JSON Schema/语义、Manifest、Python 边界、离线子集和 ZIP 生成检查。YAML 可以在本地解析，动作 SHA 已核实。真实在线工作流、GitHub 仓库设置和 pub.dev 发布没有在本轮执行；Flutter 环境结果以 Demo 的验证报告为准。

Local data/schema/semantic/manifest, boundary, offline-subset and ZIP checks were executed. YAML was parsed and action commit pins verified. Hosted workflows, repository settings and pub.dev publication were not executed in this delivery. Consult the demo report for actual Flutter-environment evidence.

## 参考 / Sources

- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Dart automated publication requirements](https://dart.dev/tools/pub/automated-publishing)
- [Flutter 3.41.5 official tag](https://github.com/flutter/flutter/tree/3.41.5)
- [checkout pin](https://github.com/actions/checkout/commit/11bd71901bbe5b1630ceea73d27597364c9af683)
- [setup-python pin](https://github.com/actions/setup-python/commit/a26af69be951a213d495a4c3e4e4022e16d87065)
- [upload-artifact pin](https://github.com/actions/upload-artifact/commit/ea165f8d65b6e75b540449e92b4886f43607fa02)
- [flutter-action pin](https://github.com/subosito/flutter-action/commit/1a449444c387b1966244ae4d4f8c696479add0b2)
