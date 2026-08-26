# V6.24-P9C — Selection Design Summary

Why the selection is built the way it is.

---

## The problem

P8's selection was correct and unpleasant. All 140 paths resolved, no option was
ever empty — and it still read as six technical dropdowns in a row. The owner's
words: *"no me gusta mucho, sobre todo la parte de selección de las series,
porque normalmente antes nosotros teníamos un contexto que era mucho mejor."*

The legacy Forecasting Selection does something different: it asks one question
at a time and answers continuously in a route panel beside the questions.

## The shape

```
Card A: Selection                       [pill: 140 operational series]
  lead line
  ┌──────────────────┬──────────────────────────────────────────┐
  │ SELECTION rail   │  breadcrumb chips                        │
  │  Metric      ▾   │  status badge + caveat badges            │
  │  DB Type     ▾   │  ┌────────┬────────┬────────┐            │
  │  Scenario  (ctx) │  │ ROUTE  │ LABEL  │ ENTITY │  ...       │
  │  Segment   (ctx) │  └────────┴────────┴────────┘            │
  │  Granularity ▾   │  context notes                           │
  │  Forest      ▾   │                                          │
  └──────────────────┴──────────────────────────────────────────┘
```

Kicker `A`, a scope pill, and a lead line — the same rhythm the legacy cards use,
so the section stops looking like a different product.

## Three states, not two

The core of it is that an axis is not simply *shown* or *hidden*:

| State | Meaning | Rendering |
|---|---|---|
| **CHOICE** | more than one real value remains | a dropdown |
| **CONTEXT** | exactly one value remains | a muted, dashed, non-interactive line |
| **LOCKED** | a parent is still unchosen | not rendered at all |

CONTEXT is the state P8 was missing. When `db_type` is `NOT_APPLICABLE` for
every IOPS series, there is nothing to choose — but there *is* something to say.
Showing a dropdown containing one useless option asks the user to make a decision
that does not exist. Hiding it entirely loses real information about the source.
Stating it does both jobs.

The wording is deliberate too. The rail shows *"does not apply to this route"* and
*"not carried by the source"* rather than `NOT_APPLICABLE` and
`UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE`. The tokens are artifact vocabulary; they
belong in the route card, not in a form label.

## Why state is explicit

The obvious implementation reads the current inputs and recomputes options. It
has a subtle failure: when a parent changes, a stale downstream value can survive
if it happens to remain valid in the new branch, and the user ends up with a path
they never chose.

So the server holds `sel` as `reactiveValues`, and each axis observer clears
every axis below it in one place. Reset becomes a property of the design rather
than something each control has to notice.

## Why the final label is dynamic

`navigation_contract.key_axis_status` already told us what the final value
represents — P7 emitted it and P8 never read it. A user picking `apcp150` from a
control labelled "Key" is being shown implementation vocabulary; the same control
labelled "Forest" is showing them their own domain.

The fallback to *Operational Key* fires only while granularity is still mixed. It
is neutral rather than wrong, and it disappears as soon as the user picks a
granularity.

## Why Demand Nature is a card cell, not a control

The legacy Selection has a Demand Nature axis. Copying it would have been the
easy parity move and it would have been a lie: `demand_nature` is constant
`Organic` across all 140 series, so the control could never do anything.

It is also why `route_path` is never parsed by position. The token in slot 1 is
`Organic` for HDD but `Phoenix` for SSD — the same index means different things.
Parsing it would have produced a control that looked plausible and was wrong.

So demand nature is **read per series** from `actuals_normalized` and shown in
the route card. If the cohort ever stops being uniformly Organic, the card tells
the truth without any code change.

## Why one selection, not two

P8 gave the Viewer and Forecast pages independent filter bars, so choosing a
series meant choosing it twice. Worse, the two could silently disagree.

Now a single `selected_series()` reactive drives both. The Viewer owns the
controls; Forecast shows a read-only mirror with the same breadcrumb and a line
saying where to change it. That matches the constraint exactly — Forecast may
have its own *model* selector later, but never its own *series* selector — and it
avoids two synchronised controls fighting each other.

## Why the context notes read the way they do

Three notes can appear, and each reads a field:

| Note | Field | Tone |
|---|---|---|
| Champion is not a recommendation | `champion_visible` | attention, amber |
| Accuracy is low confidence | `low_confidence_backtest_window_flag` | moderate, blue |
| Most recent value is zero | `trailing_zero_latest_actual_flag` | soft, grey |

Three tones, not three alarms. 87 of 140 series carry at least one caveat; if
every one of them shouted, the user would learn to ignore all of them. The
no-signal note is the only one styled with real weight, because it is the only
one that changes what you should conclude.

No series is named anywhere in the code.

## What this stage deliberately left alone

Charts are still Plotly. There is no horizon selector, no model families, no
champion star on a control, no Analyze/Reset, no assistant, no downloads.

Every one of those was tempting while working in the same files. All of them are
P9D through P9G. A change made here would have been a change nobody validated in
isolation — which is exactly what rules 6 and 7 exist to prevent.
