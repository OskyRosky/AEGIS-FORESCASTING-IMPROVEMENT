# V6.24-P9G — Evidence-Aware Assistant

**Stage:** V6.24-P9G
**Scope:** assistant panels on the V6.24 Viewer and Forecast pages
**Downloads:** **deferred to P9G2** — not implemented, not pretended.
**Shiny remains read-only.** No governed artifact was modified.

---

## 1. The rule that shaped this stage

> *If the assistant cannot receive context from the selected series, do not
> mount it as if it could.*

I checked that before writing anything. The existing assistant retrieves
**precomputed mock responses indexed by `page_id`**; `llm_client.R` takes no
arguments at all. There is no path for a series to enter. So Option B was not
"less good" — it was impossible, and the honest answer was to build a
selection-aware local evidence assistant.

Full reasoning: `v6_24_p9g_assistant_architecture_decision.md`.

---

## 2. What was built

**One new file**, `R/v6_24_assistant_helpers.R`:

- `v6_24_evidence()` — builds the A–F context from seven governed artifacts,
  rebuilt on every request from the *current* selection and applied config
- `v6_24_assistant_intent()` — routes free text to 14 answerable categories or
  to a refusal
- `v6_24_assistant_answer()` — deterministic composition; every number printed
  came from an artifact column

Panels sit at the end of the Viewer and Forecast pages: 7 and 6 quick prompts,
a free-text box, a Generate button, an answer panel, an **"Evidence used"**
footer naming the artifacts consulted, a caveat line, and a local-composition
stamp.

---

## 3. The grounding proof

Claiming "it does not invent" is worthless without a check. So every value the
assistant printed in the browser was **re-derived independently from the
parquet files** in `v6_24_p9g_assistant_grounding_validation.csv` — 20 values
including champion name, rank metric and value, median WAPE and MAE, rank 2 and
rank 3 models with their WAPEs, observation count, actual date range, latest
actual, forecast window, step count, forecast min/max, backtest row count,
caveat badge, ranking policy, and the no-signal champion reason.

**20 / 20 matched.**

---

## 4. Governance behaviour verified in the browser

| Case | Result |
|---|---|
| `champion_visible = TRUE` | names the champion, cites `P6C_RANKING_POLICY_V2` |
| `champion_visible = FALSE` | *"No model can be presented as a winner for this series."* — no "best", no "recommended model is" |
| "Is this a 4-year forecast?" | states 30 steps, explicitly denies a longer horizon |
| "Why did demand increase because of a business event?" | evidence-not-available, amber panel, **no artifact cited** |
| "Should we buy more capacity?" | refused — no capacity or cost field exists |
| "How is the weather today?" | refused |
| Negative / extreme values | counts printed, "never clipped" |

The refusal is the required sentence verbatim:
*"I do not have evidence for that in the current V6.24 artifacts."*

---

## 5. Three real bugs I found in my own work

**1. Wrong function signature, silently.** I called
`v6_24_final_axis_label(series_id)`, but it takes contract **rows** and returns
`list(label=, basis=)`. It would not have errored — it would have hit its
"no rows" default and printed **"Operational Key"** for every series. Caught by
running the builder headless before touching the UI. Now prints "Region"
correctly.

**2. Three quick prompts routed to refusals.** My first intent router put the
unsupported guards first, so `should (i|we)` swallowed **"What should I pay
attention to?"** and **"What should I tell a stakeholder?"**, and `why is`
swallowed **"Why is this only a 30-step forecast?"** — two of them required
quick prompts. The buttons pass an explicit intent so they still worked, but a
user *typing* those words got a refusal. Reordered so answerable phrasings match
first, and narrowed the guards to real causal/action verbs. A 19-case routing
table now asserts expected intents: **19/19**.

**3. Contradictory caveat prose.** The panel read *"This series carries 1 caveat
code."* immediately followed by *"No material caveat for this series."* Both
came from real fields — `caveat_badge` and `caveat_message` are separate
judgements — but printed flat they contradict. The message is now framed as the
contract's materiality assessment.

## And one probe of mine that was wrong

My first horizon check flagged the answer as claiming a 4-year forecast. It was
matching the phrase **inside the denial**. The check now asserts three separate
things: states 30 steps, denies a longer horizon, and does not assert one.

---

## 6. A field that looked wrong and is not

`trailing_zero_latest_actual_flag` is **FALSE for all 15 no-signal series**.
That looked backwards. Checked against the artifact: the flag marks a trailing
zero tail on an *otherwise non-zero* series (4 such series exist). All-zero
series are covered by `no_signal_flag`. The assistant reads it verbatim, which
is correct.

---

## 7. Downloads — deferred, not done

Not implemented. The prompt says not to implement downloads if it would risk the
assistant, and the assistant was the whole stage.

There is also a real design question first: a ranking export must carry the
`champion_visible` gate, or a CSV would present a winner the UI refuses to
present. That contract belongs to **P9G2**. Assessment in
`v6_24_p9g_optional_downloads_assessment.csv`.

---

## 8. Governance

- **0** processed artifacts modified · **0** raw · **0** V1–V5 · **0** legacy files
- No SQL, no model execution, no forecast regeneration, no accuracy or ranking
  recalculation, no file writes
- **No network call and no API dependency** anywhere in the assistant path
- P9E's Highcharter charts and DT tables unchanged; legacy Forecasting intact
- No push, no `git add .`

---

## 9. P9F was skipped

The sequence went P9E → P9G. The **Forecast champion-first executive layout**
specified in the P9D note has not been built. The champion *default* and the
suppression language are correct, but the layout redesign has not happened.
Flagged as Q5 — worth confirming before P9H.

---

## 10. Next stage

**READY_FOR_P9H_FINAL_VISUAL_QA**, with P9G2 (downloads) and possibly P9F
outstanding. Neither blocks a visual QA pass.

`V6_24_P9G_EVIDENCE_AWARE_ASSISTANT_COMPLETED`
