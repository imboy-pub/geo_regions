# 数据与工具实测记录 / Executed data and tooling checks

UTC: 2026-11-13T03:42:12.686284+00:00

这些是实际本地执行结果；不表示 Flutter、真实浏览器布局、GitHub 在线 CI 或公开发布已经通过。
These are local execution results, not Flutter/browser-layout/hosted-CI/publication evidence.

| Check | Result |
|---|---|
| pinned source offline reproducibility | PASS |
| schema and data integrity | PASS |
| manifest matches all resources | PASS |
| actual Japan persisted selection | PASS |
| tooling boundary tests | PASS |
| declared package readiness | PASS |
| production seed rejection expected | PASS (expected rejection) |
| selected offline payload | PASS |
| reference demo behavior (not Flutter or browser) | PASS |
| YAML syntax parse (not hosted workflow execution) | PASS |
| explicit asset entries and license notices | PASS |
| data release assembly | PASS |
| data release extracted offline reproducibility | PASS |
| data release extracted schema and integrity | PASS |
| release ZIP checks | PASS |
| CI scope selection from real temporary Git commits (7 cases) | PASS |

44 项 Python 测试通过（27 项数据/工具边界，17 项状态/安装器安全回归）；seed 的 production 校验按预期返回非零，证明没有将研究种子误算为生产就绪。
Forty-four Python tests passed: 27 data/tooling boundary cases and 17 state/installer safety regressions. The expected nonzero production gate confirms this research seed is not silently accepted as production data.

完整命令和输出见 `tooling-validation.json`；数据覆盖汇总见 `data-validation.json`。
See tooling-validation.json for exact commands/output and data-validation.json for coverage.
