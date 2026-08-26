# V6.24-P9B — Forecasting UX Parity Study — Closure Summary

**P9B WAS STUDY ONLY. No code, CSS, UI, server, helper or governed artifact was
modified — and that is proved by sha256, not asserted.**

**Verdict: `READY_FOR_P9C_WITH_CAVEATS`.**

---

## 1. What was produced

Twenty-two deliverables: two inventories, two code maps, a 27-element parity map
in both CSV and narrative form, a Highcharts migration study, assistant and
download reuse studies, a staged plan for P9C through P10, a 15-risk register,
governance notes, eight open questions and a 37-check validation.

## 2. The headline

**The data layer is sound and needs no change. Every gap is presentational, and
every field required to close them already exists in the governed artifacts.**

Of 27 elements compared: **6 where V6.24 already leads**, **18 gaps**, 3 equal or
deferred.

## 3. Where V6.24 already leads — and must not regress

1. **Overview coverage cards** — Forecasting has no landing summary at all. The
   owner asked for this to be kept.
2. **No-signal champion suppression** — encodes P6C and P7. The highest-severity
   regression risk in the register.
3. **Low-confidence backtest-window flag** — derived, never hardcoded.
4. **Persistent 30-step horizon disclosure** — the misrepresentation P6 blocked.
5. **Caveat transparency** — eleven machine-readable codes.
6. **Read-only governance** — 35 load-time validations, byte-identical artifacts.

## 4. The gaps, grouped

**Selection (P9C)** — the owner's main complaint. Legacy asks one question at a
time and answers continuously in a route panel; V6.24 asks six at once and answers
in one line. No breadcrumb chips, no route cards, no status badge, and the last
axis is always labelled "Key" even when the user is choosing a Forest.

**Backtest configuration (P9D)** — essentially absent. No horizon selector, no
family grouping, no champion star, one model at a time, no Analyze/Reset.

**Charts (P9E, P9F)** — the wrong library. This was my error in P8:
`R/libraries.R` line 11 already declared `highcharter` with the comment
*"interactive forecast charting (Forecast Viewer)"*. The convention existed and I
broke it.

**Assistant and downloads (P9G)** — both absent from V6.24, both already built in
the app.

## 5. Four findings that change how P9C–P9G should be built

**The four-family display cannot come from the V6.24 artifact.** Legacy groups
models into Growth Baseline / Statistical / Machine Learning / Deep Learning.
V6.24 carries only Baseline / Challenger / Neural, and **the two partitions cut
across each other** — `ETS Explicit` is Challenger in V6.24 but Statistical in the
legacy display; `LinearRegression` is Baseline but Machine Learning. The
four-family split must be taken from `forecast_viewer_model_outputs.csv`, which
already classifies the identical 15 model names. Recorded as Q3.

**The horizon selector is directly feasible.** `model_backtests_15_models`
carries `horizon_steps` with values 1–30, semantically identical to legacy
`horizon_days`. The 5/10/15/20/25/30 radios transfer with no data work.

**Demand Nature has no V6.24 equivalent.** It is constant `Organic` across all 140
series, so it cannot discriminate. And `route_path` is **not positionally
uniform** — SSD carries `Phoenix` where HDD carries `Organic` — so synthesising
the axis by parsing position would produce a wrong control. Show it as route
context, never as a filter. Recorded as Q2.

**The assistant is page-keyed, not selection-aware.** `llm_explain_get(page_id)`
returns a fixed pack per page. Mounted naively beneath a selected series, it would
appear to describe that series while describing the section. An assistant that
confidently describes the wrong series is worse than no assistant. Recorded as Q5
and it must be decided before P9G.

## 6. Two things the legacy code already knew that P8 rediscovered painfully

`taxonomy_navigation.R` line 532 uses
`outputOptions(output, "breadcrumb", suspendWhenHidden = FALSE)`. The legacy code
already handled outputs inside CSS-toggled sections. P8 found this through a page
that rendered **blank in a browser while 48 validation checks and 56 smoke checks
passed**.

That is recorded as **risk R13, severity HIGH**: `testServer` has no DOM, and an
HTTP `GET /` only sees the server-rendered shell. **Every P9x stage must close
with a real browser check that reads values, not markup.**

## 7. Scope discipline

Two fixes were tempting and both were left alone: the `key_axis_status` label is a
two-line change, and the `GOVERNED_30_STE...` wrap is a CSS tweak. Neither was
made. A fix smuggled into a study is a fix nobody validated. Both are recorded in
the parity map with their target stage.

## 8. Governance

Fifty-six Shiny files and 22 governed artifacts were fingerprinted with sha256
before the study began and re-verified at the end. No SQL, no model execution, no
regeneration, no recalculation, no push, no `git add .`.

One honest note: the first validation run reported all 56 files and all 22
artifacts as modified. That was a bug in my own comparison — PowerShell's
`Get-FileHash` returns uppercase hex and Python's `hexdigest()` returns lowercase,
so every comparison failed. The same case-sensitivity family of bug that produced
a wrong stale-flag count in P6 and a false validation failure in P6B. Fixed by
normalising both sides; the corrected run confirms zero modifications.

## 9. P9C readiness — READY_FOR_P9C_WITH_CAVEATS

P9C may start. Three questions should be answered first, because deciding them
mid-build is exactly the improvisation this stage exists to prevent:

- **Q1** — confirm the P9D/P9E ordering. The two owner documents disagree. This
  plan assumes config first, then chart, because the chart consumes the selection.
- **Q3** — confirm taking the four-family classification from the legacy artifact.
- **Q4** — confirm that Viewer and Forecast should share one selection.

Q5 (assistant scope) blocks P9G, not P9C.

---

**V6_24_P9B_FORECASTING_UX_PARITY_STUDY_COMPLETED**
