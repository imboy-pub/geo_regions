# Geo Regions Data Protocol 1.0 / 地区数据协议 1.0

日期 / Date: 2026-11-13 · 状态 / Status: implementation baseline, seed profile

本规范是项目开放数据契约，不是 IETF/ISO 发布的标准。大写 MUST/SHOULD 表示本项目的要求。代码与数据遵循各自许可证。

This is an open project contract built on existing standards, not an IETF or ISO standard. MUST/SHOULD express this project's requirements. Code and data retain their respective licenses.

## 1. 标准映射 / Standards mapping

| Topic / 领域 | Standard / 采用规范 | Project decision / 本项目补充 |
|---|---|---|
| Country identifiers | ISO 3166-1 alpha-2 | `CN`, `JP`；首批catalog有限，不能仅因两字母格式就认定有效国家 |
| Subdivision identifiers | ISO 3166-2 where present | `iso3166-2:JP-13`；统计区划使用独立namespace，不能伪装ISO |
| Locales | BCP 47 / RFC 5646 | canonical resource tags plus explicit host aliases |
| Language matching | RFC 4647 lookup principles | script aliases are explicit, not inferred by truncation |
| JSON | RFC 8259, UTF-8 | no duplicate keys, non-finite numbers, BOM or ambiguous duplicate IDs |
| Schema | JSON Schema 2020-12 | structural validation plus independent semantic checks |
| Transport | RFC 3986, RFC 9110/9111 | HTTPS remote base, relative safe resource paths, normal HTTP cache semantics |
| Integrity | SHA-256, FIPS 180-4 | full file bytes after HTTP content decoding; not a signature |

参考链接 / Source links: [REFERENCES.md](REFERENCES.md)。

## 2. 文件角色 / Resource roles

Paths below are relative to the dataset root `data/`. Manifest paths MUST NOT include a leading `data/` prefix when the deployment base already identifies that root.

以下路径相对于 `data/` 根。部署base已指向数据根时，不再拼接第二个data。发布资源可以由任意兼容镜像提供。

| File | Manifest kind | Identity and compatibility |
|---|---|---|
| `countries.json` | `countries` | `datasetId` + catalog revision |
| `catalog_i18n/{locale}.json` | `country-names` | locale + exact `compatibleCatalogRevision` |
| `regions/{CC}.json` | `structure` | country + structure revision |
| `i18n/{locale}/{CC}.json` | `locale` | country + locale + exact `compatibleStructureRevision` |
| `manifest.json` | not listed inside itself | sorted resources + manifest revision |

Manifest lists the immutable expected resources. Bundled manifest is a subset; `registry.json` is a descriptor-only copy of the full manifest for discovering remote availability. It does not imply every resource has been downloaded.

国家名称小包解决国家列表国际化，不能为了展示十个国家名字而加载十份地区大包。地区root的名称与目录名称应一致，但它们属于不同用途的独立资源。

Small catalog-name packs localize the country list without downloading every country's structure or large name pack. Root names and catalog names should agree but serve separate resources.

## 3. 共同字段 / Common fields

`protocolVersion` is exactly `"1.0"` in this baseline. `datasetId` is `"geo-regions-seed"` for this delivery and is a namespace, not a server address. Each published file has a content-derived `revision`. A source reference resolves to a lock-file entry with repository, full commit SHA, path, full SHA-256, byte size, retrieval date, source date/version and license.

当前Schema对未声明顶层字段采取严格校验，版本1.0输入不能偷偷添加不兼容字段。未来版本应发布新Schema和兼容策略；新增国家或语言使用现有字段，不要求协议升级。SDK不能声称接受任意未知minor版本，只能接受明确支持的版本。

The 1.0 schemas are strict about undeclared fields. Future contract versions require new schemas and compatibility rules. Adding countries/locales within the existing shape does not require a protocol upgrade. SDKs reject unsupported versions explicitly.

`coverage` is metadata, not a replacement for validation. `sourceRefs` links to the checked-in lock/provenance records; serving clients need not download raw upstream files. Packaged notices must accompany distributed data as required by the source license.

## 4. 地区节点 / Region nodes

Required node fields: `id`, `parentId`, `kind`, `name`, `childrenStatus`. Optional fields include `code`, `nativeLocale`, `aliases`, and source-default-name metadata `nameLocale`, `nameQuality`.

