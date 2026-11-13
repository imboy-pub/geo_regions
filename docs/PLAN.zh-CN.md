# geo_regions 两阶段执行计划

版本：1.0 · 日期：2026-11-13 · 固定任务：`geo-regions-v1`

英文：[PLAN.en.md](PLAN.en.md)。需求：[PRD.zh-CN.md](PRD.zh-CN.md)。执行提示词：[ZCODE_START.zh-CN.md](../prompts/ZCODE_START.zh-CN.md)。任务清单：[tasks.json](../.plans/geo-regions-v1/tasks.json)。

## 1. 执行原则

目标仓库 `/Users/leeyi/project/imboy.pub/geo_regions`，预期 origin `https://github.com/imboy-pub/geo_regions`。读取实际 `AGENTS.md`、git 状态、worktree、现有代码后再行动；本路径不等于当前交付环境已经访问了用户 Mac。这个 ZIP 是可导入的交付基线，不含生产 SDK 完工声明。

第一节点是 **P1-01：有精心 UI/UX 的可运行 Demo**。包名、BSD-3-Clause 和首批语言已确认，不再以此要求人工确认。第一节点使用已有小 fixture 和协议草案，随后在 P1-02 固化契约，再替换为真实 SDK；不能等全部数据完成才展示 Demo。

默认沿用 ZCODE 当前模型和推理配置，不自动提高档位。默认最多两个并行工作者，协调者统一合并，避免与 IMBoy 既有长任务争抢资源。单仓库同一文件只能一个写入者；manifest、schemas、公共接口及 pubspec 的合并由协调者串行完成。

继续会话使用固定任务 ID，不用当前日期新建 RUN_ID。`.plans/geo-regions-v1/state.json` 保存任务证据、分支、工作树和检查点；只有证据与当前输入吻合的任务才能继续算完成。所有 pending 状态是真正待实施；本包已有原型/工具/数据只是输入，不自动把 SDK 任务置 completed。

## 2. 两阶段与依赖

| 阶段 | 完成目标 | 出口 |
|---|---|---|
| Phase 1 | 独立 Flutter 库、十国种子治理、十语解析、可选 UI、按需/离线工具及 CI | 可审阅 release candidate；无 IMBoy 耦合 |
| Phase 2 | IMBoy 接入、旧资料兼容、保存导航、三端必要适配 | 真实验收证据、灰度与回滚方案 |

顺序与并行关系：P1-01 → P1-02；随后 P1-03、P1-04、P1-06 可在所有权隔离后并行；P1-05 接 P1-04；P1-07 接数据/加载/资产工具；P1-08 汇总。P2-01 的只读盘点可在 P1-02 之后提前做，其余第二阶段改造在 Phase 1 出口通过后推进。

## 3. Phase 1 任务卡

### P1-01 · 首个可运行 Demo 与 UI/UX 验收

- 前置：仓库定位、现有改动保护；使用交付的 `demo/flutter` 与 `demo/web_preview`。
- 步骤：导入原型 → 安装/检查 Flutter → 运行 bootstrap → 格式/分析/Widget 测试 → 在 Web 与一类设备或桌面实际运行 → 对照 UX 规范修正。
- 交付：可运行 Flutter Demo、README、两种宽度/明暗/RTL 截图和交互记录；保留 fixture 标识，不假装远程请求实际发生。
- 测试：`dart format --output=none --set-exit-if-changed lib test`、`flutter analyze --fatal-infos`、`flutter test`、`flutter build web --release`（在 demo/flutter）。实际命令先按 demo README 确认平台生成步骤。
- 验收：搜索→导航→选择→语言切换保持 ID→重试→完成全流程；390 px 与 1280 px 无关键溢出；RTL、大字体、键盘、读屏状态可用。HTML 通过不得替代 Flutter 编译/布局通过。
- 退出：AT-01/02/03/04 有证据；设备缺失记 BLOCKED，只完成可运行端的子检查，P1-01 不虚标完成。无需用户逐项确认；执行者用客观标准修复。

### P1-02 · 固化数据协议与消费者契约

