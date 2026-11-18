# CN 数据来源决策报告 / CN Data Source Decision Report

> 调查日期 / Investigated: 2026-11-18
> 状态 / Status: **CONDITIONAL — 待属主决策 / awaiting owner decision**
> 范围 / Scope: `geo-regions-seed` CN 分支的官方现势数据来源（`docs/superpowers/specs/2026-11-16-ten-country-official-region-completion-design.md` Batch 1 门禁）

---

## English Summary

**New finding:** the 全国行政区划信息查询平台 (National Administrative Divisions Information Query Platform) runs directly on the Ministry of Civil Affairs' own subdomain **`xzqh.mca.gov.cn`** — copyright footer "版权所有：中华人民共和国民政部", ICP 京ICP备13012430号. This supersedes the earlier Batch-0 finding that only the third-party mirror `udu.org.cn` hosted this platform (udu.org.cn is now unreachable from both our egress paths; it is moot).

Verified capabilities (2026-11-18, all commands reproducible):

1. `POST http://xzqh.mca.gov.cn/selectJson` (empty `shengji`) returns the **complete prefecture-level list with official 区划代码** — 341 rows: 337 coded entries (incl. 4 municipalities) + 4 provincial-direct county grouping rows. Mainland only (no 81/82/83 HK/MO/TW codes) — matches the CN profile's excluded kinds.
2. `/description?dcpid=1` indexes **official county-and-above change records for every year 2001–2026**, full text with government announcement dates. Sample verified: 2024 铁门关市 adjustment (2024-05-31), 云南 德钦/维西 adjustment (2024-09-27), new counties 和康县/和安县 (2024-12-27); 2025 重庆两江新区 (2025-11-07); 2026 草湖市 establishment (2026-04-17).
3. `/statistics/` publishes the official annual 行政区划统计表 1998–**2022** (latest: 34 省级 / 333 地级 / county breakdown per province) — an authoritative validation baseline, frozen at 2022.

**County cascade — verified after full-width parenthesis discovery:** the province dropdown values embedded server-side use **full-width parentheses**（`北京市（京）`，U+FF08/U+FF09）. With the exact option values the cascade fully works: `shengji=北京市（京）` → prefecture; `+&diji=北京市` → all 16 districts with official codes (110101 东城区…；110103 崇文/110104 宣武 absent = post-2010 merges — the data is genuinely current, not a stale copy). Spot-checked 河北省（冀）→石家庄市 → 22 county entities (130102–130184). **Complete 3-level enumeration ≈ 370 API calls (~34 provinces × avg ~11 prefectures) — trivially scriptable. The A' path is engineering-ready.**

**License gap (the decision):** the platform asserts copyright (民政部) but publishes **no explicit open-data or redistribution license** — unlike the other eight countries' sources (GoS 2.0, KOGL-1, PD, OGL v3, Dl-DE-BY, fr-lo, CC-BY-4.0). Under PRC law the individual 公告 texts are likely outside copyright (著作权法第五条: official documents), and 政府信息公开条例 governs proactive disclosure, but the assembled code tables' database rights and BSD-3 redistribution compatibility **require an owner judgment call**. Per the design gate ("不能确认时停止 CN 数据提交"), no production data was generated from this source in this round.

Decision options and the minimal question list are in §5–§6.

---

## 1. 背景：CN 在 seed 中的现状

| 项 | 现状 |
|---|---|
| seed CN 数据 | `data/regions/CN.json` 3,430 节点（1 country + 31 省级 + 333 地级 + 2,974 县级 + 82 乡级样例 + 9 statistical-group） |
| 来源 | modood/Administrative-divisions-of-China `pca-code.json`（commit c49d495，**WTFPL v2**）+ CLDR 省级码 |
| 时效 | **2023-06-30 冻结快照**；上游已声明停更（`docs/DATA_COVERAGE.md` 已如实标注"不能称 2026 现势行政数据"） |
| Phase 2 目标 | Batch 1：官方来源补到县级并处理 2023 后变更（本报告的门禁对象） |

Batch 0（2026-11-17）结论：国家统计局 2024-10 起不再公开统计用区划代码（新统计法）；民政部主站栏目改版链接失效；候选渠道 udu.org.cn 待验。**本轮（2026-11-18）调查更新了全部三项。**

## 2. 候选来源对比

