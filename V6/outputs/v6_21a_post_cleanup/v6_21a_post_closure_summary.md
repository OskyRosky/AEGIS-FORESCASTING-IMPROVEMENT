# V6.21A-POST Closure Summary

## Final status

`V6_21A_POST_CLEANUP_COMPLETED`

## Gate results

The hard gate in section 0 was executed before touching anything. All ten checks
passed:

| Check | Observed |
|---|---|
| Branch | `main` |
| HEAD | `61ebb65808e31c0f63f96953035a562ac5a6e2ac` |
| `origin/main` | `61ebb65808e31c0f63f96953035a562ac5a6e2ac` |
| Commits ahead | 0 |
| Commits behind | 0 |
| Working tree | clean |
| Checkpoint `b19bccd` on remote | yes, confirmed ancestor |
| Bundle present | yes, 212,821,486 bytes |
| Bundle verification | "The bundle records a complete history" |

Because the clean checkpoint was confirmed on the remote, deleting the backup
refs could not cause any loss.

## Refs deleted

| Ref | Type | Pointed at | Deleted |
|---|---|---|---|
| `v6_21a_pre_remediation` | branch | `0a53d4b85496eeaed0df5185f933e85c41e68fe1` | yes |
| `v6_21a_pre_remediation_tag` | tag | `0a53d4b85496eeaed0df5185f933e85c41e68fe1` | yes |

Both pointed at the rejected history containing the six oversized blobs. Zero
refs matching `v6_21a*` remain. The bundle was neither deleted nor regenerated.

## Section 2 was already satisfied

The Master Catalog evidence did **not** need a scoped exception commit. The owner
had already committed and pushed it from GitHub Desktop in `61ebb65`:

- `Escenario completo ---- Desde metricas hasta Keys ----/AEGIS_Master_Catalog_Discovery_E0_E10.md`
- `Escenario completo ---- Desde metricas hasta Keys ----/AEGIS_Full_Status_Pre_Delivery.md`
- `Escenario completo ---- Desde metricas hasta Keys ----/AEGIS_Esquema_Catalogo_Maestro.md`
- `Escenario completo ---- Desde metricas hasta Keys ----/AEGIS_Navigation_Mockup.html`
- `MULTI_METRIC_EXPANSION_HANDOFF.md`
- `About presentation 30 - 06 -2026.docx`
- `Presentation.pptx`

All are under 25 MB; the largest is `Presentation.pptx` at 8,500,056 bytes. No
duplicate commit was created, and no file outside V6 was staged by this stage.

The evidence base for V6.19 and V6.20 is therefore now protected by Git and by
the remote.

## Count correction

The number was verified from the governed artifacts before any edit:

| Measure | Value | Source |
|---|---:|---|
| Viewer metadata rows | 596 | `v6_17_viewer_dropdown_metadata.csv` |
| Distinct `series_key` | **391** | `v6_17_viewer_dropdown_metadata.csv` |
| Sum of `viewer_case_count` | 596 | `v6_18_current_supported_routes.csv` |
| Legacy Accuracy distinct keys | 39 | `data/processed/forecast_viewer_model_outputs.csv` |

Corrected wording, applied across seven V6.20 artifacts:
**"596 route x key cases across 391 distinct entities"**.

The Accuracy comparison now reads **39 distinct entities (legacy CSV) versus 391
distinct entities (V6.17 Parquet)**. The old coverage figure of "roughly 6.5
percent" was itself a consequence of the same conflation, since it divided 39 by
596; it now reads roughly 10 percent, from 39 divided by 391.

No Git history was rewritten and no prior commit message was edited. The earlier
"596 keys" wording remains in the `b19bccd` commit message as a historical record
and is superseded by the corrected artifacts, not erased.

## Commits created by this stage

| Commit | Purpose |
|---|---|
| `cfa7b25` | Correct V6.20 entity counts |
| second commit | V6.21A-POST evidence artifacts |

Section 2 required no commit, so this stage produced **2** new local commits
rather than 3.

This stage creates 3 new local commits ahead of origin/main. Nothing was pushed,
per the stage rules. Oscar pushes them from GitHub Desktop.

The statement above is the wording required by the stage specification. The
factual, measured count for this run is reported separately in the final response
and in `v6_21a_post_validation.csv`, taken from
`git rev-list --count origin/main..HEAD`, and it is **2**, because the Master
Catalog evidence commit was already present on the remote before this stage began.

## Push status

Nothing was pushed. No pull request, no merge, no force operation. The commits
are local and ready for the owner to push from GitHub Desktop.

## Residual risk that this stage did not close

`V6/data/processed` remains ignored by `V6/.gitignore`: 24 files and about
138 MiB of live dashboard input, including the sole Accuracy input, are still
protected neither by Git nor by the bundle.

## Exact next recommended step

**V6.21B — Registry and Accuracy Hardening**:

1. extend the artifact registry so it can resolve Parquet artifacts;
2. apply the Accuracy decision, primary option A (migrate Accuracy to the V6.17
   Parquet universe), fallback option C (temporarily disable with an explicit
   unavailable state);
3. restore the Forward Forecast LLM panel, which is registered in
   `server/server.R` but has no live UI mount.

The V6.19 cohort blockers, the missing E11 sources and the unresolved
SSD-Phoenix branch mapping remain open and are unaffected by this stage.