- 前置：P1-01；使用本包协议/Schema/数据作为候选，不重新发明标准。
- 步骤：核对六类 Schema；固定 stable ID、root-inclusive path、locale aliases、revision/quality 算法、childrenStatus 与错误分类；加入 JSON 合法但语义非法的负例。
- 交付：`docs/PROTOCOL.md`、`schemas/`、宿主接口说明、兼容性与弃用策略；明确 strict remote verifier 前置。
- 测试：`python3 tool/geo_data.py validate --schema`，`python3 -m unittest discover -s tests -v`；实现 Dart parser 后同一测试向量跨语言比较。
- 验收：重复键、父级缺失/循环、跨国父级、悬空译名、revision 错配、路径穿越和损坏资源均拒绝；合法 source-quality 元数据保留。
- 退出：GR-01/02/06/07/11 对应契约无互相矛盾；不把标准格式检查等同地理事实校验。

### P1-03 · 十国数据审核、十语质量与扩展队列

- 前置：P1-02；输入 `sources/`、导入器、覆盖报告；不把互联网实时抓取放入普通 CI。
- 步骤：离线重建 → 核对 commit/hash/license → 逐国确认来源范围与统计层级 → 优先复核 IMBoy 使用路径 → 逐语审核 provisional、繁体缺口和同名歧义 → 输出发布 profile。
- 交付：十国可重建结构、100 个地区名称包、10 个国家目录名称包、来源与质量报告、剩余任务表。实际数量随扩展变化，以 manifest 为准。
- 测试：`python3 tool/import_data.py --check`；全量 validator；语言增加前后结构哈希比较；源版本差异与兼容性报告。
- 验收：已有源数据不编造翻译；明确 reviewed/qualified/provisional/native/missing；中国历史快照与异常 crosswalk 可追溯；unknown 下级不冒充终点。生产支持范围不能由“文件存在”自动推定。
- 并行：按 [DATA_WORKPACKAGES.md](DATA_WORKPACKAGES.md) 拆国家及语言；工作者只写各自 staging，协调者合并数据和 manifest。
- 退出：产品宣称覆盖与证据一致；未完成全球范围是公开 backlog，不写成已完成。核心 IMBoy 支持路径未复核时发布门禁不通过。

### P1-04 · SDK 模型、索引与名称解析

- 前置：P1-02；可与 P1-03/P1-06 并行。新增根 Flutter package `geo_regions`；不得将 Demo 假装生产库。
- 步骤：实现 parser、模型、root-inclusive selection、路径校验、索引、基础搜索、别名映射、质量过滤和语言回退。
- 交付：`lib/geo_regions.dart`、纯数据入口、模型/名称测试、API 使用说明；只依赖 Flutter SDK。
- 测试：单元测试覆盖同名节点、非三级结构、国家单选、无翻译/质量不足、zh-CN 与 zh-Hant 分离、跨 dataset ID、revision 不匹配、删除/改父迁移。
- 验收：显示语言变化不改 selection identity；解析器返回 typed errors；当前1.0严格Schema和未来版本演进有统一规则，未支持的字段/版本明确拒绝。

### P1-05 · 加载、缓存、完整性与并发

- 前置：P1-04；数据结构可先用确定性向量，最终必须验证 P1-03 数据。
- 步骤：实现 AssetBundle loader、可注入 remote loader/store/verifier、dedupe、缓存索引、资源状态机、generation token、原子更新与旧版本集合回退。
- 交付：数据 Repository、fake adapters、严格远程配置检查、缓存清理与大小配额接口、真实远程示例适配。
- 测试：AT-06/07/08/09/10/11；使用可控制延迟与乱序的 loader、可失败的 store。验证 SHA-256 在 JSON 解码和写入之前检查。
- 验收：无网络无缓存明确 unavailable；坏下载不改旧文件；旧请求不覆盖新选择；同资源只一次底层加载；不将不兼容版本拼接。Web 无无条件 dart:io import。

### P1-06 · 离线资源生成与宿主接入 CLI

- 前置：P1-02；可与 P1-03/P1-04 并行。
- 步骤：复用 Python工具作为 golden reference，提供 `bin/assets.dart`；从 package_config 解析安装位置；配置按结构、国家×语言、catalogLocales 独立；生成精确 pubspec asset 条目和校验报告。
- 交付：Dart CLI、配置 Schema/样例、全离线/混合/在线三个案例；构建前执行入口，陈旧配置失败检测。
- 测试：两个不同国家×语言组合；拷贝产物与源 hash 一致；实际 `flutter build web`/移动资源清单无未选数据；缺资源、损坏、symlink、危险输出和重跑失败保护已有产物。
- 验收：从已安装包而非仓库绝对路径能生成；新增语言不升级 SDK；未选数据只留 descriptor、不留payload；记录 gzip/uncompressed 发布大小。

