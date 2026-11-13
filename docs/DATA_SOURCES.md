# 数据来源与可复现加工 / Data sources and reproducible processing

整理日期 / Prepared: **2026-11-13**。项目名称固定为 **geo_regions**。

本交付包实际下载、保留并加工了公开 GitHub 数据；不只是候选链接列表。生产分片为 10 个国家、10 种语言，源快照可能包含这些国家之外的原始条目，不能因此声称库的全球行政结构已经完成。

This package includes downloaded source snapshots and generated data for ten countries and ten locales. Raw upstream files may contain additional countries; that does not imply complete global SDK coverage.

## 1. 实际采用的源 / Included sources

| Source | Immutable commit | Actual use | Declared license |
|---|---|---|---|
| [unicode-org/cldr-json](https://github.com/unicode-org/cldr-json) | [`7d2b9cb11cec08f4d333ad73209deb3df0711c3b`](https://github.com/unicode-org/cldr-json/commit/7d2b9cb11cec08f4d333ad73209deb3df0711c3b) | CLDR 49 subdivision containment, ten locale territory-name files, subdivision aliases, JSON qualified subdivision-name snapshots | [Unicode-3.0 data notice](../licenses/third_party/Unicode-3.0.txt) |
| [unicode-org/cldr](https://github.com/unicode-org/cldr) | [`96e54b273d2da4ec6fbad350ba19ff23fa24a588`](https://github.com/unicode-org/cldr/commit/96e54b273d2da4ec6fbad350ba19ff23fa24a588) | `release-49` source XML with explicit per-name draft quality; all ten locale source files retained | Unicode-3.0 |
| [modood/Administrative-divisions-of-China](https://github.com/modood/Administrative-divisions-of-China) | [`c49d495b40ac73eb1a66f6eeae5f8fd10696f035`](https://github.com/modood/Administrative-divisions-of-China/commit/c49d495b40ac73eb1a66f6eeae5f8fd10696f035) | `dist/pca-code.json`: historical mainland China province / statistical middle level / county or township display tree | [WTFPL v2](../licenses/third_party/WTFPL.txt) |

CLDR JSON 49 发布说明可由 [固定提交](https://github.com/unicode-org/cldr-json/commit/7d2b9cb11cec08f4d333ad73209deb3df0711c3b)核对；XML 的 `release-49` tag 解析为上表固定提交。每个使用文件的原始 URL、SHA-256、字节数、许可证、来源版本都在 [`sources/source-lock.json`](../sources/source-lock.json)。`sourceRefs` 使用该文件中 `localPath` 作为外键，不靠显示名称关联来源。

The source lock records the exact repository, commit, upstream path, raw URL, local path, SHA-256, byte length, declared license and source version for each of the 36 retained source files. The imported payloads are derived from these exact bytes. `sourceRefs` join to the lock by `localPath`.

### 关键原始文件 / Key immutable files

- [CLDR subdivision containment](https://github.com/unicode-org/cldr-json/blob/7d2b9cb11cec08f4d333ad73209deb3df0711c3b/cldr-json/cldr-core/supplemental/subdivisionContainment.json)：国家与下级地区的源关系。
- [CLDR subdivision aliases](https://github.com/unicode-org/cldr-json/blob/7d2b9cb11cec08f4d333ad73209deb3df0711c3b/cldr-json/cldr-core/supplemental/aliases.json)：中国统计省码与 CLDR 省级代码的桥接依据之一。
- [CLDR English subdivision XML](https://github.com/unicode-org/cldr/blob/96e54b273d2da4ec6fbad350ba19ff23fa24a588/common/subdivisions/en.xml)：默认英文名称及上游 draft 状态。
- [CLDR Simplified Chinese subdivision XML](https://github.com/unicode-org/cldr/blob/96e54b273d2da4ec6fbad350ba19ff23fa24a588/common/subdivisions/zh.xml)：现成的简体中文地区名称；多数为 provisional。
- [CLDR Traditional Chinese subdivision XML](https://github.com/unicode-org/cldr/blob/96e54b273d2da4ec6fbad350ba19ff23fa24a588/common/subdivisions/zh_Hant.xml)：该版本只有少量显式名称，未假装全覆盖。
- [CN historical tree](https://github.com/modood/Administrative-divisions-of-China/blob/c49d495b40ac73eb1a66f6eeae5f8fd10696f035/dist/pca-code.json) 和 [source update notice](https://github.com/modood/Administrative-divisions-of-China/blob/c49d495b40ac73eb1a66f6eeae5f8fd10696f035/README.md)：上游声明数据为 2023-06-30 快照且已停止更新。

## 2. 十国实际来源映射 / Mapping for all ten countries

| Catalog code | Country / 国家 | Structure | Name sources | Source profile boundary |
|---|---|---|---|---|
| CN | China / 中国 | CLDR province codes plus modood historical tree | CLDR ten-locale names; source-native Chinese for mainland descendants | Mainland starter profile; no HK/MO/TW subtrees in this seed |
| JP | Japan / 日本 | CLDR containment | CLDR | 47 prefectures; municipal data remains an expansion task |
| KR | South Korea / 韩国 | CLDR containment | CLDR | 17 first-level subdivisions; not a complete municipal tree |
| US | United States / 美国 | CLDR containment | CLDR | 57 source subdivisions including territories; no county/city layer |
| GB | United Kingdom / 英国 | CLDR containment, recursively expanded | CLDR | Four constituent countries and reachable source subdivisions |
| DE | Germany / 德国 | CLDR containment | CLDR | 16 states; municipal layer not included |
| FR | France / 法国 | CLDR containment, recursively expanded | CLDR | Source regions, overseas entries and reachable subdivisions |
| IT | Italy / 意大利 | CLDR containment, recursively expanded | CLDR | Source regions and reachable subdivisions; not all comuni |
| RU | Russia / 俄罗斯 | CLDR containment | CLDR | The pinned source's 83 entries; do not substitute a different territorial profile silently |
| SA | Saudi Arabia / 沙特阿拉伯 | CLDR containment | CLDR | 13 source regions; not a city-level tree |

The scope is an administrative name and selection dataset. No polygons, geocoding, precise boundaries, street-address validation or coordinates are promised. Published code lists are snapshots; they are not proof that every entry is an up-to-date authoritative administrative entity.

## 3. 加工流程 / Transformation rules

1. 校验所有原始文件与 source-lock 的 SHA-256 和字节数一致。默认操作不联网。 / Verify every locked source before transformation; default operation is offline.
2. 从 CLDR containment 递归提取这 10 个 catalog 的子树，拒绝多父节点、错误国家前缀和重复身份。 / Recursively extract the declared profiles and reject unexpected parent relationships.
3. 每个默认名称保留 `nameLocale` 与 `nameQuality`；CN原文另有 `nativeLocale`。默认名称与语言包共同遵守质量策略，缺名只能返回 `identifier` 状态的代码，不能伪装成本地化名称。 / Default names retain their locale and quality; apply the same quality policy as locale packs.
4. 国家根 ID 为 `cc:XX`；CLDR subdivision ID 规范化成 `iso3166-2:XX-SUFFIX`。ID 不含译名，不依赖列表顺序。 / Use code-based stable seed IDs, never translated labels or array positions.
5. CN 省级复用 CLDR ID，下级原始统计节点使用 `cn-stat:<code>`。保留原始分组与跨层级结构。 / Retain original grouping nodes and variable depth.
6. 省码关联先用 CLDR aliases；只有一个已记录的异常通过**唯一、完全相同**的两个源中文名称关联。完整映射保存在 [`cn-province-crosswalk.json`](../sources/cn-province-crosswalk.json)。禁止模糊匹配。 / One pinned-source inconsistency is recorded rather than hidden.
7. 从 XML 的本地、非 `alt` 条目提取名称；不把继承标记 `↑↑↑` 或缺值标记当作名称。保留每个名称的上游 draft 状态。 / Skip alternate and sentinel entries, retain source quality literally.
8. CN 简体语言包用原始中文名称覆盖同 ID 候选翻译，质量标记 `source-native`。 / Prefer original source Chinese over a candidate translation for the same node.
9. 繁中缺口保留为空，不做无记录简繁转换、不把英文复制成翻译。 / Missing Traditional Chinese names remain absent.
10. 地区结构、语言包和独立国家名包分别生成。切换国家名语言不要求下载全部国家结构。 / Separate small country-name packs from country-region language packs.
11. 自动生成覆盖报告；实际缺失量和质量统计来自文件，不从目标承诺反推。 / Compute coverage from the actual generated files.

### 内容版本 / Content revisions

规范 JSON 用 Python 表达为 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')`，无末尾换行。版本值是前缀加该字节串 SHA-256 的前 16 个十六进制字符。

| Payload | Prefix | Hashed value |
|---|---|---|
| Country structure | `s-` | `nodes` array in deterministic ID order |
| Country catalog | `c-` | `countries` array in declared catalog order |
| Locale pack and country-name pack | `l-` | `{ "names": ..., "translationQualityById": ... }` |

Quality metadata participates in language revisions: a provisional name gaining a qualified status must invalidate its prior content revision even if the spelling is unchanged. Manifest SHA-256 hashes cover the complete published UTF-8 file bytes, separately from these logical revisions.

## 4. 许可证和发布边界 / License and distribution boundaries

项目自有 Dart、Python、Shell、文档和 CI 配置可遵循仓库的 BSD-3-Clause；**这不会把上游数据转成 BSD**。

| Material | Applicable notice | Required handling |
|---|---|---|
| CLDR raw and transformed data | Unicode-3.0 | Keep the complete copyright and permission notice with the data or associated documentation |
| CN modood raw and transformed data | WTFPL v2 as declared by upstream | Retain its exact license and provenance; do not claim ISO/official certification |
| New project code | Repository BSD-3-Clause | Retain the three-clause BSD notice |
| Future contributors' own translations | A compatible, explicitly selected data license | Record authorship/source and contribution permission; do not silently relabel third-party text |

[`licenses/third_party/Unicode-3.0.txt`](../licenses/third_party/Unicode-3.0.txt) contains the upstream data notice. Its introductory restriction concerns the separate UTS #35 specification publication; this package ships data snapshots, not a reproduction of that specification. [`WTFPL.txt`](../licenses/third_party/WTFPL.txt) is the exact upstream license, whose legal title is preserved verbatim.

Preserve these notices in the distributable package and any generated offline subset. A network-hosted data copy must also make the notices available. A schema validator proving that the notice exists is not a substitute for checking a new source's actual rights.

### 调研但未采用 / Evaluated, not included

- [wooorm/iso-3166](https://github.com/wooorm/iso-3166)：仓库声明 MIT，但 [README](https://github.com/wooorm/iso-3166/blob/13e7feb32753216511747ff1d96f0d51c560050d/readme.md) 说明机器数据从 Wikipedia 抓取。为简化本轮数据授权与来源链，直接采用同一个 CLDR 体系的 containment 和译名，没有再混入这个源。
- 本轮未采用需要把衍生数据库统一按 ODbL 处理的全球 cities 数据源。以后若引入此类数据，单独审计和声明对应数据义务；代码 BSD 不自动覆盖其数据许可。

## 5. 本地重建与校验 / Offline reproduction

在交付包或仓库根目录运行：

```sh
python3 tool/import_data.py --check
python3 tool/import_data.py
```

第一条验证锁定源及全部生成物是否一致，不改写生成文件；第二条从已保留的本地源重建。仅当源文件丢失且需要重取时使用：

```sh
python3 tool/import_data.py --download --check
```

`--download` 只请求 source-lock 中的固定 commit URL，并在写入前要求 SHA-256 完全匹配。它不会自动跟随 main、更新数据版本或接受新许可证。新增国家、语言或更新源必须单独产生可审查的 source-lock 变更。

When a new source is proposed, review its immutable revision, license, source date, country/territory profile, ID continuity and linguistic quality before adding it to the lock. Source refresh and dataset release are separate operations. This seed does not require online requests for CI validation.

## 6. 后续接入需保持的限制 / Required follow-up behavior

- 默认正式 SDK 策略过滤 `provisional` 与 `unconfirmed`；Demo 允许显式开启候选名称预览。两种模式都需显示真实回退来源，不改变 ID 路径。
- `approved-in-source` 与 `cldr-json-qualified` 只说明上游状态；本轮没有逐节点母语人工审校。`projectReviewed` 始终为 0。
- CN source-native 只是历史源的原文，不能因为是中文就忽略现势更新风险。
- 任一国家真正更深层的数据未到位时，应展示明确的覆盖边界；网络加载失败、数据未知与真实无下级不能合并成同一状态。
- 数据扩展的并行任务见 [DATA_COVERAGE.md](DATA_COVERAGE.md)，对应的完整执行与验收顺序由 Plan 控制。

Default production name policy excludes provisional and unconfirmed names. Candidate preview is explicit. Data absence, source coverage limits, network errors and administrative leaves remain separate states. The coverage report and main Plan define the remaining parallel completion work.
