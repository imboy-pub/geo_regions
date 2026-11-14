# Candidate dataset sources

- Node structures + en names + 8 upstream translations: staging/csc-snapshot (dr5hn/countries-states-cities-database @ e9c4dec, ODbL-1.0)
- catalog_i18n/* (10x10 country names): _task_packages/geo_regions_source_audit_2026-11-13/data/catalog_i18n (CLDR 49 pinned, Unicode-3.0)
- FR x9 locales: Wikidata P374 community labels fill missing cells (CC0-1.0, staged extract, provisional)
- US/DE/IT/GB/RU/SA/KR: Wikidata labels joined by the snapshot rows' own wikiDataId QIDs (CC0-1.0, staged extracts, provisional)
- GeoNames alternateNamesV2 labels via CSC wikiDataId -> wkdt rows (CC-BY-4.0, staged extracts, provisional; fills what Wikidata lacks)
- FR/JP: CSC upstream translations re-joined through the staged qid->nid bridge for rows the name-matching inheritance missed (ODbL-1.0, provisional)
- zh-Hant: zh-Hant is s2t-derived machine-candidate + FR wikidata community labels
- All non-en translations are provisional; AI proof-reading samples do not flip quality words
- This candidate dataset is NOT production data (maturity stays research-seed)
