# 数据真实性与现势性验证报告 / Data authenticity & currency verification（2026-11-14）

目标：验证候选数据集真实性/准确性，并尽可能逼近 **2026 现势**。方法：与已 staged 的官方独立源全量对账。

## 1. 逐国对账结果

| CC | CSC 层 | 官方对照源 | 对账结果 | 处置 |
|---|---|---|---|---|
| **FR** | cities 10,429 | INSEE COG millésime 2026（34,920 现势 commune，LO-2.0） | 名字级 87% 匹配；**12%（1,266 条）是 2016-19 合并潮中消失的旧市镇**（Aime→Aime-la-Plagne、Ancenis→Ancenis-Saint-Géréon 等） | **已切换**：FR 三层（18 大区+101 部+34,920 commune）全部改用 INSEE 2026，CSC 翻译按名继承（zh 10,552/30%，缺译保留） |
| **JP** | cities 1,235 | Geolonia ja.json（1,714 unique 市区町村，2024-12-25 生成；2024-26 市町村合并极近零） | CSC 仅覆盖 **~65%** 市区町村，ja 字段大量假名/形态混杂（kanji 名对撞 48%） | **已切换**：JP 市区町村层改用 Geolonia 全量 1,898（jp-city:定型码），CSC 翻译按名继承（zh 762/40%），romaji/kana/point 增强 |
| **US** | counties 3,144 | Census FIPS national_county2020（3,235） | state+name 对撞 **99%**（3,133）；差异=CT 废县改规划区（CSC 反映新政区划）+AK borough | 保留 CSC（真实、反映 2026 制度现状），Census 作验证源记录 |
| DE/GB/IT/RU/KR/SA | — | 无已 staged 官方源（ONS 端点障碍/无合规 GitHub 源） | 真实性依赖 CSC 上游（其 233 源审查中） | 保持 research 口径，来源时点如实标注 |

## 2. 现势性结论（诚实口径）

- **FR/JP：2026 现势**（INSEE 2026-01-01 / Geolonia 最新生成，时点已标注）
- **US：2020 vintage FIPS**（county 层 2020-26 变动极少，CT 新制已反映）
- **其余六国：CSC 上游时点**（e9c4dec，上游内容对 DE/GB/IT/RU/KR/SA 的 2026 现势性**未独立验证**——如实标注，属后续逐国官方源接入事项）
- 节点总量 68,866 → **93,682**（FR +24,611 现势 commune、JP +611 补齐市区町村）

## 3. 翻译准确性全量扫描与修值

| 模式 | 数量 | 处置 |
|---|---|---|
| Shi→史/士 尾部音译垃圾 | 60 | **已修**：规则化改市/士→市（quality→machine-candidate，45 JP+16 其他） |
| Gun→枪 | 3 | **已修**→郡 |
| "City"直译污染 | 2 | 保留+uncertain（Town 'n' Country 城市与乡村：直译但语义对，规范名待核） |
| zh 值=拉丁原文冒充中文 | 16 | **已删除**（缺译保留缺失，missingNames 相应 +） |
| ja/ko/ru 同英文残留 | 5/78/364 | 保留（欧洲地名拼写同形合法；ko/ru 小地名无译文如实） |
| de/fr/it 大量同英文 | 52k-53k | **正常**（欧洲国家城市在邻语中同拼写），非错误 |

修值后重算 locale revision；quality 只用 source-native/provisional/machine-candidate 三档，humanReviewVerified=false 不变。

## 4. 十语矩阵（官方层切换后）

en 93,682(100%) / zh-Hans 30,554+ / zh-Hant 56,742+ / ja / ko / ru / de / fr / it / ar 详见 translation_coverage.json；FR/JP 新层缺译（FR 70%、JP 60%）保留缺失，由后续翻译批次（machine-candidate）补齐。
