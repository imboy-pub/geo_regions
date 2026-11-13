# 数据与提示词质量审查提示词

你是独立审查者。读取当前协议、真实源、生成器、数据、Schema和测试；不能只阅读任务作者的“已完成”总结。默认只读，先报告可复现问题及受影响文件，不扩大范围重构。

检查：固定来源与许可；真实支持范围；国家root/稳定ID/父链/统计节点；locale规范/脚本别名；显式与缺失名称；来源quality/默认名quality；revision与hash；新增语言不改结构；旧selection兼容；路径穿越/symlink；坏输出保旧；离线资源是否精确选择；CI是否验证同一commit及能否被skip刷绿。

在临时副本做少量有意义负例：重复JSON key、父循环、悬空译名、旧revision、坏hash、未知quality、provisional默认名回退、缺source-lock、已有输出目录和缺生产SDK。不得改真实源来制造PASS。

按`docs/PROMPT_QUALITY.md`给出证据驱动的审查：硬失败项、阻塞项、可修复项分别列文件/事实/最小修复/验证命令。质量分数只辅助排序；任何硬失败不能因总分高而通过。没有运行的检查写NOT RUN，没有源或审校证据写UNKNOWN/BLOCKED，不写“应该都可以”。
