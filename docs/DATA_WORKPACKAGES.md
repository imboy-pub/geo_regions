# 数据并行工作包 / Parallel data work packages

版本 / Version: 1.0 · 日期 / Date: 2026-11-13 · 关联任务 / Parent task: **P1-03**

本文件把当前十国/十语种子的真实缺口、新增国家和新增语言拆成可独立执行、可验收、可续跑的工作包。完整范围与数字以 [DATA_COVERAGE.md](DATA_COVERAGE.md) 和 `sources/coverage-report.json` 为准。它不把研究种子升级为已完成的生产数据库。

This document divides existing gaps and future country/language additions into resumable, testable work packages. The coverage report is authoritative. A plan or scaffold does not constitute production-ready data.

## 1. 调度和文件所有权 / Scheduling and ownership

**默认两个工作者，一名协调者；最多两个数据任务同时写入。** 沿用现有模型/推理设置。已有 IMBoy 长任务繁忙时降到一个工作者，不通过自动提升模型或增加并行度解决堵塞。

**Default: two workers and one coordinator; at most two data work packages write concurrently.** Keep existing model/reasoning settings. Reduce to one worker when other IMBoy work is resource constrained.

| Role / 角色 | May write / 可写 | Must not write / 禁止直接写 |
|---|---|---|
| Worker A | `.data_staging/<package-id>/` 中分配的国家/语言候选、局部报告、拟议补丁 | 生产 `data/`、全局 source-lock、manifest、policy、schema、共享 importer |
| Worker B | 另一个工作包独立的 staging；不触碰 A 的 staging | 同左；不通过共享 CSV/JSON 隐藏冲突 |
| Coordinator | 审查后串行合并 source-lock、导入器、policy、catalog、正式 data、manifest和报告 | 不覆盖用户已有改动，不把未审核候选无条件提为正式 |

每个工作包在 `.plans/geo-regions-v1/evidence/P1-03/<package-id>/` 保留输入结构 revision、源 commit/hash、分支或 worktree、已执行命令、退出码、报告和下一步。状态只有 pending / in_progress / blocked / completed；证据不完整不能记 completed。重新启动会话按固定 package ID 恢复，不重建空目录覆盖上次进度。

Retain the baseline structure revision, source hashes, branch/worktree, commands, exit codes, reports and next action for each package. Resume by persistent package ID; never erase prior progress to manufacture a fresh run.

**结构和语言并行的约束：** 语言工作者针对明确冻结的结构 revision 翻译。若另一工作者更新该国结构，协调者先审查 ID/父子差异，再迁移语言候选和重算兼容版本。不能仅把 `compatibleStructureRevision` 换成新字符串就声称兼容。

**Structure/name concurrency:** Translation work targets a frozen structure revision. After structural changes, review changed identities and parents before rebasing names. Blindly replacing the compatibility revision is not validation.

## 2. 本轮缺口优先级 / Priorities grounded in the delivered seed

