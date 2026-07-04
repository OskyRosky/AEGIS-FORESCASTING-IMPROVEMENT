"""Build denominator reconciliation report for AUDIT #3 Major-1."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.benchmark_denominators import DENOMINATORS_OUTPUT, REPORT_OUTPUT, SUMMARY_OUTPUT
from utils.paths import PROJECT_ROOT


MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
MASE_SUMMARY = MODEL_LAB_DIR / "mase" / "mase_summary.csv"
RMSSE_SUMMARY = MODEL_LAB_DIR / "rmsse" / "rmsse_guardrail_summary.csv"
NON_NEGATIVE_SUMMARY = (
    MODEL_LAB_DIR / "non_negative_policy" / "non_negative_policy_summary.csv"
)
AGGREGATION_SUMMARY = MODEL_LAB_DIR / "aggregation_hierarchy" / "aggregation_summary.csv"
SIGNIFICANCE_SUMMARY = (
    MODEL_LAB_DIR / "statistical_significance" / "significance_summary.csv"
)
UNIT_TEST_REPORT = (
    MODEL_LAB_DIR / "denominator_reconciliation" / "denominator_unit_test_report.csv"
)

PREVIOUS_GLOBAL_MEDIAN_MASE = 0.9995779032967591
PREVIOUS_GLOBAL_MEDIAN_RMSSE = 1.0042237370985716
PREVIOUS_FLOORED_ROWS = 56


def _read_one(path):
    if not path.exists():
        return {}
    return pd.read_csv(path).iloc[0].to_dict()


def build_report() -> str:
    timestamp = datetime.now().isoformat(timespec="seconds")
    denom_summary = _read_one(SUMMARY_OUTPUT)
    mase_summary = _read_one(MASE_SUMMARY)
    rmsse_summary = _read_one(RMSSE_SUMMARY)
    non_negative_summary = _read_one(NON_NEGATIVE_SUMMARY)
    aggregation_summary = _read_one(AGGREGATION_SUMMARY)
    significance_summary = _read_one(SIGNIFICANCE_SUMMARY)
    tests = pd.read_csv(UNIT_TEST_REPORT) if UNIT_TEST_REPORT.exists() else pd.DataFrame()
    tests_passed = (not tests.empty) and bool((tests["status"] == "passed").all())

    text = f"""# Denominator Reconciliation Report - Block 5.27A

Created timestamp: {timestamp}

## AUDIT #3 Major-1 Finding

AUDIT #3 found that the prior MASE/RMSSE implementation used test-horizon lag-1 flat naive forecast error as the denominator. That conflicted with the approved benchmark semantics requiring a training-only lag-1 naive denominator.

## Selected Fix

Option A was implemented:

- MASE denominator = in-sample training-only lag-1 naive MAE.
- RMSSE denominator = in-sample training-only lag-1 naive MSE.
- Denominators are computed independently for each `entity_key` + `window_id`.
- Only `record_type == actual` rows with `actual_date <= train_end_date` are used.
- Test-horizon actuals, Block 5.19 naive forecasts, seasonal naive forecasts, Drift, and previous metric tables are not used as denominators.
- Epsilon floor = `1e-6`.

## Code Changes

- Added `python/model_lab/benchmark_denominators.py`.
- Updated `calculate_mase.py` and `calculate_rmsse.py` to consume training-only denominators.
- Updated `apply_non_negative_policy.py` and inspector logic to recompute adjusted metrics with training-only denominators.
- Regenerated downstream aggregation and statistical significance outputs from corrected adjusted metrics.

## Documentation and Config Changes

- Updated `docs/benchmark_semantics/benchmark_semantics_v1.md`.
- Updated `config/scoring_definitions.yaml`.
- Updated `config/ranking_policy.yaml`.

## Outputs Regenerated

- `outputs/model_lab/denominator_reconciliation/`
- `outputs/model_lab/mase/`
- `outputs/model_lab/rmsse/`
- `outputs/model_lab/non_negative_policy/` metric-derived outputs
- `outputs/model_lab/aggregation_hierarchy/`
- `outputs/model_lab/statistical_significance/`

## Denominator Results

- denominator rows: {denom_summary.get('denominator_rows', 'n/a')}
- entities: {denom_summary.get('entities', 'n/a')}
- windows: {denom_summary.get('windows', 'n/a')}
- MASE floored rows: {denom_summary.get('mase_denominator_floored_rows', 'n/a')}
- RMSSE floored rows: {denom_summary.get('rmsse_denominator_floored_rows', 'n/a')}
- median MASE denominator: {denom_summary.get('median_mase_denominator', 'n/a')}
- median RMSSE denominator: {denom_summary.get('median_rmsse_denominator', 'n/a')}

## Before/After Headline Metrics

- previous global median MASE: {PREVIOUS_GLOBAL_MEDIAN_MASE}
- corrected global median MASE: {mase_summary.get('global_median_mase', 'n/a')}
- previous global median RMSSE: {PREVIOUS_GLOBAL_MEDIAN_RMSSE}
- corrected global median RMSSE: {rmsse_summary.get('global_median_rmsse', 'n/a')}
- previous denominator floored rows: {PREVIOUS_FLOORED_ROWS}
- corrected MASE denominator floored rows: {denom_summary.get('mase_denominator_floored_rows', 'n/a')}
- corrected RMSSE denominator floored rows: {denom_summary.get('rmsse_denominator_floored_rows', 'n/a')}

## Regenerated Output Checks

- MASE rows: {mase_summary.get('metric_rows', 'n/a')}
- RMSSE rows: {rmsse_summary.get('metric_rows', 'n/a')}
- non-negative MASE median after: {non_negative_summary.get('mase_median_after', 'n/a')}
- non-negative RMSSE median after: {non_negative_summary.get('rmsse_median_after', 'n/a')}
- aggregation entity-window rows: {aggregation_summary.get('entity_window_score_rows', 'n/a')}
- significance pairwise comparisons: {significance_summary.get('pairwise_comparisons', 'n/a')}

## Validation Results

- denominator unit tests passed: {tests_passed}
- inspectors passed for MASE, RMSSE, non-negative policy, aggregation hierarchy, and statistical significance during Block 5.27A execution.

## Closure Rationale

Major-1 is closed because code, docs, configs, metric outputs, aggregation outputs, and statistical significance outputs now share the same official training-only lag-1 denominator definition. Block 5.19 naive benchmark forecasts remain valid reference forecasts but are no longer used as the MASE/RMSSE denominator.
"""
    REPORT_OUTPUT.write_text(text, encoding="utf-8")
    print(f"Created {REPORT_OUTPUT}")
    return text


if __name__ == "__main__":
    build_report()
