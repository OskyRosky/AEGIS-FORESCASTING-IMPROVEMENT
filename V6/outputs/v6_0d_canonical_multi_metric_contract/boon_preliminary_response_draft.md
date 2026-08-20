# Preliminary response draft — Boon / SSD-Phoenix NAMPRD07

**Status: PRELIMINARY DRAFT. Not sent. Not the final evidence pack.**
The validated evidence pack is stage V6.0G, which runs after the multi-metric
artifacts are built and integrated.

---

## Draft message

> Hi Boon,
>
> Short answer: yes, we do have accuracy evidence for SSD-Phoenix on NAMPRD07, but
> with an important limitation.
>
> Both SSD-Phoenix Low-Vol tables are loaded on our side, and NAMPRD07 appears in
> both, with 57 and 58 evaluation windows respectively. Average MAPE is around
> 4.5% and average accuracy around 95.5%.
>
> The worst window we observe is 2026-04-20 to 2026-04-26: mean actual 8,688.15
> against a mean forecast of 9,268.95, which is roughly a +6.68% bias, with
> accuracy around 93.31%. The bias is consistently positive, so the forecast is
> running above actuals rather than below.
>
> The limitation: those tables retain a single forecast version (2026-03-12) and
> have no target-date dimension. So we can report the observed error, but we
> cannot yet produce cross-plan drift or error-by-horizon analysis for SSD-Phoenix.
> That would need either more retained versions or a fact-grain source.
>
> One thing worth confirming: NAMPRD07 is a forest-level key, not a region key.
> Our HDD reporting currently runs at region grain, which is part of why this did
> not surface earlier.
>
> Right now we are cleaning up the metric contract so the dashboard keeps each
> source separate. We found that the two SSD-Phoenix variants were being blended
> in our internal rankings because they share the same key and version, which we
> are fixing before we publish anything on this.
>
> Happy to walk through the detail whenever useful.

---

## Notes for internal review before sending

| Point | Status |
| --- | --- |
| Numbers verified directly against the source extracts, not against the defective ranking output | Confirmed in V6.0C |
| Single-version limitation stated explicitly | Yes |
| No claim of drift or horizon analysis | Yes |
| Forest grain confirmed locally rather than asserted | Yes |
| Internal ranking defect mentioned honestly without over-explaining | Yes |
| Does not promise a delivery date | Yes |

Open question Q15 still applies: confirm with Chinmay what is appropriate to send
now versus after V6.0F integration.
