# Stage 07 — Block 7.12-PREVIEW — FORECASTING / TTL Placeholder + Capacity Readiness Barometer

## Summary

The FORECASTING / TTL page was upgraded from a single "Planned" card into a
clean, intentional **planned-state preview**. It clearly states that the
governed TTL source is not available yet, shows a **capacity view readiness
barometer** (data/source readiness — NOT capacity health), explains what the
page will eventually show, and lists the source checklist still required.

No TTL value, capacity health score, date-to-exhaustion, or resource pressure
metric is calculated or inferred. The dashboard remains read-only.

Per Oscar's instruction, every element that is **not yet available / still to
be built** is flagged inline with `**` markers so it is easy to spot as future
work.

## TTL source status

- Artifact key: `ttl_capacity` -> expected at
  `outputs/model_lab/ttl/ttl_capacity_view.csv`.
- Registry status: **roadmap** (artifact does not exist).
- The page reads this status via `get_artifact_status()` only — no compute.
- See `stage07_12_PREVIEW_ttl_source_status.csv` for the full checklist.

## Readiness barometer

A horizontal three-zone meter:

1. **Source missing** (current pinned position)
2. **Source connected**
3. **Ready for interpretation**

Labeled explicitly as **data/source readiness**, not capacity health and not
operational health. State: "source unavailable"; Readiness: "0% · pending
source". Neutral, planned-state colors (no red panic language).

## Content NOT implemented because the source is missing (** future work **)

- ** Time-to-impact (days/months to a capacity threshold)
- ** Capacity pressure by entity / forest / region / SKU
- ** Forecast-to-capacity bridge
- ** Governed TTL artifact
- ** Entity mapping
- ** Capacity threshold definition
- ** Forecast linkage

These are shown as future views / pending-source checklist items, not as data.

## Files modified

- `shiny_app/ui/tabs.R` — rewrote `section_ttl()`.
- `shiny_app/www/custom.css` — appended TTL callout + barometer styles
  (additive only, plus dark-theme variants).

## Validation

All checks in `stage07_12_PREVIEW_ttl_validation.csv` are **pass**. Home (post
REV1) and Universe still render; Tournament remains unpopulated; sidebar and
shell intact.

## Runtime

- URL: http://127.0.0.1:3838
- HTTP status: 200 (LEN 67170)
- Logs: `ttl_preview_stdout.log`, `ttl_preview_stderr.log`

## Recommendation

READY_FOR_OSCAR_VISUAL_REVIEW_7_12_PREVIEW_TTL