| Package ID | Priority | Scope / 范围 | Inputs and ownership / 输入与所有权 | Acceptance / 验收 |
|---|---|---|---|---|
| DP-00 | P0, first | 固定现有36源、4143节点基线；记录支持范围 / Freeze the current baseline | Coordinator; lock, coverage and validation outputs | 离线重建一致、source hash一致、完整验收清单；其他工作包以此为基线 |
| DP-01-ZH-HANT | P0 | 优先补繁中；当前仅13/4143显式地区名 / Traditional Chinese gaps | Worker A; only zh-Hant candidate packs and provenance | 保留真实语种/来源/质量；原结构hash零变化；先覆盖IMBoy确认的常用路径，再按国家扩大；不把简体复制为繁体 |
| DP-02-CN-I18N | P0 | CN非简体深层名称：en、ja、ko、ru、de、fr、it、ar；zh-Hant由DP-01单写 / CN lower-level names in other locales | Worker B; disjoint country–locale files, frozen CN revision | 每个新增名称有源或可审查贡献证据；同名节点按ID区分；不承诺一次完成全部区县八语 |
| DP-03-CN-CURRENT | P0 | 复核2023-06-30以后CN撤并、更名和层级变化 / Review changes since the historical snapshot | Worker A after DP-01's current slice; structural candidates only | 官方变更证据、数据许可与可复现转换；迁移映射明确；无法证实时保留历史标记，不更新日期冒充现势 |
| DP-04-PROFILES | P0 | HK/MO/TW独立catalog/profile与CN引用边界 / Additional configurable profiles | Worker B after DP-02's current slice; independent staging | 确定每条目的来源范围、根ID、层级、语言、现势日期及重复显示策略；不静默嵌入CN，也不把“地区”分类当主权声明 |
| DP-05-JP-KR | P1 | JP市区町村、KR市郡区 / Municipal expansion | Country-specific structural candidates | 固定可再分发来源，父级唯一，撤并差异和现势日期；不能凭城市列表猜行政树 |
| DP-06-US-GB | P1 | US县/城市与GB当前源口径核对 / Deeper scope and currency | Separate country candidates | 处理非严格树关系、独立城市与县的关系、代码重用；保留真实profile而不硬套三级 |
| DP-07-DE-FR-IT | P1 | DE市镇、FR communes、IT comuni / Municipal expansion | One country per slice | 来源层级、跨级节点、现势日期、许可和迁移表；避免不同年份相互拼接 |
| DP-08-RU-SA | P1 | RU/SA更深行政层级与源范围复核 / Deeper divisions and source profiles | Separate country candidates | 声明采用的地区口径；不混合不兼容立场/年份；同一ID不在不同来源间偷换实体 |
| DP-09-LOCALE-REVIEW | P1 | 现有CLDR provisional译名复核 / Review existing provisional names | Locale–country slices outside DP-01/02 ownership | 保留原始CLDR质量元数据；新增独立项目审核记录，不能伪改上游draft为approved |
| DP-10-NEW-COUNTRY | P2, repeatable | 在已支持十国之外新增国家 / New-country template | New ISO catalog code and independent staging | 来源、许可、结构、默认名称质量、十语国名、缺口报告、compatibility/manifest检查全部明确 |
| DP-11-NEW-LOCALE | P2, repeatable | 增加es等新语言 / New-locale template | New BCP47 locale, frozen structure set | catalog名称全覆盖；地区名称可稀疏但不造假；原结构hash与revision完全不变 |
| DP-12-INTEGRATE | Per batch | 合并、复现、差异、支持范围和release资料 / Integrate each accepted batch | Coordinator only | 所有相关gate通过，剩余BLOCKED公开，不把部分数据标全球完整 |

“P0”表示优先处理的风险或缺口，不承诺全部工作能在一次会话内完成。可先交付一个范围明确的可审阅批次；只有该批次满足全部证据要求才标 completed。

P0 identifies priority, not a promise to source and review every name in one session. Complete bounded, explicit batches and record the remaining scope separately.

## 3. 两工作者的建议执行轮次 / Suggested two-worker rounds

| Round | Worker A | Worker B | Coordinator gate |
|---|---|---|---|
| 0 | Read-only source/profile inventory | Read-only linguistic coverage inventory | DP-00 baseline |
| 1 | DP-01-ZH-HANT: catalog + agreed IMBoy paths | DP-02-CN-I18N: one locale and agreed CN paths | Check structure hashes unchanged; accept a bounded language batch |
| 2 | DP-03-CN-CURRENT | DP-04-PROFILES | Review identities, profile boundaries and migration; rebase names if needed |
| 3 | One of DP-05/06 country slices | One of DP-07/08 country slices | Independent sources; serial global manifest integration |
| 4 | DP-09 language review slice | DP-10 country or DP-11 new-locale slice | Publishable coverage and regression evidence |

