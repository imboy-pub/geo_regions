# 消费者契约 / Consumer Contract

版本：1.0 · 日期：2026-11-13 · 任务：`geo-regions-v1` P1-02

本文件固化 [PROTOCOL.md](PROTOCOL.md) 面向宿主/消费者的可执行契约：宿主接口形状、错误分类、locale 别名表、质量默认值、兼容性与弃用策略。协议规范本身以 PROTOCOL.md 与 `schemas/` 为准；本文不引入新语义，只做收口与实现指引。

## 1. 六类资源与 Schema（冻结）

| 资源 | Schema | 身份/兼容键 |
|---|---|---|
| 国家目录 `data/countries.json` | `schemas/countries.schema.json` | datasetId + catalog revision（`c-` 前 16 hex） |
| 目录名称 `data/catalog_i18n/{locale}.json` | `schemas/country-names.schema.json` | locale + 精确 `compatibleCatalogRevision` |
| 地区结构 `data/regions/{CC}.json` | `schemas/structure.schema.json` | country + structure revision（`s-`） |
| 地区译名 `data/i18n/{locale}/{CC}.json` | `schemas/locale.schema.json` | country + locale + 精确 `compatibleStructureRevision` |
| 清单 `data/manifest.json` | `schemas/manifest.schema.json` | 资源按 path 升序排序、path 唯一（语义检查强制） |
| 选择值 | `schemas/selection.schema.json` | `pathIds` 首项必须 `cc:XX`；父子边/国家/revision 须对结构语义校验 |

P1-02 收口新增：manifest 资源**按 path 排序**为 MUST（`tool/geo_data.py verify_manifest` 强制，负例 `test_manifest_unsorted_resources_rejected`）。Schema 层保持"形状 + 严格 additionalProperties=false"；排序、唯一 path、父子边、跨语言 revision 兼容属于语义层，黄金参考实现在 `tool/geo_data.py`，Dart SDK（P1-04）必须用同一测试向量对齐。

## 2. 错误分类（typed errors，宿主必须可区分）

| 错误 | 触发 | 不得合并为 |
|---|---|---|
| `network` | 传输失败/超时/断线 | 空 children |
| `notFound` | 404/资源不在 manifest | 空 children |
| `unsupportedVersion` | protocolVersion/revision 不在支持集 | 空 children |
| `integrityMismatch` | 长度或 SHA-256 不符（在任何 JSON 解码**之前**检查） | 解析错误 |
| `parseFailure` | 字节合法但 JSON/Schema/语义非法 | 空 children |
| `unknownCoverage` | `childrenStatus=unknown` 的范围未知 | "没有下级地区" |
| `configurationError` | 严格远程模式未注入可靠 verifier 等 | 任意运行时错误 |

黄金参考：`tests/test_geo_data.py`（重复键/重复 ID/循环/跨国父级/悬空译名/revision 错配/路径穿越/percent-encoding/symlink/hash 损坏/乱序 manifest 均拒绝）。

## 3. Locale 别名表（显式，项目级）

| 宿主界面 locale | 资源 locale | 说明 |
|---|---|---|
| zh-CN | zh-Hans | 脚本别名显式配置，不靠截断推断 |
| zh-Hant | zh-Hant | 不与 zh-Hans 混用 |
| en-US | en | |
| ja-JP | ja | |
| ko-KR | ko | |
| ru-RU | ru | |
| de-DE | de | |
| fr-FR | fr | |
| it-IT | it | |
| ar-SA | ar | RTL 验证语言 |

匹配顺序（PRD §9）：规范化请求及显式别名 → RFC 4647 风格匹配 → 宿主默认 locale → 节点来源默认名（受质量过滤）→ 稳定 ID。解析 API 返回 requested/resolved locale、quality、isFallback。

## 4. 质量默认值（production profile）

