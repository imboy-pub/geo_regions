# 数据校验、新语言和新国家规则 / Data validation and extension rules

执行命令说明见 [TOOLING.md](TOOLING.md)，并行分工见 [DATA_WORKPACKAGES.md](DATA_WORKPACKAGES.md)。本文件规定质量门槛，不把脚本通过等同人工审校通过。

## 1. 数据进入仓库的四个状态 / Four maturity states

| State | Meaning / 含义 | Allowed action / 允许行为 |
|---|---|---|
| draft | 缺来源、空翻译或待填字段 / Incomplete provenance or content | 只留staging；拒绝加入发布数据 |
| research-seed | 可重建、来源明确，范围/现势/译名仍需复核 / Reproducible sourced seed | 开发、测试、明确标识的演示与种子草稿release |
| reviewed | 有覆盖范围和复核记录 / Reviewed against a declared scope | 进入生产候选验证，仍需产品与平台验收 |
| production | 已通过产品声明范围的发布检查 / Accepted release scope | 可由维护者按授权发布 |

修改status字符串不能创造review证据。地理真实性、主权口径、译名正确性和时效性需要来源与审核记录；脚本只检查可执行约束。生产SDK解析质量还需逐名称allowlist，metadata不能绕过它。

Changing a status does not establish review. Source provenance, territorial profile, current validity and language accuracy require evidence. Scripts validate machine-checkable constraints, not human approval.

## 2. 必须检查的规则 / Required rules

| Rule | Reject or report / 结果 |
|---|---|
| Source missing license, commit/version, hash, date or transformation | 拒绝正式导入 / Reject promotion |
| Duplicate JSON keys, bad UTF-8, non-finite values, unnormalized text | 拒绝 / Reject |
| Duplicate IDs, orphan/cross-country parent, cycle, wrong root | 拒绝 / Reject |
| Country code passes regex but not reviewed catalog policy | 只生成draft，不能声称ISO注册验证已通过 / Draft only |
| Translation key outside the compatible structure | 拒绝 / Reject |
| Name without per-ID quality or default name without known quality | 种子明确未知；生产拒绝 / Explicit unknown; reject production |
| Changed quality with unchanged locale revision | 拒绝 / Reject |
| Changed hierarchy with stale compatibility or selection path | 拒绝旧兼容声明 / Reject stale compatibility |
| Partial/unknown children presented as a confirmed administrative leaf | 拒绝产品验收 / Reject product acceptance |
| Runtime fallback copied into source translation files | 拒绝假覆盖 / Reject inflated coverage |
| Hash/length mismatch, unsafe path or symlink escape | 拒绝且不替换有效输出 / Reject and preserve valid output |
| Removed or reparented node | 输出迁移影响，不自动接受 / Require migration review |

相同拼写不必然代表漏翻；很多地名跨语言相同。质量判定依据来源与语言规则，而不是简单比较英文字符串。Conversely, a different spelling does not prove a correct translation.

## 3. 日常校验 / Routine checks

在项目根运行 / From the repository root:

```bash
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema --report build/reports/data-validation.json
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
```

`--check`只比较和报告；不会更新远端main或替换源数据。完整Schema需要开发依赖 `python3 -m pip install -r tool/requirements-ci.txt`，推荐在项目虚拟环境安装。

The checker is offline and deterministic. Schema validation needs the development-only dependency file. It introduces no Flutter runtime dependency.

```bash
python3 tool/geo_data.py validate --schema --production
```

**本次seed在这条命令下预期失败。** 失败表示未达到生产成熟度，不是完整性工具坏了。不得删除seed标签、放宽质量白名单或给未知名称硬填approved来刷绿。

This seed intentionally fails the production gate. Do not relabel or weaken the gate to manufacture a passing release.

## 4. 新增语言 / Add a locale

```bash
python3 tool/geo_data.py add-locale --locale es --out staging/locale-es --dry-run
python3 tool/geo_data.py add-locale --locale es --out staging/locale-es
```

