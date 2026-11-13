# ZCODE 主执行提示词

将下方完整内容粘贴到ZCODE。先将交付包安全导入目标仓库；若尚未导入，执行者可按README定位并调用无覆盖导入工具。此提示词不假定ZCODE某个版本一定有某个名称的任务工具。

---

你现在是 geo_regions 项目的主执行者。请实际执行以下两阶段计划，持续推进已授权的实现、修复、测试和本地交付，不停留在复述计划，也不在每个小任务结束后询问是否继续。

## 固定上下文

- 主仓库：`/Users/leeyi/project/imboy.pub/geo_regions`
- 预期远端：`https://github.com/imboy-pub/geo_regions`（等价SSH URL可）
- 包名：`geo_regions`，已确定。
- 固定任务ID：`geo-regions-v1`；不要按日期/时间新建另一个RUN_ID。
- 文档默认Markdown；沿用当前已选模型和推理强度，不自行提高。
- 计划：`docs/PLAN.zh-CN.md`、`docs/PLAN.en.md`。
- 产品：`docs/PRD.zh-CN.md`、`docs/PROTOCOL.md`。
- 数据/CI/接入：`docs/DATA_RULES.md`、`docs/DATA_WORKPACKAGES.md`、`docs/TOOLING.md`、`docs/CI_CD.md`、`docs/IMBOY_INTEGRATION.md`。
- 机器任务表：`.plans/geo-regions-v1/tasks.json`。
- 状态：`.plans/geo-regions-v1/state.json`；证据：`.plans/geo-regions-v1/evidence/<任务ID>/`。

## 先恢复，再执行

1. 读取仓库及父目录有效AGENTS.md，检查pwd、origin、HEAD、dirty diff、branch和全部worktrees。核实数据/配置/工具是否已导入；不要假设Mac路径在当前执行环境可用。
2. 若计划尚未导入，定位用户提供的geo_regions交付目录；用其中`tool/install_bundle.py --target <主仓库> --dry-run`检查，再`--apply`添加缺失文件。它拒绝覆盖冲突；存在冲突时读取并合并本次相关差异，不直接解压覆盖仓库、不重置已有改动。不能找到交付目录时报告具体缺失文件，不凭空编造计划。
3. 先检查固定分支`task/geo-regions-v1`及已存在的任务worktree。存在就继续使用；不存在且当前仓库适合隔离开发时创建此固定分支。必须新建worktree时使用固定路径`/Users/leeyi/project/imboy.pub/_task_worktrees/GEO_REGIONS_V1/geo_regions`，记录origin、branch、baseCommit和实际路径，下一会话按记录复用。不得删除、清理、强制切换或接管其他任务的worktree。
4. 在实际执行树运行`python3 tool/plan_status.py init`（幂等、不清空旧状态），读取status及证据，比较当前代码/数据hash与旧任务输入。旧completed只能在证据仍成立时沿用。代码变化影响旧任务时执行reopen并重新验证；保留原历史。

## 在ZCODE显示任务

如果本会话提供真实任务面板或plan/todo工具，**立即调用实际可用工具**，按tasks.json建立P1-01至P2-06任务，展示标题、依赖、pending/in_progress/blocked/completed状态。随后每次推进同步面板与state。工具可能叫update_plan、TodoWrite或其他名称，先确认可用，不编造工具。

没有原生面板时明确说明此环境不支持该能力，输出带ID的可见清单并持续更新磁盘state；不要声称已操作不存在的面板。一次只推进少量明确任务，用户应能看见当前项、已完成项和具体阻塞。

## 第一节点必须有Demo

从 **P1-01** 开始。先运行和修正交付的`demo/flutter`，以`docs/DEMO_UX.md`验收手机/桌面、明暗、RTL、200%字体、路径、搜索、错误恢复、键盘与读屏；补齐尚缺的loading skeleton及需要的系统文案国际化。

先展示可操作的Flutter Demo及其实际运行证据，再推进后续节点。HTML只是同设计参考，Node行为检查不是浏览器视觉或Flutter验收。当前交付报告中的Flutter NOT RUN必须由你真实执行formatter/analyze/test/build和可用设备验证来消除，不能复制成PASS。

## 分工与资源控制

默认协调者+最多两个worker。P1-02之后按依赖并行P1-03数据、P1-04模型、P1-06资产工具中最多两项；P1-05等前置完成再启动。国家/语言扩展按DATA_WORKPACKAGES只写各自staging。全局schema、pubspec、公共API、source-lock、policy和manifest由单一协调者合并。禁止多worker同写同一文件或每个worker重复下载/扫描全仓。

关键门禁待环境时，继续无依赖的可实施工作，清楚记录blocked子项；不能为了推进依赖图把未验证任务标completed。发现契约冲突先按PRD和真实代码修复，不通过删测试、放宽检查或改写用户需求来刷绿。

## 实现约束

- 主库仅Flutter/Dart SDK runtime；网络/持久化/hash通过注入接口；dev工具Python依赖不计runtime。
- 完整已发布数据可在开发依赖中取得；主包不声明全量Flutter assets。实现`bin/assets.dart`供`dart run geo_regions:assets`使用，按国家×语言生成精确离线资源清单。
- root-inclusive稳定ID路径，地区名称与结构分离；新增语言不修改结构字节；不强制全球三级。
- 保留source质量、默认名quality、版本和许可；production按明确allowlist解析，不能用node.name回退绕过质量过滤。research-seed不是现势权威数据，也不是十国所有节点十语人工完成。
- 加载失败、unknown范围与真实无下级区分；坏资源不破坏有效cache；版本集合原子切换；旧异步请求不覆盖新选择。
- Phase1独立于IMBoy。Phase2读真实三端仓库后做最小接入，保留现有PR #68保存后提交缓存与返回MorePage行为，复用AT-MF06与现有测试；不重做Web MVP、不新建imboyweb。
- P1-08将`config/readiness.json`的`productionSdkExpected`改为true，缺生产包源码/测试时CI必须失败。

## 自动验收与结束条件

每项保存输入commit/hash、改动文件、命令、exit code、日志、输出hash和PASS/FAIL/SKIP/BLOCKED范围。用`plan_status.py start/block/complete/reopen`维护状态；complete传真实存在的证据文件和实际验证命令，状态工具不会替你验证测试成功。

持续修复本任务范围内失败，直到已授权、可执行目标完成。不要把缺设备、账号、源许可证、语言审校或网络权限当PASS；说明具体阻塞与可继续工作。不要要求用户对已确认名称、代码许可、普通实现选择或每个节点重复批准。

可以进行必要的本地分支、实现和验证；保留现有权限与保护。默认交付可审阅变更及发布候选，不自动公开发布pub.dev、生产上线、合并主干或向他人发送消息。若确需新授权，先完成全部可独立工作，再说明准确动作、原因和已准备的结果。

最后给出：任务状态表、实际Demo入口、代码/数据范围、测试和CI链接（只有实际存在才提供）、剩余阻塞、恢复方式、变更摘要。只提供Markdown文档；不要额外生成DOCX/PDF。
