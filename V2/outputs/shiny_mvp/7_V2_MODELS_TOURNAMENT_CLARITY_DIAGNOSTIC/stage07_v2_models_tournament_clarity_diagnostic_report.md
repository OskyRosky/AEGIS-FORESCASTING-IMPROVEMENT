# Stage 07 — V2 Models > Tournament Clarity Diagnostic

**Status:** READY_FOR_OSCAR_REVIEW_V2_MODELS_TOURNAMENT_CLARITY_DIAGNOSTIC
**Date:** 2026-06-24
**Type:** Diagnostic only — NO code, data, models, or champion changed.
**Active root:** V2 (V1 frozen).

---

## 1. General Summary
The current Models > Tournament page is technically correct but overloaded: 8 KPI
cards (several disconnected), a 12-column standings table, a confusing MASE-vs-RMSSE
scatter, a heavy pairwise table, a "No composite score" card nobody understands, and
a policy block. Oscar wants the page to tell a simple, sports-like story: models enter,
they compete head-to-head, and ETS Explicit is selected under conditions.

The single most important finding: a governed artifact already encodes a
**win / draw / loss record per model** (`tournament_model_evidence_summary.csv`) that
is NOT currently shown. This is the natural "score" Oscar is asking for ("los goles") and
it lets us tell the story honestly without inventing anything.

