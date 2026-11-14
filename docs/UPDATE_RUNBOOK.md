# 源更新执行手册 / Source-update runbook

本文把来源审计任务 `geo-regions-source-audit-v1`（GSA-04）固化的升级合同变成可执行步骤。适用对象：任何一次真实的 CLDR/来源快照更新（生产数据根或 audit-sample 形状的数据根）。

## 0. 前提 / Preconditions

- 操作的数据根必须携带 audit sidecar：`audit/node_metadata.json`、`audit/identity_registry.json`（当前仓库 `geo-regions-seed` 数据集**尚无** sidecar——为 seed 引入身份登记属于 Phase 2 决策，见 §4）
- 新快照必须是固定 commit + URL + SHA-256 + 许可（`sources/source-lock.json` 记录）；禁止"最新 main"这类浮动引用
- 永远在旧 root 的一份拷贝上生成新 root；旧 registry 与 retired 条目**永不重建或清空**

## 1. 演练（不改任何数据）/ Rehearse

```sh
python3 tool/update_rehearsal.py --selftest
```

脚本用合成 fixture（临时目录，testOnly 标记）证明两件事：

- **场景 A**：未申报的节点删除被 `check` 当场拦截（active registry 必须 exact-match）
- **场景 B**：申报退役（registry `status=retired` + `audit/migrations.json` 逐变更 review 证据）可以放行，`reviewedMigrationRecords` 覆盖全部 breaking changes

## 2. 真实更新步骤 / Real update

1. 固定新快照入 `sources/raw/`，更新 `sources/source-lock.json`（commit/URL/sha256/sizeBytes/license）
2. 在旧 root 拷贝上重跑生成/导入流程，更新受影响数据
3. 一键合同检查（把当前 HEAD 固定为 old-root，工作树为 new-root，或显式传两目录）：

```sh
git archive HEAD | tar -x -C /tmp/geo-old-root   # 或任意固定基线
python3 tool/update_rehearsal.py --old-root /tmp/geo-old-root --new-root .
```

4. 结果判读：
   - `breakingChanges` 为空且 `policyChanged=false` → 直接合入
   - `breakingChanges` 全部有对应 `reviewedMigrationRecords` → 合入时附带迁移文档
   - 任一 BLOCKED → 按 VALIDATION_RULES §2 补逐变更迁移证据，**不得**放宽校验或重建 registry
5. maturity 语义由 `config/readiness.json` 的 `expectedProductionGateRefusal` 把守（`tool/check_readiness.py` 在 CI 强制）：research 数据必须被 production 门拒绝；数据经审校可升 production 时才翻为 `false`

## 3. 边界 / Limits

- 合同只证明这两个快照的 source key、父边与身份连续；不证明行政语义、译名或全历史稳定（`historicalStability` 字段保持诚实取值）
- `humanReviewVerified=false` 是工具的固定口径：迁移文档里的 review 记录不等于真人审签
- 代码复用（一个源 code 后来指不同实体）不走本流程，需要独立 identity-reuse 契约

## 4. 待办（Phase 2 决策项）/ Open items

- 为 `geo-regions-seed` 数据集建立 node_metadata/identity_registry sidecar（当前无 sidecar，semantic_audit 对 seed 不适用）
- 决定 seed 与 audit-sample 两条 datasetId 的合并/共存策略

---

## English Summary

This runbook operationalizes the pinned-source update contract from the
`geo-regions-source-audit-v1` task (GSA-04). Rehearse offline with
`python3 tool/update_rehearsal.py --selftest` (synthetic fixtures prove an
undeclared deletion is blocked and a fully evidenced retirement passes), and run
the real contract against two data roots with
`python3 tool/update_rehearsal.py --old-root A --new-root B`
(check → check → stability; breaking changes need per-change migration evidence
in `audit/migrations.json`; retired registry entries are never removed).

The data-maturity tripwire lives in `config/readiness.json`
(`expectedProductionGateRefusal`): research seeds MUST be refused by
`tool/geo_data.py validate --production`, enforced in CI via
`tool/check_readiness.py`; flip the switch only for reviewed production data.
For the candidate dataset layer see `datasets/csc-candidate/README.md`;
`semantic_audit.py` applies to roots carrying `audit/` sidecars (CLDR-sample
shape) — the seed dataset's sidecars remain a Phase-2 decision.
