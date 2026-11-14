
---

# 第二轮：cities 层校对（180 条，每国 20）+ zh-Hant 生成记录（2026-11-14）

## 1. zh-Hant machine-candidate 包（GSA-03 路径 A 落地）

- **57,512 条 zh-Hant 候选**，全部 `machine-candidate` 质量（绝不冒充上游/审校）：
  - JP：CSC ja 汉字名直用 + 日体字归一（対→對、沢→澤、瀬→瀨 等确定映射）
  - KR/其余 7 国：zh-Hans 简转繁（保守映射表 ~420 对，模糊字台/里/后/干/松/系等**不映射保留并计数**）
  - 5 处校对修正直接生效：首爾、猶太自治州、涅涅茨自治區、漢特-曼西自治區、得克薩斯州
- 发现并修复**转换表两轮缺口**：第一轮漏字导致混体（聖玛爾特：玛→瑪缺失）；补 ~150 对后全部混体消除；杨→楊 等高频补齐
- 质量词不回写为 approved：转换候选 = 审校底稿（humanReviewVerified=false 不变）

## 2. cities 层新发现（180 条实测）

| 类 | 例 | 判定 |
|---|---|---|
| CSC 上游错误 | JP Ichikikushikino zh=**一串串木野史**（Ichiki-kushikino 拆解错误+Shi 音译成"史"）；Rishiri Gun zh=**利尻枪**（Gun=枪）；Minamiawaji Shi zh=南淡路**士**；KR Kimje=**金杰**（金堤）、Puan=**普安**（扶安）；SA "City Ghran" zh=**城市格兰**（City 直译） | **wrong**：日英后缀被音译成实义字；修正记录为审校底稿 |
| zh-Hans/hant 通道错位 | JP Buzen zh=丰前市 vs hant=豊前（ja 不带"市"）；Ōhara 大原町 vs 大原 | inconsistent：JP 双通道风格需统一审校 |
| 日体字借字 | 対馬市/野沢温泉/岩瀬（首輪 kanji-direct） | 已修：對馬市/野澤温泉/岩瀨 |
| 音译质量 | US Smithland=史密斯**蓝德**（兰）、Big Timber=大廷伯 | uncertain：音译规范需译名库核对 |
| 数据质量（非翻译） | US 名单含 Ingenio（意大利式名）；SA Ash Shi`b 未翻译保留原文 | 记录为 CSC 上游数据质量问题 |
| 缺译保留 | IT Gemini / US Pocopson 等 zh=None | **正确行为**（不虚构） |

## 3. 十语矩阵（更新后）

| locale | 覆盖 | 质量 |
|---|---|---|
| en | 68,866 (100%) | source-native |
| zh-Hans/ja/ko/ru/de/fr/it/ar | 57k-59k (83-86%) | provisional（上游 CSC 翻译） |
| **zh-Hant** | **57,512 (83.5%)** | **machine-candidate（本轮生成：JP kanji-direct + 8 国 s2t + 5 处修正）** |
| 校对状态 | states 108 条 + cities 180 条 = 288 条 AI 校对 | humanReviewVerified=false 不变 |


---

## ⚡ LIVE FIGURES（最终重生成实测 2026-11-14，优先于正文历史快照）

多轮修值与官方层切换后，正文中的轮次快照数字已过时。当前实测：

- **节点总数 93,683**（FR 35,040 / JP 1,946 / KR 327 / 其余 CSC 层）
- 十语覆盖：en 93,683 (100%) / zh-Hans 57,237 / zh-Hant **57,255**（machine-candidate+CLDR root）/ ja 57,823 / ko 57,591 / ru 58,884 / de 58,339 / fr 58,336 / it 58,345 / ar 57,291
- 已知错误模式残留：**0**（suffix/latin/garbage/混体全部规则化进生成器）
- 权威汇总文件：`translation_coverage.json`、`verification_p300_batch.json`（selfCorrections 台账）
