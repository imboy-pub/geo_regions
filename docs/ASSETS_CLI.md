# ASSETS CLI — 离线资源生成与宿主接入（P1-06）

`bin/assets.dart` 是 geo_regions 的宿主友好生成入口：从**已解析的包根**（不是仓库绝对路径，
也不是硬编码 pub cache 路径）读取 `data/`，按配置选出离线子集，并产出可直接接入宿主
pubspec 的 bundle。行为对齐 Python 黄金参考 `tool/geo_data.py::build_offline`（见下文
[与 Python 工具的关系](#与-python-工具的关系)）。

> 定位声明：本 CLI 生成的是**开发/构建期产物**（bundle、审计报告、pubspec 片段）。
> 运行时校验链（manifest SHA-256 验证、解析、缓存、远程 verifier）由 SDK repository
> 负责（`lib/geo_regions.dart` 导出的 load 层，CONSUMER_CONTRACT §5）。

## 用法 / Usage

```bash
# 规范入口（在宿主工程或本仓任意已 pub get 的目录下运行）
dart run geo_regions:assets --config <path> --out <dir> [--replace]

# 等价直跑形式（跳过 pub 解析，CI 里更快）
dart run <repo>/bin/assets.dart --config <path> --out <dir> [--replace]
```

| 参数 | 说明 |
|---|---|
| `--config <path>` | 必填。资产配置 JSON（形状见 [`config/assets.schema.json`](../config/assets.schema.json)）。 |
| `--out <dir>` | 必填。输出 bundle 目录；其父目录不存在时会自动创建。 |
| `--replace` | 可选。仅当 `--out` 已存在且带有 `.geo_regions_generation` 标记时才允许替换。 |
| `-h` / `--help` | 显示用法。 |

**包根解析**：CLI 读取**当前工作目录**的 `.dart_tool/package_config.json`，找
`name == "geo_regions"` 的条目，`rootUri`（相对路径按 package_config v2 规范相对
package_config 文件本身解析）得到包根，数据读自 `<包根>/data/`。因此：

- 在本仓内运行 → 解析到本仓；
- 在把 geo_regions 作为依赖的宿主工程运行 → 解析到 pub cache 中已安装的包；
- 在自带的 `.dart_tool/package_config.json` 指向任意副本的目录运行 → 解析到该副本
  （测试即用此机制验证"从已安装包生成"）。

找不到 package_config 或未解析 geo_regions 时以 exit 2 报错，绝不回退到仓库绝对路径。

## 配置 / Config

配置是普通 JSON，字段与 `config/assets.schema.json` 一致；本 CLI 按其语义手工校验
（未知字段拒绝、`structures` 元素必须匹配 `^[A-Z]{2}$`、`locales` 键必须是
`structures` 的子集、数组去重）。三个轴彼此独立——**新增一个 locale 永远不会改变
structure payload 的选择**（这也是把 `locales` 设计为 per-country map 的原因）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `profile` | string，可选 | 人类可读的 profile 名，写入 `report.json` 供审计。 |
| `structures` | `["CN", ...]` | 离线内置的国家结构（`data/regions/{CC}.json`）；空数组 = online-only。 |
| `locales` | `{"CN": ["zh-Hans", ...]}` | 每国自带哪些语言的地区名包（`data/i18n/{locale}/{CC}.json`）；键必须 ⊆ `structures`。 |
| `catalogLocales` | `["zh-Hans", ...]` | 离线内置的国家目录名包（`data/catalog_i18n/{locale}.json`；很小，与 structures 无关）。 |

`countries.json`（国家目录本体）始终包含。三个样例：

- [`config/assets.full-offline.json`](../config/assets.full-offline.json) — 十国结构 ×
  十语名包全离线：无网/内网/离线部署场景。
- [`config/assets.hybrid-cn.json`](../config/assets.hybrid-cn.json) — 只内置 CN 结构与
  简繁英名包（catalog 十语仍内置）：国内首发、其余国家走在线资源的混合场景。
- [`config/assets.online-only.json`](../config/assets.online-only.json) — structures 为空，
  只带 `en` 目录名包：payload 全部走在线下载 + 缓存，bundle 仅剩 descriptor。

## 产物 / Artifacts

对选中的资源，`--out` 得到（保持 `data/` 相对路径结构）：

| 文件 | 内容 |
|---|---|
| `<选中 payload>` | 选中资源的逐文件拷贝（`countries.json` 必含；未选资源**不落地 payload 文件**）。 |
| `manifest.json` | **子集 manifest**：`{protocolVersion, datasetId, revision, resources}`，只含选中条目（path/kind/revision/sha256（全文件字节）/bytes + countryCode/locale/compatibleStructureRevision/compatibleCatalogRevision），按 path 排序；`revision` 是对选中条目重新计算的 `m-` revision。 |
| `registry.json` | **全量 descriptor 清单**：`data/manifest.json` 的全部 121 条 descriptor，每条加 `bundled: true/false` 标记；**不含任何未选资源的 payload 内容**。`revision` 继承自 `data/manifest.json`（registry 是描述清单，不是 manifest，不伪造 `m-` 链）。 |
| `assets.fragment.yaml` | **精确 pubspec asset 条目**：逐文件列出（含 `countries.json`/`manifest.json`/`registry.json`），**绝不用目录行**——Flutter 的目录声明不会递归覆盖所有子目录（PRD §7.3）。 |
| `report.json` | 审计：per-file bytes/sha256/gzipBytes、总计 uncompressedBytes/gzipBytes（dart:io `gzip.encode` 逐文件估计）、profile、生成时间（UTC ISO8601）、结构 revision 集合、catalog revision。 |
| `.geo_regions_generation` | 生成标记；`--replace` 的保护凭据（见下文安全语义）。 |

### assets.fragment.yaml 的接入方式

每条形如 `- "packages/geo_regions/data/regions/CN.json"`。Flutter 构建时
（flutter_tools `_resolvePackageAsset`）会把宿主 pubspec 里的
`packages/<pkg>/<path>` 条目按 package_config 解析到**已安装包的文件**，因此：

1. **推荐（包内数据直取）**：payload 留在 geo_regions 包内（`data/` 随包分发为普通
   文件，PRD §7.1），宿主把 fragment 的条目逐行合并进**已有**的 `flutter:` 块
   （不要创建第二个 `flutter:` 根；也不要把整个 `data/` 声明为 assets）。
2. **vendor 变体**：若宿主把 `--out` 的 bundle 拷贝到自己仓库的某个目录，把 fragment
   行里的 `packages/geo_regions/data` 前缀改成实际目的地（如 `assets/geo_regions`）
   即可——fragment 是普通 YAML 行，无其它耦合。

注意第 1 种方式下 `manifest.json`/`registry.json` 两条指向包内 `data/` 的同名文件；
bundle 里生成的是**子集 manifest**。宿主若采用 vendor 方式打包 bundle，条目自然指向
vendor 后的子集 manifest；若纯按包内路径接入，应以 vendor/拷贝的方式让子集
manifest 覆盖进宿主实际声明的位置。运行时"哪份 manifest 是 bundle 的真相"由宿主的
资产声明决定，SDK 按其加载到的 manifest 校验（缺失/多余 payload 会在完整性链上暴露）。

### 构建前接入流程

`pub get` 不是任意生成脚本的执行钩子（PRD §7.4）。宿主应把生成命令放在本地构建与 CI
构建**之前**显式执行，例如：

```bash
dart run geo_regions:assets --config tools/geo_assets.config.json --out build/geo_assets
# 将 assets.fragment.yaml 条目合并进宿主 pubspec 后再 flutter build / flutter run
```

**缺失或陈旧配置直接失败**（不自动修复）：

- 配置引用不存在的国家/locale → exit 3（`selected resource missing: ...`）；
- locale 包的 `compatibleStructureRevision` 与对应 `regions/{CC}.json` 的 revision
  **不相等** → exit 3（`stale config: ...`）；catalog 同理对照 `countries.json`
  revision；
- 文件字节与 `data/manifest.json` 的 sha256/bytes 不符（损坏/手工改动）→ exit 3。

## 退出码 / Exit codes

| 码 | 含义 |
|---|---|
| `0` | 成功。 |
| `1` | 意外失败（含生成产物自检失败）。 |
| `2` | 配置/用法/环境前置错误：参数缺失或未知、config 形状非法、package_config 缺失、geo_regions 未解析。 |
| `3` | 资源缺失/陈旧/损坏：selected resource missing、stale config、stale data manifest、corrupt resource。 |
| `4` | 输出安全拒绝（见下文）。 |

stderr 均给出具体原因（哪个字段、哪个路径、期望值 vs 实际值）。

## 安全语义 / Safety

对齐 Python `guard_output`：

- **symlink 防护**：`--out` 及其祖先链上出现任何 symlink 即拒绝（exit 4）。macOS 上
  `/var` 是 symlink，因此脚本里请传 `pwd -P` 解析后的真实路径。
- **路径穿越**：输出路径禁止 `.`/`..` 组件；locale 标签校验为单一安全路径段
  （`^[A-Za-z0-9]{2,8}(-[A-Za-z0-9]{1,8})*$`，另满足 schema 的 minLength 2），
  不可能构造 `../` 或绝对路径。
- **保护区**：`--out` 不得等于文件系统根、用户 home、包根；不得落在包的
  `data/`、`sources/`、`tool/`、`schemas/`、`docs/` 内；不得是包根的祖先（exit 4）。
- **重跑保护**：`--out` 已存在且未带 `--replace` → 拒绝；带 `--replace` 但缺
  `.geo_regions_generation` 标记（非本工具生成的目录）→ 拒绝（exit 4）。
- **失败保旧**：全部校验（配置、资源、哈希、陈旧检测、输出防护）通过后才写盘；
  生成先写入 `--out` 父目录下的临时 staging 目录，再原子 rename 替换；替换失败时
  回滚恢复旧 bundle，**失败场景下旧产物永远原样保留**。

## 与 Python 工具的关系

`tool/geo_data.py`（`build_offline` / `guard_output` / `manifest_value`）是黄金参考，
本 CLI 与其行为对齐的点是：子集 manifest 形状与 `m-` revision 算法、registry=
全量 descriptor、fragment 的逐文件条目与头部注释、symlink/穿越/保护区拒绝、
标记式 replace 语义、staging 原子替换。

有意差异（Dart CLI 的宿主友好取舍）：

- 标记名固定为 `.geo_regions_generation`（Python 参考用 `.geo_regions-generated`）；
- **不拷贝** `licenses/`、`docs/` 的 notices 文件（Python offline 会带 notices/；许可
  文本的分发由包本体与发布流程负责，host bundle 不重复打包）；
- 新增 `report.json` 审计（per-file sha256 + gzip/uncompressed 大小，PRD §7.6 的
  发布大小测量入口）与 `registry.json` 的 `bundled` 标记；
- 无 `--asset-prefix`/`--dry-run`（fragment 前缀固定为 `packages/geo_regions/data`，
  vendor 场景直接改前缀；dry-run 用 exit code 与 stderr 即可观察）；
- 包根来自当前目录的 package_config 解析，而非 `--root` 参数。

数据治理：本 CLI 只读 `data/`，绝不修改、绝不自动"修复"陈旧配置；数据更新仍走
`tool/import_data.py` + `tool/generate_manifest.py` 的发布流程。