| Field | Normative meaning / 规范语义 |
|---|---|
| `id` | dataset-scoped opaque stable string; do not parse labels from it / 数据集内稳定不透明ID |
| `parentId` | exactly one parent; only country root is null / 唯一父级，只有国家根为空 |
| `kind` | source node type; statistical group is not a city / 上游节点类型，不由深度反推 |
| `code` | source administrative/statistical code, if available / 可选源编码 |
| `name` | source default display value, not necessarily native or reviewed / 来源默认显示名 |
| `nameLocale` | explicitly known locale of default name / 默认名的已知语种 |
| `nameQuality` | source quality of default name / 默认名的来源质量 |
| `nativeLocale` | only when supported by source evidence / 仅在来源确证原生名时使用 |
| `aliases` | explicit names for search, never implicit migration / 明确搜索别名，不等于ID迁移 |
| `childrenStatus` | `complete`, `partial`, `unknown` within documented profile / 声明范围内的下级完整性 |

Each structure contains one root `cc:{countryCode}`. Every other node reaches that root with no cycles or orphan parents. IDs are unique; sibling names need not be. Lists MUST NOT imply a legal administrative rank. Chinese statistical groups and 9-digit source nodes are retained with distinct kinds.

`complete` 不代表这个地方在现实世界没有更细地区；它表示本文件声明范围内的下级收录情况。`unknown` 的空children不能满足“真实行政叶”条件。业务若允许选到省/都道府县，使用明确的可选层级策略，不伪称已选全球最深层。

`complete` is completeness within declared coverage, not proof that no finer real-world geography exists. An empty `unknown` node is not a verified administrative leaf. Hosts can explicitly allow selection at a supported level.

默认名必须遵循同一质量策略。过滤了provisional译名后，再直接使用同样来自provisional源的`node.name`会绕过过滤，禁止这样实现。缺少默认名质量时严格模式保守处理，最后可显示稳定ID并说明名称不可用。

Default names obey the same quality policy. Filtering a provisional locale value and then accepting the same provisional text from `node.name` is a policy bypass. Treat unknown quality conservatively; a stable ID is the final non-name display fallback.

## 5. 语言包与质量 / Locale packs and quality

Region packs contain `countryCode`, `locale`, `compatibleStructureRevision` and `names`, where keys are node IDs from that exact structure. Catalog-name packs contain `locale`, `compatibleCatalogRevision`, and names keyed by existing catalog country codes. Empty/missing translations remain missing; empty text must not count as translation.

`coverage.translationQualityById` MUST preserve a source-quality value for every imported name. Current values include:

| Quality | Meaning / 含义 | Default production resolution |
|---|---|---|
| `approved-in-source` | Source explicitly approved; no project review claimed / 上游明确批准 | Eligible |
| `contributed` | Source's contributed status / 上游contributed | Eligible, status retained |
| `cldr-json-qualified` | Passed CLDR JSON export threshold, exact individual XML grade unspecified / 达到JSON导出阈值 | Eligible, not relabeled approved |
| `source-native` | Native source name, not translation into other locales / 原生来源名 | Eligible for its own locale/fallback |
| `provisional` | Source tentative / 上游暂定 | Excluded unless explicit opt-in |
| `unconfirmed` | Source unconfirmed / 上游未确认 | Excluded unless explicit opt-in |
| Other/unknown/machine candidate | Not approved by this baseline / 未知或机器候选 | Excluded; fail closed |

Dataset maturity (`research-seed`) and individual name quality are separate. A pack can contain some eligible names and still be a non-production dataset because coverage, currency or review is incomplete. Integrity PASS never implies geographic or linguistic correctness. `--production` is an additional gate, not proof of legal/linguistic review.

发布扩展语言时不修改结构；返回值建议包括requestedLocale/resolvedLocale/quality/isFallback。该解析API是Phase1待实现要求，不是本包已有生产实现。

Adding a language changes no structure. The future resolver returns requested/resolved locale, quality and fallback status. This API is a Phase 1 implementation requirement, not an already shipped production implementation.

## 6. 内容版本 / Content revisions

The seed encoding is a deterministic project serialization, **not a claim of RFC 8785 canonicalization**. Define `C(x)` as UTF-8 JSON with recursively sorted object keys, preserved array order, literal Unicode (`ensure_ascii=false`), no extra whitespace (`separators=(',', ':')`), no trailing newline and no non-finite numbers. The included Python functions are the reference; Dart implementation requires cross-language golden vectors.

| Type | Revision payload |
|---|---|
| Structure | `s-` + first 16 hex chars of SHA-256(C(nodes)) |
| Catalog | `c-` + first 16 hex chars of SHA-256(C(countries)) |
| Either locale kind | `l-` + first 16 hex chars of SHA-256(C({names, translationQualityById})) |
| Manifest | `m-` + first 16 hex chars of SHA-256(C(resources)) |

质量变化即使不改文字，也必须改变locale revision。节点默认名质量属于nodes，变化也改变structure revision。Manifest中的`sha256`始终是实际文件全部字节的64位十六进制哈希，包含文件中metadata和排版；短revision不是安全哈希的替代品。

