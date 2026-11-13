# 提示词与执行结果质量规则 / Prompt and execution quality

提示词是工作约束，不是质量证明。分数用来发现缺项；最终通过由真实产物和验收决定。Prompt quality does not replace execution evidence.

| Dimension / 维度 | Weight | Observable criterion / 可观察标准 |
|---|---:|---|
| Scope and output / 范围输出 | 15 | 命名输入、目录、任务ID、目标产物与非目标 |
| Source and license / 来源许可 | 20 | 确切源、version/commit、license、dates、hash，不可得时如何处理 |
| Identity and contract / 身份契约 | 15 | stable IDs、root path、revision、locale、quality、兼容性 |
| Ownership and resume / 所有权续跑 | 15 | 独立staging/文件所有权、固定taskID、state、恢复与冲突策略 |
| Verification / 验证 | 20 | 真实命令、正负例、证据位置、PASS/FAIL/SKIP/BLOCKED区分 |
| Truthful reporting / 如实报告 | 15 | 缺失不编造、机器候选不假装审核、未运行不假装成功 |

建议阈值90/100，但以下任何一项都直接失败：无许可的数据进入生产；以名称/数组序号作地区identity；复制英语冒充多语；改`compatibleRevision`但不验证；删除测试/质量门禁刷绿；覆盖用户未授权改动；伪造task面板、截图、测试或CI结果；用seed声称全球完成。

Suggested score: at least 90/100, with no hard failures. A high score cannot override missing license, fabricated data, unstable identity, bypassed validation, overwritten work or fabricated evidence.

每个提示词输出必须给出：可审阅文件、实际命令与结果、覆盖与限制、源依据、下一步；不用“任务已全部完成”代替这些证据。独立reviewer至少复验一个最可能出错的关键约束，而不是重复作者的全部低价值检查。

For each work package, retain reviewable files, actual results, coverage/limitations, source evidence and the next action. Independent review should target a concrete failure risk. Do not run broad redundant tests just to inflate test counts.