每轮只启动前置已满足且没有同文件所有权冲突的工作。遇源不可用、账号缺失、许可不清或无人能完成语言复核时，记录该子项具体 blocker，继续其他独立子项。不得通过改低验收条件、伪造下载或宣布“来源无问题”来解除阻塞。

Start only packages with satisfied prerequisites and disjoint ownership. Source availability, access, license clarity and reviewer availability are not guaranteed. Record a precise blocker and continue independent work; do not weaken acceptance to manufacture a pass.

## 4. 每个工作包必须交付什么 / Required package contents

在自己的 staging 中提交以下内容，再由协调者审查合并：

| Artifact / 产物 | Required information / 必需内容 |
|---|---|
| `SOURCE_REVIEW.md` | 仓库/官方源链接、固定commit或不可变版本、查询日期、数据有效日期、实际许可与署名义务；候选源不等于已验证源 |
| `source-lock.proposed.json` | 新原始文件相对路径、精确URL、SHA-256、字节数和license；不是直接覆盖全局source-lock |
| Raw snapshots | 仅可再分发且已实际获取的字节；不能把错误页当数据文件 |
| Candidate JSON | 与协议一致的国家/语言候选；明确draft/candidate/research-seed状态和覆盖范围 |
| `TRANSFORM.md` | 输入→输出规则、异常、ID连续性与何处保留原始值；提供可重跑的转换补丁 |
| `REVIEW.md` | 名称与事实核验方法、审校者/证据（确有才填）、不确定项；机器输出不得自称人工审核 |
| `DIFF.json` | 增删、改名、改父、代码重用、名称quality变化；需要迁移的项必须突出 |
| `CHECKS.md` | 实际命令、退出码、测试输入、报告路径、PASS/FAIL/SKIP/BLOCKED；没执行的写未执行 |
| `NEXT.md` | 下次从哪里继续，哪些输入已固定，哪个文件由谁拥有 |

For human contributions, retain author/source permission and review evidence without exposing unnecessary personal data. A claimed reviewer name without an actual review is not evidence. Public-domain or permissive source claims must be grounded in the source's terms.

## 5. 新增国家流程 / Adding a country

下面以未包含的 CA 为脚手架示例；这条命令只生成待填草案，并不获得加拿大数据，也不证明已获得相关数据许可。

The CA example generates a draft only. It neither downloads Canadian data nor establishes permission to redistribute it.

```sh
python3 tool/geo_data.py add-country --country CA --out .data_staging/DP-10-CA --dry-run
python3 tool/geo_data.py add-country --country CA --out .data_staging/DP-10-CA
```

1. 核对该代码与声明profile；明确是国家/地区清单项而非业务自造国家。 / Verify the catalog identifier and declared source profile.
2. 先取得明确可再分发、可固定版本的真实源；缺源记BLOCKED，不按常识生成行政区。 / Obtain an actual licensed immutable source; do not invent geography.
3. 用源稳定编码分配ID；名称、列表序号、下载日期不能作为身份。 / Use stable source identities, not labels, array positions or download dates.
4. 每节点明确parentId、kind、childrenStatus和nameLocale/nameQuality；默认名和语言包遵守相同质量规则。 / Preserve identity, hierarchy and default-name quality.
5. 新国家还需补入十语catalog名称；地区名称可以稀疏，但每条有来源和质量。 / Complete catalog names; report sparse region-name coverage honestly.
6. 协调者审查 catalog 变化，并更新所有 catalog pack 的兼容revision，不能只添加国家结构文件。 / Update catalog compatibility as an integrated change.
7. 通过重建、Schema、语义、跨文件、完整性、许可、差异和实际选择路径验收。 / Complete all batch gates before promotion.

已存在的 CN 等国家应使用“更新已有数据”流程，不调用新增脚手架覆盖。新源需要对应的可重建转换器；不能手改生产JSON后保留旧的 importer/source-lock 宣称可复现。

Existing countries require an explicit update, not an overwriting scaffold. New sources require reviewed deterministic import logic. Hand-editing release JSON without updating provenance/reproduction is not acceptable.

