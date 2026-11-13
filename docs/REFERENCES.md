# 资料与依据 / References

查询日期 / Checked on: **2026-11-13**。链接为规范、维护者文档或实际使用的上游仓库；不是所有页面都构成数据准确性的独立证明。原始数据文件的精确URL/commit/hash/日期/许可，以 [source-lock.json](../sources/source-lock.json) 为准。

| ID | Source | Supports / 用途 |
|---|---|---|
| S01 | [OSI BSD-3-Clause](https://opensource.org/license/BSD-3-Clause) | 代码许可、保留通知及禁止未经允许背书 |
| S02 | [Dart publishing packages](https://dart.dev/tools/pub/publishing) | BSD推荐、分发权利、package大小与dry-run |
| S03 | [Unicode licensing policy](https://www.unicode.org/policies/licensing_policy.html), [Unicode copyright terms](https://www.unicode.org/copyright.html) | Unicode软件/数据许可范围 |
| S04 | [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html) | BCP47语言标签 |
| S05 | [RFC 4647](https://www.rfc-editor.org/rfc/rfc4647.html) | 语言匹配/lookup，不替代项目脚本别名 |
| S06 | [Flutter assets](https://docs.flutter.dev/ui/assets/assets-and-images), [Flutter pubspec](https://docs.flutter.dev/tools/pubspec) | 包资产自动打包、显式声明、子目录规则 |
| S07 | [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html) | JSON格式与互操作 |
| S08 | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | 结构校验 |
| S09 | [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html), [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html) | HTTP、缓存与URI |
| S10 | [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) | SHA-256定义；不等同签名 |
| S11 | [ISO 3166](https://www.iso.org/iso-3166-country-codes.html) | 国家/地区与行政区编码体系 |
| S12 | [CLDR UTS35 Core](https://www.unicode.org/reports/tr35/), [CLDR supplemental](https://www.unicode.org/reports/tr35/tr35-info.html) | subdivision code与containment、locale数据 |
| S13 | [unicode-org/cldr-json](https://github.com/unicode-org/cldr-json), [cldr release-49](https://github.com/unicode-org/cldr/tree/release-49) | 本包实际Unicode数据上游 |
| S14 | [modood China divisions](https://github.com/modood/Administrative-divisions-of-China) | CN历史统计层级；源README/许可证已随快照保留 |
| S15 | [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [Action SHA policy](https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/) | concurrency、permissions、完整SHA固定 |
| S16 | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), [MIT](https://opensource.org/license/mit) | 备选许可比较 |
| S17 | [IMBoy inspected commit](https://github.com/imboy-pub/imboy-flutter/commit/2cee59317de36e2f70420f46dc881b1117b034c9) | 已存在的路径/保存导航修复；执行时仍须刷新基线 |
| S18 | [geo_regions repository](https://github.com/imboy-pub/geo_regions) | 用户已建仓与BSD-3-Clause；本轮只读核对 |

## 不可变上游快照 / Pinned data snapshots

- CLDR JSON: `7d2b9cb11cec08f4d333ad73209deb3df0711c3b`
- CLDR XML release 49: `96e54b273d2da4ec6fbad350ba19ff23fa24a588`
- CN source: `c49d495b40ac73eb1a66f6eeae5f8fd10696f035`

源提取日期不等于源数据生效日期。特别是CN深层快照为2023-06-30；2026-11-13只是本轮获取/核对时间。CLDR资料中的质量与地域profile按原源保留，不把它转换为项目人工审核或现实世界完整性结论。

Retrieval dates are not effective dates. Distinguish source quality, territorial profile, project review and coverage completeness in every report.
