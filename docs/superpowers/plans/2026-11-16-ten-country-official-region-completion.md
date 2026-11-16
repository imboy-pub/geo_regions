# Ten-Country Official Region Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用可追溯的官方来源补全 CN、JP、KR、US、GB、DE、FR、IT、RU、SA 十国声明 Profile 内的现势行政结构，保持 `geo-regions-seed` 的 `research-seed` 成熟度，并为每国创建一个独立数据 Commit。

**Architecture:** `tool/import_data.py` 继续作为唯一编排入口；新增 `tool/importers/` 公共适配器契约、逐国适配器和 Profile。每国提交同时引入固定官方快照、迁移记录、适配器测试和生成产物，使该 Commit 可离线重建。

**Tech Stack:** Python 3.10+ 标准库、JSON/CSV/XML、Dart/Flutter 测试链、AtomGit CLI（`ag`）、Git。

## Global Constraints

- 数据集身份固定为 `geo-regions-seed`，协议版本固定为 `1.0`。
- 国家固定为 `CN, JP, KR, US, GB, DE, FR, IT, RU, SA`。
- 语言固定为 `zh-Hans, zh-Hant, en, ja, ko, ru, de, fr, it, ar`。
- 不改变 `expectedProductionGateRefusal=true`；所有新增资源保持 `research-seed`。
- 不引入 ODbL CSC 作为正式来源，不复制英语或运行时回退制造翻译覆盖。
- 来源必须固定 URL、版本、发布日期或生效日期、抓取日期、许可、SHA-256、字节数。
- 无法确认许可、父链或官方代码时不提交该国派生数据；报告阻塞并请求决策。
- 每国恰好一个数据 Commit，顺序为 `CN → JP → KR → US → GB → DE → FR → IT → RU → SA`。
- 最终只创建一个 PR；设计文档、本计划和任何通用修复不得伪装成国家数据 Commit。
- 现有 `demo/flutter/bootstrap.sh` 模式变更及三个 `pubspec.lock` 删除与本任务无关，不暂存、不提交。

---

## 批次总览

| 批次 | 国家 | 目的 | 批次出口 |
|---|---|---|---|
| 0 | 无 | 基线、来源门禁、公共适配器设计确认 | 基线验证通过，工作区无关变更隔离 |
| 1 | CN | 引入公共基础设施，补到县级并处理 2023 后变更 | CN 单国 Commit 可离线重建 |
| 2 | JP、KR | 补到市区町村/市郡区，验证东亚官方代码 | 两个 Commit，东亚适配器稳定 |
| 3 | US、GB | 补 county/local authority，验证大体积和混合层级 | 两个 Commit，层级与迁移审查通过 |
| 4 | DE、FR、IT | 补 Gemeinde/commune/comune，验证市镇级规模 | 三个 Commit，性能与语言兼容通过 |
| 5 | RU、SA | 处理敏感 Profile 和官方覆盖边界 | 两个 Commit，不改变既有领土口径 |
| 6 | 无 | 全量回归、PR 描述、远端验证 | 一个 PR，十国 Commit 可追溯 |

每个批次结束时执行全量数据检查并推送功能分支；批次内仍按国家逐个测试和提交。

## 文件结构

**创建**

- `config/region_profiles/{CC}.json`：国家 Profile、目标层级、官方代码体系和排除项。
- `sources/raw/official/{cc}/`：官方不可变快照及许可文本。
- `sources/migrations/{CC}.json`：旧 ID 到官方实体的迁移或显式未映射记录。
- `tool/importers/__init__.py`：适配器包入口。
- `tool/importers/common.py`：适配器契约、Profile 加载、公共迁移和覆盖率辅助。
- `tool/importers/{cc}.py`：十国官方输入规范化适配器。
- `tests/fixtures/official/{cc}/`：每国最小固定样本。
- `tests/test_official_imports.py`：所有国家复用的适配器契约测试。

**修改**

- `tool/import_data.py`：调用适配器、校验迁移、生成正式数据和覆盖信息。
- `sources/source-lock.json`：追加官方原始来源和派生来源。
- `data/regions/{CC}.json`：目标国家结构。
- `data/i18n/{locale}/{CC}.json`：与结构 revision 兼容的稀疏语言包。
- `data/manifest.json`、`sources/coverage-report.json`、`docs/DATA_COVERAGE.md`：全局派生产物。
- `docs/DATA_SOURCES.md`：国家来源、许可、版本和口径说明。