### P1-07 · 通用 Picker 与真实 Demo

- 前置：P1-03/04/05/06；复用 P1-01 设计。
- 步骤：将 demo fixture adapter 替换为 SDK；默认 UI 与数据入口解耦；提供 labels/theme/builders/selection policy；真实本地文件与 HTTP 失败、缓存恢复演示。
- 交付：可复用 widget、真实 `example/`、轻依赖接入说明、完整状态矩阵。
- 测试：AT-01–11、AT-14/15；至少一次真实远程资源校验与浏览器离线重启访问。验收请求日志证明只获取目标资源。
- 验收：默认 UI 不引用 IMBoy；Arabic RTL 与 200% 字体有效；未知数据范围不显示“已到最末级”；重试和保存状态可恢复。

### P1-08 · CI、跨平台验收与发布候选

- 前置：P1-03/04/05/06/07。CI 基础从首次导入就运行，不等本任务才加。
- 步骤：将 config/readiness.json 的 productionSdkExpected 改为 true，由 tool/check_readiness.py 强制检查生产源码/测试存在；补足库的 analyze/test/build 门禁；运行源码+数据校验；记录最低支持 Flutter 与 IMBoy3.41.x 的兼容证据；执行 package dry-run、离线包体审计、许可证分发检查。
- 交付：真实 workflow URL、测试摘要、版本变更记录、包体与性能报告、草稿 release；安装/升级/回滚说明。
- 验收：必需 summary gate 不因 paths 过滤悬空；数据-only PR不无故启动Flutter；声明SDK已实现时不能因源码缺失绿灯；关键 SKIP 均显式阻止宣告完成。数据 tag 不可覆盖同版本内容。
- 发布边界：本计划授权本地开发和可审阅材料，不默认公开 pub.dev 发布、合并主干或生产切换。发布配置/账号缺失记录一次，其余工作继续。

## 4. Phase 2 任务卡

### P2-01 · IMBoy 真实基线盘点

- 前置：P1-02 后可只读并行；正式改造需 P1-08。
- 输入：`imboyapp`/`imboy`/`imboyadmin` 实际路径、AGENTS、worktrees、origin、当前提交；不得假设目录名就是远端名。
- 交付：接口/文件/测试清单，旧 region 样本，已有测试复用矩阵，当前进行中任务冲突地图。
- 已核实参考：Flutter main `2cee59317de36e2f70420f46dc881b1117b034c9`（2026-11-13查询）已带 PR #68 路径及保存导航修复；执行时重新确认，不重做它。
- 验收：明确旧字符串及缓存行为、后端实际可存字段和管理端展示点，列出缺失仓库；未读源码不凭空新建迁移接口。

### P2-02 · 宿主数据适配与账号隔离

- 前置：P1-08、P2-01。
- 交付：复用现有 HTTP/缓存基础设施的 loader/store/verifier；locale aliases、labels、离线 CN 与在线其他国家配置。
- 验收：不为此重复引入网络框架；Web存储适配可用；两个账号的选择不串；缓存数据可复用但账号资料隔离；结构包与语言包组合符合配置。

### P2-03 · 用户资料协议及迁移

- 前置：P1-08、P2-01；可与 P2-02并行，后端文件所有权独立。
- 步骤：按真实 API 选择兼容的新字段/JSON结构；保留 legacy string；服务端验证dataset/country/path/revision，不信任客户端显示名。旧数据只有唯一可信映射才迁移。
- 交付：兼容契约、最小后端/管理端必要改动、幂等迁移、回滚脚本/说明、旧新客户端互操作测试。
- 验收：同名/空格名称/旧行政码/删除或合并地区不猜；不确定标 unresolved 并保留原文；迁移重跑不损坏数据；旧客户端仍读到原有字符串。

### P2-04 · 替换地区数据源并保持保存导航

- 前置：P2-02/03。
- 交付：保留 IMBoy iOS 风格 `SetRegionPage`、provider、`MorePage` 接入；内部改用 ID路径和名称解析。
- 验收：深层选中→返回上层→再次进入→完整路径仍正确；服务端成功才提交持久化；失败仍停留可重试；成功后统一返回MorePage；重复点击单次保存；换语言不导致hasChanged误判。
- 测试：复用现有 widget regression与AT-MF06；新增真正loader/cache验证，与Widget fake分离。

