# Locked source snapshots / 固定源快照

`source-lock.json` identifies 36 exact public GitHub files, with immutable commit URLs, complete SHA-256 values, sizes, retrieval date, declared upstream version and license.

- `raw/cldr/`: CLDR 49 JSON catalog/containment/alias data and source XML names with original draft metadata.
- `raw/modood/`: the 2023-06-30 mainland China statistical tree and the upstream update notice.
- `cn-province-crosswalk.json`: generated, deterministic province-code mapping, including one recorded CLDR alias inconsistency.
- `coverage-report.json`: generated counts; not an upstream source and not a claim of human review.

原始文件按字节保留。不能编辑原始文件后仅重写哈希来伪装成原始下载；对新版本的变更必须更改固定源引用并附差异证据。许可证原文在 `licenses/third_party/`。

The raw snapshots are preserved byte-for-byte. An intentional source update must change the immutable upstream reference and carry a reviewable diff; it must not masquerade as the original download by merely replacing its hash.

```sh
python3 tool/import_data.py --check
```

Full source and transformation documentation: [DATA_SOURCES.md](../docs/DATA_SOURCES.md).
