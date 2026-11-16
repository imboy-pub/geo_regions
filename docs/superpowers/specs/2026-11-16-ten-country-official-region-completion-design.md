# 十国官方行政区划数据补全设计

日期：2026-11-16
状态：已确认
目标分支：`main`
实施分支：`feat/ten-country-official-regions`

## 1. 背景与目标

正式 `geo-regions-seed` 当前包含 CN、JP、KR、US、GB、DE、FR、IT、RU、SA 十国，但除 CN 外，多数国家只有 CLDR 可达的一级或浅层 subdivision。现有九国 CSC 候选数据具有不同 datasetId、ID 体系、许可和成熟度，不能直接并入正式数据集。

本设计在不宣称生产就绪、不直接引入 ODbL CSC、不要求一次完成十语人工审校的前提下，使用可追溯、可再分发的官方或一手来源，补全十国各自声明 Profile 内的现势行政结构，并保持数据可离线重建。

## 2. 完成定义

每个国家必须完成以下闭环：

1. 明确行政 Profile、目标深度、官方代码体系、包含项、排除项和来源口径。
2. 固定来源版本、URL、发布日期或生效日期、抓取日期、许可、SHA-256 和字节数。
3. 提供可复现的国家适配器及必要的公共导入基础设施。
4. 生成国家结构、兼容的稀疏语言包、来源记录、覆盖报告和 ID 迁移记录。
5. 保留同一现实实体的既有 ID；所有删除、替代和改父均有明确映射或无法映射说明。
6. 通过适配器测试、离线重建、Schema、拓扑、来源、语言兼容、Manifest 和 Selection 校验。
7. 数据继续保持 `research-seed`，生产门禁继续按预期拒绝未审数据。

如果来源无法固定、许可不允许再分发、父链无法核实或数据不符合目标行政 Profile，不得用 ODbL CSC、无来源 AI 数据或名称猜配绕过。实施者必须在对应国家提交前报告阻塞并请求决策。

## 3. 国家 Profile 基线

| 国家 | 目标基线 | 不包含 |
| --- | --- | --- |
| CN | 省级、地级、县级行政结构；保留现有统计快照身份并提供现势迁移 | 不为追求深度批量加入居民点、村居委会或无可靠父链的乡镇 |
| JP | 都道府县及市、区、町、村 | 非行政城市榜单和居民点 |
| KR | 广域自治团体及市、郡、区，按官方父链处理自治区 | 虚构整合市和无官方代码的别名实体 |
| US | 州及同等级别、county 和 county equivalent | 普通城市清单、place 居民点和 MCD |
| GB | 构成国及目标 Profile 声明的 local authority 行政层 | parish、community、选区和普通城市清单 |
| DE | 州及官方行政下级，目标到 Gemeinde | 普通居民点和非行政城市榜单 |
| FR | region、department、commune，并按官方规则处理海外实体 | 普通居民点和非行政城市榜单 |
| IT | region、官方省级实体、comune | 已废止实体和普通居民点 |
| RU | 保持现有 territorial profile，补到可独立核验的区或市级行政单元 | 通过更换政治或领土口径制造额外覆盖 |
| SA | region 及 governorate，按官方父链处理 | 无官方父链的城市或居民点清单 |

最终 Profile 以官方数据能够支持的行政类型和父链为准。无法核验的下级覆盖必须使用 `childrenStatus=unknown` 并记录缺口，不能把缺失写成行政叶节点。

“现势”指实施时可获得的各国官方最新稳定发布。各国可以具有不同发布日期或生效日期，但必须分别记录，不得统一填入抓取日期冒充生效日期。

## 4. 来源与许可

来源优先级为：官方开放数据、官方授权镜像、能够证明一手来源和再分发权利的镜像。每个来源必须固定到不可变版本；如果官方接口没有版本标识，则保存原始快照并记录接口 URL、抓取日期、官方发布日期和响应哈希。

原始字节进入 `sources/`，来源身份进入 `sources/source-lock.json`。派生提取件必须记录生成器、输入哈希和转换过程。默认导入和 CI 不访问网络。

第三方数据继续适用其原始许可，项目 BSD-3-Clause 不重新授权第三方数据。所有再分发和 notice 义务必须随数据保留。许可不明确时不得提交派生数据。

## 5. 模块设计

`tool/import_data.py` 继续作为统一 CLI 和编排入口。为避免将十国官方格式堆入单个文件，实施时增加逐国适配器和共享的规范化构建辅助模块。

