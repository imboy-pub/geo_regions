# 固定任务状态 / Persistent task state

`tasks.json`是14节点任务定义，不是已完成证明。`tool/plan_status.py init`首次创建state；重跑保留现有状态。state/evidence默认不入Git，但保留在实际执行worktree磁盘，供新会话继续。跨机器恢复需由用户提供这些状态与证据，不能仅凭聊天总结推断。

```bash
python3 tool/plan_status.py init
python3 tool/plan_status.py status
python3 tool/plan_status.py start P1-01
```

真实验证后才记录完成，例如（先实际创建该证据文件）：

```bash
python3 tool/plan_status.py complete P1-01 \
  --evidence .plans/geo-regions-v1/evidence/P1-01/result.md \
  --command 'flutter analyze --fatal-infos && flutter test && flutter build web --release' \
  --note 'Actual commands/results and UX scope are recorded in result.md'
```

这个helper不运行上述字符串，不验证测试真的成功；协调者必须核对日志。文件hash也不自动证明当前源码仍与当时输入一致。

```bash
python3 tool/plan_status.py verify-evidence
python3 tool/plan_status.py reopen P1-01 --note 'Inputs changed; rerun affected checks'
```

reopen会使传递下游任务回到pending，并保留历史，避免前置失效下游仍保持假completed。block已completed任务会拒绝，需先reopen。state锁若遗留先检查PID/会话和工作区，没有证据不要盲删。

Mirror IDs/status to ZCODE's actual task UI if available. The JSON file itself does not create a UI task panel. Do not invent unavailable task-tool calls.
