# V6.0D — Computability and Availability Contract

Controlled vocabularies and the rules that derive them. Allowed values are listed
in `computability_and_availability_values.csv`.

---

## 1. Why capability is declared upstream

If the dashboard decides what is computable, every new metric requires UI logic
and the app drifts back toward metric-specific branching. Under this contract the
producer declares capability and the dashboard only obeys it.

## 2. The five booleans

| Boolean | True only when |
| --- | --- |
| `accuracy_computable` | The source provides or supports point accuracy for the identity tuple |
| `drift_computable` | Two or more distinct `forecast_version` values exist for the identity within the same source |
| `forecast_curve_computable` | `source_family = fact`, meaning a target date column exists |
| `cross_plan_computable` | `drift_computable` is true and the compared versions share one unit |
| `horizon_error_computable` | A target date exists **and** actuals overlap the forecast window |

Two invariants follow directly from V6.0C evidence:

- A metrics table can never set `forecast_curve_computable` or
  `horizon_error_computable` to true. That is a grain limitation, not a volume
  one, so more rows will never change it.
- A single retained version can never set `drift_computable` or
  `cross_plan_computable` to true.

## 3. Derivation precedence for computability_status

Evaluated top down; the first match wins.

| Order | Condition | Resulting status |
| --- | --- | --- |
| 1 | No source located or no rows available | `not_computable` |
| 2 | Blocked by an unresolved classification decision | `blocked_by_mapping` |
| 3 | Blocked by an undecided methodology question | `blocked_by_methodology` |
| 4 | A comparison is requested but the unit is unverified | `blocked_by_unit` |
| 5 | `accuracy_computable` and exactly one forecast version | `single_version_accuracy_only` |
| 6 | `accuracy_computable` and two or more versions but no target date grain | `accuracy_only` |
| 7 | All five booleans true | `fully_computable` |
| 8 | Data supports an analysis the dashboard does not yet read | `blocked_by_dashboard_integration` |
| 9 | Otherwise | `blocked_by_data` |

`not_computable_reason` accumulates every applicable code, pipe separated, and is
mandatory whenever the status is not `fully_computable`.

## 4. Applying the contract to the current snapshot

Derived from the V6.0C evidence, for illustration. V6.0E must reproduce these
values from data rather than copy them.

| Source | Versions | Grain | Expected status |
| --- | --- | --- | --- |
| `hdd_region_metrics` | 3 | metrics | `accuracy_only` with `NO_TARGET_DATE_GRAIN` and `SHINY_NOT_CONNECTED` |
| `hdd_forest_metrics` | 3 | metrics | `accuracy_only` with the same two reasons |
| `ssd_phx_lvwe_metrics` | 1 | metrics | `single_version_accuracy_only` |
| `ssd_phx_lvne_metrics` | 1 | metrics | `single_version_accuracy_only` |
| `hdd_region` fact, local extract | 1 | fact | `single_version_accuracy_only` for cross plan, with `NO_ACTUALS` blocking horizon error |
| CPU, SSD-MCDB, SSD Total and Organic | unknown | unknown | `blocked_by_mapping` or `not_computable` with `SOURCE_NOT_LOCATED` |
| IOPS | unknown | unknown | `not_computable` with `SOURCE_NOT_LOCATED` and deferred availability |

## 5. View gating rules for V6.0F

| View | Rendered only when |
| --- | --- |
| Accuracy table and heatmap | `accuracy_computable = true` |
| Cross version accuracy trend | `drift_computable = true` |
| Plan to plan comparison | `cross_plan_computable = true` |
| Forecast curve | `forecast_curve_computable = true` |
| Error by horizon | `horizon_error_computable = true` |

When a view is gated off it must be **hidden with an explicit reason**. It must
never render empty, never render zeros, and never silently fall back to another
metric's data.

Single-version accuracy must be labelled as accuracy evidence for one forecast
version. Presenting it as drift is a contract violation.

## 6. Availability versus computability

They are independent axes and both are required.

- `availability_status` answers whether the data is here.
- `computability_status` answers what may legitimately be done with it.

A source can be `local_ingested` and still `single_version_accuracy_only`. That is
exactly the SSD-Phoenix case and it is why one field alone is insufficient.
