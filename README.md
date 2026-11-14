# geo_regions · PRD、计划、数据与工程基线

**Phase 1 已完成（2026-11-14，本地 main 26+ commit）。代码 BSD-3-Clause，数据按来源分层许可，协议 1.0 冻结，生产就绪门禁已开启（`productionSdkExpected=true`）。数据成熟度分层明确：正式层 research-seed，候选层独立管理。**

Phase 1 is complete (2026-11-14, local main). Code is BSD-3-Clause, data licensing is layered by source, protocol 1.0 is frozen, and the production-readiness gate is on. Data maturity is explicit: the product layer stays research-seed, the candidate layer is managed separately.

## 1. 从哪里开始 / Start here

| Need / 需求 | File |
|---|---|
| PRD中文 / Chinese PRD | [docs/PRD.zh-CN.md](docs/PRD.zh-CN.md) |
| PRD英文 / English PRD | [docs/PRD.en.md](docs/PRD.en.md) |
| Plan中文 / Chinese plan | [docs/PLAN.zh-CN.md](docs/PLAN.zh-CN.md) |
| Plan英文 / English plan | [docs/PLAN.en.md](docs/PLAN.en.md) |
| 协议 / Protocol | [docs/PROTOCOL.md](docs/PROTOCOL.md) |
| 消费者契约 / Consumer contract | [docs/CONSUMER_CONTRACT.md](docs/CONSUMER_CONTRACT.md) |
| Demo 与设计 / Demo and UX | [demo/README.md](demo/README.md), [docs/DEMO_UX.md](docs/DEMO_UX.md) |
| **演示站 / Demo site** | [docs/PAGES_DEMO.md](docs/PAGES_DEMO.md)（上线后 https://imboy-pub.github.io/geo_regions/） |
| 覆盖与来源 / Coverage and sources | [docs/DATA_COVERAGE.md](docs/DATA_COVERAGE.md), [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) |
| 工具与扩展 / Tooling and extension | [docs/TOOLING.md](docs/TOOLING.md), [docs/DATA_RULES.md](docs/DATA_RULES.md), [docs/DATA_WORKPACKAGES.md](docs/DATA_WORKPACKAGES.md) |
| **源更新合同 / Update contract** | [docs/UPDATE_RUNBOOK.md](docs/UPDATE_RUNBOOK.md) |
| Phase 1 发布候选 / Release candidate | [docs/RELEASE_CANDIDATE_P1.md](docs/RELEASE_CANDIDATE_P1.md), [docs/RELEASE_NOTES_TEMPLATE.md](docs/RELEASE_NOTES_TEMPLATE.md) |
| **九国候选数据集 / Candidate dataset** | [datasets/csc-candidate/README.md](datasets/csc-candidate/README.md) |
| ZCODE 启动 / Start | [prompts/ZCODE_START.zh-CN.md](prompts/ZCODE_START.zh-CN.md) |
| 新会话续跑 / Resume | [prompts/ZCODE_RESUME.zh-CN.md](prompts/ZCODE_RESUME.zh-CN.md) |
| 国家/语言/审查提示词 / Worker prompts | [ADD_COUNTRY](prompts/ADD_COUNTRY.zh-CN.md), [ADD_LOCALE](prompts/ADD_LOCALE.zh-CN.md), [REVIEW_DATA](prompts/REVIEW_DATA.zh-CN.md) |
| 代码/数据许可 / Licensing | [docs/LICENSE_POLICY.md](docs/LICENSE_POLICY.md), [CONTRIBUTING.md](CONTRIBUTING.md) |
| GitHub CI/CD | [docs/CI_CD.md](docs/CI_CD.md) |
| IMBoy 改造 / Integration | [docs/IMBOY_INTEGRATION.md](docs/IMBOY_INTEGRATION.md) |

## 2. Demo 与演示站 / Demo and site

浏览器直接打开 [demo/web_preview/index.html](demo/web_preview/index.html)（自包含静态原型，无外链）。完整交互 demo 在 `demo/flutter`（Flutter 3.50.0，190+11 测试绿，`?locale=ar&dark=1&semantics=1` 深链可用）。

GitHub Pages 演示站：push main 后由 [.github/workflows/pages.yml](.github/workflows/pages.yml) 自动构建部署（仓库 Settings→Pages→Source=GitHub Actions 一次性开启）；`/preview/` 提供静态原型。详见 [docs/PAGES_DEMO.md](docs/PAGES_DEMO.md)（含 gitee Pages 现状说明）。

