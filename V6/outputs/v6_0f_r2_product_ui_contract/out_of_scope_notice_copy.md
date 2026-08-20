# V6.0F-R2 — Out-of-Scope Notice Copy

Approved wording for what the dashboard shows about metrics and scenarios that exist in the reference portal but are not exposed. Per D1, D2 and D3.

---

## 1. Memory — out-of-scope notice

**Placement:** static info panel under the Metric control, on both Viewer and Forecast. Always visible. Not a tooltip, not a modal.

**Title**

> Metrics not included in this release

**Body**

> **Memory** appears in the reference portal metric list but is not available in this dashboard.
>
> Reason: no populated forecast source was found in TesseractEarthDW. The demand views `vw_SubstrateBE_Demand_Memory_Forest` and `vw_SubstrateBE_Demand_Memory_Region` return 0 rows, and `vw_SubstrateBE_MemoryRawData` contains raw server telemetry only, with no forecast series.
>
> Memory will be added once a validated forecast source is confirmed. No estimated or placeholder values are shown in the meantime.
>
> *Verified against TesseractEarthDW on 2026-08-12 (V6.0F-R1 inventory).*

**Rules**

| # | Rule |
|---|---|
| N1 | Memory never appears in the Metric dropdown, not even disabled. |
| N2 | The notice states the reason and the verification date. |
| N3 | The notice never implies the data is coming soon on a specific date. |

---

## 2. Forecast-only badge notice

**Placement:** inline, next to the chart title, whenever the selected combination is AMBER.

**Short badge label**

> Forecast only

**Expanded text**

> Actual values are not available for this metric in Tesseract, so no Actual vs Forecast comparison is shown. The chart displays the forecast series only.

**Applies to:** CPU, CPU Failover, IOPS, IOPS Failover, SSD - Phoenix, SSD - MCDB.

---

## 3. Full-comparison badge

**Short badge label**

> Actual + Forecast

**Applies to:** HDD - EDB and HDD - Basilisk, at both Region and Forest granularity.

---

## 4. SSD-Phoenix scenario scope notice

**Placement:** helper text under the Scenario control, shown only when Metric = SSD - Phoenix.

> Showing the 2 scenarios used by the reference portal: **Low Volume No Efficiency** and **Low Volume With Efficiency**.
>
> Tesseract contains 22 additional SSD scenarios. They are documented in the V6.0F-R1 inventory but are not exposed in this release pending scope confirmation.

---

## 5. Snapshot provenance line

**Placement:** footer of both pages.

> Data snapshot: TesseractEarthDW · extracted `<snapshot_date>` · sources: `<n>` tables · V6.0F-R1 contract.

`<snapshot_date>` and `<n>` are populated in R6. Until then the line reads:

> Data snapshot: pending governed extraction (R6). Current pages use legacy artifacts.

---

## 6. Prohibited wording

| # | Never say |
|---|---|
| P1 | "No data" without a reason |
| P2 | "Coming soon" with a committed date |
| P3 | Anything implying an actual series exists when it does not |
| P4 | Any number not traceable to a Tesseract table |
