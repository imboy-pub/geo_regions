# CN 数据来源决策报告 / CN Data Source Decision Report

> 平台调查 / Platform investigation: 2026-11-18
> 属主确认 / Owner decision: 2026-11-19 (Asia/Shanghai)
> 状态 / Status: **限定准备工作已授权；MCA 数据再分发依据仍未确认**
> 范围 / Scope: `geo-regions-seed` CN 来源、文献证据及迁移规则准备；不是数据更新或发布批准。

## English summary

The owner confirmed the four decisions in §6: retain **C** as the current historical seed, prepare **A** as the conditional next step, and defer **A′**. Documentation, a bounded reference index, migration rules and synthetic validation are authorized. Nationwide acquisition, real CN data import, production-gate changes and release are outside this decision. PR #5 merging is a separate decision.

The 2026-11-18 report established the official MCA platform and successful prefecture/county sample queries. Those observations do not establish nationwide completeness, a uniform effective date, redistribution rights or historical identity continuity. No API probes were repeated for this preparation.

Code remains BSD-3-Clause; third-party data retains its applicable terms. A research-seed label does not supply redistribution rights. Owner risk acceptance cannot substitute for third-party permission where permission is legally required.

## 1. 审查基线与现有数据

| 项目 | 固定基线 |
|---|---|
| 原调查 PR / report | [PR #5](https://github.com/imboy-pub/geo_regions/pull/5), HEAD `1e181bd08ff26ed6079a92105ff7ff468e989df9` |
| 政策 main | `46b8779607af35af27b1ca158ee44bd7f9f099aa` |
| CN 种子 | 3,430 节点；大陆31省 profile，含统计分组及部分乡级样例 |
| 历史来源 | modood `c49d495b40ac73eb1a66f6eeae5f8fd10696f035` 的 `pca-code.json`，上游声明 WTFPL v2；另保留 CLDR 等材料各自许可 |
| 数据日期 / 成熟度 | 2023-06-30 / `research-seed`；未验证为2026年现势 |
| 本轮数据状态 | 未改 CN 结构、语言包、source-lock、manifest 或生产门禁 |

[LICENSE_POLICY](LICENSE_POLICY.md) 明确：上游 WTFPL 声明不能独立证明全部底层权利、准确性或时效性；根目录 BSD 不重新许可第三方数据。
[DATA_RULES](DATA_RULES.md) 和[官方来源补全设计 §4](superpowers/specs/2026-11-16-ten-country-official-region-completion-design.md)仍适用，许可不明确时不得提交派生数据。

## 2. 已有平台证据及其限度

本节保留2026-11-18的调查结论；原请求和记录见[固定版本报告](https://github.com/imboy-pub/geo_regions/blob/1e181bd08ff26ed6079a92105ff7ff468e989df9/docs/CN_SOURCE_DECISION.md)。
原报告称快照保存在本地 `staging/cn-mca-platform/evidence/`，这些未提交的文件不是本次可随仓库复验的证据件。

| 已记录观察 | 可以支持 | 不能据此支持 |
|---|---|---|
| `xzqh.mca.gov.cn` 为民政部官方子域，页脚有民政部版权声明 | 来源身份得到较强支持；第三方镜像不再是必要渠道 | 已取得开放许可、所有字段必然受保护或必然不受保护 |
| `selectJson` 空省参数返回341行：337带码行（含4直辖市）及4分组行 | 已验证该请求的响应形态 | 341个真实地级行政实体，或全国县级数据完整 |
| 精确全角括号参数下，北京16区、石家庄22县级样本级联成功 | 县级级联样本可获取；不再标“县级API待逆向” | 全国所有分支均通过、2026现势完整 |
| 北京样本不含崇文/宣武旧条目 | 样本不是相应旧区划形态 | 全国数据更新截至2026 |
| 公告栏目覆盖2001—2026；统计表栏目至2022 | 存在变更文献线索和历史统计参照 | 公告与查询码表已全部同步；2022计数证明2026覆盖 |

原报告约370次请求是采集规模估计，未验证全国枚举、重试、口径归一和迁移成本，不作为“一个会话完成”的交付承诺。公告中的日期也不能自动当作行政生效日期。

## 3. 证据目录与时间窗口

有限文献核查和待补项见[CN证据目录](evidence/cn-source/README.md)及[候选索引](evidence/cn-source/candidates.json)。
这里只存来源链接、文献日期和简短研究概括，不存官方响应、行政码表、真实迁移映射或公告全文。

A 的待核区间从 **2023-07-01** 开始，不能跳过2023年下半年。候选索引覆盖数个代表事件，**不是全国完整变更目录**，不能据其推导“数据更新至2026”。

页面发布、公告成文、批准、生效、挂牌及本项目核查日期分别记录；未知保留为空。2026-11-18原报告的德钦/维西日期为2024-09-27，本次官方页面索引显示2024-10-10；两种来源的日期含义仍待对应，不互相覆盖。

2026-11-19接续补核已直接读取重庆市政府原公告及同文号官方转载，六条候选现为四条主页面正文已读、两条主页面仍仅检索索引。
迪庆州政府公报另提供云政发〔2024〕22号的正式转引；它不替代2024年原通知，也未解决上述两日期关系。
逐次取得方式、字段出处及未解决事项见[具体材料审查记录](evidence/cn-source/MATERIAL_USE_REVIEW.md#2-接续观察记录)；全部生效日期仍未知。

随后取得的[德钦县政府沿革正文](https://www.deqin.gov.cn/jzyg.html)将2024-07-29表述为批准日。
该日期作为附有来源限定的沿革陈述保存，不填入未取得原文件的成文或生效日期，也未解决两个公告页面日期的对应关系。
安阳、云南原文件的本次有限检索已结束；待补证目标、材料使用问题及有新线索后的接续条件见[补证问题单](evidence/cn-source/MATERIAL_USE_REVIEW.md#6-待补证问题单与接续条件)。

## 4. 权利依据与发布边界

| 类别 | 已有依据 | 本项目处理 |
|---|---|---|
| 法律事实 | [著作权法第5条](https://ipc.court.gov.cn/zh-cn/news/view-6244.html)列明特定国家机关文件、单纯事实消息等排除范围 | 具体公告、附属内容和所提取材料分别判断，不把政府网站整体视为豁免 |
| 法律事实 | 同法第15条涉及具有独创性选择或编排的数据汇编；第24条研究使用存在条件 | 不把单项事实与整体汇编混为一谈；研究种子不是公开分发许可 |
| 法律事实 | [政府信息公开条例第24条](https://www.mee.gov.cn/zcwj/gwywj/202001/t20200108_758139.shtml)规定检索、查阅、下载功能 | 可获取不能单独推出开源再许可 |
| 工程与法律适用判断 | 从正式公告独立记录必要事实，较整表提取更便于限定材料范围 | A 有条件优先，尚不认定其全部材料已清权 |
| 尚待确认 | 拟使用内容的保护范围、访问条款、下游离线/商业/跨地域分发依据及授权主体权限 | 按实际材料补依据；必要时取得专业意见或权利人授权 |

可用依据包括明确许可，或针对具体材料有充分支持的无需许可依据；并非要求为每项事实取得书面许可。
属主确认的是推进范围，未认定 MCA 数据已获许可。接受残余风险不会创造第三方权利，也不把未知许可改成已批准。

**具体材料接续发现：**[重庆市政府网站版权声明](https://wap.cq.gov.cn/wzxg/bqsm/202509/t20250901_14956023.html)含署名、商业使用和镜像限制；[新疆政府网站声明](https://www.xinjiang.gov.cn/xinjiang/wzsm/tydp.shtml)的已读文本未列明本项目所需的开放再分发授权。
前者条款对具体事实使用的适用性与效力、后者材料的无需许可依据均未审定。不能把“公告正文已读”写成“可公开分发”，也不把一站声明套用到MCA平台或其他政府网站。
两项限定材料的候选论证、反证与分发交接条件已整理为[使用依据审查草稿](evidence/cn-source/MATERIAL_USE_REVIEW.md)，没有作最终法律或授权决定。

代码保持 [BSD-3-Clause](https://opensource.org/license/bsd-3-clause)。既有数据继续保留 WTFPL、Unicode-3.0、CC-BY-4.0、CC0 等各自适用条款及完整来源说明。

**发布目录隔离：** [package_release.py](../tool/package_release.py)递归打包整个 `sources/`。未经确认的MCA原始或派生数据即使尚未导入 `data/regions/CN.json`，也不能先放入公开 `sources/`。公开Git、PR附件、已发布Release、Demo资源及CDN都不能以研究标签跳过使用依据。`.gitignore`只防误提交，不提供法律授权。

## 5. 路径比较与选择

| 维度 | A：历史基线+公告增量 | A′：官方平台整表 | C：保留历史种子 |
|---|---|---|---|
| 来源 | 官方增量+第三方历史基线 | 官方直接来源，完整性尚待核验 | 固定第三方快照，可重建 |
| 再分发 | 逐材料依据待确认，基线权利链继续适用 | 尚无明确开放/再分发依据 | 不新增MCA来源问题；不是零风险 |
| BSD | 代码BSD与数据条款分离 | 兼容性未证实，不直接断言冲突 | 保持既有分层许可 |
| 时效 | 从2023-07-01连续核查后才能声明实际覆盖区间 | 采集日期不等于生效日期或完整性 | 明确2023-06-30历史基线 |
| 身份迁移 | 事件可解释变更；统计树转换仍需审查 | 全面核对实体、统计分组、父链和历史关系 | 保留现有ID与路径，未来更新成本仍存在 |
| 成本判断 | 可分批投入；持续人工判断和防遗漏 | 首轮成本较高；来源与授权稳定后可能更省维护 | 近期新增工作最少，仍需解释时效限制 |
| 当前决定 | 只推进证据、规则和合成验证 | 暂缓采集及实源导入 | 维持现有对外数据状态 |

不承诺“年均个位数变更”或固定会话内完成。未来获得稳定、许可明确的官方快照时，可以重新比较A与A′的维护成本；当前不扩大来源调查到其他国家或替换源。

## 6. 已确认的四项属主决定

确认日期：**2026-11-19（Asia/Shanghai）**。确认人：项目属主（本次会话明确确认；不是法律专业意见或第三方授权）。

确认原文：

> 确认以上四项，按文档、证据目录、迁移规则和合成样本验证的限定范围继续推进。PR #5 是否合并另行决定。

1. **授权判定：** 暂不接受未明确使用依据的MCA原始或派生数据进入可公开分发的research-seed。继续整理来源和法律依据；后续记录明确许可或针对具体材料成立的无需许可依据。残余风险接受不替代确需取得的第三方许可。
2. **路径选择：** 当前维持C，A为下一步优先方向，A′暂缓。A从2023-07-01起补核，建立文献证据和迁移研究规则；不直接宣称全国2026现势完整。
3. **工程启动：** 本轮限定文档、证据目录、迁移规则和合成样本验证。不启动全国采集，不提交新CN数据；A真实数据导入及A′全量采集另行决定。生产门禁保持现状。
4. **发布口径：** 继续标注“CN大陆研究种子；统计基线2023-06-30；未验证为2026年现势数据”。来源调查不计作数据更新。未来A列实际核查区间；未来A′分别记录采集日期、上游生效日期和覆盖状态。代码BSD、数据条款分别保留。

PR #5 的文档合并、真实数据导入、数据发布和成熟度提升分别决定。本次确认不批准合并或公开新CN数据。

## 7. 迁移准备与接续入口

- [CN迁移规则](CN_MIGRATION_RULES.md)：同实体保ID、改父、拆并、歧义、统计分组及日期处理。
- [证据目录及任务状态](evidence/cn-source/README.md)：候选与待核事项、验证入口。
- [具体材料使用依据审查](evidence/cn-source/MATERIAL_USE_REVIEW.md)：取得过程、两项待审卡及未来分发说明的交接条件。
- [更新合同](UPDATE_RUNBOOK.md)：当前seed缺身份登记sidecar；CLDR合成审计不能冒称CN实源审计。
- [数据规则](DATA_RULES.md)：旧release不覆盖，旧selection按其dataRevision解释。

本次合成验证只证明指定工具契约，不证明行政真实性、全国覆盖、法律许可、真人审签或CN真实迁移已经完成。尚无真实CN迁移表；未实现拆并后继选择器。


## 附：2026-11-18原调查的 RU/SA 记录

以下保留原报告的历史记录；2026-11-19的CN限定准备未复验或推进RU/SA。


- **RU**：Rosstat `rosstat.gov.ru` 从“数据路由 404”恶化为**站点级 403 IP 封锁**（“Доступ к сайту запрещён”，数据中心出口 IP 139.162.84.229；WebFetch 服务端同遭俄国家 CA SSL 拒绝）。家庭宽带出口可能不受影响。A/B/C 决策选项不变，证据更新为“IP 级封锁，恢复时间不可预期”。
- **SA**：GASTAT `stats.gov.sa` 本轮 **200 可达**（此前 SPA 超时）；但其数据门户 DataSaudi 仅 region 级指标，**无 governorate 级数据集、无官方编码表**。NCAR `ncar.gov.sa` 仍超时。A/B/C 选项不变，证据更新为“GASTAT 渠道恢复但内容不满足门禁接口（sa-governorate:{official-code}+阿语官方名）”。

（RU/SA详证见原调查所引用的Batch 5报告与既有来源记录。）
