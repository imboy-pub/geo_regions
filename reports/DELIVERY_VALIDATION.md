# 交付验收记录 / Delivery verification

日期 / Date: 2026-11-13。此报告记录本次交付实际做过的工作，不等于计划中的生产SDK已经完成。

## 1. 本地实际通过 / Executed locally

| Check | Result | Evidence / 边界 |
|---|---|---|
| 上游源固定与原始字节校验 | PASS | 36份固定commit源文件；hash/bytes/license/version记录 |
| 离线重建 | PASS | `tool/import_data.py --check`，124个派生输出一致 |
| JSON Schema与语义 | PASS | 十国4,143节点、100地区语言包、10国家名小包、父链/无环/quality/revision |
| Manifest | PASS | 121个资源完整清单，全字节SHA-256与大小一致 |
| Selection | PASS | 真实JP东京root-inclusive ID路径、父边与revision |
| Python测试 | PASS | 44项：27项数据/工具边界，17项无覆盖导入及任务状态安全 |
| Demo JavaScript行为 | PASS | 22项，使用Node及DOM替身，**不是浏览器布局/键盘验收** |
| Demo Shell脚本语法 | PASS | `bash -n demo/flutter/bootstrap.sh` |
| 离线子集 | PASS | 15个数据资源1,320,132 bytes；不包含其他9国结构payload |
| Flutter asset条目与声明 | PASS | 21个显式条目，含manifest/registry及许可/来源；全部文件真实存在 |
| 数据Release打包演练 | PASS | ZIP解压后再次离线重建与Schema检查；未发布远端 |
| Workflow YAML | PASS | 本地解析与固定action引用审查；不是GitHub在线运行 |
| 状态任务定义 | PASS | 14节点依赖有向无环，ID完整，P1-01为首节点 |

机器原始报告：[tooling-validation.json](tooling-validation.json)、[data-validation.json](data-validation.json)。详细记录：[TOOLING_VALIDATION.md](TOOLING_VALIDATION.md)。

## 2. 预期拒绝 / Expected rejection

`python3 tool/geo_data.py validate --production`对当前research-seed返回失败，这是正确行为。完整性通过、文件存在或很多名称有值，都不等于已通过生产现势与语言审核。测试验证的就是拒绝不合格发布profile，而不是修改标签来绕过门禁。

The production gate intentionally rejects the research seed. Integrity, populated files and source-quality labels are not proof of current authoritative geography or native-speaker review.

## 3. 未执行与具体原因 / Not executed and why

| Item | Status | Reason / 下一步 |
|---|---|---|
| Flutter格式化/静态分析 | NOT RUN | 当前执行环境无Flutter/Dart；P1-01在ZCODE本地运行并修正 |
| 5项Flutter Widget测试 | NOT RUN | 已提供测试源码，未获得运行结果 |
| Flutter Web/native build | NOT RUN | 没有SDK/设备构建环境；不得称已编译 |
| HTML真实浏览器视觉 | BLOCKED | 本地Chromium启动遇socket权限限制；提权动作被自动审批拒绝（sandbox_approval=false）；正式云浏览器直接file URL也被协议安全策略拒绝。已停止该路径，没有通过换地址/间接执行绕过 |
| 200%文字/读屏/真实键盘 | NOT RUN | 代码已改善并有测试要求；Node替身不验证几何布局与真实辅助技术 |
| GitHub在线CI/CD | NOT RUN | 本轮交付配置文件，未push或启动远端workflow |
| 仓库main/tag保护与pub.dev | NOT CONFIGURED | 需首次在线结果及真实维护者配置；不能靠YAML声称已启用 |
| IMBoy源码迁移 | NOT STARTED | Phase2计划与真实基线已准备；本次未改三端仓库 |
| 十国各层级十语人工审校 | INCOMPLETE | 保留provisional、zh-Hant与CN非中文深层缺口，见并行工作包 |

The blocked escalation was automatically rejected; no successful browser or Flutter result is claimed. The delivery remains usable as a development handoff, and the first planned task explicitly performs the missing runtime/UX checks.

## 4. 数据事实边界 / Data limitations

- 10国而非全球完成；覆盖深度按国家不同。统计树深度不等于法定行政级别。
- CN深层为2023-06-30历史统计快照；现势更新有独立任务。
- zh-Hant共13个显式地区名称（10国root+GB3），不能称完整繁中地区库。
- CN简中覆盖3,430/3,430；其他语种深层大量缺失。其余显式名称也保留各自source quality。
- CLDR的approved-in-source或qualified不代表本项目做过人工审核；默认名也带quality，禁止回退绕过。
- 代码BSD-3-Clause与第三方Unicode-3.0/WTFPL分别保留；尚未把种子提升为生产发布。

## 5. 封包检查 / Archive checks

最终开发交付ZIP包含README、双语PRD/Plan、协议/接入/规则、数据与完整原始源、脚本/测试/Schema、Demo、CI/CD和提示词。排除Git元数据、build产物、SDK缓存、pycache、机器状态和秘密信息；不创建DOCX/PDF。

`CONTENTS.sha256`记录包内文件字节哈希（不包含自身），可在解压根运行`shasum -a 256 -c CONTENTS.sha256`验证。封包后再对解压副本做导入源重建、manifest与selection校验。此项的机器结果见 [archive-verification.json](archive-verification.json)。报告不嵌入ZIP自身哈希，避免自指；最终包另经完整CRC和CONTENTS字节校验。