国家适配器只负责将官方输入转换为统一内部表示：

- 官方代码、稳定身份和父代码；
- 行政类型、默认本地名和可追溯名称；
- 生效、废止和替代信息；
- 来源字段和质量证据。

公共构建逻辑继续负责：

- ID 唯一性、父链、国家边界和环检测；
- 旧 ID crosswalk 与迁移验证；
- 节点排序、canonical JSON 和 revision；
- 稀疏语言包、名称质量和兼容 revision；
- Manifest、覆盖报告和离线重建。

每国使用独立 Profile 配置，避免把国家特定规则散落在通用解析器中。公共基础设施随首个国家 CN 提交引入，后续国家复用；只有通用缺陷修复才能修改既有公共行为，并必须由相应国家提交中的测试证明。

## 6. 数据流

```text
官方快照与许可证据
  → source-lock 固定版本和哈希
  → 国家适配器规范化
  → 旧 ID crosswalk / 父链验证
  → 公共构建器生成结构及稀疏语言包
  → Schema、拓扑、来源、覆盖和重建检查
  → 更新该国数据、总 Manifest 与覆盖报告
```

抓取和重建分离。抓取工具可以联网并保存不可变快照；`import_data.py --check` 和常规 CI 只读取已锁定文件。

## 7. ID、名称与版本规则

- `datasetId` 保持 `geo-regions-seed`。
- 同一现实实体优先保留现有 ID；新增节点使用官方稳定代码。
- 禁止按名称猜配、复用已删除 ID、静默改父或通过名称相似度自动接受迁移。
- 对删除、拆分、合并、替代和改父记录旧 ID、新 ID、原因和来源。
- 无法可靠映射的旧实体必须进入显式未映射清单，不能自动取首个候选。
- 旧名称只在实体身份不变时继承；官方名称可以替换机器候选，但必须保留真实质量和来源。
- 不复制英语或运行时回退来制造十语覆盖，真实缺口保持缺失。
- 结构变化后重新计算 revision，并同步所有关联语言包的兼容 revision。
- 不改变现有国家清单或用 territorial profile 表达主权立场。

## 8. 测试与验证

每个国家适配器使用小型固定样本测试以下情况：

- 正常层级和官方代码解析；
- 重复代码、缺失父级、父链环和跨国父级；
- 已废止实体、拆分合并和无法映射实体；
- 名称来源、质量和稀疏语言包；
- 目标 Profile 覆盖和 `complete`/`unknown` 边界。

每国提交前执行：

```bash
python3 tool/check_readiness.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema --report build/reports/data-validation.json
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py offline --config config/offline.example.json --out build/offline-assets
flutter test
```

`--production` 的预期结果是拒绝 research-seed；其他命令必须成功。重复执行离线包命令时使用独立输出目录或现有安全替换流程。Flutter 不可用时必须明确报告未验证项，不能声称通过。

每国覆盖报告提供前后对照：节点总数、层级分布、覆盖状态、名称质量，以及保留、新增、删除、替代和改父的 ID 数量。

## 9. Commit 与 PR 边界

从最新 `origin/main` 创建 `feat/ten-country-official-regions`，最终只创建一个 PR。

国家按以下顺序串行实施，每国恰好一个数据 Commit：

1. CN
2. JP
3. KR
4. US
5. GB
6. DE
7. FR
8. IT
9. RU
10. SA

每国 Commit 包含该国适配器、Profile、锁定来源、迁移记录、测试和生成产物，同时更新累计的 source-lock、Manifest 和覆盖报告，使该提交本身可以离线重建和通过数据校验。

本设计文档单独提交，不混入任何国家数据 Commit。当前工作区已有的 `demo/flutter/bootstrap.sh` 模式变化及三个 `pubspec.lock` 删除均与本任务无关，保持未暂存，不纳入 PR。

PR 描述必须逐国列出来源版本、许可、目标 Profile、快照日期、覆盖变化、迁移影响和实际验证结果，并明确未完成的层级或许可限制。PR 不宣称十语人工审校完成，不将 `expectedProductionGateRefusal` 改为 `false`。

## 10. 非目标

- 不引入 ODbL CSC 作为正式数据来源。
- 不将 research-seed 提升为 reviewed 或 production。
- 不完成十语人工审校或机器补齐全量翻译。
- 不扩展到普通城市、居民点、邮编、选区或地理边界坐标。
- 不重构 SDK、Picker、网络加载或持久缓存。
- 不自动发布数据 Release、pub.dev 包或 Demo。
