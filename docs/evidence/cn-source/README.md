# CN 研究证据目录 / CN research evidence

本目录对应[已确认决定](../../CN_SOURCE_DECISION.md#6-已确认的四项属主决定)，不是行政数据源、原始响应归档或真实迁移表。
固定调查基线为PR #5的 `1e181bd08ff26ed6079a92105ff7ff468e989df9`，政策基线为main的 `46b8779607af35af27b1ca158ee44bd7f9f099aa`。

## 1. 内容与证据等级

[candidates.json](candidates.json)只含六条代表性文献的链接、日期、简短自写概括和待核项。
`candidateId` 是文献索引号，绝非行政实体ID；文件没有行政代码、旧/新ID映射、官方响应或公告全文。
其研究窗口目标为2023-07-01至2026-11-19，`coverageThrough=null`、`coverageComplete=false`，不表示已经核查完该区间。

| 索引 | 研究线索 | 本轮取得情况 | 仍须确认 |
|---|---|---|---|
| cn-reference-001 | 安阳2023年下半年跨县级区域调整 | 官方沿革页检索索引；正文403 | 原通知、日期含义及目标层级影响 |
| cn-reference-002 | 铁门关2024年部分区域调整 | 官方公告正文已读 | 批复、生效日、范围及代码证据 |
| cn-reference-003 | 德钦/维西2024年下级单位归属调整 | 主页面仅检索索引；另有已读官方公报转引 | 原通知及2024-09-27/2024-10-10日期对应关系 |
| cn-reference-004 | 和康2024年新设事件 | 官方公告正文已读 | 生效日、代码与继承关系 |
| cn-reference-005 | 重庆2025年撤设与部分划转 | 原公告及官方转载正文已读 | 生效日、代码、区分去向的信息及网站条款适用 |
| cn-reference-006 | 草湖2026年新设事件 | 官方公告正文已读 | 生效日、代码与历史范围关系 |

每条 `effectiveDate=null`、`autoMigrationEligible=false`，使用依据均未审定。
没有用公告日、页面日期或“近日批准”代填生效日。只有检索内容的条目不能标成正文复核通过。
原报告另提到和安县；本次未独立复核，不把它冒充已核条目。

接续后主页面取得状态为四条正文已读、两条仅检索索引；补充文献不是新的行政事件，也不提高全国覆盖率。
读取渠道、日期出处、两个具体材料的使用依据草稿和仍待审定的问题见[MATERIAL_USE_REVIEW](MATERIAL_USE_REVIEW.md)。
JSON中的 `lastCheckedOn`、`reviewNotes` 与 `supportingReferences` 只描述文献核查；`rightsStatus`仍表示真实数据导入审查未完成。

## 2. 文件与发布边界

- 可继续补本文献索引、来源对应关系、人工审查意见和明确的待核问题；不承诺全国完整。
- 使用真实材料前先记录针对具体材料的许可或无需许可依据；按既有[许可政策](../../LICENSE_POLICY.md)处理。
- 本目录不进入 `sources/source-lock.json`，不被国家导入器消费，也不是 `sources/migrations/CN.json`。
- 未清权的官方响应和派生数据不进入公开Git、附件、数据ZIP、Demo或CDN。`sources/`会被数据打包器递归收录。
- 合成数据只在测试临时目录生成，禁止复制到数据或语言包。仅保存自写研究摘要不等于批准原材料再分发。

## 3. 当前任务状态与接续

| 工作项 | 状态 | 下一步 |
|---|---|---|
| 四项属主决定及实施边界 | DONE | 已确认，不重复要求属主确认相同准备范围 |
| 原报告中现势、完整性和许可过强措辞 | DONE | 按实际证据升级，避免采集日期冒充生效日期 |
| 六条有限文献候选 | DONE / bounded | 四条主页面正文已读、两条仅检索索引；完整区间核查仍未完成 |
| CN迁移研究规则 | DONE | 见[迁移规则](../../CN_MIGRATION_RULES.md) |
| 新增合成跨快照用例 | IMPLEMENTED | 实际验证记录见下节 |
| 两项具体材料的使用依据研究卡 | DRAFT / pending | 草湖、重庆各限定材料及用途；不是数据使用结论 |
| 全国变更完整性、各事件生效日、代码与身份关系 | OPEN | 继续有限文献核查，不按名称猜配 |
| 真实CN来源使用依据与数据导入 | BLOCKED / not approved | 补具体依据并取得范围明确的实施决定 |
| A′全国采集、数据发布、生产成熟度提升、PR合并 | NOT AUTHORIZED | 分别决定，不从准备工作批准中推导 |

新会话先读本目录、决策报告和迁移规则，核对当前HEAD是否改变，再接续OPEN事项。
不重复已确认的平台接口调查；不重建旧identity registry、不覆盖历史release、不改变数据质量门。
本轮未进行对外咨询；如需联系官方，先准备问题，由属主另行决定发送。

## 4. 验证入口与范围

```sh
python3 -m unittest discover -s tests -p 'test_cn_migration_rehearsal.py' -v
python3 -m unittest discover -s tests -p 'test_semantic_audit.py' -v
python3 -m unittest discover -s tests -p 'test_geo_data.py' -v
python3 tool/update_rehearsal.py --selftest
git diff --check
```

新增测试复用原有CLDR合成fixture及审计API，不是CN实源适配器。原有改名、退役和身份重绑定用例直接复用。
`humanReviewVerified=false`保持诚实；迁移记录中的合成审查人并非真人审签。
通用source校验只检查固定来源和非空license等机器约束，不能证明许可证有效；这里没有通过修改生产门禁假装完成清权。

上一轮已执行记录（对应提交 `056ddc4f87d01478393fc71b4212a5fffe926095`；2026-11-19，Python 3.12.14）：

| 验证 | 实际结果 |
|---|---|
| 新增CN准备合成用例 | 6/6 PASS |
| 既有semantic audit回归 | 22/22 PASS |
| 既有geo_data边界回归 | 26/26 PASS |
| update_rehearsal自测 | 未申报删除按预期阻断；有逐条证据的退役按预期通过；总退出码0 |
| 文档及改动范围检查 | 58个相对链接可解析；仅6个预期文档/测试文件改变 |
| git diff --check | PASS |

共54项相关单元测试通过。未运行本地全量真实数据重建或Flutter测试，未把本轮结果宣传为完整CI或法律清权通过。
数据、来源锁、生产工具、schema、config和workflow均无改动；GitHub CI状态以对应提交的实际运行记录为准。

## 5. 本次文献接续与验证

接续起点为上述提交，仍只处理原六条候选。本次补足重庆原公告及转载正文，保存云南相关原文件的正式转引线索，并为草湖、重庆建立具体材料的待审记录。
重庆网站声明的限制性表述与新疆网站声明未见开放授权的事实分别记录，不推导通用的网站法律结论。详见[审查记录](MATERIAL_USE_REVIEW.md)。

本次只改五个文档/研究元信息文件，没有修改测试或执行工具；不重复上轮54项测试，也不把旧结果冒称新提交的完整测试结果。
本次实际检查结果：JSON解析及六条候选的未批准状态检查通过；31个相对Markdown链接（其中7个带锚点）及7个JSON文档引用全部可解析；改动范围恰为五个预期文档/研究元信息文件；`git diff --check`通过。
本轮没有对外发送咨询。下一步仍可补原通知或细化材料分析；真实数据导入、数据发布及PR合并仍须分别决定。

## English scope

This is a bounded bibliography, not a nationwide change ledger or a geography dataset.
Four candidate primary pages have been read; two remain official search-index evidence only.
An additional official cross-reference does not substitute for the referenced original document.
All effective dates are unknown and all automatic migration flags are false.
The owner authorized preparation only. Synthetic contract tests do not prove actual CN continuity,
licensing, source completeness or human review. Material-specific use reviews remain drafts.
