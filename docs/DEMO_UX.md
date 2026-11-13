# Demo 与 UI/UX 验收 / Demo and UI/UX Acceptance

版本 / Version: 1.0 · 2026-11-13

## 1. 首节点目标 / First milestone goal

**中文：** P1-01 首先交付能实际操作的 Flutter 地区选择 Demo，展示地区选择、国际化、数据可用状态和确认结果。不能等数据管道与生产 SDK 全部完成后才展示界面。演示夹具先支持 UI 评审；后续节点再替换为真实协议、数据与加载器。

**English:** P1-01 delivers an interactive Flutter region picker before the entire data pipeline or production SDK is finished. Deterministic fixtures unblock UI review. Later milestones replace fixtures with the production protocol, dataset and loaders.

本 ZIP 包已提供 / Included in this ZIP:

- `demo/flutter/lib/main.dart`：Flutter 界面与演示状态机 / Flutter UI and demonstration state machine.
- `demo/flutter/lib/fixtures.dart`：10 国少量节点、10 语界面标签 / Small fixtures for ten countries and primary labels in ten languages.
- `demo/flutter/test/widget_test.dart`：5 项关键 Widget 测试源码 / Five focused Widget test cases.
- `demo/flutter/bootstrap.sh`：安全生成 Web 平台目录 / Web platform generation without replacing authored files.
- `demo/web_preview/index.html`：相同设计方向的独立 HTML 交互参考 / Self-contained interactive HTML design reference.
- `demo/web_preview/test_logic.cjs`：Node 标准库行为检查 / Dependency-free behavior checks.

## 2. 设计方向 / Design direction

| 决策 / Decision | 设计与目的 / Design and purpose |
|---|---|
| 色彩 / Color | 冷灰背景、白色卡片、紫色主操作、绿色离线状态；深色使用独立表面层次。/ Cool neutral background, white cards, purple actions and green offline status; dark mode retains clear surface hierarchy. |
| 主信息 / Primary information | 国家 → 当前层级 → 完整路径 → 确认操作，阅读顺序稳定。/ Country, current level, full path and confirmation remain in a predictable reading order. |
| 桌面 / Desktop | ≥850 px：左侧国家导航，右侧地区选择与确认结果。/ At 850 px and above, country navigation sits beside the picker and result. |
| 手机 / Mobile | <850 px：横向国家选择栏与纵向卡片，不压缩为三列滚轮。/ Below 850 px, use horizontal country choices and stacked cards. |
| 字体与图标 / Typography and icons | 系统字体、Flutter 内置图标；HTML 使用内联 SVG。没有远程字体或图片。/ System fonts, built-in Flutter icons, and inline SVG for HTML; no remote font or image assets. |
| 层级表达 / Hierarchy | 可点击面包屑、返回上一级、完整 ID 路径。/ Clickable breadcrumbs, one-level back, and complete stable-ID path. |
| 选中与保存 / Selection and confirmation | 浏览路径是草稿；确认后才更新结果快照；放弃修改需确认。/ Navigation edits a draft; confirmation updates the result snapshot; discarding asks for confirmation. |
| 非完整数据 / Incomplete data | 无下级示例显示“已到示例数据最深层级”，不声称真实行政叶节点。/ Exhausted fixtures say “Deepest fixture level reached,” without claiming an actual administrative leaf. |
| 可用状态 / Availability | 随包、模拟在线、已缓存是不同状态；失败和无匹配结果使用不同文案。/ Bundled, simulated online and cached are distinct; errors are distinct from empty search results. |

品牌主标题 / Hero: “每个地方，都有你的语言。” / “Every place. Your language.”

默认主操作 / Primary action: “确认选择” / “Confirm selection”.

## 3. 必须观察到的行为 / Required observable behavior

| ID | 场景 / Scenario | 通过标准 / Pass condition |
|---|---|---|
| UX-01 | 深层选择 / Deep selection | 中国→广东→深圳→南山，完整路径包含全部祖先；回到广东不残留深圳/南山。/ The full ancestry is retained; returning to Guangdong clears deeper draft nodes. |
| UX-02 | 语言切换 / Language switch | 10 种语言可切换；已有地区 ID 和确认结果 ID 不变。缺失地区译名按原生名回退。/ Ten primary UI languages; IDs remain stable and missing fixture names fall back to native names. |
| UX-03 | RTL | 阿语界面方向镜像，路径 ID/JSON 保持 LTR；输入和按钮不被截断。/ Arabic mirrors layout while IDs/JSON remain LTR; controls remain readable. |
| UX-04 | 未缓存且离线 / Offline without cache | 选择未加载国家出现错误与重试；不会显示“没有下级地区”。/ An uncached country shows an error and retry, not a terminal-level state. |
| UX-05 | 已缓存且离线 / Offline with cache | 在线模拟加载成功后，切到离线仍能选该国家。/ A previously loaded fixture is usable offline. |
| UX-06 | 请求竞争 / Request race | 快速点击日本再中国，迟到的日本结果不会覆盖中国状态。/ A late response for Japan cannot replace a newer China selection. |
| UX-07 | 搜索 / Search | 名称、原生名、ID 可查询；无结果有明确状态；清除后恢复当前层级。/ Search matches names, native names and IDs; empty results are explicit and clearing restores the current level. |
| UX-08 | 草稿与确认 / Draft and confirmation | 点击地区不自动保存；确认输出新的稳定 ID 结果；放弃能恢复已确认结果。/ Browsing does not auto-save; confirmation emits a new stable-ID selection; discard restores it. |
| UX-09 | 响应布局 / Responsive layout | 390×844、768×1024、1280×900 无横向页面溢出；国家栏可横向滚动。/ No page overflow at these viewports; the mobile country strip scrolls independently. |
| UX-10 | 可访问性 / Accessibility | 键盘可遍历控件，焦点可见；点击目标至少 44 px；200% 文字缩放仍能完成选择。/ Keyboard traversal, visible focus, targets of at least 44 px, and usable selection at 200% text scaling. |
| UX-11 | 深浅主题 / Themes | 主要文字、输入、错误、选中状态和禁用状态在两种主题都可辨认。/ Text, input, errors, selection and disabled states remain distinguishable in both themes. |
| UX-12 | 结果契约 / Result contract | 原型的 `datasetId=geo-regions-ui-fixture`，不可误当真实地区主键保存入 IMBoy。/ Fixture IDs are never persisted as production IMBoy regions. |