**公共接口**

`tool/importers/common.py` 必须提供：

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SourceNode:
    official_code: str
    parent_code: str | None
    kind: str
    name: str
    name_locale: str
    name_quality: str
    children_status: str

@dataclass(frozen=True)
class CountryDraft:
    profile: str
    source_refs: tuple[str, ...]
    nodes: tuple[SourceNode, ...]
    migration_records: tuple[dict, ...]

def load_profile(root: Path, country_code: str) -> dict: ...
def load_adapter(country_code: str): ...
def validate_draft(root: Path, country_code: str, draft: CountryDraft, previous_nodes: list[dict]) -> None: ...
```

Profile 文件必须包含且只能包含这些字段：`schemaVersion` 固定为整数 `1`；`countryCode` 为两位国家代码；`profile` 为非空稳定字符串；`officialCodeSystem` 为来源官方代码体系名；`targetKinds` 和 `excludedKinds` 为非空字符串数组；`sourceBaseline` 必须逐字等于 `source-lock.json` 中该国主来源的 `upstreamVersion`。`load_profile` 拒绝缺失字段、额外字段、错误国家代码和无法在 source-lock 中解析的 `sourceBaseline`。

迁移文件必须包含 `schemaVersion`、`countryCode`、`records`。每条形如 `oldId`、`disposition`、`newId`、`reason`、`sourceRef` 五个字段的对象。`disposition` 只能是 `preserved`、`replaced`、`retired`、`unmapped`。`retired` 和 `unmapped` 的 `newId` 为 `null`；其他处置必须引用现存节点 ID。

`validate_draft` 必须拒绝重复官方代码、缺失父代码、父链环、跨国父代码、未知 Profile、未声明的行政类型、空名称、非法质量值和非法迁移处置。

`tests/test_official_imports.py` 使用参数化契约，对每个国家加载同目录 fixture，并验证：

- fixture 生成的 ID 唯一且父链可解析；
- Profile 的国家代码、目标层级与 fixture 一致；
- 每条迁移记录引用真实旧 ID 或明确标记 `unmapped`；
- 语言包 revision 与结构 revision 兼容；
- 不存在的下级为 `unknown` 而不是伪造叶节点。

---

### Task 1: Batch 0 预检与 Batch 1 CN

**Files:**
- Create: `config/region_profiles/CN.json`
- Create: `sources/raw/official/cn/`
- Create: `sources/migrations/CN.json`
- Create: `tool/importers/common.py`
- Create: `tool/importers/cn.py`
- Create: `tests/fixtures/official/cn/nodes.csv`
- Create: `tests/test_official_imports.py`
- Modify: `tool/import_data.py:20-611`
- Modify: `sources/source-lock.json`
- Modify: `data/regions/CN.json`, `data/i18n/*/CN.json`
- Modify: `data/manifest.json`, `sources/coverage-report.json`, `docs/DATA_COVERAGE.md`, `docs/DATA_SOURCES.md`

**Interfaces:**
- Consumes: 现有 `build(root)`、`revision()`、语言包生成和 `main()` 检查入口。
- Produces: `SourceNode`、`CountryDraft`、`validate_draft()` 和 `tool.importers.cn.build(root)`。

**来源门禁：** 国家统计局统计用区划代码与民政部行政区划公告作为候选一手来源。许可、可再分发条款、官方发布日期和代码层级必须在提交前写入 `sources/source-lock.json`；不能确认时停止 CN 数据提交，不用 modood 或 CSC 冒充现势。

- [ ] **Step 1: 执行基线预检**

```bash
git status --short --branch
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 -m unittest discover -s tests -v
```

Expected: 当前 `main` 基线通过；无关修改仍在工作区且未暂存。任何基线失败先修复环境或报告，不继续数据变更。

- [ ] **Step 2: 写 CN Profile 和 fixture 测试**

`config/region_profiles/CN.json` 按公共 Profile 字段写入：`profile` 为 `CN-mainland-official-current`，`officialCodeSystem` 为官方统计区划代码体系，`targetKinds` 为 `province`、`prefecture`、`county`，`excludedKinds` 为 `township`、`village`、`hk`、`mo`、`tw`，`sourceBaseline` 取 CN 官方主来源在 source-lock 中的 `upstreamVersion`。

fixture 至少包含省、地级、县级各一条，以及一个父级未知节点：

```csv
official_code,parent_code,kind,name,name_locale,name_quality,children_status
110000,,province,北京市,zh-Hans,source-native,complete
110100,110000,prefecture,市辖区,zh-Hans,source-native,complete
110101,110100,county,东城区,zh-Hans,source-native,unknown
```

测试使用 `unittest` 加载 fixture，断言 `validate_draft()` 返回 `None`，并断言把县级父代码改为 `999999` 时抛出包含 `missing parent` 的 `ValueError`。

- [ ] **Step 3: 运行新测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，`tool.importers.common` 或 CN adapter 尚不存在。

- [ ] **Step 4: 实现公共契约和 CN 适配器**

实现 `SourceNode`、`CountryDraft`、Profile 校验、适配器注册表和 `validate_draft()`。CN adapter 读取已锁定的官方快照，转换为 `CountryDraft`；旧 `cn-stat:` ID 仅在官方代码与实体身份均可精确对应时保留，否则写入 `sources/migrations/CN.json` 并标记未映射原因。

`tool/import_data.py` 的 CN 分支改为调用 adapter，不再从 modood 生成正式 CN 结构。公共语言包、revision 和输出逻辑继续复用现有实现。

- [ ] **Step 5: 运行 CN 测试和离线重建**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
git diff --stat
```

Expected: 测试通过；重建无 stale output；差异只包含 CN Profile、来源、迁移、CN 数据、语言包和全局派生产物。

- [ ] **Step 6: 执行 CN 数据验证**

```bash
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
```

Expected: 前四条成功；`--production` 明确拒绝 research-seed；Manifest 无漂移。

- [ ] **Step 7: 提交 CN**

```bash
git add config/region_profiles/CN.json sources/raw/official/cn sources/migrations/CN.json \
  tool/importers/common.py tool/importers/cn.py tests/fixtures/official/cn \
  tests/test_official_imports.py tool/import_data.py sources/source-lock.json \
  data/regions/CN.json data/i18n data/manifest.json sources/coverage-report.json \
  docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete CN official administrative regions"
git status --short --branch
```

Expected: 只创建 CN 数据 Commit；无关文件仍未暂存。

---

### Task 2: Batch 2a JP

**Files:**
- Create: `config/region_profiles/JP.json`
- Create: `sources/raw/official/jp/`
- Create: `sources/migrations/JP.json`
- Create: `tool/importers/jp.py`
- Create: `tests/fixtures/official/jp/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/JP.json`, `data/i18n/*/JP.json`, 全局派生产物

**Interfaces:**
- Consumes: Task 1 的 `SourceNode`、`CountryDraft`、`validate_draft()`。
- Produces: `tool.importers.jp.build(root)`，ID 使用 `jp-municipality:{official-code}`，现有 47 个都道府县 ISO ID 保留。

**来源门禁：** 数字厅地址基础登记或总务省 e-Stat 的官方地方公共团体代码。必须覆盖都道府县、市、区、町、村及政令指定都市的区，记录官方基准日和开放许可。无法确认区町村父链时保留 `unknown`。

- [ ] **Step 1: 写 JP fixture**

fixture 包含一个都道府县、一个市、一个政令市辖区，以及一个官方已废止代码。废止代码必须仅出现在迁移记录，不进入活动结构。

- [ ] **Step 2: 写失败测试**

在 `tests/test_official_imports.py` 增加 JP 参数项，断言 47 个现有都道府县 ID 全部保留、市区町村 ID 前缀正确、废止代码不出现在节点集。

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，JP adapter 尚不存在。

- [ ] **Step 3: 实现 JP 适配器和 Profile**

按官方代码建立都道府县到市区町村的父子关系。行政区名称使用日文官方名，`nameQuality` 记为 `source-native`；不能从英文或中文 CLDR 复制日语名称。迁移记录逐条保存旧 ID、官方代码、处置和原因。

- [ ] **Step 4: 重建并验证**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
```