| 来源 | 等级 | 数据内容 | 现势性 | 机器可读 | 许可/授权 | 判定 |
|---|---|---|---|---|---|---|
| **xzqh.mca.gov.cn 平台**（本轮新发现） | **A**（民政部官方 gov.cn 子域，版权所有=民政部） | 区划代码+名称（省/地级实测；县级待逆向）；逐年变更公告 2001–2026；统计表 1998–2022 | **2026 现势**（含 2026-04 草湖市） | JSON API 已实证（`selectJson`）；公告为 HTML 全文 | **未明示开放许可**（仅版权声明）——见 §4 | **可信度最高；授权待属主拍板** |
| 国家统计局 stats.gov.cn | A | 统计用区划代码（历史版本至 2023） | 2023 为最后公开版（2024-10 起停发） | 旧路径 404；本期未找到可下载入口 | 未验（页面不可达） | 渠道萎缩；可作历史基线补充 |
| modood/Administrative-divisions-of-China | C（第三方整理，上游自报源自民政部/统计局公开资料） | 省地县乡五级码表 | 2023-06-30 冻结停更 | ✓ JSON（seed 现用） | **WTFPL v2（明示、干净）** | 现役基线；不能称现势 |
| CLDR subdivision | B | 省级 ISO 3166-2 码+十语名 | 随 Unicode 版本更新 | ✓ | Unicode-3.0 | 仅省级（seed 已用） |
| Wikidata（P300/P13971） | B | 省市县级多语标签+官方码 join | 社区维护，滞后不一 | ✓ SPARQL | CC0 | 已用于 seed i18n 叠加；不作结构真源 |
| GeoNames | C | 罗马字/别名 | 滞后 | ✓ dump | CC-BY-4.0 | 已用于 en 罗马字叠加；不作结构真源 |
| dr5hn/countries-states-cities-database | C | 省州市三级 | 滞后且来源混合（含 ODbL CSC 血统） | ✓ | ODbL（share-alike 风险） | **排除**（设计稿点名禁冒充） |
| CSC 候选层 | C | 同上 | 同上 | ✓ | ODbL | **排除**（不得并入正式集） |
| udu.org.cn | D | 第三方镜像（自述数据源自民政部） | 未知 | 未知 | 未知 | **不可达**（curl 000 + WebFetch ECONNRESET，双出口）——已被官方平台取代，不再调查 |

## 3. 官方平台实测证据（可复现）

证据快照：`staging/cn-mca-platform/evidence/`（gitignored 本地件；平台在线可直接复验）。

```bash
# ① 地级全量+官方区划代码（341 行，UTF-8 JSON）
curl -s -X POST 'http://xzqh.mca.gov.cn/selectJson' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' \
  -H 'Referer: http://xzqh.mca.gov.cn/map' --data 'shengji='
# 样例行: {"diji":"北京市","quHuaDaiMa":"110000","quhao":"", ...}

# ② 逐年变更公告索引（2001–2026）
curl -s 'http://xzqh.mca.gov.cn/description?dcpid=1'   # GBK 编码
curl -s 'http://xzqh.mca.gov.cn/description?dcpid=2026'

# ③ 官方年度统计表（1998–2022）
curl -s 'http://xzqh.mca.gov.cn/statistics/2022.html'  # 34省级/333地级/分省县级分解
```

关键实证细节：

- `selectJson` 空参返回 **341 行**：337 行带 6 位官方码（11/12/31/50 四直辖市各 1 行，65 新疆 14 行与官方口径一致）+ 4 行“（省/自治区）直辖县级行政单位”分组行（县级市在分组内，需级联枚举）。**无 81/82/83 港澳台前缀** → 与 CN profile 的 `excludedKinds: hk/mo/tw` 一致。
- 变更公告为**全文**且带公文出处（例：“新疆维吾尔自治区人民政府2024年12月27日公告”），可直接结构化为迁移记录（设计稿 §7 口径）。
- 统计表 2022 为最新一期（该栏目 2022 后停更）→ 作 2023 前的计数基线；2023 后计数校验用平台查询数据。
- **县级级联已打通（全角括号关键）**：省级参数须用页面内嵌下拉的精确值——**全角括号** `北京市（京）`/`河北省（冀）`（此前半角/裸名/GBK/码四种形态全返回 `[]` 的根因）。级联实测：北京 16 区（110101–110118，崇文/宣武缺席=2010 合并后形态 ✓ 数据非陈旧拷贝）、石家庄 22 县级（130102–130184 ✓）。全国三级完整枚举 ≈ 370 次调用，可脚本化。证据件：`selectJson_beijing_districts.json`、`selectJson_sjz_county_sample.json`。
- stats.gov.cn：域名可达，但旧统计区划代码路径 404、`/sj/tjbz/` 为 JS 壳页；本期未发现 2023 快照的可下载入口（Batch 0 结论维持）。

