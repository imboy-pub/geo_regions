# ZCODE 续跑提示词

继续固定任务 `geo-regions-v1`，主仓库 `/Users/leeyi/project/imboy.pub/geo_regions`。

先读取有效AGENTS.md、git状态、worktree记录、`docs/PLAN.zh-CN.md`、`.plans/geo-regions-v1/tasks.json`和已有state/evidence。优先复用`task/geo-regions-v1`及它已经使用的worktree，不按日期创建新RUN_ID，不重新初始化或覆盖状态，不删除其他工作树。

运行`python3 tool/plan_status.py status --json`与`verify-evidence`；证据hash通过仍须检查输入代码/数据是否变化。已失效任务reopen并复验，保留历史。先用ZCODE本会话实际提供的任务工具恢复可见面板；没有工具就明确说明并显示ID状态清单，不伪造面板操作。

沿用`prompts/ZCODE_START.zh-CN.md`全部约束，从第一个真正未完成且前置已满足的任务继续，最多两个worker。第一节点Demo尚未实际验收时优先完成；不要用HTML/Node结果冒充Flutter结果，不把research-seed冒充production，不因为只有blocked设备项就停止所有独立工作。

每次推进写state和证据。继续已授权实现、测试和修复，不在普通步骤间反复确认。遇真实不可消除阻塞先完成独立工作，再说明缺什么、已尝试什么、哪个任务受影响。最终给当前结果和下次续跑所需事实，不重写整份计划。
