# geo_regions Release Candidate — Phase 1（任务 geo-regions-v1）

日期：2026-11-14 · 状态：**draft，供维护者审阅** · 分支 `task/geo-regions-v1`

本文件汇总 Phase 1 的发布候选证据。按授权边界，本材料不执行 push、GitHub Release、pub.dev 上传或主干合并；全部为本地可审阅产物与命令记录。

## 1. 代码与数据范围

| 项 | 值 | 证据 |
|---|---|---|
| 数据集 | `geo-regions-seed`，manifest `m-00f97c86c14ada75`（121 资源：10 结构 / 100 语言包 / 10 目录包 / 1 国家目录） | Round 0 盘点 121/121 磁盘 hash 一致；`import_data.py --check` 重建一致 |
| 节点 | 4,143（CN 3,430 / JP 48 / KR 18 / US 58 / GB 222 / DE 17 / FR 125 / IT 127 / RU 84 / SA 14） | `round0_inventory.md` §1 |
| 来源 | 36 个锁定源文件（CLDR 49 `7d2b9cb1` / CLDR XML `96e54b27` / modood `2023-06-30 快照`），Unicode-3.0 / WTFPL | `sources/` + `validate --schema` sourceFilesVerified=36 |
| 数据成熟度 | **research-seed**；`humanReviewVerified: false`；production 模式有意拒绝本种子 | `validate --production` 行为 + DP backlog |
| 包版本 | `0.1.0-wip.1`（draft） | CHANGELOG.md |

## 2. 门禁与测试摘要（本地实测）

| 套件 | 结果 |
|---|---|
| Python 数据工具（tests/） | 45/45 OK |
| Dart SDK 数据层 + 加载层 + UI（test/） | 190/190 passed |
| demo/flutter | 11/11 passed |
| HTML 参考行为（test_logic.cjs） | 22 checks PASS |
| `flutter analyze --fatal-infos`（根包/demo/example） | No issues |
| `dart format --set-exit-if-changed` | 0 changed |
| 真 Chrome 交互验收 | P1-01 + P1-07 两份 transcript（深层路径/unknown 语义/竞态/离线恢复/真实数据集） |

## 3. 包体与性能审计

| 产物 | 大小 |
| `pub publish --dry-run` 压缩包 | **1 MB**（3 个有意布局偏离：samples/docs/tests 为数据集仓库结构；server 端验证在 CI 执行） |
| 全离线 payload（full-offline 案例，121 资源） | uncompressed **2,130,387 B** · gzip ≈ **255,922 B** |
| 混合 payload（hybrid-CN 案例） | uncompressed **1,320,132 B**（与 TOOLING.md Python 参考一致） |
| 数据发布 ZIP（data-v2026.11.14 本地重建） | **965,732 B** · sha256 `67728632…e2e3`（含 .sha256 附件） |

## 4. 版本兼容记录

- 最低支持 Flutter：`environment: flutter >=3.47.0`（material_ui/cupertino_ui 要求）；CI 与统一 SDK 决策钉 **3.50.0**（tag → `ab2912035e160d9cad6306df307576da6128ebdb`）。
- IMBoy（Flutter 3.50.0，PR #68 路径已在 main）兼容：SDK 仅要求 Flutter SDK runtime + 注入接口，无版本耦合点；IMBoy 3.41.x 名称的历史字符串迁移属 Phase 2（P2-03）。
- 数据 tag 与代码版本独立（`data-vYYYY.MM.DD[.N]`）；同一 tag 内容不可覆盖（release workflow 从 tag commit 重跑全部 CI 后创建草稿 ZIP Release）。

## 5. 安装 / 升级 / 回滚（SDK 通用）

- **安装**：见 `docs/SDK_INTEGRATION.md`（五步：依赖 → `dart run geo_regions:assets` 生成子集 → pubspec fragment → repository → Picker）。
- **升级（数据）**：新 `data-v*` tag + 更新 bundled manifest；`updateTo` 原子切换，失败保留当前集（stale-coherent 可离线回退）。
- **升级（代码）**：revision 精确匹配拒绝跨版本拼接；不兼容 manifest/资源按 typed errors 明确报错，不静默。
- **回滚**：宿主回退到上一发布集合（bundled manifest 为不可变集合）；缓存键含 revision，旧集合资源不被新版本污染；数据 tag 从不重写。
- **IMBoy 专用灰度/回滚**：Phase 2 P2-06 交付（配置开关 + 旧 region 读取路径回退），本文件不预支。

## 6. CI 与 workflow URL

- workflow 配置已就位（`.github/workflows/ci.yml` 钉 3.50.0、required gate、release-data.yml 不可覆盖 tag）。
- **真实 run URL：待 push 后由 CI 生成**（本授权不包含 push/发布动作）。push 后在 GitHub Actions 页获取 run 链接补录。

## 7. 剩余阻塞（如实，不冒充 PASS）

1. `flutter drive` Chrome 集成测试：dwds `AppConnectionException` 环境 BLOCKED（两轮会话复现）；替代证据 = 真 Chrome transcript + 190+11 测试。
2. iOS/Android 真机运行：未执行（无设备授权记录）。
3. VoiceOver/TalkBack 真会话：未执行；a11y 语义树可用性已客观验证（CDP 快照）。
4. 语言人工审校：未完成（research-seed 定义使然）；DP-01 繁中（4,111 缺口）/DP-02 CN 八语（27,184）/DP-09 provisional 复核（fr 715 / de 714 / it 712）为公开 backlog。
5. P2 级 UI 瑕疵：release 下错误详情显示 minified 异常名。

## 8. 变更摘要（Phase 1 提交序列）

7ef2142 P1-01 demo 验收 → f95254b P1-02 协议固化 → a88d0a6 P1-04 SDK 数据层 → 090a93f P1-06 资产 CLI → e073ae6 P1-05 加载层 → b1a8682 CI 文档对齐 → 5c82926 P1-07 Picker+真实 demo → P1-08（本提交）。
