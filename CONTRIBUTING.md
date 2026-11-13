# Contributing / 参与贡献

欢迎问题报告、代码、数据、翻译、文档和测试贡献。请先读 [PRD](docs/PRD.en.md)、[协议](docs/PROTOCOL.md) 和 [数据规则](docs/DATA_RULES.md)。Contributions of all these kinds are welcome; read the protocol and data rules first.

## Small, reviewable changes / 小范围可审阅改动

说明问题、改动行为、兼容性和验证方法。一个国家或一种语言的独立改动尽量单独提交。只修改与本次目标相关的文件，保留现有版权和来源。

Explain the problem, behavioral change, compatibility and validation. Prefer one country or locale per focused data change. Preserve notices and provenance.

## Code / 代码

原创代码贡献以根LICENSE的BSD-3-Clause提供，贡献者保留版权。主Flutter包运行时只依赖SDK。先复用测试，只有实际行为/风险变化才补有意义的测试。No separate CLA is required by this baseline.

## Data and names / 数据与名称

附不可变源链接、commit/version、license、源日期、抓取日期、转换说明及差异报告。翻译没有来源就保持缺失；机器生成、音译、简繁转换明确标候选，不能冒充人工审核。父级/ID更改必须有兼容方案，不按名称猜测删除或合并。

Include immutable sources, licenses, dates, transformations and diffs. Preserve unknowns. Machine-generated candidates require explicit labeling and review. Identity and parent changes require migration handling.

## Before opening a PR / 提交前

```bash
python3 tool/import_data.py --check
python3 tool/geo_data.py validate --schema
python3 -m unittest discover -s tests -v
node demo/web_preview/test_logic.cjs
```

Flutter改动还需format/analyze/test和Demo Web构建；生产SDK存在后按CI运行库测试。Schema校验依赖见tool/requirements-ci.txt。Record any unavailable check as blocked; do not mark it passed.

## Review / 评审

维护者检查语义、来源、许可、质量与兼容性。测试通过不自动证明地理现势或译名准确；缺少源证据可请求补充。欢迎任何人参与，不保证每一项提交自动合并。
