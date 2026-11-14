# datasets/csc-candidate — 九国候选数据集（审阅材料）

这是 `geo-regions-source-audit-v1` 任务产出的**研究候选数据集**的审阅材料目录。
它与仓库根 `data/`（正式数据集 `geo-regions-seed`，SDK/CI 消费）的关系：

| | `data/`（正式） | `datasets/csc-candidate/`（候选） |
|---|---|---|
| datasetId | `geo-regions-seed` | `geo-regions-csc-candidate` |
| 角色 | 产品交付层，SDK/demo/CI 消费 | 十语准备与校对的候选层，**不并入正式层** |
| 许可 | CLDR+历史源混合 | ODbL 为主（CSC）+ CLDR catalog |
| 成熟度 | production 口径门禁 | research-seed（production gate 应拒绝） |
| 生成 | `tool/import_data.py` ← `sources/raw/` | `tool/build_csc_candidate.py` ← `staging/csc-snapshot/` |

## 目录内容（入 git 的部分）

- `SOURCES_NOTICE.md` — 来源与许可声明（ODbL/Unicode-3.0 分层，不混标）
- `DATA_VERIFICATION_2026.md` — 九轮真实性与 2026 现势对账全记录（含 selfCorrections 台账）
- `PROOFREADING_REPORT.md` — AI 翻译校对报告（288 条逐条判定 + LIVE FIGURES）
- `proofreading_queue.json` — P0-P3 人工审校工作队列
- `verification_*.json` — 网络取证原件（P300 批量 / FR INSEE / JP Geolonia / US Census / DE / IT）

## 数据体（不入 git，本地再生）

`data/` 与 `config/`（~72MB 协议 1.0 数据体：93,683 节点、90+10 语言包）是
**派生物**，由生成器从固定快照一键再生：

```sh
python3 tool/build_csc_candidate.py      # 需要 staging/csc-snapshot/（见 fetch_manifest.json）
python3 tool/geo_data.py validate datasets/csc-candidate
```

真源 = 生成器 + `staging/csc-snapshot/`（24/24 文件 sha256 固定）。可再生 JSON
（coverage/抽样/一致性清单）同样不入 git。

## 与正式层的关系边界

候选层**永不直接并入** `data/`：datasetId、许可口径（ODbL share-alike）、成熟度
（research-seed）三者都不同。未来若决策采纳某部分，须按 `docs/UPDATE_RUNBOOK.md`
的更新合同逐项走迁移审校，且 CN 历史低层数据（`data/` 独有）不受影响。
