# IMBoy ECC 使用案例 / geo_regions

> 本文是可直接复制到 Codex 会话的 ECC 使用案例库。每个案例均可独立复制，以 `$skill-name` 开头。原 72 个工程案例各提供一个提示词；新增功能场景提供 A 新增功能、B 优化现有功能、C 测试现有功能三个独立提示词。
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
> **案例编号全局唯一**：ECC-001 至 ECC-121。四个仓库按职责分配，后端主仓提供统一索引。

## 本仓库范围

本文件包含 geo_regions 工程案例 6 个，以及地区数据场景复刻/功能迭代案例 2 个；合计 8 个（ECC-004、046–050、108–109）。原 prompts/ 中的 ZCODE 工作提示词保持不变。
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

> 本组面向客户业务场景复刻。每个场景提供三条独立提示词：A 新增功能；B 优化现有功能（重点适用于新模型复审旧 AI 代码）；C 测试现有功能。将提示词中的“客户”替换为具体客户、行业、角色和目标流程。



#### ECC-108 · 客户国家/地区/地址选择场景

**场景：** 地区选择和本地化

**A · 新增功能 · `product-capability` + `orch-add-feature` + `test-collaboration`**

```text
$product-capability $orch-add-feature $test-collaboration

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/业务流程：[填写客户行业、角色、业务目标、关键流程和特殊规则]。目标范围：[填写端、模块和子功能]。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、权威概念文档、接口契约、实际代码和测试。把实现状态明确标注为 CURRENT、TARGET、LOCKED、UNKNOWN 或 NOT_VERIFIED；不得把文档/API 存在等同于端到端交付。

任务类型：新增功能。

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

先判断现有能力能否通过配置或组合满足需求，只有确认存在真实能力缺口才新增代码。输出 capability contract：角色、用户旅程、状态机、权限与数据归属、接口、迁移兼容、失败恢复、观测和验收标准。需求不完整时列出阻塞问题并停在方案阶段；需求明确后按 TDD 先写失败测试再实现，遵守仓库架构和测试合同。先过计划门禁，不 commit/push/合并/部署。
```

**B · 优化现有功能 / 新模型复审旧 AI 代码 · `brownfield-retrospective` + `security-review` + `test-collaboration` + `verification-loop`**

```text
$brownfield-retrospective $security-review $test-collaboration $verification-loop

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/业务流程：[填写客户行业、角色、业务目标、关键流程和特殊规则]。目标范围：[填写端、模块和子功能]。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、权威概念文档、接口契约、实际代码和测试。把实现状态明确标注为 CURRENT、TARGET、LOCKED、UNKNOWN 或 NOT_VERIFIED；不得把文档/API 存在等同于端到端交付。

任务类型：优化现有功能，特别用于新一代 AI 模型独立复审旧 AI 模型生成的实现。

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

按 brownfield-retrospective 的 slice-first 方法，将范围限制在约 15 个文件或 2000 行以内。不要信任旧模型自评、代码注释或现有测试完整性；独立重建真实行为，追踪调用链、数据流、权限边界、失败路径、并发/竞态、资源生命周期和跨端契约。先建立改动前测试/性能/错误行为基线。

检查正确性、边界条件、异常处理、幂等/重试、安全、性能热点、重复/过度抽象、可维护性和跨端一致性。重点排查 AI 常见盲点：只改响应没改查询/持久化、只修主路径漏掉其他分支、字段/可空性漂移、异常吞掉、UI-only 权限、mock 通过但真实路径失败、测试与实现共享同一假设。

每个发现提供文件/行号、证据、影响、风险和最小修复方案。优先行为保持型优化；先新增/修正测试证明问题，再做最小改动。涉及公共 API/WS、数据库结构、E2EE、权限语义或用户可见行为变化时先请求确认。重点检查数据可追溯性、稳定 ID/pathIds、Manifest 原子切换、hash 校验、缓存和 SDK 公共契约。

先在会话中输出基线、差距登记和改进方案；不要自动创建 docs/retro 或重复审计文档。完成批准范围内的修改后运行定向测试、相关静态检查和 diff review，报告改动前后证据及未验证项。不 commit、不 push、不合并、不部署。
```

**C · 测试现有功能 · `test-collaboration` + `ai-regression-testing` + `verification-loop`**

