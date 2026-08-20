# Preliminary response draft for Boon — updated at V6.0E

**Status: PRELIMINARY DRAFT. Not sent.** The validated evidence pack is V6.0G.

All figures below now come from the new governed artifacts
(`official_metric_rankings.csv`), not from the defective legacy ranking that
blended the two SSD-Phoenix variants.

---

## Draft message

> Hi Boon,
>
> Yes, we do register accuracy for SSD-Phoenix on NAMPRD07. Here is what we can
> and cannot say today.
>
> NAMPRD07 is a **forest**-level key, and it appears in both SSD-Phoenix Low-Vol
> sources, kept separate:
>
> - Low-Vol **with** Efficiency: 57 evaluation windows, average MAPE 4.51%, average accuracy 95.49%.
> - Low-Vol **without** Efficiency: 58 evaluation windows, average MAPE 4.50%, average accuracy 95.50%.
>
> The worst window in both is 2026-04-20 to 2026-04-26: mean actual 8,688.15
> against a mean forecast of 9,268.95, a bias of about **+6.68%**, with accuracy
> around **93.31%**. The bias is consistently positive, so the forecast is running
> above actuals rather than below.
>
> The limitation: both sources retain a **single** forecast version (2026-03-12)
> and have no target-date dimension. So we can report the observed error, but we
> cannot yet produce cross-plan drift or error-by-horizon for SSD-Phoenix. That
> needs either deeper version retention or a fact-grain source.
>
> One correction worth flagging internally: our earlier internal ranking merged
> the two Low-Vol variants because they share the same key and forecast version.
> We have rebuilt those artifacts so each variant stays separate. The numbers
> above are from the corrected build.
>
> Next step on our side is wiring these metrics into the dashboard so this is
> visible rather than something we have to query by hand.

---

## Internal notes before sending

| Point | Status |
| --- | --- |
| Numbers sourced from the corrected multi-metric rankings | Yes |
| Variants reported separately | Yes, 137 groups that were previously blended |
| Single-version limitation stated explicitly | Yes |
| No drift or horizon claim made | Yes |
| Forest grain confirmed from data, not asserted | Yes |
| Final evidence pack still pending | V6.0G |

Open question Q15 remains: confirm with Chinmay what is appropriate to send now
versus after the V6.0F dashboard integration.