Quality changes alter locale revisions even when spelling does not. Default-name quality belongs to nodes and changes structure revisions. Full 64-hex SHA-256 and byte length cover the actual file, including metadata/formatting. Short revision labels never replace full integrity hashes.

兼容性按相等revision检查，而不是“更新时间接近”。只新增语言时structure revision不变；结构任何变化导致新的revision时，必须重新生成/验证兼容语言包，不能只手改compatible字段。

Compatibility requires exact referenced revisions. Adding a locale leaves structure revisions unchanged. Changed structures require regenerated/revalidated compatible packs, not a manual compatibility-label edit.

## 7. Manifest和远程契约 / Manifest and remote contract

Each resource entry contains `path`, `kind`, `revision`, `sha256`, `bytes` and applicable country/locale/compatibility fields. Entries are sorted by path and paths are unique. No absolute paths, backslashes, drive prefixes, query strings, fragments, encoded traversal, `.`/`..` components or symlink escapes are permitted in resource keys.

远程base由宿主配置，不写死IMBoy域名。解析相对路径后应保持批准的base origin/前缀；跨origin重定向由宿主loader明确策略控制。网络失败、404、版本不支持、完整性不符、解析失败、范围未知分别返回可诊断错误，不统一变成空children。

Hosts configure the remote base and redirect policy. Resolved resource paths remain within the approved base. Network failure, missing resource, unsupported version, hash mismatch, parse failure and unknown coverage are distinct conditions.

建议immutable资源URL使用版本目录或内容hash。HTTP `Cache-Control`/ETag用于传输缓存，不能替代Manifest资源身份或SHA验证。校验的是解码HTTP Content-Encoding后的原始JSON文件字节；传输层压缩长度不能与资源bytes混淆。Web源需要正确CORS与`application/json`内容类型。

Use immutable versioned/content-addressed resource URLs. HTTP caches and ETags do not replace manifest identity or integrity. Verify decoded entity bytes, not compressed wire length. Web hosts require compatible CORS and JSON content types.

## 8. Selection契约 / Selection contract

Fields: `protocolVersion`, `datasetId`, `countryCode`, `dataRevision`, `pathIds`; optional `displaySnapshot` and `displayLocale` are display conveniences. `pathIds` begins with `cc:XX`, has no repeated IDs and follows actual parent edges to the selected node. Country-only selections have a one-element path.

真实可校验样例 / Actual fixture: [selection.JP.json](../samples/selection.JP.json)。`selection.schema.json`只能检查形状，父子边/国家/revision必须对结构做语义校验。

The selection schema validates shape only; validate country, revision and parent edges against the referenced structure. Persist identity rather than joining labels with spaces. A selected node's parent move or retirement needs a migration record; do not silently rewrite the user's meaning.

宿主保存是独立事务：选择器返回draft selection → 宿主提交后端 → 成功后更新账号缓存并退出。失败保持草稿且可重试；不因换语言而标记用户更改了地区。这个顺序特别保护IMBoy已有PR #68修复。

Host persistence remains separate: return a draft selection, save to the server, then commit account cache and exit. On failure keep the draft. Changing display language does not change selection identity.

## 9. 消费者最低义务 / Minimum host responsibilities

| Host MUST / 使用方必须 | Why / 原因 |
|---|---|
| Pin/resolve dataset release and verify resources | Avoid mixing identities and versions / 防混用 |
| Preserve stable IDs and root-inclusive paths | Names change with language / 名称不稳定 |
| Supply loader/store/verifier for strict remote mode | SDK-only core cannot assume transport/storage / 保持通用 |
| Provide UI labels, current locale and selection policy | Region-name packs do not translate the entire app / 职责分离 |
| Declare generated assets and run preparation before build | Runtime laziness does not reduce bundled payload / 真正控制包体 |
| Preserve source notices and expose them with distribution | Data licenses remain applicable / 保留许可 |
| Separate public cache from account selections | Multi-account isolation / 防账号串数据 |
| Use stale coherent releases explicitly, never arbitrary mixtures | Correct offline recovery / 离线一致性 |

The host need not use Riverpod, Dio, slang or any specific backend. Alternative languages/platforms can implement this same JSON contract.

## 10. 版本迁移与扩展 / Migration and extension

新增国家/语言按 [DATA_WORKPACKAGES.md](DATA_WORKPACKAGES.md) 和 [DATA_RULES.md](DATA_RULES.md) 执行。更改来源口径、ID、父链、行政范围或译名质量都需要差异报告。`removed/reparented/renamed`有不同影响：文字变更不表示实体迁移；ID删除需要兼容记录；父链变化必须重新验证保存路径。

Changes in scope, IDs, parentage or quality require a diff. Renaming, removal and reparenting are different operations. Preserve old releases for compatibility windows. Changing the seed dataset namespace to a production namespace is an explicit migration; do not persist demo fixture selections as production user data.
