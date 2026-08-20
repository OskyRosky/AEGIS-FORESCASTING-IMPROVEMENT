# AEGIS V6.0E — Closure Summary

**Stage:** V6.0E — Multi-Metric Artifact Builder
**Status:** `V6_0E_MULTI_METRIC_ARTIFACT_BUILDER_COMPLETED`
**Date:** 2026-08-11
**Nature:** artifacts built and validated. No Shiny change, no SQL, no Azure, no legacy artifact modified.

---

## 1. What was built

A registry-driven builder and ten governed artifacts.

| Component | Path |
| --- | --- |
| Declarative registry | `V6/config/metric_registry.csv` (16 sources) |
| Builder | `V6/python/multi_metric/build_multi_metric_artifacts.py` |
| Validation harness | `V6/python/multi_metric/validate_v6_0e.py` |
| Official artifacts | `V6/outputs/metrics_multi/` (10 files) |
| Evidence | `V6/outputs/v6_0e_multi_metric_artifact_builder/` (8 files) |

Both scripts use the Python standard library only, so the build is reproducible
inside the container without adding an image dependency.

## 2. The headline result

| Measure | Legacy | V6.0E | Meaning |
| --- | --- | --- | --- |
| Metric rows | 27,067 | 27,067 | No row lost and none invented |
| Ranking groups | 736 | **873** | The 137 blended SSD groups are now separate |
| Groups drawing from more than one source | 137 | **0** | Isolation is structural |
| Identity columns on each row | 0 | 44 | Identity travels with the data |

The difference of exactly 137 is the defect measured in V6.0C, now resolved.

For the validation case NAMPRD07 the two variants no longer collapse:

| Series | Windows | Avg MAPE | Avg accuracy |
| --- | --- | --- | --- |
| Low-Vol with Efficiency | 57 | 4.5133 | 95.4867 |
| Low-Vol without Efficiency | 58 | 4.4984 | 95.5016 |

The legacy blended value of 4.5058, which corresponded to no real series, is gone.

## 3. Coverage

Four local sources normalized: HDD region 2,550 rows, HDD forest 8,828, SSD-Phoenix
LVWE 7,776, SSD-Phoenix LVNE 7,913. Twelve declared-but-unlocated sources are
reported with an availability status, a limitation and a next action. No metric was
fabricated for them.

## 4. Validation

33 of 35 tests pass, 0 blocking failures, 2 deferred to stages that have a runtime.
All 14 frozen artifacts rehash unchanged. All 15 assistant preservation checks pass.

## 5. Defects found and fixed inside this stage

Three problems were caught by the stage's own checks rather than shipped:

| Issue | Resolution |
| --- | --- |
| The assistant pack builder held a hardcoded map of source names | Replaced with labels derived from the resolved registry |
| The availability writer defaulted a scenario to `Enterprise` | Replaced with the distinct values actually read from the source, or `not_applicable` |
| A blocked source still advertised a renderable view | View lists are now empty unless the status is renderable, and a fact source with no accuracy is `blocked_by_data` rather than `not_computable` |

Two test definitions were also corrected because they produced false positives: the
Azure check matched the word inside a comment, and the raw-data check matched a
filename in the lineage. Both now assert real conditions.

## 6. What was not done, deliberately

- Shiny was not touched. Integration is V6.0F.
- The HDD fact source was not normalized into the metrics artifact. It has no
  precomputed accuracy columns and its actuals do not overlap the forecast window.
- `T34` export formats and `T35` container parity were not executed. They need a
  running app and a container, which belong to V6.0F and V6.0H.
- No stakeholder decision was resolved. D2, D3, D4, D5 and D10 remain open and the
  affected rows carry `pending_mapping` rather than a guess.

## 7. Next stage

**V6.0F — Shiny Multi-Metric Integration.** Not authorised yet. Its input
specification is `v6_0f_shiny_integration_requirements.md`, including the twenty
visual checks that must be verifiable on screen.
