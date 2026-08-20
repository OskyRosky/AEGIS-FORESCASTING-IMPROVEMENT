# V6.23-P0 | Selector source diagnosis

## Which source feeds the Viewer selector

**`v6_18_navigation_contract.csv`**, and nothing else.

The chain, verified in code rather than assumed:

```
ui/tabs_v6_16_viewer.R  section_explorer()
  └─ taxonomy_navigation_ui("fvp_taxonomy")

R/viewer_pilot.R  viewer_pilot_server()
  └─ taxonomy_navigation_server("fvp_taxonomy", "viewer")

R/taxonomy_navigation.R
  ├─ taxonomy_navigation_data()      reads v6_18_navigation_contract.csv
  ├─ taxonomy_page_rows("viewer")    filters on viewer_visible   <-- the gate
  └─ taxonomy_operational_rows(...)  filters on viewer_eligible
```

The exact gate was `R/taxonomy_navigation.R`:

```r
taxonomy_page_rows <- function(page, contract = taxonomy_navigation_data()) {
  visible <- taxonomy_page_column(page, "visible")   # "viewer_visible"
  contract[contract[[visible]], , drop = FALSE]
}
```

With `viewer_visible = FALSE` on every SSD row, the Metric selector could only
ever offer HDD.

## Ruling out the alternatives

| Candidate source | Feeds the selector? | Evidence |
|---|---|---|
| `v6_18_navigation_contract.csv` | **YES** | Sole input to `taxonomy_navigation_data()` |
| `v6_17_viewer_dropdown_metadata.csv` | No | Used by `viewer_pilot.R` only to answer "does a backtest exist for this case", via `fvp_pilot_available()` |
| `v6_22_cohort_manifest.csv` | No | A generation plan for V6.23; Shiny never reads it |
| Hardcoded / backtest-only source | No | The only hardcoded value was the header pill string `"596 entities / 6 routes"` |

Worth stating plainly: the V6.22 cohort manifest is **not** wired into Shiny and
was not wired in by this fix. The contract remains the single navigation source.
The two now agree at 894 cases, but they agree because both derive from the same
V6.17 artifacts, not because one reads the other.

## The one genuinely hardcoded thing

`ui/tabs_v6_16_viewer.R` printed the literal string `"596 entities / 6 routes"`.
That is now derived at runtime from the contract through a new helper,
`taxonomy_viewer_scope()`.