## 6. 新增语言和补已有语言 / New locale versus an existing-locale update

以新语言 `es` 为脚手架示例：

```sh
python3 tool/geo_data.py add-locale --locale es --out .data_staging/DP-11-es --dry-run
python3 tool/geo_data.py add-locale --locale es --out .data_staging/DP-11-es
```

脚手架故意留下空名称，不能直接发布。已有 `zh-Hant` 的缺口采用 DP-01 更新流程；工具会拒绝重复新建已存在语言。

Scaffolds intentionally contain empty names and are not publishable. Existing zh-Hant uses the update workflow; the tool rejects duplicate creation.

- 先确定规范BCP47 tag、显式宿主aliases、方向与脚本；不得假定 `zh` 自动表示简繁通用。 / Fix the resource tag, aliases, direction and script explicitly.
- 只向当前结构存在的ID添加名称；同名不同节点不合并，名称包含空格不拆成路径。 / Add names by existing IDs; do not merge duplicates or split names into paths.
- 语言包兼容一个明确结构revision。国家名目录包兼容明确catalog revision。 / Keep explicit compatibility links.
- 国家名称需覆盖当前catalog；地区名称可以缺失，由运行时真实回退补显示，不把回退写入源包计翻译。 / Catalog names cover the catalog; missing region names remain absent.
- 新语言前后所有 `regions/*.json` 完整文件hash和revision都必须不变。若改变，则拆分成独立结构任务。 / Structure files and revisions must remain byte-identical.
- `l-` revision包括names与translationQualityById；质量变更也必须更新版本。 / Quality changes participate in locale revisions.

### 机器翻译、音译和简繁转换 / Machine translation, transliteration and script conversion

这些工具可以产生**候选**，但不是经过核验的来源名称。只写staging候选文件，标记 `candidate` 或 `machine-translated-candidate`，记录源名、源语言、目标语言、方法/工具版本、生成日期和待核验项。未审校候选不得进入正式允许列表，不能把质量改成 `approved-in-source`、`source-native` 或虚构的人工reviewed来通过门禁。

These methods may create candidates only. Retain source text/language, target locale, method/tool version, generation date and open review items. Candidates stay outside production until their policy and review evidence are explicitly accepted. Do not relabel machine output as upstream-approved, source-native or human-reviewed.

保留上游CLDR原draft状态。若项目后来审核了某条翻译，另建项目review证据/覆盖层，不能修改原始XML或声称上游已经批准。来源字节必须与source-lock保持一致。

Preserve upstream draft attributes and original bytes. A later project review requires separate evidence or an override layer; it does not retroactively change upstream approval.

## 7. 协调者集成和验收 / Coordinator integration gates

以下命令对**合并到完整候选仓库后的数据**执行，不直接对缺失catalog/manifest的单个draft目录执行。协调者在隔离分支或已登记的任务worktree中集成，保护其他任务与用户改动。

Run these against a complete integrated candidate checkout, not an isolated incomplete scaffold. Preserve all unrelated worktrees and changes.

```sh
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema --no-manifest
python3 tool/geo_data.py manifest
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py validate --schema --report .plans/geo-regions-v1/evidence/P1-03/data-validation.json
python3 -m unittest discover -s tests -v
```

新增源或扩展批次需要先把可复现转换逻辑、锁定源和生成结果一并集成，才可期待 `import_data.py --check`通过。Schema依赖按 `tool/requirements-ci.txt`安装。不能删掉该检查来放行无法重建的数据。

When adding sources, integrate the importer changes, source lock and generated output together before expecting the reproduction check to pass. Install schema dependencies from `tool/requirements-ci.txt`; do not remove the gate to accept unreproducible data.

结构更新还需比较前后文件，例如：

```sh
python3 tool/geo_data.py diff --old .data_staging/baseline/CN.json --new data/regions/CN.json
```

`--require-no-removals`可用于本应没有删除/改父的批次；确有行政调整时，不是绕过报错，而是提供迁移证据并检查旧selection。语言批次另比完整结构hash，证明没有碰结构。