Expected: 测试与 Schema 通过；production 按预期拒绝；47 个旧都道府县 ID 无删除。

- [ ] **Step 5: 提交 JP**

```bash
git add config/region_profiles/JP.json sources/raw/official/jp sources/migrations/JP.json \
  tool/importers/jp.py tests/fixtures/official/jp tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/JP.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete JP official municipalities"
```

Expected: 只创建 JP 数据 Commit。

---

### Task 3: Batch 2b KR

**Files:**
- Create: `config/region_profiles/KR.json`
- Create: `sources/raw/official/kr/`
- Create: `sources/migrations/KR.json`
- Create: `tool/importers/kr.py`
- Create: `tests/fixtures/official/kr/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/KR.json`, `data/i18n/*/KR.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共 `SourceNode`、`CountryDraft`、`validate_draft()`。
- Produces: `tool.importers.kr.build(root)`，ID 使用 `kr-municipality:{official-code}`，现有 17 个广域自治团体 ID 保留。

**来源门禁：** 行政安全部居民登录行政区域代码或官方开放数据平台。必须区分广域自治团体、市、郡、自治区和一般区，不得重新引入虚构整合市。许可需可再分发。

- [ ] **Step 1: 写 KR fixture 和失败测试**

fixture 包含广域团体、市、郡、自治区四层样例，以及一个旧整合市代码。测试断言整合市只出现在退役迁移记录，活动节点父链全部解析。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，KR adapter 尚不存在。

- [ ] **Step 3: 实现 KR 适配器**

按官方代码和父链生成节点；韩国官方名称保留 `source-native`。若自治区与市的官方父子关系不稳定，使用 Profile 声明的官方类型，不按名称自动挂接。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/KR.json sources/raw/official/kr sources/migrations/KR.json \
  tool/importers/kr.py tests/fixtures/official/kr tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/KR.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete KR official municipal regions"
```

