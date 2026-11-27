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

> **时间估算说明**：时间为单个案例的一次 A/B/C 模式执行预算，包含仓库阅读、代码分析、必要实施及相关验证；不是保证完成时间。A/B/C 只能选择一种执行。30 分钟及以上建议安排 ZCODE 闲时任务。遇到缺少设备、数据库、凭据、外部服务或需求决策时，应报告 BLOCKED/NOT RUN，不能为了符合预算而跳过验证。复杂度按当前仓库结构与案例提示词范围估算，实际会随工作树状态、测试环境和缺陷数量变化。
## 案例清单

### 项目理解与架构分析

#### ECC-004 · geo_regions SDK 架构梳理

**预计执行时间：20 分钟**（单次执行；包含代码阅读、定向实施/分析与相关验证）

**Skills：** `codebase-onboarding` · `contract-first`

```text
$codebase-onboarding $contract-first

只读分析 geo_regions。梳理数据导入、Schema、Manifest、Revision、SHA-256、Repository、Cache、Bundled、Remote、地区索引、名称解析和 Selection 完整链路。区分已经实现、尚未实现和仅有设计的功能。
```

### geo_regions 数据与 SDK

#### ECC-046 · 新增国家和语言数据

**预计执行时间：60 分钟**（单次执行；包含代码阅读、定向实施/分析与相关验证）

**Skills：** `change-impact` · `test-collaboration`

```text
$change-impact $test-collaboration

为 geo_regions 新增指定国家或语言制定实施方案。检查来源许可、source-lock、导入工具、数据质量、Schema、Manifest、locale revision、缺失翻译和 CI scope。严格区分 research-seed、candidate 和 production 数据，不得将机器生成内容直接认定为正式数据。
```

#### ECC-047 · Manifest 完整性

**预计执行时间：60 分钟**（单次执行；包含代码阅读、定向实施/分析与相关验证）

**Skills：** `security-review` · `test-collaboration`

```text
$security-review $test-collaboration

审计 Manifest、Revision、SHA-256 和资源加载链路。验证重复键、路径穿越、符号链接、资源长度不符、哈希错误、缓存污染、旧版本资源混用和并发请求。确保远程资源在 JSON 解码之前通过完整性验证。
```

#### ECC-048 · 数据来源和许可证审计

**预计执行时间：45 分钟**（单次执行；包含代码阅读、定向实施/分析与相关验证）

**Skills：** `change-impact` · `docs-governance`

```text
$change-impact $docs-governance

审计所有数据来源、来源快照、commit、URL、SHA-256、许可和生成工具。检查正式层与候选层的来源隔离、AI 生成数据标识和人工审校证据。找出无法证明来源或许可的资源。
```

#### ECC-049 · 生产成熟度审查

**预计执行时间：45 分钟**（单次执行；包含代码阅读、定向实施/分析与相关验证）

**Skills：** `production-audit` · `test-collaboration`

```text
$production-audit $test-collaboration

审计 geo_regions 是否达到生产 SDK 准入要求。检查 productionSdkExpected、readiness、生产数据质量、SDK 测试、远程完整性验证、缓存、错误分类和发布产物。明确阻塞项，不得把 Phase 1 或 Demo 完成等同于生产就绪。
```

#### ECC-050 · 接入 Flutter 方案

**预计执行时间：60 分钟**（单次执行；包含代码阅读、定向实施/分析与相关验证）

**Skills：** `contract-first` · `change-impact` · `parallel-execution-optimizer`

```text
$contract-first $change-impact $parallel-execution-optimizer

规划 geo_regions 接入 imboy-flutter。检查当前 SDK、IMBOY_INTEGRATION.md、CONSUMER_CONTRACT.md 和 Flutter 地区选择代码。明确 SDK、宿主 Adapter、账号缓存、结构化 Selection、旧字符串兼容、保存事务及测试责任。核对各仓当前 HEAD，不采用未经验证的历史 SHA/API。
```


## IMBoy 地区数据与国际化场景复刻（geo_regions）

> 本组面向客户业务场景复刻。每个场景提供三条独立提示词：A 新增功能；B 优化现有功能（重点适用于新模型复审旧 AI 代码）；C 测试现有功能。将提示词中的“客户”替换为具体客户、行业、角色和目标流程。



