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

## 5. 第二轮现势对账（KR 虚构实体修复 + 六国盘点）

| CC | 发现 | 处置 |
|---|---|---|
| **KR** | CSC states=16：**虚构实体 "Jeonnam-Gwangju Integrated Special City"**（2024 讨论未实施的整合市）且缺 Gwangju/全南分立；38 个子节点（全南郡市+光州区）混挂其下 | **已修**：删除虚构实体，拆出 iso3166-2:KR-17（South Jeolla/全罗南道）+ iso3166-2:KR-18（Gwangju/光州）两个真实 2026 广域团体（含 zh-Hans/ja/ko 名），38 子节点按 Gwangju/Gwangsan-gu→KR-18、其余→KR-17 分流；**KR 现为 17 广域团体、0 孤儿** |
| **RU** | CSC 83 联邦主体 vs 2026 现行 85 | 自洽：83 = 85 − Crimea − Sevastopol（争议主体 CSC 上游有意排除）；短命名形态（Altai vs Altai Krai）非缺实体 |
| **SA** | 13 regions | ✓ 与 2026 现势一致 |
| **DE** | 16 州 ✓（Wikidata P300 对账 16/16）；Gemeinde 层 7,107 vs GV100 ~10k+ 覆盖缺口 | 州级通过；县级缺口如实（Destatis 直链 HTML 驱动） |
| **IT** | 省级 CSC 129 vs Wikidata IT- 131 近对齐；cities 10,216 vs ISTAT 现势 ~7,900（**多出 ~2,300，疑含已合并/变更实体**）；ISTAT 官方 CSV 直链 404 | 省级初步通过；cities 层现势缺口**待 ISTAT 源接入**（SPARQL 间歇限流，深对账暂 BLOCKED_ENV） |
| **GB** | 221 一级单位=4 国混合层级（unitary 82/metro 36/LB 32/county 23/council 32/district 11/country 3/province 1/city 1），England 国层级缺失 | 实体真实但结构口径杂；ONS 接入前如实保留 |

## 6. 结论（2026 现势达成度）

- **2026 现势已达成**：FR（INSEE 2026-01-01）、JP（Geolonia 最新）、KR（17 广域团体修正后）
- **高置信通过**：US（99% counties）、RU（83 自洽）、SA（13）、DE 州级（16/16）
- **缺口如实**：IT cities 层（待 ISTAT）、DE 县级（待 Destatis）、GB（待 ONS）、RU cities（无独立源）、KR 光州 4 区 CSC 缺失
- 每节点的 sourceRefs 与时点标注使 2026 达成度可审计

## 7. 第八轮收口探测（2026-11-14）

| 项 | 结果 |
|---|---|
| **DE 市镇覆盖** | Wikidata Q26266 计数 **10,178** vs CSC 7,107 → **CSC 仅 ~70% 覆盖**（定量确认，与 JP 同类上游缺口）；Destatis 官方源接入仍是唯一根治路径（BLOCKED_ENV） |
| **KR 光州 4 区** | CSC KR-18 仅 2 子（Gwangju/Gwangsan-gu），Wikidata 查询限流未能二次证实——上游缺口记录维持 |
| **GB-ENG** | England 实体+码**完整在场**（iso3166-2:GB-ENG）——连续三轮的"England 缺失"疑虑彻底关闭 |

翻译侧第七轮后无新增已知错误类别：五类模式全量扫描干净、修值规则全部进生成器（重生成保持）、模糊字/日体字残留归零。

## 8. 翻译继承上限实验（第九轮，2026-11-14）

| 实验 | 结果 | 结论 |
|---|---|---|
| FR 宽松归一化继承 | 名字级匹配 93%→94%（+86 条） | 继承率 30% 的瓶颈是**结构性**的：INSEE 2026 的 24,368 个合并新名在 CSC 旧翻译集中不存在——提升需大规模**翻译生成**（非校对），超出本轮范畴 |
| JP 宽松归一化继承 | 41%（无实质变化） | 同上：CSC 旧集与 Geolonia 现势集的交集上限 |
| KR 光州 SPARQL | 限流持续 | 缺口记录维持 |

**翻译覆盖的真实路径**（属主决策项）：按国分批的 machine-candidate 翻译生成（如 FR 24,368 新名 zh-Hans/zh-Hant），每批附校对记录——这是"十语全覆盖"的下一步，规模约数十万条，应作为独立批次任务而非校对轮的隐含工作。