1. 明确BCP47标签、脚本、方向、宿主别名；西班牙语仅为例子，不能自动替换用户当前十语目标。
2. 为现有全部国家生成空语言draft和小型国家名称draft。脚本确认结构字节未改变，不把英文复制为译文。
3. 获取许可明确的同语言源，按稳定ID或可审计的标准code关联；不凭名称模糊猜配。记录source quality和缺失数。
4. 机器建议、音译、简繁转换放候选文件，写明生成方法和未审状态；有证据的审核才能提升质量等级。
5. 改生成器/源锁与语言policy；不手改生成JSON后遗留不可重建状态。若新源需额外格式转换，其代码同样要提交。
6. 合并前比较全部地区结构SHA-256：必须不变。验证所有ID、revision、国家名称覆盖、RTL/字体与回退。
7. 更新manifest和覆盖报告；发布新的语言资源，不要求消费者升级核心库。

Agree the locale; scaffold empty drafts; obtain and map sourced names; retain candidates as candidates; update generator/provenance/policy; prove unchanged structures and valid fallback; then generate the release. The script does not perform translation or claim linguistic approval.

## 5. 新增国家 / Add a country

```bash
python3 tool/geo_data.py add-country --country ES --out staging/country-ES --dry-run
python3 tool/geo_data.py add-country --country ES --out staging/country-ES
```

先定义国家/地区catalog口径与可交付层级，再决定source。必须有可追溯源、明确license和稳定代码。生成一个root，按可信父链建立节点；没有下级数据就写unknown，不补出“看上去完整”的省市县。现有国家文件原则上保持不变；源编码命名空间不同不能碰巧同名就合并。

Define the catalog profile and supported depth before importing. Require a stable, licensed source. Create exactly one root and trustworthy parent links. Preserve unknown coverage instead of manufacturing a three-level hierarchy. Keep unrelated countries unchanged.

扩展catalog、十语国家名称、目标语言包、policy、源锁及生成器；未翻译的地区名称留缺失。新增国家使catalog revision变化，对应十语国家名包必须重新校验兼容；这不要求已有地区结构改变。

Adding a country changes the catalog and its compatible catalog-name packs, not necessarily existing structures. Missing regional names remain missing.

## 6. 更新已有源 / Update an existing source

```bash
python3 tool/geo_data.py diff --old previous/CN.json --new staging/CN.json
python3 tool/geo_data.py diff --old previous/CN.json --new staging/CN.json --require-no-removals
```

新增、删除、改父、改名分别报告。纯改名保留ID；编码变化需要明确identity crosswalk。撤并/一对多/歧义映射不得自动选择首项。旧release不覆盖；保存旧selection时用dataRevision解释，不依赖最新树强行通过。

Report additions, removals, parent changes and renames separately. Retain identity on a pure rename. Preserve old releases and resolve old selections against their recorded revision. Ambiguous migrations require reselection.

标准行政编码也可能被上游重用，因此“使用ISO/code生成首版ID”不等于以后永远无需身份治理。更新时若同一code代表不同实体，必须保留旧实体退役记录、给新实体分配新稳定ID，不能把它当普通改名。CLDR自身也记录过行政编码重用案例，见 [UTS35 subdivision identifiers](https://www.unicode.org/reports/tr35/)。

Standard codes can be reused. An initial code-derived ID does not remove the need for identity governance. A reused code for a different entity requires retirement/migration records and a new stable identity, not a silent rename.

## 7. 并行与完成定义 / Parallel ownership and done criteria

国家worker只写自己的结构staging；语言worker只写自己的locale staging。同一country结构更新期间，语言worker以冻结的structure revision作输入，集成时重新验证，不允许自己更新公共manifest。协调者串行合并source-lock/policy/schema/importer/manifest。

交付必须包含：变更摘要、不可变来源、license、输入/输出hash、命令exit code、覆盖/质量统计、差异、未解问题、迁移影响。没有找到来源的任务标BLOCKED，继续独立任务，不制造数据。完整国家或语言支持由产品声明和审核证据定义，不由文件数量定义。

Workers own isolated staging outputs; one coordinator merges shared registries and manifests. Every work package supplies provenance, hashes, results, coverage/quality, diffs and unresolved issues. Missing evidence is a blocker, never permission to invent content.
