# V6.24-P9D → P9F — Forecast Champion Default Note

Written during P9D so the decision is recorded while the reasoning is fresh.
**P9D implements none of this.** The Forecast page was not touched.

---

## The product decision

> *"En Forecast debería mostrarse principalmente el ganador/champion, no una
> comparación grande de todos los modelos. El Viewer/Backtest es donde uno
> compara modelos, horizontes y familias. El Forecast debería ser más ejecutivo:
> 'para esta serie seleccionada, este es el forecast recomendado'."*

Two pages, two jobs:

| Page | Question it answers | Shape |
|---|---|---|
| **Viewer / Backtest** | *Which model should I trust for this series?* | Comparison: horizons, families, several models at once |
| **Forecast** | *What is the recommended forecast for this series?* | Executive: one line, the recommended one |

## What P9F should build

**Default view: the champion only.**

For a series where `champion_visible = TRUE`, the Forecast page opens showing the
champion's 30-step forecast and says so plainly — the champion model name, the
metric it won on, and its value. One line, not fifteen.

**When `champion_visible = FALSE`, nothing may be sold as a winner.**

Show `ETS Explicit` as the governance reference model, and say clearly that it is
a reference and not a recommendation, using the same wording P9C and P9D already
use:

> *Champion is not meaningful for this no-signal series.*

The 15 no-signal series must never see the words "recommended", "best" or
"champion" applied to a model on the Forecast page.

**A secondary "compare other models" affordance is acceptable**, but it must be
opt-in and clearly secondary — a collapsed section or an explicit selector, never
the default view. If a user wants a real comparison, the Viewer is where they
should go.

## What P9D already prepared

- `v6_24_champion(series_id)` returns the champion model **and** a `meaningful`
  flag read from `navigation_contract.champion_visible`. P9F should use this
  rather than reading the field again.
- `V6_24_REFERENCE_MODEL` is `"ETS Explicit"`, defined once.
- `v6_24_model_label(model, champion)` draws the star only when the champion may
  be presented, so reusing it on the Forecast page gives correct behaviour for
  free.
- The shared `selected_series()` from P9C already drives the Forecast page, so
  P9F does not need to touch selection at all.

## One coincidence P9F should not misread

For all 15 no-signal series, P6C's deterministic tie-break crowned
**ETS Explicit** — which is also the governance reference model. So on those
series the "champion" name and the "reference" name are the same string.

That is expected and harmless, but P9F must not conclude from it that the
champion is therefore fine to show. The gate is `champion_visible`, not the model
name.

## What P9F must not do

- Do not make the forward horizon a control. It is fixed at 30 steps because that
  is the proven capability of the governed models, and P6 blocked any longer
  claim. The banner stays a label.
- Do not clip negative forecasts. 573 forecast rows are negative and were
  preserved deliberately end to end.
- Do not compute anything. `forecast_outputs` already holds every value.

## Validation P9F should carry

- A signal-present series shows the champion forecast by default, named.
- A no-signal series shows the reference model with the not-meaningful message
  and **no** star, and no wording implying a recommendation.
- Exactly 30 forward points.
- No page renders "4-year", "1,440" or "1440".
- Negative and extreme flags survive to the display.