Use `--require-no-removals` when removals/reparenting should be absent. Genuine administrative changes require reviewed migration evidence and legacy-selection tests, not suppression of the difference.

| Gate | Pass means / 通过含义 | Does not prove / 不能证明 |
|---|---|---|
| Source integrity | 字节、固定版本、hash匹配 | 来源地理事实一定正确 |
| Schema + semantics | 格式、ID、父链、版本与跨文件引用合法 | 所有行政层级已收齐 |
| Language quality | 每条质量可追溯，默认策略无候选绕过 | 全部语言经母语人工审核 |
| Reproduction | 同一源和转换得到同一产物 | 上游一定仍然现势 |
| Coverage | 宣称范围与数字一致 | 缺失等于现实不存在 |
| License | 适用许可、署名和来源被审查并保留 | 根目录BSD可覆盖任意第三方数据 |
| Integration | 只合入接受的文件，manifest由一人生成 | 本地通过等于GitHub CI已经运行 |

`python3 tool/geo_data.py validate --schema --production`是更严格的发布检查；当前research-seed应失败，不能为了绿灯把它改名为production。未来生产profile也仍需地理/语言人工证据，工具不验证人类审核事实。

The strict production command is expected to reject this research seed. A renamed status is not a promotion. Geographic and linguistic evidence remains required beyond mechanical checks.

## 8. 工作包提示词模板 / Worker prompt template

```text
你负责 geo_regions 的 <PACKAGE_ID>。先读 PRD、PROTOCOL、DATA_SOURCES、DATA_COVERAGE
和 DATA_WORKPACKAGES，再读取本工作包已有状态与staging。

基线结构revision：<REVISION>；源锁：<SOURCE_LOCK_HASH>。
允许写入：.data_staging/<PACKAGE_ID>/。
只读：生产data、sources、schemas、policy和全局manifest。
不要改其他工作者文件，不要提高并发，不要清理任何已有worktree。

完成一个范围明确的候选批次：<COUNTRY/LOCALE/IDS OR SOURCE_CHANGE>。
必须给出固定来源、实际许可证、原始字节hash、确定性转换、ID/父级差异、
名称quality、coverage、运行命令和真实结果。机器翻译/转换只能标candidate。
无法取得来源、许可不明或缺人工语言审校时，记录具体BLOCKED并继续独立工作；
不得造源、伪造审核、猜测行政实体或把回退计为翻译。

最后提交SOURCE_REVIEW、拟议source-lock、候选文件、TRANSFORM、REVIEW、DIFF、
CHECKS和NEXT给协调者。只有协调者可以合并正式数据和重建全局manifest。
```

English equivalent:

```text
Own <PACKAGE_ID> for geo_regions. Read PRD, PROTOCOL, DATA_SOURCES,
DATA_COVERAGE and DATA_WORKPACKAGES, then resume its existing state/staging.

Pinned structure revision: <REVISION>; source-lock hash: <SOURCE_LOCK_HASH>.
Write only .data_staging/<PACKAGE_ID>/. Production data, sources, schemas,
policy and the shared manifest are read-only. Preserve all other workers'
files and worktrees; do not increase concurrency automatically.

Deliver one bounded candidate batch: <COUNTRY/LOCALE/IDS OR SOURCE_CHANGE>.
Provide immutable provenance, actual license, raw-byte hashes, deterministic
transformation, identity/parent differences, name quality, coverage and real
command results. Machine translation/conversion remains candidate-only.
Record precise BLOCKED items for unavailable sources, unclear rights or
missing linguistic review, and continue independent work. Never invent
sources, administrative entities or reviews, or count fallback as translation.

Hand the coordinator SOURCE_REVIEW, proposed source-lock, candidates,
TRANSFORM, REVIEW, DIFF, CHECKS and NEXT. Only the coordinator promotes data
and rebuilds the shared manifest.
```