```text
$test-collaboration $ai-regression-testing $verification-loop

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/业务流程：[填写客户行业、角色、业务目标、关键流程和特殊规则]。目标范围：[填写端、模块和子功能]。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、权威概念文档、接口契约、实际代码和测试。把实现状态明确标注为 CURRENT、TARGET、LOCKED、UNKNOWN 或 NOT_VERIFIED；不得把文档/API 存在等同于端到端交付。

任务类型：测试现有功能，独立验证旧 AI 实现。

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

当前功能场景：客户国家/地区/地址选择场景（地区选择和本地化）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为 IMBoy 客户复刻国家、省州、城市、区县等地区选择功能。评估 geo_regions SDK 当前稳定 API、生产数据成熟度、候选数据隔离、locale、离线资源、远程加载、身份稳定性和 Flutter 宿主 Adapter。明确研究 seed、candidate 和生产数据边界，不得承诺尚未生产化的数据覆盖。

实施已批准的 geo_regions/IMBoy 集成差异。先读取 CONSUMER_CONTRACT、IMBOY_INTEGRATION、SDK_INTEGRATION 和当前 SDK 代码，验证真实导出 API、revision 与 storage adapter。遵守 stable ID/pathIds、SHA-256、locale quality、缓存隔离和 Flutter 平台差异。补充宿主测试，不将候选数据混入生产层。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

先不要修改业务实现。盘点单元、集成、契约、E2E、平台/设备测试和 CI 门禁，建立“需求/不变量 → 测试资产或 TEST-ID → 命令 → 证据”矩阵。覆盖正常路径、权限拒绝、非法输入、边界值、重复请求、并发、超时、故障恢复、旧数据兼容和跨端行为。

针对 AI 生成代码特别检查 mock/sandbox 与真实路径不一致、数据库查询/写入字段遗漏、序列化遗漏、仅测 happy path、异常吞掉、重试重复副作用和测试 fixture 迎合实现。只新增有区分力的测试，不复制重复用例、不降低阈值、不扩大 skip。使用 tool/import_data.py、tool/geo_data.py、tool/check_readiness.py、semantic audit、manifest 检查及 tests 现有入口。

逐项报告 PASS/FAIL/BLOCKED/NOT RUN、真实命令、退出码、数量和证据位置。发现缺陷先提供复现与最小修复建议；未经授权不修改业务代码。不得把未执行或环境缺失标记为 PASS。
```


#### ECC-109 · 客户国际化地区数据扩展

**场景：** 多国家多语言客户数据接入

**A · 新增功能 · `product-capability` + `orch-add-feature` + `test-collaboration`**

```text
$product-capability $orch-add-feature $test-collaboration

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/业务流程：[填写客户行业、角色、业务目标、关键流程和特殊规则]。目标范围：[填写端、模块和子功能]。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、权威概念文档、接口契约、实际代码和测试。把实现状态明确标注为 CURRENT、TARGET、LOCKED、UNKNOWN 或 NOT_VERIFIED；不得把文档/API 存在等同于端到端交付。

任务类型：新增功能。

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

先判断现有能力能否通过配置或组合满足需求，只有确认存在真实能力缺口才新增代码。输出 capability contract：角色、用户旅程、状态机、权限与数据归属、接口、迁移兼容、失败恢复、观测和验收标准。需求不完整时列出阻塞问题并停在方案阶段；需求明确后按 TDD 先写失败测试再实现，遵守仓库架构和测试合同。先过计划门禁，不 commit/push/合并/部署。
```

**B · 优化现有功能 / 新模型复审旧 AI 代码 · `brownfield-retrospective` + `security-review` + `test-collaboration` + `verification-loop`**

```text
$brownfield-retrospective $security-review $test-collaboration $verification-loop

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/业务流程：[填写客户行业、角色、业务目标、关键流程和特殊规则]。目标范围：[填写端、模块和子功能]。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、权威概念文档、接口契约、实际代码和测试。把实现状态明确标注为 CURRENT、TARGET、LOCKED、UNKNOWN 或 NOT_VERIFIED；不得把文档/API 存在等同于端到端交付。

任务类型：优化现有功能，特别用于新一代 AI 模型独立复审旧 AI 模型生成的实现。

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

按 brownfield-retrospective 的 slice-first 方法，将范围限制在约 15 个文件或 2000 行以内。不要信任旧模型自评、代码注释或现有测试完整性；独立重建真实行为，追踪调用链、数据流、权限边界、失败路径、并发/竞态、资源生命周期和跨端契约。先建立改动前测试/性能/错误行为基线。

检查正确性、边界条件、异常处理、幂等/重试、安全、性能热点、重复/过度抽象、可维护性和跨端一致性。重点排查 AI 常见盲点：只改响应没改查询/持久化、只修主路径漏掉其他分支、字段/可空性漂移、异常吞掉、UI-only 权限、mock 通过但真实路径失败、测试与实现共享同一假设。

每个发现提供文件/行号、证据、影响、风险和最小修复方案。优先行为保持型优化；先新增/修正测试证明问题，再做最小改动。涉及公共 API/WS、数据库结构、E2EE、权限语义或用户可见行为变化时先请求确认。重点检查数据可追溯性、稳定 ID/pathIds、Manifest 原子切换、hash 校验、缓存和 SDK 公共契约。

先在会话中输出基线、差距登记和改进方案；不要自动创建 docs/retro 或重复审计文档。完成批准范围内的修改后运行定向测试、相关静态检查和 diff review，报告改动前后证据及未验证项。不 commit、不 push、不合并、不部署。
```

