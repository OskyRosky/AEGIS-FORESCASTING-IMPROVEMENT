# FastNeuralAR_MLP Policy

Generated: 2026-06-13T16:08:35

## Purpose

FastNeuralAR_MLP is introduced as the lightweight neural replacement for the
current official challenger set after NBEATS was deferred for runtime
impracticality. It keeps a neural-style comparison in the MVP without requiring
heavy deep-learning training loops or dependency stacks.

## MVP Suitability

The model uses `sklearn.neural_network.MLPRegressor` with fixed parameters and
lagged historical actuals as features. It is designed to run quickly across the
locked 454 entity-windows and to remain suitable for future container and Azure
automation.

## Conceptual Relationship to NNETAR

Like R's NNETAR, the model is an autoregressive neural network: recent lagged
values are the inputs and the next value is the supervised target. Forecasts are
generated recursively for the 30-day horizon.

## Leakage Policy

- Training uses only actual values with `date <= train_end_date`.
- No future actual values are used in recursive forecasting.
- Horizon day 2 and later may use prior model predictions, not test actuals.

## Tuning Policy

- Lags are capped at 30 and reduced only when history is insufficient.
- Hidden layer size is fixed at `(32,)`.
- Activation is `relu`, solver is `adam`, `max_iter` is 300, and random seed is
  42.
- No official metric feedback tuning, no tournament feedback tuning, and no
  champion feedback tuning are allowed in this block.

## Runtime Policy

FastNeuralAR_MLP is classified as `light_or_medium`. It may replace heavier
neural candidates in MVP official execution when those candidates are runtime
impractical.

## Automation and Container Suitability

The dependency footprint is limited to `scikit-learn`, `numpy`, and `pandas`.
This is compatible with a lightweight Python container profile and avoids the
Python 3.14 neuralforecast/ray blocker that affects NHITS.