#### ECC-108 · 客户国家/地区/地址选择场景

**预计执行时间（单选一种模式）：A 新增功能 60 分钟 · B 优化现有功能 45 分钟 · C 测试现有功能 30 分钟**

**场景：** 地区选择和本地化

**A · 新增功能 · `product-capability` + `orch-add-feature` + `test-collaboration`**

```text
$product-capability $orch-add-feature $test-collaboration

业务场景：客户国家/地区/地址选择场景（地区选择和本地化）。客户信息：[填写客户行业、用户角色、业务目标、关键流程、特殊业务规则、数据规模和验收指标]。本次范围：[填写具体端、模块、功能切片]。

任务：为该场景新增功能。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、架构/产品文档、API/WS/数据契约、真实代码和测试。以代码与可执行证据为准，标记 CURRENT、TARGET、LOCKED、UNKNOWN、NOT_VERIFIED；不能把文档/API 存在等同于功能已经端到端交付。

读取该场景对应的领域概念、路由/接口、数据模型、Flutter/Admin 消费入口和现有测试，先做能力盘点：哪些可直接复用、哪些可通过配置组合、哪些确实缺失。不得重复造轮子或把未开放能力当作已交付。

为真正缺失的能力形成 capability contract：角色与权限、用户旅程、状态机、输入输出、数据归属、API/WS、迁移兼容、失败恢复、观测和验收标准。客户输入不完整时列出阻塞问题并停在方案阶段；需求明确时按 orch-add-feature 的计划门禁执行，先写失败测试再实现最小差异。数据来源许可、source-lock、稳定 ID/pathIds、Schema、Manifest、Revision、SHA-256、候选/生产数据隔离和 SDK 消费契约。

运行相关定向测试和契约/架构门禁。只修改批准范围，不 commit、不 push、不合并、不部署。
```

**B · 优化现有功能 / 新模型复审旧 AI 代码 · `brownfield-retrospective` + `security-review` + `test-collaboration` + `verification-loop`**

```text
$brownfield-retrospective $security-review $test-collaboration $verification-loop

业务场景：客户国家/地区/地址选择场景（地区选择和本地化）。客户信息：[填写客户行业、用户角色、业务目标、关键流程、特殊业务规则、数据规模和验收指标]。本次范围：[填写具体端、模块、功能切片]。

任务：优化现有功能，重点用于新一代 AI 模型复审和改进旧 AI 模型生成的代码。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、架构/产品文档、API/WS/数据契约、真实代码和测试。以代码与可执行证据为准，标记 CURRENT、TARGET、LOCKED、UNKNOWN、NOT_VERIFIED；不能把文档/API 存在等同于功能已经端到端交付。

按 brownfield-retrospective 的 slice-first 方法，把范围限制在约 15 个文件或 2000 行以内。不要信任旧模型自评、注释或现有测试完整性；独立重建真实行为、调用链、数据流、权限边界、失败路径、并发/竞态、资源生命周期和跨端契约，建立改动前测试/性能/错误行为基线。

重点检查：逻辑正确性、边界条件、异常处理、幂等与重试、安全、性能热点、重复/过度抽象、可维护性和跨端一致性；特别排查只改响应未改查询/持久化、只修主路径漏掉其他分支、字段/可空性漂移、异常吞掉、UI-only 权限、mock 通过但真实路径失败、测试与实现共享错误假设等 AI 常见盲点。

每项发现提供文件/行号、证据、影响、风险和最小修复方案。优先行为保持型优化；先新增/修正测试证明问题，再做最小改动。涉及公共 API/WS、数据库结构、E2EE、权限语义或用户可见行为变化时先请求确认。数据来源许可、source-lock、稳定 ID/pathIds、Schema、Manifest、Revision、SHA-256、候选/生产数据隔离和 SDK 消费契约。

先在会话中输出基线和差距清单；不要自动创建 docs/retro 或重复报告。对范围内明确且行为保持的改进可以实施；完成后运行相关测试、静态检查和 diff review，报告改动前后证据与未验证项。不 commit、不 push、不合并、不部署。
```

