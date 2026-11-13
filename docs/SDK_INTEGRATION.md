# SDK 集成指南 / SDK Integration Guide

版本 / Version: 1.0 · 2026-11-14 · 任务 / Task: `geo-regions-v1` P1-07

本文面向宿主（含 IMBoy Phase 2 预留）说明 geo_regions SDK 的轻依赖接入：
公共 API 面、Picker 状态矩阵、离线/混合/在线三种模式与远程注入要求。
协议细节见 [PROTOCOL.md](PROTOCOL.md)；消费者契约见
[CONSUMER_CONTRACT.md](CONSUMER_CONTRACT.md)；CLI 见
[ASSETS_CLI.md](ASSETS_CLI.md)。本文件只写 SDK 通用接入；IMBoy 的账号/
导航/缓存隔离属于 Phase 2（P2-02）。

---

## 1. API 面 / API surface

全部公共类型从 `package:geo_regions/geo_regions.dart` 导出，运行时仅依赖
Flutter/Dart SDK（GR-12：无第三方 runtime 包，无 dart:io）。

| 层 | 类型 | 作用 |
|---|---|---|
| 数据 | `GeoRegionsRepository` | 编排 cache → bundled → remote 的加载、SHA-256 验证、去重、generation token、原子 manifest 切换 |
| 数据 | `GeoManifest` / `GeoManifestEntry` | 发布集合的解析身份；宿主自行解析（子集 manifest 或 registry descriptor 均可） |
| 加载 | `GeoResourceLoader` / `GeoCacheStore` / `GeoHashVerifier` / `GeoBytes` / `GeoCacheKey` | 注入式宿主契约（CONSUMER_CONTRACT §5） |
| 查询 | `GeoRegionIndex` / `geoSearch` / `GeoNameResolver` | 路径索引、搜索、名称解析（质量门控 + locale 链） |
| 选择 | `buildGeoSelection` / `validateGeoSelection` | draft 构建与语义校验（PROTOCOL §8） |
| UI | `GeoRegionPicker` | 默认地区选择 UI（本文 §2） |
| UI | `GeoRegionDataSource` / `GeoRepositoryDataSource` | Picker 的数据入口接口与仓库默认实现 |
| UI | `GeoPickerLabels` / `GeoPickerTheme` | 文案（十语默认表）/ 视觉 token |
| UI | `GeoSelectionPolicy` / `GeoPickerItem` / `GeoPickerAvailability` | 选择策略 / 展示行 / 可用性徽章 |

**解耦原则**：Picker 只消费 `GeoRegionDataSource`（`loadCountries` /
`openCountry` / `loadChildren` / `search` / `resolveSelection` /
`resolveLabels` / `availabilityOf`）。宿主可以：
- 直接用默认的 `GeoRepositoryDataSource`（仓库驱动）；
- 或者自己实现该接口（测试、预览、代理后端），`resolveSelection` 内部用
  `buildGeoSelection` 保证选择值符合协议；
- UI 完全替换时通过 `rowBuilder` / `countryBadgeBuilder` / `labels` /
  `theme` 定制默认 UI，而不必触碰数据层。

## 2. GeoRegionPicker

```dart
GeoRegionPicker(
  dataSource: dataSource,            // §1 的数据入口
  displayLocale: 'zh-CN',            // 名称解析 locale（走别名表 zh-CN→zh-Hans）
  countryCode: 'CN',                 // 可选：宿主持有国家切换时钉住；null = 内置国家首屏
  policy: GeoSelectionPolicy.allowIntermediate,
  labels: GeoPickerLabels.forLocale('zh-CN'),       // 可覆写单条文案
  theme: GeoPickerTheme.fromTheme(Theme.of(context)), // 可省略
  onConfirmed: (GeoSelection draft) { /* 宿主提交事务 */ },
  onCountryChanged: (cc) { /* 内置首屏模式下的国家变化回调 */ },
  expandBody: false,                 // true = 内部滚动并填满高度；false = shrink-wrap 嵌入宿主滚动视图
)
```

### 选择策略 / selection policy

| 策略 | 可确认目标 | 说明 |
|---|---|---|
| `countryOnly` | 仅国家（路径长度 1） | 中间节点展示但锁定，不可进入 |
| `allowIntermediate` | 国家 + 任意已知覆盖节点 | `unknown` 覆盖节点不可确认（`requireKnownCoverage` 语义，AT-11） |
| `requireLeafWithinDeclared` | 仅声明叶（`complete` 且无列出子级） | `unknown`/`partial`/有子级的节点均不可确认；国家根始终可确认（PROTOCOL §8 明确国家级选择合法） |

策略同时在 UI 层（确认按钮禁用 + 锁图标）与数据层
（`resolveSelection` 抛 typed error）双重执行。

### 状态矩阵 / state matrix

