# 数据工具与扩展规则 / Data tooling and extension rules

版本 / Version: 2026-11-13 · Protocol 1.0 · `geo-regions-seed`

## 1. 交付边界 / Delivery boundary

本目录工具已实现，使用 Python 3.10+ 标准库。可选 JSON Schema 校验只在开发和 CI 环境安装 `jsonschema`；它不是 Flutter 运行时依赖。未来的 `dart run geo_regions:…` 开发者入口属于实施计划，不能把本轮 Python 命令说成已经发布的 Dart API。

These development tools are implemented in Python 3.10+ using the standard library. The optional JSON Schema checker is a development/CI dependency, never a Flutter runtime dependency. The planned Dart developer CLI is not implemented by these scripts.

所有命令在仓库根目录执行。独立路径可使用 `python3 tool/geo_data.py --root /absolute/repository COMMAND`，`--root` 必须放在子命令之前。`validate_data.py` 等包装脚本默认定位自身仓库，不接受 `--root`。

Run commands from the repository root. For another repository, place `--root /absolute/repository` before the subcommand. Convenience wrappers infer their own repository root.

## 2. 日常验证 / Routine verification

```bash
python3 tool/import_data.py --check
python3 -m pip install -r tool/requirements-ci.txt
python3 tool/geo_data.py validate --schema --report build/reports/data-validation.json
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
```

`import_data.py --check` 从已固定提交和哈希的本地上游快照重建预期内容，只比较、不改写。普通验证默认离线，不向 GitHub 拉取最新数据。源刷新需显式执行导入工具的 `--download`，且下载字节仍必须匹配锁定 SHA-256。

`import_data.py --check` reconstructs expected outputs from the vendored, commit-pinned source snapshots without overwriting them. Routine checks are offline. Explicit `--download` still accepts only bytes matching the locked source SHA-256.

| 关卡 / Gate | 实际检查 / What it checks |
|---|---|
| JSON | UTF-8、重复键、非 JSON 数字、空名称、控制字符、NFC / UTF-8, duplicate keys, invalid numbers, empty names, controls, NFC |
| Schema | 六份本地 JSON Schema 2020-12 / Six local JSON Schema 2020-12 contracts |
| 结构 / Structure | 单根、全局唯一 ID、父节点存在、跨国父节点、循环、完整根路径 / One root, globally unique IDs, parent existence, cross-country links, cycles, root paths |
| 语言 / Language | 已审定标签清单、路径和标签一致、悬空 ID、精确结构版本兼容、质量标记对应 / Reviewed locale list, path/locale match, dangling IDs, exact revision compatibility, quality metadata |
| 国家清单 / Catalog | 国家代码唯一、rootId 一致、每个目录语言包覆盖全部已交付国家 / Unique codes, matching roots, complete delivered-country catalog translations |
| 来源 / Sources | 不可变完整提交、原始字节数、SHA-256、sourceRefs 外键 / Full immutable commits, raw byte count, SHA-256, sourceRefs foreign keys |
| Manifest | 资源路径、重复条目、版本、字节数、SHA-256、是否遗漏资源 / Paths, duplicates, revisions, bytes, SHA-256, complete resource inventory |
| 输出安全 / Output safety | 拒绝路径穿越、符号链接、覆盖源目录；替换需生成标记 / Reject traversal, symlinks and source-directory overwrite; replacement requires generation marker |

`validate --schema` 通过只证明数据满足当前种子完整性约束。它不能证明名称在所有语言里准确、行政划分是当前官方版本或数据已通过母语人工校审。报告明确输出 `humanReviewVerified: false`。`--production` 增加严格门禁，并会**有意拒绝本轮 research-seed 数据**；生产模式同时要求 source-lock 存在、每资源明确声明 reviewed/production 成熟度，以及译名和节点默认名都满足显式质量白名单；删掉状态或把未知状态改成候选不能绕过。

A successful integrity check does not establish linguistic accuracy, current official administrative coverage or native-speaker approval. The report explicitly states `humanReviewVerified: false`. The optional `--production` gate intentionally rejects this research seed. Production validation also requires a pinned source lock, an explicit reviewed/production maturity state for every resource, and a closed quality allowlist covering both locale entries and node default names. Removing a seed label is not a substitute for review.

语种语法检查覆盖常规 BCP 47 标签，并用 `config/data_policy.json` 中的人工审定规范标签与别名表约束发布；它不是完整 IANA 注册表验证器，也不处理所有历史 grandfathered 标签。新标签需要在规则评审中完成规范化。