**C · 测试现有功能 · `test-collaboration` + `ai-regression-testing` + `verification-loop`**

```text
$test-collaboration $ai-regression-testing $verification-loop

业务场景：客户国家/地区/地址选择场景（地区选择和本地化）。客户信息：[填写客户行业、用户角色、业务目标、关键流程、特殊业务规则、数据规模和验收指标]。本次范围：[填写具体端、模块、功能切片]。

任务：测试现有功能，独立验证旧 AI 模型生成的实现。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、架构/产品文档、API/WS/数据契约、真实代码和测试。以代码与可执行证据为准，标记 CURRENT、TARGET、LOCKED、UNKNOWN、NOT_VERIFIED；不能把文档/API 存在等同于功能已经端到端交付。

先不要修改业务实现。盘点该场景已有单元、集成、契约、E2E、平台/设备测试和 CI 门禁，建立“需求/不变量 → 测试资产或 TEST-ID → 命令 → 证据”矩阵。覆盖正常路径、权限拒绝、非法输入、边界值、重复请求、并发、超时、故障恢复、旧数据兼容和跨端行为。

针对 AI 生成代码特别检查 mock/sandbox 与真实路径不一致、数据库查询/写入字段遗漏、序列化遗漏、仅测 happy path、异常吞掉、重试重复副作用和测试 fixture 迎合实现。只新增有区分力的测试，不复制重复用例、不降低阈值、不扩大 skip。tool/import_data.py、tool/geo_data.py、tool/check_readiness.py、semantic audit、manifest 检查和 tests 现有入口。

逐项报告 PASS/FAIL/BLOCKED/NOT RUN、真实命令、退出码、测试数量和证据位置。发现缺陷先提供复现和最小修复建议；未经授权不修改业务代码。不得把未执行或环境缺失标记为 PASS。
```

#### ECC-109 · 客户国际化地区数据扩展

**预计执行时间（单选一种模式）：A 新增功能 60 分钟 · B 优化现有功能 45 分钟 · C 测试现有功能 30 分钟**

**场景：** 多国家多语言客户数据接入

**A · 新增功能 · `product-capability` + `orch-add-feature` + `test-collaboration`**

```text
$product-capability $orch-add-feature $test-collaboration

业务场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。客户信息：[填写客户行业、用户角色、业务目标、关键流程、特殊业务规则、数据规模和验收指标]。本次范围：[填写具体端、模块、功能切片]。

任务：为该场景新增功能。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、架构/产品文档、API/WS/数据契约、真实代码和测试。以代码与可执行证据为准，标记 CURRENT、TARGET、LOCKED、UNKNOWN、NOT_VERIFIED；不能把文档/API 存在等同于功能已经端到端交付。

读取该场景对应的领域概念、路由/接口、数据模型、Flutter/Admin 消费入口和现有测试，先做能力盘点：哪些可直接复用、哪些可通过配置组合、哪些确实缺失。不得重复造轮子或把未开放能力当作已交付。

为真正缺失的能力形成 capability contract：角色与权限、用户旅程、状态机、输入输出、数据归属、API/WS、迁移兼容、失败恢复、观测和验收标准。客户输入不完整时列出阻塞问题并停在方案阶段；需求明确时按 orch-add-feature 的计划门禁执行，先写失败测试再实现最小差异。数据来源许可、source-lock、稳定 ID/pathIds、Schema、Manifest、Revision、SHA-256、候选/生产数据隔离和 SDK 消费契约。

运行相关定向测试和契约/架构门禁。只修改批准范围，不 commit、不 push、不合并、不部署。
```

**B · 优化现有功能 / 新模型复审旧 AI 代码 · `brownfield-retrospective` + `security-review` + `test-collaboration` + `verification-loop`**

