# V4.5 — Page Prompt Templates (per page_id)

> One template per MVP page. Each template tells the provider which evidence to read, what the
> response must cover, and which guardrails apply. Placeholders in `{{ }}` are filled from the
> governed evidence pack (V4.2) / deterministic insights (V4.3) at request time. **No real LLM and
> no Azure are activated by these templates.**

Common to every template:
- Obey `v4_5_system_prompt.md`.
- Return JSON per `v4_5_output_schema.json`.
- Always include the explain-not-decide caveat and the 2026-06-28 snapshot caveat in `limitations`.
- If the page evidence is missing, return `confidence: "insufficient_evidence"`.

---

## champion_overview

**Evidence inputs:** `v4_2_evidence_pack_champion_overview.json`, V4.3 cards
`champion_overview_*`.

**Must cover:**
- ETS Explicit **remains champion under governed conditions** (not re-fit, not changed).
- Champion accuracy on record: median MASE `{{champion_mase}}`, median RMSSE `{{champion_rmsse}}`.
- Governed model scope = `{{model_scope}}`.
- `{{candidates_advanced}}` candidates advanced; champion retained for review.

**Guardrails:** no absolute-winner language; no suggestion of automatic change.

---

## tournament

**Evidence inputs:** `v4_2_evidence_pack_tournament.json`, V4.3 cards `tournament_*`.

**Must cover:**
- `{{models_ranked}}` models ranked **for review**.
- Closest **documented challenger** by MASE ratio: `{{closest_challenger}}` at
  `{{closest_ratio}}x` the champion (e.g., SMLP-TCN at 2.72x) — when present in evidence.
- All challengers remain **documented challengers**; none advanced over the champion.

**Guardrails:** challengers only; never "winner"/"best"; rankings are descriptive.

---

## forecast_viewer

**Evidence inputs:** `v4_2_evidence_pack_forecast_viewer.json` (filtered + capped), V4.3 cards
`forecast_viewer_*`, risk flag `RF01` (namespace).

**Must cover:**
- Evidence was **filtered, summarized, and capped**; full forecasts/actuals were not passed
  (`{{rows_in_selection}}` of `{{rows_total}}`, `{{rows_embedded}}` embedded sample).
- Forecast horizon span `{{horizon_start}}` to `{{horizon_end}}` (when present).
- **Model namespace limitation**: Forecast Viewer model labels differ from tournament/governance
  names; the two must never be conflated.

**Guardrails:** make data minimization explicit; depends on on-screen filters/selection in later
phases; surface the namespace limitation in `limitations`.

---

## governance_risks

**Evidence inputs:** `v4_2_evidence_pack_governance_risks.json`, V4.3 cards `governance_risks_*`.

**Must cover:**
- Governance/risk explanation is **bounded by the evidence pack**; no risks inferred beyond data.
- TTL snapshot coverage: `{{ttl_entities}}` entities; months-to-live min `{{ttl_min}}`,
  median `{{ttl_median}}` (when present).
- Governed scope `{{model_scope}}` with `{{risk_flag_count}}` models carrying a recorded risk flag.

**Guardrails:** never invent risks; if evidence is missing, return **insufficient evidence**.
