# 数据覆盖报告 / Data coverage report

生成日期 / Prepared: 2026-11-13。由 `tool/import_data.py` 从固定 GitHub 快照生成；可重现。

**状态 / Status: research-seed。不是全球完整数据库，也不是所有行政节点已完成十语人工校审的正式发布。**

**This is a reproducible research seed, not a globally complete or human-reviewed ten-language gazetteer.**

## 实际覆盖 / Actual coverage

共 10 个国家数据分片、10 种语言、4,143 个节点（包括国家根节点）。

Each of the ten small country-name packs has all ten catalog names. Region-name packs are sparse and carry per-ID upstream quality metadata.

| 国家 / Country | 所有节点 / Nodes | 国家下直属节点 / Root children | 覆盖说明 / Scope |
|---|---:|---:|---|
| CN | 3,430 | 31 | 大陆31省 + 2023统计分组/地市/县区/部分乡镇；不含港澳台子树 / Mainland statistical snapshot |
| JP | 48 | 47 | CLDR47都道府县；不含市区町村 / 47 prefectures |
| KR | 18 | 17 | CLDR17省级；不含市郡区 / 17 first-level subdivisions |
| US | 58 | 57 | CLDR57州、地区及领地条目；不含县市 / 57 source subdivisions, including territories |
| GB | 222 | 4 | CLDR constituent countries + reachable subdivisions |
| DE | 17 | 16 | CLDR16州；不含市镇 / 16 states |
| FR | 125 | 26 | CLDR regions/overseas entries + reachable subdivisions |
| IT | 127 | 20 | CLDR regions + reachable subdivisions |
| RU | 84 | 83 | CLDR83条目；保留上游口径 / 83 entries in the pinned source profile |
| SA | 14 | 13 | CLDR13行政区；不含城市 / 13 regions |

## 名称覆盖矩阵 / Explicit-name coverage

每格为“源中有显式名称 / 该国节点总数”；**存在不等于已审校**。数字包含国家根名称，不含运行时回退复制。

Cells count explicit source names / total nodes, including the country root. Presence does not imply review. Runtime fallback is never counted as translation.

| Country | zh-Hans | zh-Hant | en | ja | ko | ru | de | fr | it | ar |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CN | 3430/3430 | 3430/3430 | 3079/3430 | 32/3430 | 32/3430 | 32/3430 | 3079/3430 | 3079/3430 | 3079/3430 | 32/3430 |
| JP | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 |
| KR | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 |
| US | 52/58 | 52/58 | 58/58 | 52/58 | 51/58 | 52/58 | 52/58 | 52/58 | 52/58 | 52/58 |
| GB | 218/222 | 218/222 | 222/222 | 220/222 | 214/222 | 218/222 | 219/222 | 220/222 | 218/222 | 136/222 |
| DE | 17/17 | 17/17 | 17/17 | 11/17 | 17/17 | 17/17 | 17/17 | 17/17 | 17/17 | 17/17 |
| FR | 116/125 | 116/125 | 125/125 | 71/125 | 116/125 | 113/125 | 116/125 | 116/125 | 116/125 | 116/125 |
| IT | 127/127 | 127/127 | 127/127 | 121/127 | 127/127 | 125/127 | 127/127 | 127/127 | 127/127 | 127/127 |
| RU | 84/84 | 84/84 | 84/84 | 84/84 | 84/84 | 84/84 | 84/84 | 84/84 | 84/84 | 84/84 |
| SA | 14/14 | 14/14 | 14/14 | 14/14 | 14/14 | 14/14 | 14/14 | 14/14 | 13/14 | 14/14 |

## 上游质量统计 / Upstream quality counts

| Locale | Explicit | Approved in XML | JSON-qualified / contributed | Provisional | Unconfirmed | Source-native | Missing | Project reviewed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| zh-Hans | 4124 | 3 | 10 | 682 | 0 | 3429 | 19 | 0 |
| zh-Hant | 4124 | 3 | 10 | 4111 | 0 | 0 | 19 | 0 |
| en | 3792 | 734 | 10 | 3048 | 0 | 0 | 351 | 0 |
| ja | 671 | 3 | 10 | 658 | 0 | 0 | 3472 | 0 |
| ko | 721 | 3 | 10 | 708 | 0 | 0 | 3422 | 0 |
| ru | 721 | 3 | 10 | 708 | 0 | 0 | 3422 | 0 |
| de | 3774 | 3 | 10 | 3761 | 0 | 0 | 369 | 0 |
| fr | 3775 | 3 | 10 | 3762 | 0 | 0 | 368 | 0 |
| it | 3772 | 3 | 10 | 3759 | 0 | 0 | 371 | 0 |
| ar | 644 | 3 | 10 | 631 | 0 | 0 | 3499 | 0 |

### 质量字段的准确含义 / Exact quality semantics

