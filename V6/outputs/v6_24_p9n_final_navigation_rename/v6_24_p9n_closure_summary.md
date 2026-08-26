# V6.24 P9N - Final product navigation rename, closure summary

**Status: COMPLETED** - 44/44 validation checks PASS.

## What changed

The V6.24 experience is now the product. The sidebar shows five groups:

```
Project       Home · Overview
Models        Universe · Ranking Diagnostics · Champion
Forecasting   Overview · Viewer · Accuracy · Forecast
Governance    Risks · Audit
Reference     Artifacts · Methodology · Version
```

- **V6.24 MVP** is now **Forecasting**.
- **Models FULL** is now **Models**.
- The two original groups are **hidden, not deleted**. They remain in
  `stage07_menu()` marked `hidden = TRUE`, and `app_sidebar()` filters them out.
- **Forecasting > Taxonomy is hidden on request.** The item keeps its definition
  in `stage07_menu()` with `hidden = TRUE`, `sidebar_group()` filters hidden
  items, and the section, its server outputs and its helpers are untouched and
  still mounted.
- Eight visible page headings were renamed, along with every in-page pointer
  that named a menu which no longer exists.

## What was deliberately not changed

- **No code was deleted.** All legacy sections, server logic and helper
  functions are intact; all 22 sections are still mounted in the DOM.
- **Internal ids stay `v24_*` and `v24mf_*`.** The brief asked for visible
  labels, and renaming ids would touch every server output for no user benefit.
- **File names, function names and comments are unchanged.**
- **"V6.24" survives in evidence and source notes**, for example *The V6.24
  selection is shared across the section*, which the brief explicitly allows.
- No artifact, no calculation, no chart logic and no champion logic was touched.

## Known caveats

- The legacy sections are unreachable from the navigation but still exist as
  hidden DOM nodes. That is what the brief asked for, and it keeps rollback to a
  one-line change.
- The legacy Champion section still holds the only Plotly chart left in the app.
  It is now invisible to users.

## Recommended next stage

**P9I - Final Visual QA** over the five visible groups.