Expected: 测试通过；17 个既有广域 ID 无未解释删除；只创建 KR 数据 Commit。

---

### Task 4: Batch 3a US

**Files:**
- Create: `config/region_profiles/US.json`
- Create: `sources/raw/official/us/`
- Create: `sources/migrations/US.json`
- Create: `tool/importers/us.py`
- Create: `tests/fixtures/official/us/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/US.json`, `data/i18n/*/US.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.us.build(root)`，state ID 保留 ISO 形式，county 使用 `us-county:{five-digit-FIPS}`。

**来源门禁：** Census Bureau 年度 Gazetteer 或官方 county boundary attribute 文件。许可应为美国联邦政府公共领域；必须记录年度版本。Profile 只含 state/state equivalent 和 county/county equivalent，不含 place、MCD 或城市清单。

- [ ] **Step 1: 写 US fixture 和失败测试**

fixture 包含州、县、county equivalent 和一个缺失县的州。测试断言县级 ID 为 5 位 FIPS、缺失覆盖的州为 `unknown`、place 记录不生成节点。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，US adapter 尚不存在。

- [ ] **Step 3: 实现 US 适配器**

按官方 FIPS 生成 county；保留现有 57 个 CLDR state/territory ID。若官方文件缺少现有条目，记录覆盖缺口且保留原节点，不删除旧节点冒充现势。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/US.json sources/raw/official/us sources/migrations/US.json \
  tool/importers/us.py tests/fixtures/official/us tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/US.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete US official counties"
