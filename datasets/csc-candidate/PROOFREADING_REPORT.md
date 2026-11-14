
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
- 十语覆盖（五级证据链全部应用：FR=P374 INSEE / JP=P429 dantai / GB/IT/RU/DE=P300 ISO / 七国 CSC wikiDataId QID 直取 / FR·JP 行翻译 qid 桥 / GeoNames alternateNamesV2 wkdt 行）：en 93,683 (100%) / zh-Hans **83,868** / zh-Hant **83,889** / ja **63,497** / ko **60,078** / ru **73,332** / de **85,560** / fr **85,534** / it **85,514** / ar **61,403**（累计闭合 ~163k 缺口格）
- QID 直取卷明细：US 提取件 20,051 节点（zh-Hans 17,462/de 18,684/fr 19,757/ru 10,589/ja 11,461/ko 6,921/ar 16,689）、DE 7,370 行 QID 97%、IT 9,896 行 96%、GB 3,460 行 88%、RU 5,878 行 83%
- CSC 翻译桥（2026-11-14）：FR/JP 层按名字归一化继承 CSC 翻译会静默漏接拼写分歧的行；行内 wikiDataId ↔ staged Wikidata 抽取件 qid 构成精确二次 join，桥回 FR 367 节点 + JP 268 节点的漏接译文（+1,043 格）；52 个散落未填格为 ZH_GARBAGE_DROPS 有意治理（如 The Acreage→面积、LMS→学习管理系统等机器直译），非漏接
- GeoNames alternateNamesV2 通道（2026-11-14，最后一个证据通道，已关闭）：alternateNamesV2.zip（205MB，sha256 bfc309fa…）含 `wkdt` 行=Wikidata QID 本身，CSC wikiDataId 直换 geonameid 免 SPARQL；**15,333/83,523 QID 命中**（FR 市镇仅 16 节点带 wkdt——GeoNames 对法国小市镇几乎无 wkdt 同步）；fill-missing 实收 **+608 格**（US ru 604 / DE zh 2 / IT ru 1），JP/FR 桥接节点标签已被 Wikidata 全覆盖、GeoNames 零增量；提取件 id 空间教训：FR/JP 必须走桥（fr-commune:*/jp-city:*），直接行 csc-city:* 键为幻影（首轮误报 2,180 可填格）
- 残余缺口 156,978 格 = **长尾**：小市镇在目标语维基无标签、CSC 无译文、GeoNames 无对应语别名、或行无 QID（US ~7k/语、FR ja/ko/ar ~23k/语、JP 无条市村等）——**五个证据通道全部应用并关闭**；出路 = 规则转写/AI 生成工程（进行中：ja/ko 已落地，ar/zh/fr-eng 待片）或人工贡献；候选层审阅不受阻
- 规则转写工程首片（2026-11-14，commit e168bab 之后）：**RU ja +1,714 格**（西里尔→片假名规则表，`tool/gen_candidate_rule_transcriptions.py`，28 个标准译名 eval 锚点 100% 通过才落盘；正字法级规则：词首/词中辅音、鼻音同化、те→テ、词尾清化 б/в→フ г→ク、ва 词尾→ワ、ое 词尾→エ；数字后缀/乌克兰字母行诚实跳过）。**质量词 machine-candidate**（(nid,locale) 二元组归因，与 provisional 精确区分）。残余 160,472 → **158,758**
- 规则转写工程第二片（2026-11-14，commit 080f60d 之后）：**RU ko +1,780 格**（西里尔→谚文，韩国外来语标记法；jamo 组字索引改为**参考音节经验推导**——硬编码 18 字母序与 Unicode 19 槽错位、ㅅ 实为 index 9；成典规则：sonorant н/м/л 받침、в+с → ㅂ 받침（하바롭스크）、л 元音间/辅音后一律 double（볼로그다/슬라블/들로）、нк+辅音 → ㅇ 同化省略（상트）、词尾清化送气 б/в→프 г/к→크、词尾软 рь→리（트베리）、词尾 й 合并（니즈니）、E 어두 예/자음 뒤 에；32 锚点 100% 过闸）。残余 158,758 → **156,978**（ko 总覆盖 60,078→61,858）
- 已知错误模式残留：**0**（suffix/latin/garbage/混体全部规则化进生成器）
- 权威汇总文件：`translation_coverage.json`、`verification_p300_batch.json`（selfCorrections 台账）、staged 取数件 `staging/wikidata-fr/fr-labels.json`（CC0，sha256 记录于生成日志）
