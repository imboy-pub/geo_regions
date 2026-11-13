# Semantic audit tests / 语义审计测试

Run from this package root / 在本包根运行：

```bash
python3 -m unittest discover -s tests -p 'test_semantic_audit.py' -v
python3 tool/semantic_audit.py check --report reports/semantic-audit.json
python3 tool/semantic_audit.py resolve --country JP --id iso3166-2:JP-13 --locale zh-Hant
python3 tool/semantic_audit.py stability --old-root . --new-root .
```

22 tests exercise duplicate IDs, orphans, invented levels, wrong node kinds,
source-parent disagreement, source-key/code consistency, script-preserving locale
selection, missing names, quality filtering including default names, immutable
identity records, retirement history, exact migration events and evidence hashes,
explicit alias script boundaries and snapshot binding of locale policy.
All generated test geography and review records are explicitly synthetic; they
are not production data and do not assert that a human reviewed a migration.

22 项测试覆盖重复ID、孤儿、虚构行政等级、错误节点类型、源父级不符、源编码一致性、
保留文字系统的语言匹配、缺译、默认名质量过滤、稳定身份、退休历史及精确迁移记录。
还覆盖显式别名不能跨文字系统以及语言策略须纳入快照指纹。
测试内地区和审签均为临时合成数据，不能导入发布数据，也不能作为真人审核证据。

## Scope / 范围

- The checker reuses the existing Protocol 1.0 integrity implementation. Node
  metadata stays in an audit sidecar; client schemas are unchanged.
- `administrativeLevel` and `administrativeType` must be null in this CLDR-only
  profile. Tree depth is verified against the pinned containment snapshot,
  without claiming current official administrative rank.
- Requested locales follow explicit aliases, script-preserving lookup, host
  default `en`, an eligible source default name, then stable ID. Missing or
  filtered translations stay absent; fallback never fills a locale pack.
  An alias cannot change or discard a script explicitly specified by the
  requested tag; `zh-CN` to `zh-Hans` remains a valid explicit policy.
- `source-native`, `approved-in-source`, `contributed`, and
  `cldr-json-qualified` are eligible. Other quality labels are excluded.
  These labels describe the recorded upstream quality, not project review.
- A same-directory comparison returns `SAME_SNAPSHOT_ONLY`. It is not evidence
  of real stability across upstream releases. For two supplied snapshots, a
  pass checks those files only and makes no completeness claim about history.
- Registry identity fields and retired IDs are immutable. A reused source code
  under a new ID is also blocked until a separately reviewed identity-reuse
  contract is implemented; migration review entries cannot override this rule.
- A migration review record is checked for exact affected IDs, old/new values,
  snapshot bindings, an identified reviewer and nonempty evidence hash. This
  is machine verification of a recorded review, not proof of human approval.

## Migration record / 迁移记录

Place optional records at `audit/migrations.json`. The script prints snapshot
fingerprints from `check`; they bind the manifest, source lock, locale policy
(`config/data_policy.json`) and audit sidecars. The migration file is excluded
from its own fingerprint. Stability reports include `policyChanged`.

```json
{
  "schemaVersion": 1,
  "datasetId": "same dataset on both sides",
  "fromSnapshot": "full SHA-256 from the old check",
  "toSnapshot": "full SHA-256 from the new check",
  "events": [
    {
      "id": "stable affected ID",
      "change": "reparented",
      "from": "old parent ID",
      "to": "new parent ID",
      "review": {
        "status": "reviewed",
        "reviewer": "actual reviewer identity",
        "reviewedAt": "YYYY-MM-DD",
        "evidence": "audit/reviews/actual-review-record.txt",
        "evidenceSha256": "full SHA-256 of the evidence file"
      }
    }
  ]
}
```

The example is a shape illustration, not an approval. A deletion uses
`change: "removed"`, `from: "active"`, `to: "retired"` and keeps the registry
entry as retired. Every breaking change needs one matching event; duplicate,
unrelated, missing, stale or modified-evidence events are rejected. The strict
CLDR profile rejects invalid kind/code changes before migration review.
