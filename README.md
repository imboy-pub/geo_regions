# geo_regions · PRD、计划、数据与工程启动包

**交付日期：2026-11-13。文档仅Markdown。包名已确定为`geo_regions`，代码沿用BSD-3-Clause。**

这是一套可供ZCODE直接接续实施的工程基线：双语PRD/两阶段计划、Demo原型、真实十国种子数据、十语文件、数据工具与测试、CI/CD配置和提示词。**生产Flutter SDK尚待实施；本包的数据成熟度为research-seed。** 不把种子包、HTML预览或本地工具检查称为已发布生产库。

This is an executable development handoff: bilingual requirements/plan, a Demo prototype, real ten-country data, ten locale sets, reproducible tools/tests, CI/CD and execution prompts. The production SDK remains a Phase 1 implementation task; the data is a research seed.

## 1. 从哪里开始 / Start here

| Need / 需求 | File |
|---|---|
| PRD中文 / Chinese PRD | [docs/PRD.zh-CN.md](docs/PRD.zh-CN.md) |
| PRD英文 / English PRD | [docs/PRD.en.md](docs/PRD.en.md) |
| Plan中文 / Chinese plan | [docs/PLAN.zh-CN.md](docs/PLAN.zh-CN.md) |
| Plan英文 / English plan | [docs/PLAN.en.md](docs/PLAN.en.md) |
| 使用者协议 / Consumer contract | [docs/PROTOCOL.md](docs/PROTOCOL.md) |
| Demo与设计 / Demo and UX | [demo/README.md](demo/README.md), [docs/DEMO_UX.md](docs/DEMO_UX.md) |
| 真实覆盖及来源 / Coverage and sources | [docs/DATA_COVERAGE.md](docs/DATA_COVERAGE.md), [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) |
| 工具与扩展 / Tooling and extension | [docs/TOOLING.md](docs/TOOLING.md), [docs/DATA_RULES.md](docs/DATA_RULES.md), [docs/DATA_WORKPACKAGES.md](docs/DATA_WORKPACKAGES.md) |
| ZCODE启动 / Start | [prompts/ZCODE_START.zh-CN.md](prompts/ZCODE_START.zh-CN.md) |
| 新会话续跑 / Resume | [prompts/ZCODE_RESUME.zh-CN.md](prompts/ZCODE_RESUME.zh-CN.md) |
| 国家/语言/审查提示词 / Worker prompts | [ADD_COUNTRY](prompts/ADD_COUNTRY.zh-CN.md), [ADD_LOCALE](prompts/ADD_LOCALE.zh-CN.md), [REVIEW_DATA](prompts/REVIEW_DATA.zh-CN.md) |
| 代码/数据许可 / Licensing | [docs/LICENSE_POLICY.md](docs/LICENSE_POLICY.md), [CONTRIBUTING.md](CONTRIBUTING.md) |
| GitHub CI/CD | [docs/CI_CD.md](docs/CI_CD.md) |
| IMBoy改造 / Integration | [docs/IMBOY_INTEGRATION.md](docs/IMBOY_INTEGRATION.md) |
| 本轮实际验收 / Actual verification | [reports/DELIVERY_VALIDATION.md](reports/DELIVERY_VALIDATION.md), [reports/TOOLING_VALIDATION.md](reports/TOOLING_VALIDATION.md) |

## 2. 第一节点就是Demo / Demo first

无需Flutter可先用浏览器打开 [demo/web_preview/index.html](demo/web_preview/index.html) 查看交互参考；它没有外链依赖，直接本地打开即可。含明暗、十语主要文案、RTL、国家/地区导航、路径、搜索、离线/失败模拟及确认。

真正Flutter原型在`demo/flutter`，与参考HTML分开。当前交付环境没有Flutter/Dart；格式化、分析、5项Widget测试与Web构建尚未运行。真实浏览器视觉检查也受环境限制，详见报告。**P1-01必须在ZCODE本地环境先跑通并修正这些项，不能把原型文件存在当作验收完成。**

```bash
cd demo/flutter
bash bootstrap.sh
dart format lib test
flutter analyze --fatal-infos
flutter test
flutter build web --release
flutter run -d chrome
```