### P2-05 · 全链路与跨端回归

- 前置：P2-04。
- 交付：十语切换、阿语RTL、离线/恢复、缓存损坏、账号切换、旧新数据的测试记录；Flutter Web、Android/iOS及现有支持桌面平台的实际结果。
- 验收：同一用户多个客户端一致；后端读写和管理端展示正确；既有路径/导航测试不回退。设备或登录信息缺失记BLOCKED而非PASSED。
- 设备执行遵循各仓库AGENTS；不修改原生平台受保护文件以绕过构建/测试要求。

### P2-06 · 灰度、文档与交接

- 前置：P2-05。
- 交付：配置开关、回退到旧region读取路径的说明、兼容窗口、源数据更新流程和验收总表。
- 验收：回滚不用删除新数据；迁移可重入；代码和数据release均可定位；所有GR需求有PASS或经明确接受的范围说明，关键未通过不标完成。
- 输出可审阅diff/commit/草稿PR材料；没有明确授权不执行公开发布、生产操作或合并。

## 5. 验收矩阵

| 测试ID | 主要场景 | 覆盖需求 |
|---|---|---|
| AT-01 | 响应式Demo、键盘与读屏 | GR-09 |
| AT-02 | 深层路径、同名节点、国家单选 | GR-01/08/10 |
| AT-03 | 十语切换ID不变、RTL | GR-02/07/09 |
| AT-04 | loading/empty/error/offline/retry状态分离 | GR-05/09 |
| AT-05 | 新语言前后结构hash相同 | GR-02/11 |
| AT-06 | 目标国家按需下载、切语只补语言 | GR-04 |
| AT-07 | 并发去重及乱序响应 | GR-05 |
| AT-08 | hash损坏/短读/非法JSON不污染缓存 | GR-06 |
| AT-09 | 未配置verifier的远程严格模式报错 | GR-06/12 |
| AT-10 | 更新原子切换、旧版本一致回退 | GR-05/06 |
| AT-11 | 离线无缓存与unknown子级不冒充叶 | GR-05/10 |
| AT-12 | 编译产物只有选定payload | GR-03/13 |
| AT-13 | 源固定、许可、离线重建、差异 | GR-11/15 |
| AT-14 | provisional过滤、繁中缺口有据回退 | GR-07 |
| AT-15 | SDK无IMBoy/第三方runtime耦合 | GR-12/16 |
| AT-16 | 保存成功/失败/重复点击/返回MorePage | GR-14 |
| AT-17 | legacy迁移歧义、幂等、旧客户端兼容 | GR-01/14 |
| AT-18 | Web与原生真实缓存/账号隔离 | GR-13/14 |
| AT-19 | CI门禁、只数据PR、草稿发布可重建 | GR-15 |
| AT-20 | 相同版本不同内容拒绝、可回滚 | GR-06/15 |

## 6. 证据、状态与续跑

每个任务保存：输入commit与源hash、改动文件、执行命令、exit code、报告路径、输出hash、测试范围及PASS/FAIL/SKIP/BLOCKED。目录 `.plans/geo-regions-v1/evidence/<task>/` 只保存必要证据；不提交密钥、大型SDK缓存或设备账号。

任务状态为 pending / in_progress / blocked / completed。开始前确认依赖已完成；完成需要验证命令输出和可用证据。新会话读取state和git差异，再重新验证受变化影响的任务；不能仅看到completed就跳过。工具只管理状态，不替代代码审查或自动证明测试成功。

若ZCODE有原生任务面板，调用其真实task/update_plan/TodoWrite能力显示这些ID、状态和下一步，持续同步state；不同版本工具名称可能不同。若没有此能力，明确说明并提供终端清单，不伪造工具调用。任务进度与可恢复状态不能只存在聊天记录里。

## 7. 首次执行命令

```bash
cd /Users/leeyi/project/imboy.pub/geo_regions
python3 tool/plan_status.py init
python3 tool/plan_status.py status
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 -m unittest discover -s tests -v
```

先按 README 安全导入交付包；Schema依赖见 `tool/requirements-ci.txt`。然后执行 P1-01。此处命令用于检查交付输入，不代表已完成后续生产SDK。