The browser can open the self-contained prototype directly. The full Flutter demo builds green on 3.50.0; GitHub Pages deploys it automatically on push (one-time repo setting required). See docs/PAGES_DEMO.md for the gitee situation.

## 3. 两层数据 / Two data layers

**正式层 `data/`（geo-regions-seed）**：10 国 4,143 节点，100 地区语言包，10 国家名录包，结构可变层级；CN 含统计分组与部分九位乡镇节点（2023-06-30 历史快照，不声称现势）。CN 市/县级已叠加 GeoNames 机器匹配罗马字到全部拉丁语系（en/fr/de/it，3,062 条 `provisional`，CC-BY-4.0，提取件逐字节钉死）；zh-Hant 全线为 zh-Hans 的记录式保守简繁转换（tool/s2t_places.py，歧义字保持原形，`provisional`）；非拉丁语系（ja/ko/ru/ar）保持诚实回退待真实转写。demo 对 provisional 名明确 opt-in，UI 以徽标如实标注（未翻译回退 / provisional 暂定）。CLDR 49 的 provisional 译名默认被生产门禁过滤；所有 quality 与缺失数真实保留。

**候选层 `datasets/csc-candidate/`（geo-regions-csc-candidate）**：9 国 93,683 节点三层（states/counties/cities），FR 已切 INSEE 2026 现势（34,920 commune）、JP 已切 Geolonia 全量市区町村、KR 已修 17 广域团体；十语覆盖 en 100% / zh-Hant 57,255 machine-candidate / 其余 83-86% provisional。**派生数据体不入 git**——由 [tool/build_csc_candidate.py](tool/build_csc_candidate.py) 从固定快照再生，层级边界与再生配方见 [datasets/csc-candidate/README.md](datasets/csc-candidate/README.md)。

The product layer (data/) is the frozen research seed with full provenance. The candidate layer (datasets/) is the nine-country deep-region dataset with official 2026 layers for FR/JP; its body is derived and regenerable, only documents and evidence are versioned.

## 4. 验证门禁 / Gates

```bash
python3 tool/import_data.py --check          # 从锁定源复现正式层
python3 tool/geo_data.py validate --schema   # Schema+语义门
python3 tool/check_readiness.py              # 包存在性+maturity tripwire
python3 tool/geo_data.py manifest --check    # manifest 完整性
python3 -m unittest discover -s tests -v     # 70 tests
node demo/web_preview/test_logic.cjs         # demo 行为检查
python3 tool/semantic_audit.py check --report build/reports/semantic.json   # 语义/身份/回退（CLDR sample profile）
```

`validate --production` 会**按预期拒绝**当前数据（research-seed；tripwire 由 `expectedProductionGateRefusal` 把守）——这不是应删除的门禁，正式数据需经审校翻转开关。语义审计（`tool/semantic_audit.py`）与源更新演练（`tool/update_rehearsal.py --selftest`）见 [docs/UPDATE_RUNBOOK.md](docs/UPDATE_RUNBOOK.md)。

## 5. CI/CD 与离线资源 / CI/CD and offline assets

CI（`.github/workflows/ci.yml`，Flutter 3.50.0）：数据重建/Schema/语义/hash/selection/测试、按变更范围运行 Flutter、required gate；Actions 按完整 SHA 固定。演示站部署独立工作流（pages.yml）。CD 对 data tag 执行同提交验证与打包，创建**草稿 Release**，不自动发布 pub.dev。

离线资产：`config/offline.example.json` + `python3 tool/geo_data.py offline --config config/offline.example.json --out generated/geo_regions_assets`；合并 `assets.fragment.yaml` 到宿主 `flutter.assets`，不能声明第二个 `flutter:` 根或全量 `data/`。远程 base/loader/store/verifier 由宿主适配。

## 6. 历史与边界 / History and boundaries

- 交付基线（2026-11-13 包）的原始双语 PRD/Plan 保留在 [docs/PRD.*.md](docs/PRD.zh-CN.md) 与 [docs/PLAN.*.md](docs/PLAN.zh-CN.md)；历史交付包已删除，**git 仓库是唯一真源**。
- 本机没有第二份"交付副本"；`_task_packages/` 与 `staging/` 是本地瞬态目录（gitignored），不作为仓库文档。
- 文档治理审计：git 跟踪文档内链接完整；审计器对 gitignored 瞬态目录（staging/_task_packages 内部相对链接）的告警不属仓库文档范畴。
