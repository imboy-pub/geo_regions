# IMBoy 独立接入方案 / IMBoy integration

本方案属于Phase 2，不在本次交付中修改IMBoy源码。Source baseline checked on 2026-11-13: `imboy-pub/imboy-flutter` main at `2cee59317de36e2f70420f46dc881b1117b034c9`.

## 1. 已核实行为 / Verified baseline

| File | Existing behavior / 当前行为 | Integration responsibility / 改造责任 |
|---|---|---|
| `lib/page/personal_info/set_region/set_region_page.dart` | 显式parentPath递归；server save成功后persistSelection，统一退出编辑流程 | 保留导航/提交顺序，替换数据与ID身份 |
| `lib/page/personal_info/set_region/set_region_provider.dart` | assets/data/region.json、名称路径、空间拼接、RegionCache | 接入GeoRepository/selection；不再按空格推身份 |
| `lib/page/personal_info/widget/more_page.dart` | 调用changeInfo(field=region,value=string)，成功更新UserRepoLocal | 增加兼容契约后的结构化保存及本地名称回显 |
| `assets/i18n/` | 已有本包列出的十语目录 | 复用slang生成labels，地区名称资源独立 |

These are inspected existing behaviors, not proposed APIs. PR #68 is already present; preserve it. Recheck HEAD and working trees before implementing because this baseline may advance.

源链接 / Immutable references:

- [SetRegionPage](https://github.com/imboy-pub/imboy-flutter/blob/2cee59317de36e2f70420f46dc881b1117b034c9/lib/page/personal_info/set_region/set_region_page.dart)
- [SetRegionProvider](https://github.com/imboy-pub/imboy-flutter/blob/2cee59317de36e2f70420f46dc881b1117b034c9/lib/page/personal_info/set_region/set_region_provider.dart)
- [MorePage](https://github.com/imboy-pub/imboy-flutter/blob/2cee59317de36e2f70420f46dc881b1117b034c9/lib/page/personal_info/widget/more_page.dart)

## 2. 依赖边界 / Dependency boundary

库负责资源协议、解析、索引、名称解析、缓存调度和可选通用UI。IMBoy适配层提供现有HTTP、平台存储、可靠hash verifier、当前locale、labels、主题和业务选择策略。IMBoy保留自己的iOS风格页面、Riverpod和slang；这些不反向进入geo_regions。

The library owns reusable data behavior. IMBoy adapters supply infrastructure and business policy. Preserve the current interface design and state-management choices; do not add IMBoy dependencies to the library.

默认离线配置：国家目录与十语国家名称小包，CN结构与CN zh-Hans/zh-Hant/en语言资源；其他国家结构/语言按需加载。zh-Hant文件存在不等于CN繁中完整，实际缺失继续按质量策略回退。后续可改配置，无须改核心库。

Default offline profile bundles the catalog, ten small catalog-name packs, CN structure and three CN name packs; remaining resources are on demand. The Traditional Chinese seed is sparse and must not be marketed as complete.

## 3. 资料存储与兼容 / Persistence and compatibility

当前已证实的客户端接口仍是字符串region。结构化字段名及后端表结构**尚未核实**；P2-01必须读真实Erlang/API/数据库迁移后决定。下列是兼容目标，不是声称后端已有 `regionSelection` 字段。

The verified client currently saves a string. Inspect the real backend before choosing a new field or migration. A proposed structured selection is a target contract, not an existing API claim.

- 新客户端在服务器支持时保存identity（datasetId/countryCode/dataRevision/pathIds）与旧客户端可显示的legacy string，服务端同一事务提交。
- 服务端验证路径/国家/版本；显示快照只作显示，不作为可信身份。
- 旧客户端只改legacy string时，服务端应重新验证或失效旧结构化selection，不能保留一个与文本矛盾的旧ID。
- 无后端支持时可保留现有字符串流程并在功能开关下实验本地身份，但不得宣称已完成跨设备稳定ID迁移。
- 并发编辑复用现有记录版本/冲突机制；若现API无此机制，记录风险并选择最小兼容变更，不发明已存在的ETag接口。

New clients atomically persist structured identity and a compatible legacy value when supported. Old-client writes must not leave stale structured identities. Server validation and existing conflict semantics remain authoritative.

## 4. 旧资料迁移 / Legacy migration

状态：empty / resolved / ambiguous / unresolved / retired。空值保持空；仅有唯一、可追溯的路径匹配才能自动建立ID。不要按空格拆 `New York` 等名称，不根据“同一个区县名”猜父级，也不要把旧统计码硬当现行行政码。

Keep legacy values and migration status. Only a unique, evidenced path can resolve automatically. Ambiguous, retired or unsupported paths retain their display text and request reselection at an appropriate user interaction. Migrations are idempotent and reversible; repeated runs do not destroy unresolved input.

不确定资料不批量静默改写；迁移日志记录mapping版本、证据和结果，不能含真实账号秘密。数据集seed→production namespace的切换同样是迁移，不是只替换字符串。

## 5. 保存与返回 / Save and navigation

顺序：编辑draft → 校验允许层级 → 禁重复提交 → 调宿主server save → 成功更新账号缓存/selection → 返回MorePage。失败保持draft和当前页面，允许重试。服务端已成功而缓存写失败时，沿用现行为：不能把成功保存伪装成server失败；应刷新/修复本地状态并记录诊断。

Preserve the success boundary already present in PR #68. A locale change only recomputes labels and cannot alter IDs, mark an unchanged identity dirty or trigger a save. Returning to a parent and reopening a child must preserve the full explicit path.

## 6. 多账号、Web与管理端 / Accounts, Web and admin

公开地区文件可共享cache；用户选择必须按账号隔离，登出清理或切换命名空间。Web与原生分别注入存储，主SDK不能直接依赖dart:io。已有Web MVP继续在imboyapp的Flutter Web内完成，不能为地区组件另建imboyweb前端。

The management frontend should display identity through the same versioned contract when needed and retain legacy display compatibility. Backend/admin changes are conditional on inspected requirements, not mandatory rewrites of all three repositories.

现有长任务与worktree必须保留。geo_regions独立仓库可先完成；第二阶段修改跨仓库前先确认所有权和冲突，仅针对地区能力接入，不把群聊多选、OTP优化、客服坐席等相邻任务混入范围。

## 7. 验收与回滚 / Acceptance and rollback

复用AT-MF06和现有Widget回归，再增加独立真实loader/cache/版本测试。至少验证：CN深层路径、GB/FR/IT可变层级、JP非三级、十语/RTL、离线初次失败与缓存恢复、数据损坏、快速切换、保存失败、重复点击、账号切换、旧新客户端互操作和管理端显示。

Record actual device/Web results under P2-05. Missing devices, accounts or backend access are BLOCKED, never PASS. Rollback disables the new reader/writer behind the integration switch while preserving old strings and newly stored structured data; do not delete records to roll back.
