# V6.0D — LLM Assistant Grounding Contract (Amendment)

**Amendment to:** `canonical_metric_contract.md`
**Status:** binding for V6.0E, V6.0F, V6.0G and V6.0H.
**Nature:** preserve and extend. The assistant layer is a product feature, not an
optional extra, and the multi-metric expansion must not regress it.

---

## 1. What exists today, verified

The assistant layer is real and substantial. Measured in this stage:

| Component | Path | Size |
| --- | --- | --- |
| Explanation panel and export | `shiny_app/R/llm_explain.R` | 860 lines |
| Deterministic composition engine | `shiny_app/R/llm_compose.R` | 282 lines |
| Insight client seam | `shiny_app/R/llm_client.R` | 9 lines |
| Summary module | `shiny_app/modules/llm_summary/` | UI plus server |
| Evidence pack | `outputs/v4_4_mock_provider/v4_4_mock_responses.json` | 74,152 bytes |

The evidence pack holds **11 page-scoped responses** with **108 traceable claims**
and **78 source references**.

| Response field | Purpose |
| --- | --- |
| `page_id` | Binds the response to a dashboard section |
| `title`, `summary` | Headline narrative |
| `what_the_evidence_says`, `why_it_matters` | Body narrative |
| `sources_used` | Governed artifacts behind the answer |
| `limitations` | Explicit caveats surfaced to the user |
| `confidence` | Confidence badge |
| `claims_traceability` | `claim_id`, `claim`, `evidence_pack`, `source_artifacts`, `evidence_fields` |
| `download_payload` | Export content for MD, TXT, HTML, PDF and DOCX |

Provider metadata is `provider = mock`, `provider_stage = mock_no_llm`,
`is_real_llm = false`, `uses_azure = false`. The layer degrades gracefully when
the pack is missing and never stops the app.

## 2. Preservation invariant

| ID | Rule |
| --- | --- |
| A1 | The assistant UI must remain present on every page that has it today |
| A2 | The 11 existing page responses must keep working with unchanged behaviour |
| A3 | Quick prompts, the thinking states, the confidence badge, the limitations block, the technical traceability panel and the five export formats must all survive |
| A4 | `v4_4_mock_responses.json` is a frozen legacy artifact. It is never edited, replaced or deleted |
| A5 | Graceful degradation is preserved. A missing artifact yields an unavailable state, never a crash |

Removing, disabling or bypassing the assistant to simplify the multi-metric work
is a contract violation, not a trade-off.

## 3. Extension model, additive

The assistant's grounding is extended by a **new additive artifact** that sits
beside the frozen pack rather than replacing it.

**New artifact:** `metric_assistant_evidence_pack.json`
**Location:** `outputs/metrics_multi/`
**Producer:** V6.0E
**Consumer:** V6.0F

At read time the assistant merges two sources:

```
v4_4_mock_responses.json      (frozen, page-scoped, unchanged)
                +
metric_assistant_evidence_pack.json   (new, selection-scoped)
                =
        assistant answer
```

Merge rule: the legacy pack answers page-level questions exactly as today. The new
pack contributes the **current multi-metric selection context**. When the new pack
is absent the assistant behaves exactly as it does now.

### Required structure of the new pack

Each entry is keyed by the identity tuple and carries:

| Field | Purpose |
| --- | --- |
| `metric_id`, `metric_name` | Which metric the user is looking at |
| `db_type`, `db_type_label` | Which variant, so LVWE and LVNE are never conflated in prose |
| `scenario`, `scenario_status` | Including the `not_applicable` case |
| `granularity`, `key_namespace` | Region versus forest wording |
| `entity_key` | The selected key |
| `forecast_version`, `versions_available` | Cycle context |
| `unit`, `unit_status` | Prevents unit claims that are not verified |
| `availability_status` | What exists |
| `computability_status` | What may be claimed |
| `not_computable_reason` | Why an analysis is unavailable |
| `sources_used` | Same shape as the legacy field |
| `limitations` | Must include the single-version caveat when it applies |
| `claims_traceability` | Same five-field shape as the legacy pack |

Reusing the legacy field shapes means the renderer and the export pipeline need no
structural change.

## 4. Grounding rules

| ID | Rule |
| --- | --- |
| G1 | The assistant reads governed artifacts only. No live SQL, ever |
| G2 | No training, no fine-tuning, no model invocation in Track A |
| G3 | No recalculation of any business measure. Values are quoted, not derived |
| G4 | No mutation of any artifact, dataset, champion or governance decision |
| G5 | Every claim maps to `source_artifacts` and `evidence_fields`, as today |
| G6 | No unsupported claim. If evidence is absent the answer says so |
| G7 | No raw business values aggregated across `metric_id` in prose or in numbers |
| G8 | Single-version accuracy is never described as drift, trend, deterioration or improvement over time |
| G9 | A scenario that does not exist in the source is never named. For `not_applicable` the assistant says the source has no scenario dimension |
| G10 | The assistant never contradicts `computability_status`. If a capability is false, the narrative states the limitation instead of speculating |

## 5. Required narrative behaviours

When a selection is active, the assistant must be able to answer:

| Question | Grounded in |
| --- | --- |
| What am I looking at | `metric_name`, `db_type_label`, `granularity`, `entity_key`, `forecast_version` |
| Why is there no scenario filter | `scenario_status = not_applicable` |
| Can I compare this against the previous plan | `drift_computable` plus `not_computable_reason` |
| Why is there no forecast curve | `forecast_curve_computable = false` with `NO_TARGET_DATE_GRAIN` |
| Why is CPU not available | `availability_status` plus reason |
| How confident should I be | `confidence` plus `evidence_level` plus `unit_status` |

The SSD-Phoenix single-version case is the reference example: the assistant must
present it as accuracy evidence for one forecast cycle and explicitly state that
cross-plan drift is not available, without implying deterioration over time.

## 6. Docker and deployment

The new pack must live under `outputs/`, which is already mounted read-only into
the container. The assistant must work in the V6.0H container exactly as it does
locally, including the five export formats, which depend on the pandoc and TinyTeX
already baked into the image.
