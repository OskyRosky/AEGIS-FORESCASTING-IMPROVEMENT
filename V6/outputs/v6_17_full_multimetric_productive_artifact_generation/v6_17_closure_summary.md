# V6.17 Full Multi-Metric Productive Artifact Generation

## Current status

All locally available productive scope is assembled and validated outside
Shiny. CPU/IOPS remain `BLOCKED_NOT_AVAILABLE` because no governed productive
source exists locally. The final completion classification is therefore:

`V6_17_FULL_MULTIMETRIC_PRODUCTIVE_ARTIFACT_GENERATION_BLOCKED_SCOPE`

## Viewer

- 596 HDD key-combinations across six actual-bearing combinations.
- 15 verified AEGIS models; no 16th model.
- 2,416,050 rows.
- 39 verified legacy keys reused.
- 557 missing keys generated with 11 EDB origins and 5 Basilisk origins.
- Basilisk uses only real shorter history; no padding.
- SSD-Phoenix is absent.
- Phase B initially rejected an unstable FNAR-V2 fit before promotion. The
  failed checkpoint was archived, neural targets were normalized, FNAR-V2 used
  a bounded `tanh` activation, and the clean rerun passed all 14,745 neural
  fits with finite forecasts.

## Forecast

- Eight locally available combinations: six HDD and two SSD-Phoenix.
- 896 metric/scenario/granularity/key combinations.
- 818,980 rows including prepared HDD actual history.
- SSD-Phoenix is forecast-only and includes both required scenarios.
- CPU/IOPS are not fabricated and remain explicitly blocked.

## Governance

All model execution, revision reconciliation, version selection, assembly, and
validation occurred outside Shiny. No SQL write, Tesseract extraction, Docker,
Azure, V1-V5, Assistant/LLM, or model-universe change occurred.

## Productive dashboard and live review

- Viewer reads prepared metadata and lazily filters the 2,416,050-row Viewer
  Parquet artifact.
- Forecast reads prepared metadata and lazily filters the 818,980-row Forecast
  Parquet artifact.
- Shiny performs no training, extraction, backtesting, version selection, or
  data writes.
- HTTP 200, Viewer rendering, Forecast rendering, 15-model availability, and
  SSD-Phoenix forecast-only behavior passed in-browser.
- Total elapsed runtime at final validation: 88.27 minutes, within the
  four-hour maximum.
- Live review URL: `http://127.0.0.1:8081`.

V6.18 remains blocked pending Oscar's explicit authorization.
