# CN 迁移准备规则 / CN migration preparation rules

状态：**研究规则，2026-11-19**。按[四项属主决定](CN_SOURCE_DECISION.md#6-已确认的四项属主决定)准备；当前C历史种子不变，A实源导入和A′采集未批准。
文献候选见[证据目录](evidence/cn-source/README.md)。本文件不包含真实旧ID到新ID的映射，也不宣布CN迁移引擎已实现。

## 1. 证据与日期

逐事件记录来源URL、文号、取得方式、材料性质、使用依据及未知项。
区间从2023-07-01开始；少数2026事件不能证明整个区间已覆盖。

| 日期 | 含义 |
|---|---|
| 页面发布/更新日期 | 网站的发布时间，可能晚于成文或生效 |
| 成文/公告日期 | 公文或公告落款，不自动等于生效 |
| 批准日期 | 原批准文件中的日期；“近日批准”不能补成具体日期 |
| 生效日期 | 须有直接依据；未知保留null |
| 挂牌及本项目核查日期 | 分别记录，不反推行政生效日 |

可公开的参考元信息与实际数据使用依据分开。取得公告不等于已证明其中全部材料可按项目预期再分发。
source hash、文号和CI通过分别证明固定性、文献标识及机器检查；均不能替代法律判断。

## 2. 身份与路径规则

| 变化类型 | 研究规则 | 不允许的处理 |
|---|---|---|
| 纯改名，实体身份连续 | 保留ID；更新实际名称来源和结构revision | 因新名称生成新实体，或静默继承候选译名 |
| 代码变化，实体身份连续 | 依据明确crosswalk保留身份，保存旧码和证据 | 假定code永不变化或永不重用 |
| 改父 | 明确旧父、新父及理由；保留实体身份并重新验证保存路径 | 只换dataRevision让旧pathIds继续通过 |
| 部分区域/下级单位划转 | 先判断目标层级是否改变；可能只有边界变化，县级ID不变 | 把局部划转等同县级实体整体替换 |
| 合并/撤设/拆分 | 逐实体记录退役、后继候选及足够范围证据；歧义要求重新选择 | 自动选首个候选、按名称相似度接受继承 |
| 同一代码代表新实体 | 保留旧实体退役历史；给新身份独立ID | 把旧ID重新绑定为另一实体 |
| 统计分组变更 | 与真实行政实体分开，单独记录移除/保留/改父影响 | 将“市辖区”“省直辖县级分组”当行政城市 |
| 无法映射 | 明确unmapped及原因，保留解释旧selection的版本能力 | 删除历史记录、用unknown伪装确认叶节点 |

沿用[DATA_RULES §6](DATA_RULES.md)和[PROTOCOL](PROTOCOL.md)：旧release不覆盖，旧selection用原dataRevision解释。
新树检验通过不等于旧选择能自动迁移；语言包与新结构兼容revision须同步，但不能借此提高名称质量。

A 的官方公告可帮助解释事件，A′ 的快照差异可帮助发现变更；两者都不能仅靠diff推断真实身份继承。

## 3. 迁移记录的研究检查清单

未来获准处理真实数据后，至少需要旧/新快照标识、受影响旧ID、明确后继或unmapped原因、
旧/新父级、变化类型、文献引用、日期含义、使用依据和逐项审查记录。
本轮只研究这些字段，不填写真实映射；不新增CN官方适配器或生产schema。

仓库现有两类记录用途不同：

- `sources/migrations/{CC}.json`由各国适配器解释来源、排除项和迁移影响，不能仅凭文件存在宣称通过通用身份审计。
- `audit/migrations.json`供CLDR侧的 `semantic_audit` 核对实际变更事件、from/to snapshot和证据hash。
- 当前 `geo-regions-seed` 缺相应身份sidecar；见[UPDATE_RUNBOOK](UPDATE_RUNBOOK.md)。不把CLDR-only能力直接用于或宣传为CN实源保证。
- 未实现CN拆并后继选择器。歧义记录被拒绝，仅证明现有精确事件契约没有接受它，并不证明业务迁移已解决。
- 通用源校验并不鉴别许可真伪；未知使用依据的提交/发布保持人工阻断，本轮不改生产校验规则。

## 4. 合成验证矩阵

测试数据仅位于临时目录，`datasetId=synthetic-cn-migration-contract`，
节点和名称明确带TEST标记，审查文本明确为合成，不含真实MCA数据。

| 场景 | 验证入口 | 证明范围 |
|---|---|---|
| 有来源父边但无逐变更审查记录 | 新增用例 `test_reparent_without_per_change_review_is_blocked` | 快照分别合法仍不足以批准跨快照改父 |
| 精确改父、snapshot及证据hash齐全 | `test_reparent_with_exact_snapshot_bound_review_passes` | CLDR合成事件契约接受精确记录；真人审核仍未验证 |
| 审查记录目标与实际变化不符 | `test_review_with_wrong_target_is_rejected` | 不能把其他变更的审查记录移用过来 |
| 两处改父只审一处 | `test_one_review_cannot_cover_two_parent_changes` | 单条审查不能覆盖所有变更 |
| 正确目标位于歧义数组首位 | `test_candidate_targets_cannot_replace_one_exact_event` | 候选列表不能代替精确事件，未实现后继选择 |
| 给旧路径仅换新revision | `test_updating_revision_alone_cannot_repair_a_saved_old_parent_path` | 必须显式建立并验证新路径 |
| 改名保ID、退役不复活、身份不重绑定 | 原 `tests/test_semantic_audit.py` | 复用既有合成回归 |
| 旧revision/语言兼容/父路径 | 原 `tests/test_geo_data.py` | 复用选择与版本契约 |
| 未申报删除/有证据退役 | `tool/update_rehearsal.py --selftest` | 复用临时合成演练，不访问真实数据 |

命令和实际结果见[证据目录验证节](evidence/cn-source/README.md#4-验证入口与范围)。

## English scope

Retain identity only with entity-continuity evidence. Reparenting requires an explicit event
and a revalidated selection path. Partial territory transfers need not retire county identities.
Ambiguous successors require review/reselection; source-code equality or name similarity is insufficient.

The new tests reuse the existing CLDR-only snapshot contract using synthetic TEST identifiers.
They are not a real CN importer, successor resolver, rights checker or production migration guarantee.
