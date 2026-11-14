# 翻译校对报告 / AI proof-reading report（2026-11-14）

范围：`proofreading_samples.json` 108 条（9 国 states 层，zh-Hans + ja 双语对照）。
口径：AI 校对 ≠ 人工审签（humanReviewVerified=false 不变）；质量词保持 provisional 不回写；本报告是人工审校的**底稿**。

## 1. 发现的真实错误（修正建议，未回写包）

| ID | 层 | 语言 | CSC 值 | 判定 | 修正建议 |
|---|---|---|---|---|---|
| iso3166-2:KR-11（Seoul） | state | zh-Hans | **汉城** | **错误**：2005 年后规范译名为"首尔" | 首尔 |
| csc-state:RU-Jewish | state | zh-Hans | **犹太人** | **错误**：行政区名被截断成族群名（Jewish Autonomous Oblast=犹太自治州） | 犹太自治州 |
| csc-state:RU-Nenets | state | zh-Hans | **涅涅茨人** | **错误**：同上（Nenets Autonomous Okrug=涅涅茨自治区） | 涅涅茨自治区 |
| csc-state:RU-Khanty-Mansi | state | ja | **ハンティ・マンシ語** | **错误**：带"語"（语言）后缀，Wikidata 类交叉污染 | ハンティ・マンシ |
| csc-state:SA-Northern Borders | state | ja | **北部国境** | 存疑：日语无此直译习惯 | 国境地方（需日方资料确认） |
| csc-state:US-Texas | state | zh-Hans | 德克萨斯州 | 规范偏差：大陆现行规范"得克萨斯州" | 得克萨斯州（规范库核对） |

## 2. 风格不一致（不判错，建议统一审校）

- **JP "县"后缀混用**：岛根县/爱知县/兵库县 带"县"，冈山/千叶/东京 等不带（抽样 3/12）
- **US "州"后缀混用**：特拉华州/堪萨斯州/犹他州 带"州"，新罕布什尔/佛蒙特/夏威夷 不带（4/12）
- **SA "省"后缀混用**：哈伊勒省 带，利雅得/麦加 等不带
- DE 不判：柏林/汉堡/不来梅为城市州，德语习惯本就不带 Land；巴伐利亚两译并存
- 同类截断风险（未在抽样内全查）：RU 自治区/边疆区系列名可能被 CSC 截断（Khanty-Mansi→"汉特-曼西"缺"自治区"）

## 3. 校对通过判定（抽样内）

- JP 9/12、KR 11/12、GB 9/9、IT 11/12（Latina zh=None 为缺译保留——协议正确行为）、FR 12/12、DE 12/12、SA 10/12、RU 10/12、US 8/12
- ja 除 RU/SA 2 条外全部通过（含 KR Seoul→ソウル 正确音译）

## 4. 缺口与下一步

- zh-Hant：CSC 上游 0 条——候选数据集如实保留缺失；生产繁中走 GSA-03 备忘三路径（DP-01 审校 backlog）
- 8 语覆盖 83-86%（57k-59k/68,866）；缺译保留缺失不虚构
- 本报告 + 108 条样本是人工审校底稿；审校完成后按 UPDATE_RUNBOOK 合同逐条迁移质量词