Second key finding: the tournament is a **round-robin** (all-play-all, 78 = C(13,2)
pairwise comparisons), NOT a single-elimination bracket. A literal knockout bracket with
"rounds" and made-up scores (like the mockup's "57-43", "Round 0/1/2/3") would
**misrepresent the governed method**. The honest visual is a league-style standing
(win/draw/loss) and/or a head-to-head grid — which actually matches Oscar's own football
analogy better than a knockout bracket.

---

## 4. Current Tournament Page Diagnosis
Page title: "Tournament Standings". Subtitle: governed evidence, no recompute.

Current sections (top to bottom):
- **A. 8 KPI cards** (2 rows): Models ranked 13 · Primary metric MASE · Guardrail RMSSE ·
  Champion ETS Explicit · Confidence medium · Pairwise 78 · Champion support 8/0 ·
  "No formula" Composite Tournament Score.
  → The first row + pairwise is good. Confidence, 8/0, and "No formula" floating as cards
  are confusing and disconnected (Oscar's exact complaint).
- **B. Governed standings table** (DT, 12 columns): Model, Origin, Family, Median MASE,
  Median RMSSE, MASE guardrail, RMSSE guardrail, Coverage, Risk, Audit risk, Eligibility,
  Champion. → Useful but too wide; no win/loss record; sorted by MASE.
- **C. MASE vs RMSSE tradeoff** (plotly scatter). → Confusing. The two metrics are highly
  correlated, so a 2D plot adds little, and FastNeuralAR_MLP (MASE 739, RMSSE 164) is an
  extreme outlier that squashes all other points into the bottom-left corner. It does not
  show a "score". Recommend remove (or move to a technical collapsible).
- **D. Pairwise evidence table** (DT, 12 columns incl. bootstrap CIs, p-values, BH-adjusted
  p-values). → Valuable but very technical; should be collapsed by default.
- **E. "No composite tournament score is computed here"** shell-card. → Confuses users.
  No governed composite-score formula exists, so the page is honest, but a whole card
  saying "No formula" reads like something is missing. Recommend remove from main view.
- **F. Policy block** (Source policy / No recompute / Language policy). → Good governance
  content but belongs collapsed at the bottom.

---

## 5. Metric Inventory Summary
See `stage07_v2_models_tournament_metric_inventory.csv`. Highlights:

Available and governed:
- **official_median_mase** — primary error metric. LOWER IS BETTER. This is the "goals".
  All 13 models.
- **official_median_rmsse** — guardrail metric. All 13 models.
- **median_wmape / median_smape** — percentage error metrics, but ONLY populated for the
  6 challengers (blank for the 7 baselines). Partial coverage — good for a detail view,
  must show the gap honestly.
- **median_bias** — present for challengers only, un-normalized (values like -17656),
  confusing without context → keep hidden.
- **mase_guardrail_status / rmsse_guardrail_status** — pass / warning / fail.
- **risk_status** (low/medium/high), **audit_risk_flag**, **eligible_for_champion_consideration**,
  **champion_exclusion_reason** (only FastNeuralAR_MLP).
- **entity_count = 39** — constant coverage; low information as a column.

From `tournament_model_evidence_summary.csv` (NOT currently used, HIGH VALUE):
- **comparisons_tested** (12 per model), **supported_better_count** (wins),
  **supported_worse_count** (losses), **inconclusive_count** (draws),
  **net_supported_evidence** (wins − losses, the "goal difference").

From `tournament_pairwise_evidence.csv` (78 rows):
- model_a, model_b, **median_delta_mase** (head-to-head gap), bootstrap_ci_low/high,
  sign_test_p_value, bh_adjusted_p_value, practical_threshold (0.02),
  practically_meaningful, statistically_supported, **comparison_status**
  (supported_difference / inconclusive).

From `tournament_entity_model_scores.csv` (507 rows = 39 entities × 13 models):
- per-series MASE/RMSSE — too granular for default; possible future per-series drill-down.

---

## 6. What Is Clear Today
- Models 13, Pairwise 78, MASE = primary, RMSSE = guardrail, ETS Explicit = champion under
  conditions. These specific facts (the first card row + pairwise) are clear and liked.
- The standings table data is correct and trustworthy.

## 7. What Is Confusing Today
- Free-floating cards (Confidence, 8/0, "No formula") with no surrounding explanation.
- No visible notion of "who beat whom" or a win/loss record — the user cannot see WHY one
  model is stronger.
- MASE-vs-RMSSE scatter: meaning unclear, dominated by one outlier.
- "No composite tournament score" card reads like a missing feature.
- Pairwise table is a wall of statistics with no plain-language verdict up front.

---

## 8. MASE vs RMSSE Chart Assessment
**Recommendation: REMOVE from the main page (optionally keep inside a collapsed
"technical details" section).** Reasons: (1) MASE and RMSSE are strongly correlated, so a
2D scatter conveys little beyond the table; (2) FastNeuralAR_MLP is an extreme outlier that
collapses every other model into one corner, making it unreadable; (3) it does not represent
a single "score", which is exactly what Oscar expects from a chart. If ever kept, it must be
relabeled in plain language and the outlier handled (cap/annotate), but clarity is better
served by the win/loss story instead.

## 9. Composite Tournament Score Note Assessment
**Recommendation: REMOVE the standalone "No formula" card from the main page.** Prior audits
confirmed there is NO governed numeric composite-score formula, and we must not invent one.
Instead of a card announcing an absence, add one plain sentence inside a "How the champion is
decided" explainer: the decision combines the primary error metric (MASE), the guardrail
(RMSSE), head-to-head pairwise evidence, and governance gates (risk + eligibility) — not a
single blended number. Any residual governance wording moves to the collapsed policy section.

## 10. Bracket View Readiness
See `stage07_v2_models_tournament_bracket_readiness.csv`. Summary:
- The governed data is **round-robin**, not knockout. We can derive, WITHOUT recomputing:
  - per-model **win / draw / loss** record from `tournament_model_evidence_summary.csv`;
  - **head-to-head outcomes** from `tournament_pairwise_evidence.csv` (comparison_status);
  - MASE ordering from the scorecard.
- A literal knockout bracket with rounds and per-match "scores" (as in the mockup) is **NOT**
  in the data and would be fabricated → governance-unsafe as drawn.
- **Governance-safe options:**
  1. **League standings** (preferred, matches Oscar's football analogy): table/visual of
     W–D–L + net evidence + median MASE, ranked. Honest and directly from artifacts.
  2. **Head-to-head grid** (13×13 matrix of supported/inconclusive) — truthful round-robin view.
  3. **Illustrative bracket** ONLY if clearly labeled "visual aid derived from pairwise
     evidence — not an elimination tournament", seeded by MASE rank, edges annotated with the
     real `comparison_status` ("supported" / "inconclusive"). No invented round scores.
- Bracket/visual should be FIRST (the story); tables move below into collapsibles.

---

## 11. Recommended New Tournament Story
Plain-language framing (the football analogy Oscar used):
- The tournament is a **league where every model plays every other model** (round-robin, 78 matches).
- A model "scores" by having **lower MASE** (error). Lower MASE = better.
- **RMSSE is a guardrail** — a second error check so a model cannot win by gaming one metric.
- Each head-to-head match is **won / drawn / lost** based on governed pairwise evidence
  (supported difference vs inconclusive).
- **Risk and eligibility are the rulebook**: even a strong model can be held back (e.g.
  FastNeuralAR_MLP is excluded for an extreme-error audit flag).
- **ETS Explicit** has the lowest MASE and the strongest head-to-head record, so it is the
  **selected champion — under conditions** (never an unconditional winner).

---

## 12. Recommended New Tournament Page Structure
See `stage07_v2_models_tournament_recommended_structure.csv` for the full table. Order:
1. Header + plain subtitle (always visible).
2. Compact cards (5): Models 13 · Pairwise 78 · Primary metric MASE · Guardrail RMSSE ·
   Champion under conditions ETS Explicit.
3. "How to read this tournament" (collapsible, OPEN) — the football story above.
4. Head-to-head / league visual (the main story; league standings W–D–L, optional labeled
   bracket) (collapsible, OPEN).
5. Standings table (collapsible, CLOSED) — simplified default columns + win/loss record.
6. Goodness-of-fit / detailed metrics (collapsible, CLOSED) — wMAPE/sMAPE (challengers),
   guardrail statuses; coverage gap shown honestly.
7. Pairwise evidence (collapsible, CLOSED) — full technical table.
8. How the champion is decided + governance policy (collapsible, CLOSED) — replaces the
   "No composite score" card.

## 13. Recommended Tables / Columns
- **Standings (default columns):** Model · Family · Median MASE · Median RMSSE · W–D–L ·
  Risk · Eligibility · Champion. (Drop Origin into a tooltip/secondary; drop raw Coverage=39.)
- **Goodness-of-fit (detail):** Model · wMAPE · sMAPE · MASE guardrail · RMSSE guardrail
  (+ note: percentage metrics available for challengers only).
- **Pairwise (technical):** keep as-is but collapsed, with a plain-language "verdict" column
  (supported / inconclusive) shown first.

## 14. Recommended Sections to Remove or Collapse
- REMOVE: MASE-vs-RMSSE scatter; "No composite score" card; the disconnected
  Confidence / 8-0 / No-formula cards from the top strip.
- COLLAPSE: standings, goodness-of-fit, pairwise, governance policy.
- ADD: "How to read this tournament" + league/head-to-head visual (from existing artifacts).

## 15. Implementation Plan for Next Block (NOT implemented)
- **Block 1 — Simplify the top.** Replace 8 cards with 5 compact cards; remove the
  scatter and the "No formula" card; add the "How to read this tournament" collapsible.
- **Block 2 — Head-to-head story.** Add a governance-safe league standings (W–D–L + net
  evidence + MASE) using `tournament_model_evidence_summary.csv`; optionally a labeled
  illustrative bracket from pairwise `comparison_status`.
- **Block 3 — Collapse + slim tables.** Move standings/goodness-of-fit/pairwise into
  collapsibles with reduced default columns; add win/loss to standings.
- **Block 4 — Champion explainer + policy.** Add a short "How the champion is decided"
  block and fold governance policy beneath it.

---

## 16. Confirmation No Data/Governed Artifacts Were Modified
Confirmed. All artifacts were read-only. No CSVs written except the diagnostic outputs in
this folder.

## 17. Confirmation No Shiny Source Files Were Modified
Confirmed. No files under shiny_app/ were edited in this block.

## 18. Confirmation No Models / Forecasts / Tournaments Were Run
Confirmed. No computation; metrics read straight from existing governed artifacts.

## 19. Confirmation Champion Decision Was Not Changed
Confirmed. ETS Explicit remains the selected champion under conditions.

## 20. Risks / Open Questions
- Do you want a **league standings** (most honest, matches football analogy) as the main
  visual, OR a **labeled illustrative bracket** (closer to the mockup but must say "visual
  aid, not elimination"), OR both?
- wMAPE/sMAPE only exist for challengers (not baselines). Show them with a clear gap note,
  or omit? (Recommend show with note.)
- median_bias is un-normalized and confusing — keep hidden? (Recommend yes.)
- Keep the MASE-vs-RMSSE scatter anywhere (collapsed technical), or drop entirely?
  (Recommend drop.)

## 21. Total Execution Time
A few minutes (read-only inspection).
