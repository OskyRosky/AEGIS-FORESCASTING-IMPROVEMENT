# V6.0F-R2 — Control Cascade Specification

Applies to **Forecasting → Viewer** and **Forecasting → Forecast**. No new tab is created (D7).

---

## 1. Control order

```
Metric  →  Scenario  →  Granularity  →  Key  →  Forecast Version  →  Model / Type
```

| # | Control | Type | Populated from | Viewer | Forecast |
|---|---|---|---|---|---|
| 1 | Metric | single select | `metric_scope_register.csv` where `in_scope = yes` | yes | yes |
| 2 | Scenario | single select | `ui_decision_contract.csv` filtered by Metric and `exposed_in_first_release = yes` | yes | yes |
| 3 | Granularity | single select | distinct `granularity` for the chosen Metric + Scenario | yes | yes |
| 4 | Key | single select | distinct key values for the resolved source | yes | yes |
| 5 | Forecast Version | single select | distinct values of the resolved version column | yes | yes |
| 6 | Model / Type | multi select | `type` values, HDD Forest only (D5) | yes | no |

---

## 2. Cascade rules

| Rule | Behaviour |
|---|---|
| C1 | Each control is populated **only** from values that exist for every selection above it. No cross-product is offered. |
| C2 | Changing a control resets every control below it to its first valid value. |
| C3 | A control with a single valid value is still rendered, disabled, showing that value. |
| C4 | A control with **zero** valid values renders an explicit empty state. It never renders a blank dropdown. |
| C5 | Granularity is an independent control (D6). It is never folded into the Scenario label. |
| C6 | Model / Type is never merged with Scenario (D5). Scenario answers *which business series*; Type answers *which model produced it*. |
| C7 | Model / Type is hidden when the resolved source has no type dimension. It is not shown disabled. |
| C8 | Key values are shown exactly as stored in Tesseract, including `Forest_SKU` composites (D4). No aggregation, no relabelling. |

---

## 3. Badge behaviour

| Badge | Condition | Viewer renders | Forecast renders |
|---|---|---|---|
| 🟢 GREEN — FULL | actual **and** forecast confirmed | Actual series + forecast series | Forecast series |
| 🟡 AMBER — FORECAST-ONLY | forecast confirmed, actual not confirmed | Forecast series **only**, plus amber notice | Forecast series |
| ⚫ GREY — OUT-OF-SCOPE | no populated source | Not selectable | Not selectable |

**Hard rules**

| # | Rule |
|---|---|
| B1 | An AMBER combination **never** draws an actual series. |
| B2 | Missing actuals are **never** substituted with zeros, nulls, interpolation or forecast values. |
| B3 | Precomputed accuracy aggregates are **never** presented as a Viewer actual series (D3). |
| B4 | A GREY metric never appears in the Metric dropdown. It appears only in the out-of-scope notice (D1). |
| B5 | The badge is rendered next to the chart title, always visible, never inside a tooltip. |

---

## 4. Empty states

| Situation | Message shown |
|---|---|
| No key for the selection | "No keys available for this scenario and granularity in the current snapshot." |
| No forecast version | "No forecast version available for this selection." |
| No data after all filters | "No rows match this selection in the current snapshot." |
| Actual missing on an AMBER combination | "Actual values are not available for this metric in Tesseract. Showing forecast only." |

Every empty state names the snapshot. None of them shows an empty chart.

---

## 5. What each page keeps unchanged

| Page | Preserved |
|---|---|
| Viewer | Existing model comparison, interval display, downloads, assistant panel |
| Forecast | Existing horizon controls, interval display, downloads, assistant panel |

The new controls are added **above** the existing ones. No existing control is removed or renamed in R8/R9.
