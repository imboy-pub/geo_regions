# IMBoy ECC 使用案例 / geo_regions

> 本文是可直接复制到 Codex 会话的 ECC 使用案例库。每个案例均为独立提示词，以 `$skill-name` 开头。
>
> **使用约定**
> - 在已安装 ECC 的 Codex 会话中，复制单个案例的完整代码块执行。
> - 先确认当前工作目录和目标仓库；跨仓案例需明确各仓库实际 checkout 路径。
> - 仓库内 AGENTS.md、CLAUDE.md、项目架构文档、测试执行合同和安全规则优先于 ECC 通用建议。
> - 提示词中的“只读”案例不得修改文件；实施案例仅允许修改当前任务必需文件。
> - 默认不得 commit、push、合并、部署、执行生产写入或接触真实用户数据；需要时另行授权。
> - 不得通过删除/弱化测试、扩大 skip、关闭门禁或伪造证据制造 PASS。
> - 报告实际执行的命令、退出码、结果、未执行项和证据位置；未执行不得声称通过。
>
> **案例编号全局唯一**：ECC-001 至 ECC-072。四个仓库按职责分配，后端主仓提供统一索引。

## 本仓库范围

本文件包含 geo_regions 架构理解、数据治理和 Flutter 接入案例，共 6 个（ECC-004、046–050）。原 prompts/ 中的 ZCODE 工作提示词保持不变。

## 案例清单

### 项目理解与架构分析

#### ECC-004 · geo_regions SDK 架构梳理

**Skills：** `codebase-onboarding` · `contract-first`

```text
$codebase-onboarding $contract-first

只读分析 geo_regions。梳理数据导入、Schema、Manifest、Revision、SHA-256、Repository、Cache、Bundled、Remote、地区索引、名称解析和 Selection 完整链路。区分已经实现、尚未实现和仅有设计的功能。
```

### geo_regions 数据与 SDK

#### ECC-046 · 新增国家和语言数据

**Skills：** `change-impact` · `test-collaboration`

```text
$change-impact $test-collaboration

为 geo_regions 新增指定国家或语言制定实施方案。检查来源许可、source-lock、导入工具、数据质量、Schema、Manifest、locale revision、缺失翻译和 CI scope。严格区分 research-seed、candidate 和 production 数据，不得将机器生成内容直接认定为正式数据。
```

#### ECC-047 · Manifest 完整性

**Skills：** `security-review` · `test-collaboration`

```text
$security-review $test-collaboration

审计 Manifest、Revision、SHA-256 和资源加载链路。验证重复键、路径穿越、符号链接、资源长度不符、哈希错误、缓存污染、旧版本资源混用和并发请求。确保远程资源在 JSON 解码之前通过完整性验证。
```

#### ECC-048 · 数据来源和许可证审计

**Skills：** `change-impact` · `docs-governance`

```text
$change-impact $docs-governance

审计所有数据来源、来源快照、commit、URL、SHA-256、许可和生成工具。检查正式层与候选层的来源隔离、AI 生成数据标识和人工审校证据。找出无法证明来源或许可的资源。
```

#### ECC-049 · 生产成熟度审查

**Skills：** `production-audit` · `test-collaboration`

```text
$production-audit $test-collaboration

审计 geo_regions 是否达到生产 SDK 准入要求。检查 productionSdkExpected、readiness、生产数据质量、SDK 测试、远程完整性验证、缓存、错误分类和发布产物。明确阻塞项，不得把 Phase 1 或 Demo 完成等同于生产就绪。
```

#### ECC-050 · 接入 Flutter 方案

**Skills：** `contract-first` · `change-impact` · `parallel-execution-optimizer`

```text
$contract-first $change-impact $parallel-execution-optimizer

规划 geo_regions 接入 imboy-flutter。检查当前 SDK、IMBOY_INTEGRATION.md、CONSUMER_CONTRACT.md 和 Flutter 地区选择代码。明确 SDK、宿主 Adapter、账号缓存、结构化 Selection、旧字符串兼容、保存事务及测试责任。核对各仓当前 HEAD，不采用未经验证的历史 SHA/API。
```


## IMBoy 地区数据与国际化场景复刻（geo_regions）

> 本组面向客户业务场景复刻。每个场景提供两条独立提示词：A 用于需求/能力映射；B 用于在批准后实施客户差异。将提示词中的“客户”替换为具体客户、行业、角色和目标流程。

### ECC-108 · 客户国家/地区/地址选择场景

**场景：** 地区选择和本地化

**A · `product-lens` + `product-capability` · 客户场景映射**

```text
$product-lens $product-capability

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。
```

**B · `contract-first` + `orch-change-feature` + `tdd-workflow` · 客户差异实施**

```text
$contract-first $orch-change-feature $tdd-workflow

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。
```

### ECC-109 · 客户国际化地区数据扩展

**场景：** 多国家多语言客户数据接入

**A · `product-lens` + `product-capability` · 客户场景映射**

```text
$product-lens $product-capability

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。
```

**B · `contract-first` + `orch-add-feature` + `test-collaboration` · 客户差异实施**

```text
$contract-first $orch-add-feature $test-collaboration

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。
```

## 维护说明

- 本文只维护本仓库职责范围内的提示词；跨仓案例的统一索引位于 [imboy 后端主仓 docs/prompts/README.md](https://github.com/imboy-pub/imboy/blob/main/docs/prompts/README.md)。
- 修改案例时保持 ECC 编号不变；新增案例先在后端主仓索引登记编号和归属，避免重复。
- Skill 名称必须与 ECC `skills/<name>/SKILL.md` 中的目录名一致；ECC 升级后应重新核对可用性。
- 提示词是任务入口，不是执行结果或质量证明；验收以真实代码、测试和 CI 证据为准。