**C · 测试现有功能 · `test-collaboration` + `ai-regression-testing` + `verification-loop`**

```text
$test-collaboration $ai-regression-testing $verification-loop

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/业务流程：[填写客户行业、角色、业务目标、关键流程和特殊规则]。目标范围：[填写端、模块和子功能]。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、权威概念文档、接口契约、实际代码和测试。把实现状态明确标注为 CURRENT、TARGET、LOCKED、UNKNOWN 或 NOT_VERIFIED；不得把文档/API 存在等同于端到端交付。

任务类型：测试现有功能，独立验证旧 AI 实现。

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

当前功能场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。目标客户/目标业务流程：[请填写客户行业、用户角色、业务目标、关键流程、特殊规则和优先级]。目标范围：[请填写本次要覆盖的端/模块/子功能]。

先读取当前仓库规则和权威文档，再核对实际代码与测试。不得把设计、文档或 API 存在等同于功能已交付；明确标注 CURRENT、TARGET、LOCKED、UNKNOWN 和 NOT_VERIFIED。

任务类型：新增功能。

为客户评估新增国家、语言或行政区层级的地区数据需求。检查来源许可、source-lock、版本日期、数据完整性、机器候选标签、人工审校状态和 production readiness。输出国家覆盖、语言覆盖、许可风险和上线阻塞，不虚构数据来源。

实施已批准的地区数据接入。遵守来源固定、许可分层、稳定 ID、Schema/Manifest/Revision、SHA-256 和 maturity tripwire。先在独立候选层导入和验证，运行 import --check、schema、semantic audit、manifest 和 readiness；未经人工审校不得提升为生产数据。

请先判断需求能否由现有能力配置/组合完成；只有确认存在真实能力缺口才新增代码。输出 capability contract：参与角色、用户旅程、状态机、权限/数据边界、API/WS/客户端界面、迁移兼容、观测和验收标准。客户输入不完整或涉及产品决策时，列出阻塞问题并停在方案阶段。输入充分且任务明确时，按 TDD 先写失败测试再实现，遵循项目已有架构和测试命令。遵守 Gate：计划/契约先审阅，实施后完整验证；不 commit、不 push、不合并、不部署。

先不要修改业务实现。盘点单元、集成、契约、E2E、平台/设备测试和 CI 门禁，建立“需求/不变量 → 测试资产或 TEST-ID → 命令 → 证据”矩阵。覆盖正常路径、权限拒绝、非法输入、边界值、重复请求、并发、超时、故障恢复、旧数据兼容和跨端行为。

针对 AI 生成代码特别检查 mock/sandbox 与真实路径不一致、数据库查询/写入字段遗漏、序列化遗漏、仅测 happy path、异常吞掉、重试重复副作用和测试 fixture 迎合实现。只新增有区分力的测试，不复制重复用例、不降低阈值、不扩大 skip。使用 tool/import_data.py、tool/geo_data.py、tool/check_readiness.py、semantic audit、manifest 检查及 tests 现有入口。

逐项报告 PASS/FAIL/BLOCKED/NOT RUN、真实命令、退出码、数量和证据位置。发现缺陷先提供复现与最小修复建议；未经授权不修改业务代码。不得把未执行或环境缺失标记为 PASS。
```


## 维护说明

- 本文只维护本仓库职责范围内的提示词；跨仓案例的统一索引位于 [imboy 后端主仓 docs/prompts/README.md](https://github.com/imboy-pub/imboy/blob/main/docs/prompts/README.md)。
- 修改案例时保持 ECC 编号不变；新增案例先在后端主仓索引登记编号和归属，避免重复。
- Skill 名称必须与 ECC `skills/<name>/SKILL.md` 中的目录名一致；ECC 升级后应重新核对可用性。
- 提示词是任务入口，不是执行结果或质量证明；验收以真实代码、测试和 CI 证据为准。
