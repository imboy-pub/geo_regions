# 代码与数据许可证 / Code and data licensing

日期 / Checked: 2026-11-13

## 决策 / Decision

**保留已经选择的 BSD-3-Clause，不需要为“任何人可用、任何人可贡献”改成另一种许可。** 根目录LICENSE保留仓库已有的 `Copyright (c) 2026, imboy.pub` 原文。它允许源码/二进制形式的使用和再分发，包括修改后再分发；需保留规定的版权/许可/免责声明，并不得未经允许使用版权人或贡献者姓名为衍生产品背书。[BSD 原文](https://opensource.org/license/BSD-3-Clause)

**Keep BSD-3-Clause.** It supports the intended broad use and contribution model. Preserve the existing repository copyright. Source and binary redistribution, including modified versions, are permitted subject to the notice and non-endorsement conditions in the license.

| Option | Assessment / 评价 |
|---|---|
| BSD-3-Clause | 已选、简洁、适合Flutter生态；保留 / Already selected and suitable; keep it |
| MIT | 同样宽松，文本更短；对本需求没有必须更换的收益 / Also permissive, no compelling migration benefit here |
| Apache-2.0 | 含明确贡献者专利授权和终止条款，企业若特别重视此项可考虑；义务和文本更完整 / Explicit patent grant/termination may be useful for a future policy decision |
| Copyleft alternatives | 不是实现广泛商用/闭源集成的必要前提 / Not necessary for the stated permissive integration goal |

比较依据：[MIT](https://opensource.org/license/mit)、[Apache-2.0 §2–4](https://www.apache.org/licenses/LICENSE-2.0)、[Dart publishing guidance](https://dart.dev/tools/pub/publishing)。本建议针对当前项目目标，不宣称任何许可证能保证第三方所有权或所有使用场景的法律结果。

## 数据必须单独保留许可 / Data retains upstream licenses

| Material / 内容 | License | What ships / 随交付保留 |
|---|---|---|
| Original tooling, demo, future SDK / 原创工具、Demo、SDK | BSD-3-Clause | Root LICENSE |
| Unicode CLDR data and derived names/containment | Unicode-3.0 | `licenses/third_party/Unicode-3.0.txt`, commit/hash/source records |
| modood CN source and derived statistical hierarchy | WTFPL v2 | `licenses/third_party/WTFPL.txt`, historical source/profile notice |
| Wikidata labels (via committed P300 extract) / Wikidata 标签（经提交版 P300 提取件） | CC0-1.0 | `licenses/third_party/CC0-1.0.txt`, `sources/raw/wikidata/subdivision-labels.json` provenance + `sources/source-lock.json` `derivedSources` pin |
| GeoNames CN dump (via committed ADM2/ADM3 extract) / GeoNames CN dump（经提交版 ADM2/ADM3 提取件） | CC-BY-4.0 | `licenses/third_party/CC-BY-4.0.txt`, `sources/raw/geonames/cn-adm-rows.json` provenance + `sources/source-lock.json` `derivedSources` pin |

根目录BSD不能把CLDR或modood数据重新统一授权为BSD。数据混合文件的来源列表必须完整。复制数据到另一个仓库、转JSON或改字段名不会自动消除上游义务。

The root code license does not relicense third-party data. Preserve attribution, permissions and source records for combined/derived files. Format conversion or repository relocation does not remove upstream obligations.

Unicode原文允许分发数据/软件并要求保留许可通知；包内保留完整原文。WTFPL文本也原样保留，但上游声明的许可不独立证明全部底层来源权利、准确性或时效性。当前CN数据仍明确标历史research-seed，后续更新要继续核对源及权利链。

The Unicode notice expressly covers data files and software. The upstream WTFPL declaration is preserved; it is not independent proof of every underlying right, factual accuracy or currency. Reassess provenance for future updates.

## 贡献规则 / Contribution rules

欢迎代码、数据修正、翻译、测试、文档和问题报告。贡献者保留自己的版权；原创代码贡献按BSD-3-Clause提供。第三方数据贡献必须有可分发的来源、确切版本、许可和加工说明；不能提交从受限商业服务复制的数据或无来源的整包译名。

All contribution types are welcome. Contributors retain copyright and provide original code under BSD-3-Clause. Imported data requires a redistributable source, exact version, license and transformation record. Do not submit restricted commercial datasets or unexplained translated dumps.

首版不设置单独CLA签署门槛，也不默认强制DCO机器人；用清晰CONTRIBUTING、PR模板和自动校验降低参与门槛。维护者仍按正确性、兼容性和来源评审合并，不代表所有提交自动接受。未来如变更贡献政策，须公开说明，不能把新条款追溯强加给旧贡献。

No separate CLA or mandatory DCO bot is introduced by this delivery. CONTRIBUTING, a PR checklist and automated checks provide a lightweight process. Open contribution does not imply automatic acceptance.

## App分发与数据Release / Distribution

离线构建工具将所需第三方notice复制到生成目录，并输出明确的assets条目。宿主应将notice包含在应用分发材料中，并通过“开源许可/数据来源”入口展示或链接随包通知；不要只有开发仓库里存在、最终App和数据release里丢失。

The offline tool copies notices and emits exact asset entries. Hosts retain notices in application distribution materials and provide an appropriate license/source access point. Data releases include notices and provenance alongside resources. Keep full upstream notices intact when mirroring.