Locale syntax checks cover ordinary BCP 47 tags and an explicitly reviewed policy list. They are not a full IANA registry implementation or a complete grandfathered-tag parser. Review canonicalization before adding a locale.

## 3. 内容版本与资源完整性 / Content revisions and integrity

规范编码函数为 UTF-8 的 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))`，不附加换行。它是此数据集的确定性生成约定，**没有声称实现 RFC 8785 JCS**。资源完整性始终使用完整文件字节的 64 位十六进制 SHA-256；16 位 revision 后缀只用于内容版本标识，不能替代完整性哈希。

Canonical generation uses UTF-8 `json.dumps` with `ensure_ascii=False`, sorted keys and compact separators, without a trailing newline. This is the dataset's deterministic convention, not a claim of RFC 8785 JCS conformance. Full file SHA-256 provides integrity; the shortened revision suffix is only a version identifier.

| 前缀 / Prefix | 参与内容 / Input |
|---|---|
| `c-` | `countries` 数组 / the country array |
| `s-` | `nodes` 数组 / the node array |
| `l-` | `{"names": names, "translationQualityById": quality}`；地区包和国家清单包一致 / names plus per-name source quality, for both locale resource kinds |
| `m-` | 按资源路径排序的 `resources` 数组 / resource entries ordered by path |

各前缀后附规范内容 SHA-256 的前 16 个十六进制字符。语言质量从 provisional 改为更高等级也会产生新语言 revision，即使名称字符串没有变化。结构改变后，所有语言包必须重新确认 `compatibleStructureRevision`；不能只改字段、跳过 ID 和覆盖检查。

Append the first 16 hex characters of canonical-content SHA-256. A quality change also changes the language revision. A structure revision change requires an intentional compatibility review of every associated language pack.

## 4. 生成离线子集 / Generate an offline subset

```bash
python3 tool/geo_data.py offline --config config/offline.example.json --out generated/geo_regions_assets --dry-run
python3 tool/geo_data.py offline --config config/offline.example.json --out generated/geo_regions_assets
```

示例选择中国结构、中国简体中文/繁体中文/英语名称，以及 10 种语言的轻量国家清单；其它国家结构和语言包不会复制到离线目录。`structures` 与 `locales` 是独立选择，允许提前打包某语言、结构运行时再获取。

The example bundles the China structure, three China locale packs and ten lightweight country-catalog locale packs. Other country structures and regional names are absent from the generated directory. Structure and locale selections are independent.

生成目录含两个不同用途的清单：

- `manifest.json`：仅所选离线资源的版本、哈希与路径。
- `registry.json`：完整发布清单的描述信息，帮助宿主识别远程资源；它不含其它国家的数据字节。
- `countries.json`、`catalog_i18n/…`、`regions/…`、`i18n/…`：配置实际选择的文件。
- `notices/…`：上游许可声明与来源说明，供 App 保留并展示。
- `assets.fragment.yaml`：包含每个资源、两个清单和许可文件的显式 Flutter asset 条目；合并到宿主已有 `flutter:` 下，避免重复 YAML 根字段。

The subset manifest describes only bundled resources. The full registry contains descriptors for remote resources, not their contents. The generated `assets.fragment.yaml` explicitly lists every selected JSON file, manifest and notice. Merge its asset entries into the host's existing `flutter:` block; directory declarations do not recursively register subdirectories. When output is outside the repository, pass `--asset-prefix assets/geo_regions` (or the actual host-relative destination). Register **only the generated assets** in the host's Flutter asset configuration. Do not declare the entire package `data/` directory as Flutter assets.

重新生成需在已经带 `.geo_regions-generated` 标记的输出目录使用 `--replace`。工具先在旁边临时目录生成并验证，成功后替换；错误哈希、缺失资源或坏配置不会破坏旧输出。

Regeneration requires `--replace` and a generation marker. A verified temporary tree replaces the old output only after successful assembly. Corrupt source bytes, missing resources and invalid configuration preserve the previous output.

## 5. 新增国家 / Add a country

```bash
python3 tool/geo_data.py add-country --country ES --out staging/country-ES --dry-run
python3 tool/geo_data.py add-country --country ES --out staging/country-ES
```

1. 先确认国家/地区代码、覆盖政策、行政层级范围、上游更新时间和许可证。`ES` 只是示例，脚本不替你判断政治边界或代码归属。
2. 固定来源 repo、完整 commit、文件路径、获取日期、SHA-256、原许可；把原文件留在 `sources/raw/`，把声明加入源锁。
3. 使用源稳定代码生成 ID；不得把名称、数组下标或可变排序当 ID。无法建立可信父子关系的节点不能靠名称猜父级。
4. 只填实际获得的层级。`childrenStatus: unknown` 表示未覆盖下级，不能当成已证实的叶子。无真实后代时不要凭空合成城市层。
5. 添加国家清单条目和十语国家名称；按真实来源创建国家语言包。缺少的地区名保持缺失，运行时回退。
6. 在隔离分支中扩展 importer、policy、源锁和覆盖报告；从源码重建，不直接编辑生成 JSON 后跳过生成器。
7. 执行来源、Schema、语义、版本、哈希和覆盖校验，再生成新 Manifest。需要产品接受的覆盖范围由对应验收项决定。

First agree codes, scope, timestamps and licenses; pin and vendor the source; derive stable IDs from source identifiers; preserve honest hierarchy coverage; add catalog translations and sourced regional names; update the importer and policy on an isolated branch; then validate and regenerate the manifest. The scaffold is marked `draft`, and the validator refuses to publish it as completed data.

## 6. 新增语言 / Add a language

```bash
python3 tool/geo_data.py add-locale --locale es --out staging/locale-es --dry-run
python3 tool/geo_data.py add-locale --locale es --out staging/locale-es
```

脚本为当前国家创建**空名称映射草稿**，另建国家清单语言草稿，记录结构 revision，并前后比对结构字节。这不会把英语复制成“西班牙语翻译”，不会修改国家结构文件，也不会自动修改发布语言清单。

The command creates intentionally empty regional and catalog draft maps, records compatible revisions and verifies that structure bytes remain unchanged. It does not fill gaps with English or silently add the language to the publication policy.

验收顺序 / Acceptance order:

1. 规范标签与宿主别名映射；确定脚本方向与字体表现。/ Agree canonical tag, host aliases, direction and font behavior.
2. 优先已有可信上游名称；机器建议进入待审稿，不直接作为已批准翻译。/ Prefer sourced names; keep machine suggestions in review drafts.
3. 每条名称记录质量来源；相同拼写可以是正确名称，不能仅靠“与英语是否相同”判断是否翻译。/ Record provenance; identical spelling is not proof of an untranslated name.
4. 所有显式名称 ID 必须属于目标结构，质量标记必须一一对应。/ Require valid structure IDs and one quality marker per explicit name.
5. 确保国家清单的全部国家已有名称；地区名允许稀疏，但必须报告覆盖缺口。/ Complete the country catalog; regional coverage can be sparse and must be reported.
6. 对重要地区、歧义名称、RTL 和截断做人工校审；脚本不伪造该证据。/ Review important and ambiguous names, RTL and truncation manually.
7. 生成新的语言 revision 和 Manifest；证明所有 `data/regions/*.json` SHA-256 未改变。/ Update language revisions and manifest, and demonstrate unchanged structure hashes.

## 7. 更新与 ID 迁移 / Updates and ID migration

```bash
python3 tool/geo_data.py diff --old previous/CN.json --new data/regions/CN.json
python3 tool/geo_data.py diff --old previous/CN.json --new data/regions/CN.json --require-no-removals
```

报告分列 added、removed、reparented、renamed。改名称不改 ID。删除或重新挂接父级需要显式迁移计划；`--require-no-removals` 对两者都失败，因为旧的完整路径可能失效。迁移表需保存旧 ID、候选新 ID、原因、证据、是否可自动一对一迁移；一对多或名称歧义交给用户重新确认，不能静默选第一个。

The report separates additions, removals, parent changes and renames. Names may change without changing identity. Removed or reparented IDs require a migration plan because stored complete paths can become invalid. Ambiguous or one-to-many mappings require user reselection instead of guessing.

## 8. 本轮验证记录 / Verification in this delivery

实际执行通过：源快照重建检查、36 个来源文件校验、10 国 4,143 节点的 Schema 与语义检查、121 条资源 Manifest、44 项 Python 测试（27 项数据/工具边界，17 项状态/安装器回归）、15 个文件的离线选择。离线配置选中的数据资源共 1,320,132 字节；加上两个清单和生成标记后目录总大小更大。

Executed successfully: source reproducibility, 36 source-file integrity checks, schema and semantic checks for 4,143 nodes in ten countries, a 121-resource manifest, 44 Python tests (27 data/tooling boundaries and 17 state/installer regressions) and the fifteen-resource offline subset. Selected data-resource bytes total 1,320,132 before manifest/registry/marker overhead.

GitHub 在线 CI、真实 Flutter 分析/测试/Web 构建不属于这条 Python 验证记录；它们必须在对应运行环境产生实际证据。

Online GitHub CI and actual Flutter analysis/tests/Web builds require separate execution evidence and are not implied by the Python results.