```text
$brownfield-retrospective $security-review $test-collaboration $verification-loop

业务场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。客户信息：[填写客户行业、用户角色、业务目标、关键流程、特殊业务规则、数据规模和验收指标]。本次范围：[填写具体端、模块、功能切片]。

任务：优化现有功能，重点用于新一代 AI 模型复审和改进旧 AI 模型生成的代码。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、架构/产品文档、API/WS/数据契约、真实代码和测试。以代码与可执行证据为准，标记 CURRENT、TARGET、LOCKED、UNKNOWN、NOT_VERIFIED；不能把文档/API 存在等同于功能已经端到端交付。

按 brownfield-retrospective 的 slice-first 方法，把范围限制在约 15 个文件或 2000 行以内。不要信任旧模型自评、注释或现有测试完整性；独立重建真实行为、调用链、数据流、权限边界、失败路径、并发/竞态、资源生命周期和跨端契约，建立改动前测试/性能/错误行为基线。

重点检查：逻辑正确性、边界条件、异常处理、幂等与重试、安全、性能热点、重复/过度抽象、可维护性和跨端一致性；特别排查只改响应未改查询/持久化、只修主路径漏掉其他分支、字段/可空性漂移、异常吞掉、UI-only 权限、mock 通过但真实路径失败、测试与实现共享错误假设等 AI 常见盲点。

每项发现提供文件/行号、证据、影响、风险和最小修复方案。优先行为保持型优化；先新增/修正测试证明问题，再做最小改动。涉及公共 API/WS、数据库结构、E2EE、权限语义或用户可见行为变化时先请求确认。数据来源许可、source-lock、稳定 ID/pathIds、Schema、Manifest、Revision、SHA-256、候选/生产数据隔离和 SDK 消费契约。

先在会话中输出基线和差距清单；不要自动创建 docs/retro 或重复报告。对范围内明确且行为保持的改进可以实施；完成后运行相关测试、静态检查和 diff review，报告改动前后证据与未验证项。不 commit、不 push、不合并、不部署。
```

**C · 测试现有功能 · `test-collaboration` + `ai-regression-testing` + `verification-loop`**

```text
$test-collaboration $ai-regression-testing $verification-loop

业务场景：客户国际化地区数据扩展（多国家多语言客户数据接入）。客户信息：[填写客户行业、用户角色、业务目标、关键流程、特殊业务规则、数据规模和验收指标]。本次范围：[填写具体端、模块、功能切片]。

任务：测试现有功能，独立验证旧 AI 模型生成的实现。

先核对当前仓库 HEAD、工作区状态、AGENTS.md/CLAUDE.md、架构/产品文档、API/WS/数据契约、真实代码和测试。以代码与可执行证据为准，标记 CURRENT、TARGET、LOCKED、UNKNOWN、NOT_VERIFIED；不能把文档/API 存在等同于功能已经端到端交付。

先不要修改业务实现。盘点该场景已有单元、集成、契约、E2E、平台/设备测试和 CI 门禁，建立“需求/不变量 → 测试资产或 TEST-ID → 命令 → 证据”矩阵。覆盖正常路径、权限拒绝、非法输入、边界值、重复请求、并发、超时、故障恢复、旧数据兼容和跨端行为。

针对 AI 生成代码特别检查 mock/sandbox 与真实路径不一致、数据库查询/写入字段遗漏、序列化遗漏、仅测 happy path、异常吞掉、重试重复副作用和测试 fixture 迎合实现。只新增有区分力的测试，不复制重复用例、不降低阈值、不扩大 skip。tool/import_data.py、tool/geo_data.py、tool/check_readiness.py、semantic audit、manifest 检查和 tests 现有入口。

逐项报告 PASS/FAIL/BLOCKED/NOT RUN、真实命令、退出码、测试数量和证据位置。发现缺陷先提供复现和最小修复建议；未经授权不修改业务代码。不得把未执行或环境缺失标记为 PASS。
```

## 维护说明

- 本文只维护本仓库职责范围内的提示词；跨仓案例的统一索引位于 [imboy 后端主仓 docs/prompts/README.md](https://github.com/imboy-pub/imboy/blob/main/docs/prompts/README.md)。
- 修改案例时保持 ECC 编号不变；新增案例先在后端主仓索引登记编号和归属，避免重复。
- Skill 名称必须与 ECC `skills/<name>/SKILL.md` 中的目录名一致；ECC 升级后应重新核对可用性。
- 提示词是任务入口，不是执行结果或质量证明；验收以真实代码、测试和 CI 证据为准。