## 4. 已验证与待验证 / Verified and pending

2026-11-13 本轮执行证据 / Evidence from this delivery run:

| 检查 / Check | 状态 / Status | 范围与限制 / Scope and limitation |
|---|---|---|
| `bash -n demo/flutter/bootstrap.sh` | PASS | Shell 语法；没有启动 Flutter。/ Shell syntax only. |
| `node demo/web_preview/test_logic.cjs` | PASS, 22 checks | 十语标签、祖先路径、RTL 状态、确认去重、搜索清除、返回、放弃/恢复、模态焦点循环/Escape、深色状态、重绘焦点保持、离线/重试/缓存/竞态等。使用 DOM 替身，不是真实浏览器点击或布局验证。/ Labels, ancestry, RTL, deduplicated confirmation, search/clear/back, discard/restore, modal focus events, dark state, focus restoration and offline/error/cache/race behaviors using a DOM substitute; not real-browser input or rendering. |
| Dart format / analyze | NOT RUN | 本环境没有 `flutter` 或 `dart`，需要现场格式化并提交格式改动。/ No local Flutter/Dart SDK; formatting changes must be made before commit. |
| 5 个 Flutter Widget 测试 / Flutter Widget tests | NOT RUN | 已交付测试源码，不等于测试通过。/ Test source is included, not a passing execution. |
| Flutter Web release build | NOT RUN | 必须在 P1-01 现场执行。/ Required before P1-01 completes. |
| Chromium 浏览器 / Chromium browser | BLOCKED | 已尝试；系统 Chromium 无法创建本地 socket，报 `Operation not permitted`。同命令的提权请求被自动审批策略拒绝；没有继续绕过。/ Startup failed because a local socket was denied; the escalation attempt was automatically rejected. |
| 正式云浏览器 / Supported cloud browser | BLOCKED | 根流程直接打开本地 `file:///` 原型，被明确的 URL 协议安全策略拒绝；已停止，不更换 URL 变体、代理或间接路由绕过。/ Direct opening of the local `file:///` prototype was explicitly denied by URL-protocol security policy; no alternate URL or routing workaround was attempted. |
| 视觉、文字缩放、屏幕阅读器 / Visual, scaling, screen reader | PENDING | Node 状态测试不能证明这些通过。/ Model checks do not verify these properties. |

父执行流程如使用正式可用的浏览器工具补充验收，应在最终交付报告中记录新的实际结果；本节保留本原型制作阶段的原始证据，不把它改成“Flutter 已通过”。

If the parent workflow completes additional browser verification through an available browser tool, record that additional evidence in the final delivery report. It does not establish Flutter execution.

## 5. 现场验收步骤 / Local acceptance steps

```bash
cd /Users/leeyi/project/imboy.pub/geo_regions/demo/flutter
bash bootstrap.sh
dart format lib test
flutter analyze --fatal-infos
flutter test
flutter build web --release
flutter run -d chrome
```

**中文：** 完成 UX-01 至 UX-12，记录 Flutter 版本、提交 SHA、命令退出码、待修缺陷。至少观察中文手机界面、英文桌面界面、阿语 RTL 和深色状态。若出现溢出、加载竞争、结果 ID 错乱，修复后再标记 P1-01 完成。无需为每个像素写测试；状态与数据契约用确定性测试，布局用少量关键视图验收。

**English:** Complete UX-01 through UX-12 and record the Flutter version, commit SHA, command exit codes and unresolved defects. Inspect Chinese mobile, English desktop, Arabic RTL and dark mode. Fix overflow, races or corrupted IDs before completing P1-01. Use deterministic tests for state/contracts and a small set of representative views for layout review.

## 6. 后续生产集成边界 / Production integration boundary

本原型明确暂未实现 / Deliberately absent from this prototype:

- 真实 CDN、SHA-256、Manifest 验证、持久缓存、过期策略。/ Real CDN, integrity/Manifest validation, persistent cache and expiry.
- 数据集全部节点与全部地区译名。/ Complete region trees and full regional translations.
- 生产 `GeoRegionsRepository` 接口或 API 兼容承诺。/ A production repository API or API compatibility promise.
- IMBoy 用户资料更新与路由返回。/ IMBoy profile persistence and navigation.
- 完整 Flutter 平台构建目录与已编译安装包。/ Full generated platform directories and compiled binaries.

**中文：** 生产接入时保持界面结构，将演示状态替换为 SDK 状态；按照正式协议重做语言回退、版本匹配和加载策略。IMBoy 的保存成功才返回上一页，保存失败保留草稿；该业务导航行为在 Phase 2 验收。选择深度由宿主策略控制，本原型允许选择国家与中间节点，不把演示最深层当成“有效叶子”。

**English:** Retain the visual structure while replacing simulated state with the SDK. Implement fallback, version compatibility and loading according to the production protocol. IMBoy navigates back only after successful persistence and retains the draft on failure; verify that business behavior in Phase 2. Selection depth belongs to the host policy; the prototype permits countries and intermediate nodes, and fixture depth is not evidence of a valid administrative leaf.


## 7. 人工复查与未满足项 / Manual review and remaining gaps

**中文：** 以下是源码复查结论，不能替代编译和现场运行。修复了几个可识别的问题：品牌与路径状态改为可换行；离线控件使用弹性文字区；手机国家栏高度随文字缩放；国家选中态和加载状态补充语义；相同确认结果禁止重复提交。HTML 增加重绘焦点保持、模态背景 inert、焦点循环与 Escape、主题切换状态、44 px 清除按钮。旧请求测试明确等待旧计时器完成，语言选项使用键定位并在滚动后等待布局。

**English:** This is a source review, not compiler or runtime evidence. Identified risks were addressed: wrapping brand/path rows, flexible offline labels, text-scaled country-strip height, selected/loading semantics and duplicate-confirmation suppression. HTML now retains focus during redraw, isolates modal backgrounds, handles focus cycling/Escape, exposes theme state and gives clear buttons 44 px targets. Race tests advance past the stale timer; locale tests locate keyed options and wait for layout after scrolling.

| PRD 要求 / PRD requirement | 当前原型 / Current prototype | 第一节点或后续必须完成 / Remaining work |
|---|---|---|
| 十语完整体验 / Ten-language experience | 主要自有文案与国家名有十语表，地区 fixture 缺译回退原生名。/ Ten-language custom labels and country names; sparse fixture names use native fallback. | Flutter 的内建 `MaterialLocalizations` 明确固定 SDK 默认英文，以避免缺少代理异常；系统文字菜单和框架辅助文案尚未全语本地化。宿主国际化接入和译文评审仍待完成。/ Built-in Material localizations deliberately use supported English defaults. System menus/framework copy and linguistic review remain incomplete. |
| 手机/桌面与 200% 文字 / Responsive layout and 200% text | 已做适配代码并加入法语 200% Widget 测试源码。/ Adaptive code and a French 200% text Widget test are included. | 测试未运行，没有真实布局通过证据；需要 390/768/1280 px、RTL 和放大文字现场检查。/ Unrun tests do not establish layout success; inspect target widths, RTL and enlarged text. |
| 全流程键盘与读屏 / Keyboard and screen reader | 使用原生按钮、焦点、selected/liveRegion 与 HTML 语义；Node 仅执行事件处理器。/ Native controls and selected/live-region semantics; Node exercises handlers only. | 尚未使用真实浏览器键盘、TalkBack、VoiceOver 或桌面读屏验收，层级朗读和焦点顺序仍需实际检查。/ Real keyboard and screen-reader validation, hierarchy announcements and focus order are pending. |
| 加载占位 / Loading placeholder | 旋转进度与加载文案；错误与无结果分开。/ Progress indicator and loading copy; distinct error and empty states. | 目前没有独立骨架屏；若采用 PRD 英文版的 skeleton 目标，需在 P1-01 补齐并测试。/ A dedicated skeleton is not implemented; add it if required by the PRD skeleton target. |
| 防重复保存 / Duplicate-save protection | 原型确认同步生成结果，相同路径确认后禁用再次提交。/ Synchronous confirmation disables re-submission of unchanged selection. | 没有真正服务端保存。异步保存状态、失败保留、成功返回和账号切换属于生产接入验收。/ Async persistence, failure recovery, success navigation and account switching remain production-integration work. |
| 数据/缓存/版本 / Data, cache and versions | 内存 fixture 与模拟网络，独立演示命名空间。/ In-memory fixtures and simulated network in a separate namespace. | 不能据此证明 SHA-256、持久缓存、真实十国数据覆盖或 SDK 完成。/ This does not establish integrity validation, persistent caching, production coverage or SDK completion. |

P1-01 当前仍应为 **待执行/待验收**，不得因为本 ZIP 已带源码、HTML 和 Node 检查就标记完成。

P1-01 remains **pending execution/acceptance**; delivered source, HTML and Node checks are insufficient to mark it complete.