```

Expected: 只创建 US 数据 Commit；无 place/MCD 进入正式结构。

---

### Task 5: Batch 3b GB

**Files:**
- Create: `config/region_profiles/GB.json`
- Create: `sources/raw/official/gb/`
- Create: `sources/migrations/GB.json`
- Create: `tool/importers/gb.py`
- Create: `tests/fixtures/official/gb/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/GB.json`, `data/i18n/*/GB.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.gb.build(root)`，local authority 使用 `gb-lad:{ONS-code}`。

**来源门禁：** ONS Open Geography Portal 的地方行政当局官方层，许可为 OGL v3。必须提供 constituent country 父关系或可验证的 country 字段；不得把 221 个单位直接挂国家根来制造扁平树。

- [ ] **Step 1: 写 GB fixture 和失败测试**

fixture 包含 England、Scotland、Wales、Northern Ireland 各一个 local authority，以及一个无国家父关系的记录。测试断言无国家父关系记录导致 `validate_draft()` 失败。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，GB adapter 尚不存在。

- [ ] **Step 3: 实现 GB 适配器**

保留四个构成国节点，将其现有可达旧节点按官方 ONS 代码迁移到 local authority。无法确认旧节点与新实体的关系时写入未映射清单，不做启发式重新挂接。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/GB.json sources/raw/official/gb sources/migrations/GB.json \
  tool/importers/gb.py tests/fixtures/official/gb tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/GB.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete GB official local authorities"
```

Expected: 只创建 GB 数据 Commit；构成国父子关系可验证。

---

### Task 6: Batch 4a DE

**Files:**
- Create: `config/region_profiles/DE.json`
- Create: `sources/raw/official/de/`
- Create: `sources/migrations/DE.json`
- Create: `tool/importers/de.py`
- Create: `tests/fixtures/official/de/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/DE.json`, `data/i18n/*/DE.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.de.build(root)`，Gemeinde 使用 `de-gemeinde:{official-AGS}`。

**来源门禁：** Destatis Gemeindeverzeichnis/GV-ISYS 官方发布，许可需为可再分发的 Dl-DE-BY 或等价官方开放许可。Profile 含州、Regierungsbezirk（若官方提供）、Kreis/kreisfreie Stadt、Gemeinde。

- [ ] **Step 1: 写 DE fixture 和失败测试**

fixture 包含州、县、县级市、Gemeinde，以及一个已并入其他市镇的旧 AGS。测试断言旧 AGS 不出现在活动节点，迁移记录中必须存在替代目标。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，DE adapter 尚不存在。

- [ ] **Step 3: 实现 DE 适配器**

保留 16 个州 ID；新增官方下级。名称使用官方德语名。拆分、合并和 AGS 废止按迁移记录处理，禁止复用旧代码指向新实体。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/DE.json sources/raw/official/de sources/migrations/DE.json \
  tool/importers/de.py tests/fixtures/official/de tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/DE.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete DE official municipalities"
```

Expected: 只创建 DE 数据 Commit；16 个州 ID 无未解释变化。

---

### Task 7: Batch 4b FR

**Files:**
- Create: `config/region_profiles/FR.json`
- Create: `sources/raw/official/fr/`
- Create: `sources/migrations/FR.json`
- Create: `tool/importers/fr.py`
- Create: `tests/fixtures/official/fr/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/FR.json`, `data/i18n/*/FR.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.fr.build(root)`，region/department/commune ID 使用 `fr-region:`、`fr-department:`、`fr-commune:` 加官方 INSEE 代码。

**来源门禁：** INSEE Code officiel géographique 年度版本，许可为 Etalab Open Licence 2.0。Profile 包含 region、department、commune 和官方 COG 中的海外集体；不加入普通居民点。

- [ ] **Step 1: 写 FR fixture 和失败测试**

fixture 包含本土 region/department/commune、一个 DROM 和一个已合并 commune（commune nouvelle）。测试断言旧 commune 代码进入退役或替代迁移，活动父链完整。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，FR adapter 尚不存在。

- [ ] **Step 3: 实现 FR 适配器**

新结构按 2026 COG 官方层级生成；现有 CLDR region/overseas 节点通过官方代码映射，无法映射的旧节点写入未映射清单。语言名称优先使用官方法文；现有名称只在同一实体 ID 保留时继承。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/FR.json sources/raw/official/fr sources/migrations/FR.json \
  tool/importers/fr.py tests/fixtures/official/fr tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/FR.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete FR official communes"