运行设备以`flutter devices`实际结果为准。数据fixture独立namespace，不写入IMBoy账号。HTML/Node检查不代替Flutter/设备结果。

## 3. 数据已实际整理 / Real data included

10国：CN、JP、KR、US、GB、DE、FR、IT、RU、SA。共4,143节点（含10个国家root），100个地区名称包，10个小型国家目录名称包。结构可变层级；CN含统计分组及部分九位乡镇节点。

10语：zh-Hans、zh-Hant、en、ja、ko、ru、de、fr、it、ar。国家目录名称覆盖完整；地区译名不是每国每节点十语完整。繁中显式地区名称当前仅13/4,143；CN非中文深层仍有大量缺口。所有quality与缺失数真实保留，未复制英语填满。

CN深层源是2023-06-30历史快照；当前不声称2026现势。CLDR 49不少XML名称仍为provisional；生产默认过滤低质量状态。本包保留36份固定原始源、完整hash、许可和转换器，可完全离线重建。

## 4. 安全导入你的仓库 / Import without overwriting

先解压到仓库之外，例如`~/Downloads/geo_regions_delivery`。目标仓库已经存在并有正确origin。不要直接用解压覆盖现有工作文件。

```bash
python3 ~/Downloads/geo_regions_delivery/tool/install_bundle.py \
  --target /Users/leeyi/project/imboy.pub/geo_regions --dry-run
python3 ~/Downloads/geo_regions_delivery/tool/install_bundle.py \
  --target /Users/leeyi/project/imboy.pub/geo_regions --apply
```

工具只创建缺失文件，同字节文件保持不动；任何冲突预检即停止且不写入。不会commit、push、删除worktree或覆盖已有state。若解压路径不同，替换命令中的源路径。冲突由ZCODE读取差异后按本次范围合并，不用`--force`解决。

导入后把[主执行提示词](prompts/ZCODE_START.zh-CN.md)交给ZCODE。原生任务面板是否存在取决于ZCODE实际工具；提示词要求先发现真实能力再显示14个任务，磁盘state则始终可续跑。

## 5. 先验证输入 / Validate the handoff

开发工具要求Python 3.10+；Node用于Demo行为检查；Flutter CI固定3.41.5。Python及JSON Schema依赖只用于开发，不进入Flutter主包runtime。

```bash
cd /Users/leeyi/project/imboy.pub/geo_regions
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r tool/requirements-ci.txt
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 tool/geo_data.py manifest --check
python3 tool/geo_data.py selection --file samples/selection.JP.json --schema
python3 -m unittest discover -s tests -v
node demo/web_preview/test_logic.cjs
python3 tool/plan_status.py init
python3 tool/plan_status.py status
```

`validate --production`会**按预期拒绝**当前research-seed；这不是应删除的门禁。

## 6. 配置离线与在线资源 / Configure offline/online resources

`config/offline.example.json`默认选择CN结构、CN简繁英名称、十语国家目录小包。生成工具会复制实际所选文件、两个用途不同的manifest/registry、许可，并给出完整asset条目。

```bash
python3 tool/geo_data.py offline \
  --config config/offline.example.json \
  --out generated/geo_regions_assets --dry-run
python3 tool/geo_data.py offline \
  --config config/offline.example.json \
  --out generated/geo_regions_assets
```

合并`assets.fragment.yaml`条目到宿主已有的`flutter.assets`；不能新增第二个`flutter:`根，也不能把全量`data/`声明为assets。后续重跑只对带生成标记的目录使用`--replace`。远程资源base/loader/store/verifier由Phase1 SDK及宿主适配，当前生成器不等于运行时SDK。

## 7. CI/CD交付状态 / CI/CD status

CI配置包含数据重建/Schema/语义/hash/selection/测试、按变更范围运行Flutter、始终报告的required gate；同PR旧任务可取消，权限最小化，Action按完整SHA固定。CD对data tag执行同提交验证与打包，创建**草稿Release**，不覆盖同名release，不自动发布pub.dev。

这些工作流已完成本地配置/解析/工具验收，**本轮未推送或执行GitHub Actions，也未更改仓库设置**。首次导入推送后的实际Actions结果、required status check和tag ruleset等现场设置，按CI_CD文档完成。发布数据与代码版本独立。