## 4. 授权分析（BSD-3 兼容性）

| 维度 | 事实 | 影响 |
|---|---|---|
| 平台版权声明 | “版权所有：中华人民共和国民政部”，无任何使用条款/开放数据许可页 | 与其余八国源（均有明示许可）形成**唯一缺口** |
| 公告文本 | 《著作权法》第五条：法律、法规、国家机关的决议、决定、命令等官方文件不适用本法 → 变更公告本身大概率无著作权 | **A 路径（增量公告）法律面最干净** |
| 码表汇编 | 平台数据库作为汇编作品可能受汇编权保护；无明示许可时再分发存在不确定性 | **A' 路径（整表抓取）的主要风险点** |
| 信息公开框架 | 《政府信息公开条例》主动公开信息无禁止转载条款，但也未授予明示再许可 | 不构成禁止，也不构成授权——需属主风险判断 |
| 现役 modood 数据 | WTFPL v2（无任何限制） | 2023 基线无授权风险 |

**结论：授权是 CN 唯一的未决维度；来源权威性与数据完整性均已达标（县级 API 形态待逆向，属工程量而非可行性问题）。**

## 5. 决策选项评估（相对 Batch 0 的更新）

| 选项 | 内容 | 本轮评估更新 | 授权链 |
|---|---|---|---|
| **A（推荐）** | modood 2023 基线（WTFPL）+ xzqh.mca.gov.cn 2024/2025/2026 官方公告增量（结构化为迁移记录） | **可行性大增**：增量源已实证（逐年全文公告，年均个位数条变更）；统计表 2022 可作计数锚 | 最干净（WTFPL + 官方文件豁免） |
| **A'** | 以平台查询数据（selectJson 全量）为主源直接重建现势 | 权威性最高、2026 现势；**县级级联已实证打通（全角括号参数），完整枚举 ≈ 370 次调用——工程就绪**；前置条件仅剩：属主接受无明示许可 | 有不确定性 |
| **B** | 等待《行政区划代码管理办法》（令第79号）配套发布渠道 | 本轮未发现新渠道落地证据 | 未知 |
| **C** | 维持现状（2023 冻结快照+诚实标注） | 零成本；产品代价=CN 无现势声明 | 无风险 |

A 与 A' 非互斥：可先 A（公告增量）快速把 seed 推进到“2023 基线+官方增量至 2026-04”，再视授权判断决定是否 A' 全量切换。

## 6. 最小决策问题清单（属主只需回答这四个）

1. **授权判定**：接受“gov.cn 官方平台无明示开放许可”的数据进入 `research-seed`（研究种子层，非 BSD 再授权发布物）吗？——接受则 A' 可行；不接受则仅走 A（公告增量，法律面最干净）。
2. **路径选择**：A（快+干净，现势性=2023+增量）/ A'（全量现势，需先逆向县级 API）/ C（维持）？
3. **工程启动**：若选 A'，是否批准全量抓取脚本（级联已打通，预计 1 个会话内完成抓取+适配器+TDD+迁移记录）？
4. **发布口径**：CN 在包级元数据中标注 “2023 statistical base + official MCA increments to 2026-04”（A）或 “MCA platform snapshot 2026-11”（A'）——确认措辞。

---

## 附：本轮同步复核的 RU/SA 证据更新（2026-11-18）

- **RU**：Rosstat `rosstat.gov.ru` 从“数据路由 404”恶化为**站点级 403 IP 封锁**（“Доступ к сайту запрещён”，数据中心出口 IP 139.162.84.229；WebFetch 服务端同遭俄国家 CA SSL 拒绝）。家庭宽带出口可能不受影响。A/B/C 决策选项不变，证据更新为“IP 级封锁，恢复时间不可预期”。
- **SA**：GASTAT `stats.gov.sa` 本轮 **200 可达**（此前 SPA 超时）；但其数据门户 DataSaudi 仅 region 级指标，**无 governorate 级数据集、无官方编码表**。NCAR `ncar.gov.sa` 仍超时。A/B/C 选项不变，证据更新为“GASTAT 渠道恢复但内容不满足门禁接口（sa-governorate:{official-code}+阿语官方名）”。

（RU/SA 详证见上一轮 Batch 5 报告与 `sources/` 内既有记录；本轮仅更新可达性证据。）