```

Expected: 只创建 FR 数据 Commit；不引入 CSC ODbL 数据。

---

### Task 8: Batch 4c IT

**Files:**
- Create: `config/region_profiles/IT.json`
- Create: `sources/raw/official/it/`
- Create: `sources/migrations/IT.json`
- Create: `tool/importers/it.py`
- Create: `tests/fixtures/official/it/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/IT.json`, `data/i18n/*/IT.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.it.build(root)`，comune 使用 `it-comune:{six-digit-ISTAT-code}`。

**来源门禁：** ISTAT 官方 comuni/province 年度发布，许可需为兼容再分发的 CC BY 或等价官方开放许可。必须采用数据自身的行政区层级，不采用候选层中的历史实体或城市清单。

- [ ] **Step 1: 写 IT fixture 和失败测试**

fixture 包含 region、province、comune，以及一个已废止/合并 comune。测试断言废止代码不进入活动节点，Sardinia 等改革实体的父链由官方字段决定。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，IT adapter 尚不存在。

- [ ] **Step 3: 实现 IT 适配器**

保留 20 个 region 和可精确映射的 province ID；新增 comune。官方名称使用意大利文；历史名称作为 alias 仅在源明确提供时写入，不按名称相似度生成。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/IT.json sources/raw/official/it sources/migrations/IT.json \
  tool/importers/it.py tests/fixtures/official/it tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/IT.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete IT official comuni"
```

Expected: 只创建 IT 数据 Commit；无历史城市批量混入。

---

### Task 9: Batch 5a RU

**Files:**
- Create: `config/region_profiles/RU.json`
- Create: `sources/raw/official/ru/`
- Create: `sources/migrations/RU.json`
- Create: `tool/importers/ru.py`
- Create: `tests/fixtures/official/ru/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/RU.json`, `data/i18n/*/RU.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.ru.build(root)`，下级 ID 使用 `ru-municipality:{OKTMO}`。

**来源门禁：** Rosstat 官方 OKTMO/行政区划发布。许可和再分发权利必须确认；来源必须保持现有 83 个 CLDR territorial profile，不通过增加或删除联邦主体表达另一口径。

- [ ] **Step 1: 写 RU fixture 和失败测试**

fixture 包含现有 83 个主体中的代表项、一个区和一个市，以及一个无法映射到现行主体的旧代码。测试断言跨国或缺失父链失败，无法映射记录标记 `unmapped`。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，RU adapter 尚不存在。

- [ ] **Step 3: 实现 RU 适配器**

仅把官方下级挂接到可精确映射的现有 83 个主体；不能精确映射的主体保持原状并记录 `unknown`。官方名称使用俄文；不引入另一来源的领土解释。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/RU.json sources/raw/official/ru sources/migrations/RU.json \
  tool/importers/ru.py tests/fixtures/official/ru tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/RU.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete RU official municipal districts"
```

Expected: 只创建 RU 数据 Commit；83 个既有主体 ID 和范围不发生未申报变化。

---

### Task 10: Batch 5b SA

**Files:**
- Create: `config/region_profiles/SA.json`
- Create: `sources/raw/official/sa/`
- Create: `sources/migrations/SA.json`
- Create: `tool/importers/sa.py`
- Create: `tests/fixtures/official/sa/nodes.csv`
- Modify: `tool/import_data.py`, `sources/source-lock.json`
- Modify: `data/regions/SA.json`, `data/i18n/*/SA.json`, 全局派生产物

**Interfaces:**
- Consumes: 公共适配器契约。
- Produces: `tool.importers.sa.build(root)`，governorate 使用 `sa-governorate:{official-code}`。

**来源门禁：** 沙特统计总局或内政部官方行政区/省数据。许可需明确允许再分发；13 个 region ID 必须保留。官方源若无法给出 governorate 父链，则不扩展到 governorate。

- [ ] **Step 1: 写 SA fixture 和失败测试**

fixture 包含 13 个 region 中的代表项、一个 governorate 和一个缺失父链的 governorate。测试断言缺失父链失败，13 个既有 region ID 保留。

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_official_imports -v`
Expected: FAIL，SA adapter 尚不存在。

- [ ] **Step 3: 实现 SA 适配器**

按官方 region 代码保留现有节点，新增有官方父链的 governorate。名称使用阿拉伯文官方名；没有官方父链的城市不生成节点。

- [ ] **Step 4: 重建、验证并提交**

```bash
python3 -m unittest tests.test_official_imports -v
python3 tool/import_data.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
git add config/region_profiles/SA.json sources/raw/official/sa sources/migrations/SA.json \
  tool/importers/sa.py tests/fixtures/official/sa tests/test_official_imports.py \
  tool/import_data.py sources/source-lock.json data/regions/SA.json data/i18n \
  data/manifest.json sources/coverage-report.json docs/DATA_COVERAGE.md docs/DATA_SOURCES.md