- `approved-in-source`：CLDR XML该条无draft属性；不是本项目人工审校。 / XML has no draft attribute; not project review.
- `cldr-json-qualified`：CLDR JSON仅输出达到contributed或approved阈值的数据，JSON未逐条保留二者区别。 / Meets the CLDR JSON export threshold; exact draft distinction is unavailable in JSON.
- `provisional` / `unconfirmed` / `contributed`：逐条保留XML原值。 / Preserve upstream XML attributes literally.
- `source-native`：CN历史源提供的原始中文名称；不是人工新翻译。 / Original Chinese names from the pinned historical source.
- 缺失项不生成伪翻译。默认正式策略过滤provisional/unconfirmed；Demo可以明确开启预览并显示状态。 / Missing entries stay absent. Production defaults filter provisional/unconfirmed; demo preview must be explicit.

## 已知边界 / Known limitations

1. CN深层是2023-06-30统计快照。modood README已声明停更；不能称2026现势行政数据。 / CN lower levels are a frozen 2023 statistical snapshot.
2. CN包含31个省级节点、342个中层节点、2974个6位第三层节点及82个9位第三层节点。后两类不能都叫“区县”；按原始代码长度区分statistical-county和statistical-township。 / Tree depth is not administrative rank.
3. “市辖区”“县”“省直辖县级行政区划”等是源中统计分组，标为statistical-group；不伪造城市或跳过真实路径。 / Statistical grouping nodes remain explicit.
4. CN采用大陆starter profile；源containment的cnhk/cnmo/cntw被显式排除。HK/MO/TW未作为本次10个catalog条目发布，应另立可配置profile和补数任务。US/FR保留源内含的领地/海外条目。这些数据口径不构成主权判断。 / Scope follows declared source profiles, not a sovereignty assertion.
5. `childrenStatus=unknown`表示源覆盖到此结束，不表示该地不存在下级行政区。complete只说明当前声明profile内的子项齐备。 / Unknown leaves are not proof of no lower divisions.
6. zh-Hant显式名=zh-Hans名的记录式保守简繁转换（tool/s2t_places.py，provisional；歧义字台/咸/峰/里等保持原形走真实回退）。CLDR繁中subdivision源仅有GB三条显式名称，本包从未用简体复制冒充繁中翻译。 / zh-Hant names are a recorded conservative s2t conversion of zh-Hans (provisional); ambiguous glyphs stay unchanged with honest fallback — never simplified text posing as traditional.
7. CLDR cn15 alias指向cnmn，但同版containment与名称表使用cnnm。导入器只在唯一完全相同源中文名的条件下关联“内蒙古自治区”，并写入`sources/cn-province-crosswalk.json`。 / One source inconsistency is recorded and deterministically resolved by a unique exact source-name match.
8. 结构默认名也携带nameLocale/nameQuality，必须经过与语言包相同的质量策略；不能先过滤provisional译名，再从默认名绕过过滤。没有可信名称时仅展示identifier状态的ID/代码。 / Apply quality policy to default names as well as locale packs.
9. 地区ID中的ISO或统计码是固定快照映射。后续改名保留ID；代码重用、拆分和合并需人工确认迁移表，不能自动覆盖历史身份。 / Code reuse and boundary changes require explicit identity migration.
10. CN市/县级英文名是GeoNames机器匹配的罗马字（provisional，CC-BY-4.0），未经人工审校；匹配失败的城市开发区等节点保持缺失，不伪造。 / CN prefecture/county English names are machine-matched GeoNames romanizations (provisional, CC-BY-4.0); unmatched nodes (development zones etc.) stay missing.

## 下一版可并行补齐 / Parallel completion tracks

| Track | Scope | Required evidence before merge |
|---|---|---|
| CN-current | 2023快照后的撤并/更名，港澳台独立profile | 官方变更来源、可再分发许可、ID迁移；不得用旧快照冒充现势 |
| JP-KR | 市区町村/市郡区 | 固定源版本、父级关系、语言和许可记录 |
| US-GB | 县市与UK地区当前口径核对 | 标准代码、非树状关系处理、删除/重用差异 |
| DE-FR-IT | 市镇/commune/comune | 跨层级规则、当前覆盖日期、许可证兼容 |
| RU-SA | 更深行政层级与来源profile核对 | 不混用不同立场/年份的代码和名称 |
| zh-Hant | 人工审校机器转换的繁中条目 | 转换已由 tool/s2t_places.py 记录（167 个语料实测字对+歧义字保留清单）；补齐逐 ID 审校记录 |
| locale-review | 其余9语的provisional条目审校 | 母语审校证据、原名称差异、逐IDreview metadata，不篡改CLDR原draft状态 |

以上数据轨道按国家/语言文件拆分并行；仅由集成人生成全局manifest和覆盖报告。每条轨道必须通过源哈希、结构、跨文件、质量、打包选择与回归检查。

Run country/locale tracks in parallel with disjoint ownership. A single integrator regenerates the shared manifest and reports after all checks pass.