| 状态 | 呈现 | 语义 |
|---|---|---|
| loading | 骨架屏 + live region「正在加载…」 | 国家/层级数据请求中 |
| loaded | 行列表（子级数量>0） | 当前层级已就绪 |
| error + retry | 错误面板 + 「重试」+ typed 错误码 | 传输失败/断网/404/完整性不符/解析失败（CONSUMER_CONTRACT §2 分类，不合并为空 children） |
| bundled | 「随包离线」徽章 | 该国家由随包资产服务 |
| cached | 「已缓存」徽章 | 该国家已成功加载并被缓存，离线可用 |
| remote | 「在线」徽章 | 该国家需远程获取，离线即错误 |
| searchEmpty | 「没有匹配的地区」+ 提示 | 搜索无命中（与错误、与"无子级"三者互异） |
| noChildRegions | 「数据未包含下级地区」 | 声明覆盖 complete 且无子级 |
| coverageUnknown | 「数据范围未知」（live region） | `childrenStatus=unknown`：**不冒充"已到最末级"**（AT-11） |
| confirming | 确认按钮转圈 | `resolveSelection` 进行中，防重复确认 |
| dirty / confirmed | 「尚未确认」徽章 / 禁用确认 | 草稿与最近确认快照不同 / 相同（防重复提交） |
| discard | 确认对话框 → 恢复快照 | 放弃恢复最近确认的路径与层级 |

无障碍：全部控件可经 Semantics 触达；加载/错误/覆盖未知为 live region；
行高 ≥44 px；稳定 ID 行在 RTL 布局内保持 LTR（UX-03/10）。

### draft → 宿主提交（PROTOCOL §8）

Picker 只产出 draft（`onConfirmed`），**不**自行持久化。宿主顺序：
1. `onConfirmed(draft)` → 提交后端（宿主事务）；
2. 成功 → 更新账号缓存并退出；失败 → 保留草稿可重试；
3. 换显示语言不得改变 selection identity（`displaySnapshot` 仅展示）。
缓存（`GeoCacheStore`）只放公开资源，与账号选择严格分离。

## 3. 三种数据模式 / offline, hybrid, online

由 assets CLI 的配置决定离线子集，宿主按需组合三个注入点：

| 模式 | bundledLoader | remoteLoader + verifier | 典型配置 |
|---|---|---|---|
| 全离线 | `GeoAssetBundleLoader`（全量 bundle） | 不注入 | [`config/assets.full-offline.json`](../config/assets.full-offline.json) |
| 混合（国内首发） | 子集 bundle（CN + 目录） | 可选 | [`config/assets.hybrid-cn.json`](../config/assets.hybrid-cn.json) |
| 在线为主 | descriptor-only bundle 或不注入 | 必配 | [`config/assets.online-only.json`](../config/assets.online-only.json) |

离线子集生成与 pubspec fragment 合并见
[ASSETS_CLI.md](ASSETS_CLI.md)；`example/` 是最小可运行样例，
`demo/flutter` 是完整演示（hybrid CN 随包 + 模拟 CDN + 全部状态）。

宿主解析 manifest 的两种来源：
- **子集 manifest**（`--out` 里的 `manifest.json`）：只声明离线子集，
  适合纯离线宿主；
- **全量 descriptor**（`registry.json`，121 条全量 descriptor + `bundled`
  标记）：宿主剥离 `bundled` 字段构造 `GeoManifest`，配合远程 loader 服务
  其余资源（demo 与 example 均演示此形态）。任何未声明资源的请求都会
  得到 typed `notFound`。

## 4. 远程模式注入要求 / strict remote mode

**强制前置（AT-09）**：`GeoRegionsRepository` 在提供 `remoteLoader` 但未
提供 `verifier` 时直接抛 `configurationError`，绝不静默跳过校验。远程链路
的完整要求：

```dart
final repository = GeoRegionsRepository(
  manifest: manifest,                       // 全量身份（含未离线资源）
  remoteLoader: hostHttpLoader,             // 宿主 HTTP 栈；失败抛 GeoNetworkError/GeoNotFoundError
  remoteBase: Uri.parse('https://cdn.example.com/geo/v1/'),
  verifier: hostSha256Verifier,             // 长度 + SHA-256，在 JSON 解码之前（AT-08）
  store: hostCacheStore,                    // 原子持久写由实现负责
);
```

- loader 必须按 manifest 相对路径取回**解码后**字节，404 →
  `GeoNotFoundError`，传输失败 → `GeoNetworkError`，两者不得合并；
- repository 在解码前做长度校验，再交给 verifier 做 SHA-256
  （`geoSha256Hex` 即库内实现，可直接用于 verifier）；
- 验证+解析成功才写缓存（AT-08：坏下载永不落盘）；
- 同一身份的并发请求只触发一次底层加载（GR-05），旧请求被 generation
  token 丢弃（AT-07）；
- 换版本走 `repository.updateTo(newManifest)` 原子切换；失败保持
  stale-coherent 并置 `isStale`（AT-10）。

**请求纪律（GR-04/AT-06）**：打开某国家只请求该国家的 structure/locale
资源；catalog 与已加载结构复用缓存。demo 的 CDN 请求日志面板和
`test/ui/remote_origin_test.dart` 的服务端日志断言即验此语义。

## 5. 命名与品牌边界（GR/AT-15）

SDK 主包（lib/）及其默认 UI 不含任何宿主产品名；`GeoPickerLabels` 十语
默认表、状态文案与错误呈现全部可被宿主覆写。宿主接入时自行提供品牌层
（标题、导航、保存文案）。

## 6. IMBoy 预留点（Phase 2 才做）

- 用 IMBoy 已有 HTTP/缓存基础设施实现 `GeoResourceLoader`/`GeoCacheStore`
  （P2-02，不为此引入新网络框架）；
- 账号隔离：公开资源缓存与账号资料缓存分离；账号切换不得串选择值；
- locale aliases 对接 IMBoy 界面语言（CONSUMER_CONTRACT §3）；
- IMBoy 的「保存成功才返回」导航行为在 P2 验收；
- Web 端宿主存储适配（IndexedDB 等）按同一注入契约实现。