git commit -m "feat(data): complete SA official governorates"
```

Expected: 只创建 SA 数据 Commit；13 个 region 无未解释删除。

---

### Task 11: Batch 6 全量集成与 PR

**Files:**
- Modify: `docs/DATA_SOURCES.md`, `docs/DATA_COVERAGE.md`
- Modify: PR 描述，不修改数据文件

**Interfaces:**
- Consumes: 十个国家 Commit、所有锁定来源和迁移记录。
- Produces: 一个可审阅 PR 和完整验证记录。

- [ ] **Step 1: 核对提交序列**

```bash
git fetch origin main
git log --oneline --reverse origin/main..HEAD
git status --short --branch
```

Expected: 设计、计划提交在前；恰好十个国家数据 Commit；无无关文件；远端主分支未出现需处理的冲突。

- [ ] **Step 2: 运行全量检查**

```bash
python3 tool/check_readiness.py
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema --report build/reports/data-validation.json
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
python3 tool/geo_data.py validate --production
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py offline --config config/offline.example.json --out build/offline-assets
node demo/web_preview/test_logic.cjs
flutter test
```

Expected: 除 `--production` 必须按设计拒绝外，其余命令成功。Flutter 不可用时记录 `blocked`，不得写成通过。

- [ ] **Step 3: 核对来源、许可和迁移完整性**

```bash
python3 -c 'import json; from pathlib import Path; print([p.stem for p in Path("config/region_profiles").glob("*.json")])'
git diff --stat origin/main...HEAD
git diff origin/main...HEAD -- sources/source-lock.json docs/DATA_SOURCES.md
```

Expected: 十国 Profile 全部存在；source-lock 中每个新增来源均有许可、版本、日期、SHA 和字节数；差异中没有 ODbL CSC 数据。

- [ ] **Step 4: 推送并创建 PR**

```bash
git push origin feat/ten-country-official-regions
PR_URL=$(ag pr create -t "feat(data): complete official regions for ten countries" -b "Implements docs/superpowers/specs/2026-11-16-ten-country-official-region-completion-design.md. Adds one official-source data commit per country, fixed source evidence, explicit ID migrations, and offline-reproducible generated data. Remains research-seed; production gate still rejects the dataset." | tail -n 1)
test -n "$PR_URL"
printf '%s\n' "$PR_URL"
```

PR 描述正文必须逐国追加：来源、许可、版本/生效日期、抓取日期、Profile、节点和层级变化、迁移数量、实际验证结果、阻塞项。若 PR 创建工具不能直接设置完整描述，先创建草稿，再用 CLI 的 PR 编辑能力补齐后才请求评审。

- [ ] **Step 5: 验证 PR**

从 Step 4 输出的 PR URL 读取末尾编号并导出为 `PR_NUMBER`，然后执行：

```bash
test -n "$PR_NUMBER"
ag pr checks imboy/geo_regions "$PR_NUMBER" --watch
ag pr view imboy/geo_regions "$PR_NUMBER"
```

Expected: PR 仅包含功能分支；检查结果可追溯。失败项按日志修复后在有意义的国家 Commit 中提交，不伪造通过状态。

---

## 失败与暂停条件

遇到以下任一情况，立即暂停当前国家并报告，不进入下一个国家：

- 官方来源无法固定到具体版本、发布日期或生效日期。
- 许可不允许再分发或未明确覆盖派生 JSON。
- 目标层的官方父链缺失且无法通过官方字段恢复。
- 旧 ID 需要按名称猜配、复用或静默改父。
- 新结构需要改变国家清单、territorial profile 或 datasetId。
- 只有 ODbL CSC、无来源 AI 名称或未审城市清单可填补缺口。

暂停后保留已完成国家的 Commit 和验证证据，向用户提供来源、缺口和可选决策，不创建虚假数据提交。