- 接受：`approved-in-source`、`contributed`、`cldr-json-qualified`、`source-native`（仅对其自身 locale/回退）。
- 拒绝（fail closed）：`provisional`、`unconfirmed`、未知/机器候选（除非宿主显式 opt-in，且必须标注暂定）。
- 默认名（`node.name`/`nameQuality`）遵守同一策略；禁止"过滤译名后回退到未过滤的 node.name"绕过（负例 `test_default_name_cannot_bypass_quality_filter`）。
- `research-seed` 数据集成熟度与逐名质量相互独立；seed 不得声明为 production（`test_seed_cannot_be_claimed_as_production`）。

## 5. 宿主接口形状（loader / store / verifier）

主包（P1-04 起）运行时只依赖 Flutter/Dart SDK；以下能力全部经注入接口：

```dart
abstract class GeoResourceLoader {          // 网络/资产/自定义镜像
  Future<GeoBytes> load(Uri resourceUri);   // 返回解码 Content-Encoding 后的字节
}
abstract class GeoCacheStore {              // 持久缓存（公开资源；账号资料另存）
  Future<GeoBytes?> read(GeoCacheKey key);
  Future<void> write(GeoCacheKey key, GeoBytes bytes); // 原子写由实现负责
}
abstract class GeoHashVerifier {            // 严格远程模式必需
  Future<bool> verify(GeoBytes bytes, String expectedSha256, int expectedBytes);
}
```

- **严格远程模式前置**：未注入可靠 SHA-256 verifier 时必须抛 `configurationError`，不得静默跳过校验（AT-09）。
- 缓存键含 datasetId/kind/country/locale/revision/hash；与当前 manifest 不匹配的旧缓存不算命中。
- 更新语义：下载并验证完整兼容集合 → 原子切换活动 manifest；禁止跨版本拼接结构与译名（AT-10）。
- 宿主保存事务（PRD GR-14 / PROTOCOL §8）：选择器产出 draft selection → 宿主提交后端 → 成功才更新账号缓存并退出；失败保留草稿可重试；换语言不改变 selection identity。

## 6. 兼容性与弃用策略

1. **协议版本**：`protocolVersion="1.0"` 输入严格校验（顶层/节点 `additionalProperties:false`）；SDK 只接受明确支持的版本，不得"默认兼容"未来 minor。协议演进 = 发布新 Schema + 显式兼容规则 + 迁移记录。
2. **新增国家/语言**：使用现有字段，不升协议；新语言不改任何 `regions/*.json` 字节或 revision（负例 `test_add_language_never_changes_structure`）。
3. **数据版本**：代码与数据版本独立发布；同一资源 tag 不得覆盖为不同内容（release workflow 强制）。
4. **ID/父级变更**：`removed/reparented/renamed` 三类操作影响不同，必须走 `sources/` 迁移记录与差异报告（`test_removed_id_requires_migration`）；旧发布在兼容窗口内保留。
5. **弃用窗口**：宿主至少支持读取上一发布集合（stale coherent 显式标注）；SDK 对被移除 ID 的存量 selection 报可诊断错误，不猜映射。
6. **演示命名空间**：`geo-regions-ui-fixture` 的选择值禁止作为生产数据持久化（DEMO_UX UX-12）。

## 7. P1-02 验证记录

- `python3 -m unittest discover -s tests` → 45/45 OK（含新负例 manifest 乱序拒绝）
- `python3 tool/geo_data.py validate --schema` → integrityStatus: pass（10 国 / 4143 节点 / 100 语言包 / 36 源文件验证）
- `python3 tool/geo_data.py manifest --check` → checked: true
- `node demo/web_preview/test_logic.cjs` → 22 checks PASS
- `python3 tool/import_data.py --check` → 124 outputs 一致重建

GR-01/02/06/07/11 对应契约核对无互相矛盾（GR-01 稳定 ID+路径 → selection.schema+语义校验；GR-02 结构/译名分离 → 互不触碰的 revision 域；GR-06 完整性 → verify_manifest 字节/hash 前置；GR-07 质量可见 → §4 默认值与负例；GR-11 治理 → sourceRefs/lock + import --check 可重建）。
