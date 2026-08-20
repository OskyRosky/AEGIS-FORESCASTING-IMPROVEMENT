# V6.0D — Marker Update Plan

Marker files describe project state. V6.0C found two of them stale (defect D-08).
V6.0D is authorised to update documentation and markers, so the plan below is
**applied** in this stage. No logic, no legacy artifact and no Shiny file is
touched.

---

## 1. V6/VERSION_INFO.md

| Field | Before | After | Reason |
| --- | --- | --- | --- |
| `current_status` | V6.0B Azure readiness complete | V6.0D canonical multi-metric contract complete, Azure paused | Reflects the real stage |
| `next_stage` | V6.1 Identity / RBAC / Key Vault | V6.0E Multi-Metric Artifact Builder | Azure is paused until V6.0H passes |
| `next_block` | V6.1 Track A pending permissions | V6.0E pending explicit authorisation | Same |
| Active Root Rules, first bullet | "All active work must happen inside V5" | "All active work must happen inside V6" | V6 has been the active root since V6.0A; the rule contradicted the file's own header |
| Active Root Rules, frozen versions | "V1, V2, V3 and V4 are frozen" | "V1 through V5 are frozen" | V5 closed with `V5_DOCKER_LOCAL_MVP_CLOSED` |

## 2. V6/config/project_root_policy.json

| Field | Before | After | Reason |
| --- | --- | --- | --- |
| `next_stage` | V6.0A baseline clone parity validation | V6.0E multi-metric artifact builder | V6.0A and V6.0B are closed |
| `next_block` | V6.0B Azure readiness | V6.0E pending authorisation, Azure paused until V6.0H | Reflects the revised sequence |
| `azure_deployment_status` | absent | paused_until_v6_0h | Makes the pause explicit and machine readable |
| `multi_metric_contract_version` | absent | v6.0d | Lets any consumer detect the contract generation |

## 3. What is deliberately not changed

- No governance field: champion, model scope and horizons are untouched.
- No `shiny_policy` or `llm_policy` change: both remain read-only.
- No status token of a closed stage is rewritten.
- Historical artifacts are not rewritten to change path text, per the standing
  `historical_artifacts_rewrite_policy`.

## 4. Verification

After applying, both files must state V6 as the active root, name V6.0E as the
next stage, and record the Azure pause. Verified in `v6_0d_validation.csv` checks
V18 and V19.
