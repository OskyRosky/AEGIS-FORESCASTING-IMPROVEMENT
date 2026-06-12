# Challenger Dependency Installation Log (Block 5.29B-Fix)

Generated: 2026-06-12T15:50:18

## Environment

- Python: 3.14.6 (pythoncore-3.14-64)
- pip: 26.1.2
- Install scope: project interpreter (user-approved).

## Commands Executed

- `python -m pip install --upgrade pip setuptools wheel`
- `python -m pip install statsmodels statsforecast lightgbm xgboost torch neuralforecast darts pmdarima  (combined attempt - failed on scipy source build for statsforecast)`
- `python -m pip install statsmodels lightgbm xgboost pmdarima  (succeeded)`
- `python -m pip install torch  (succeeded)`
- `python -m pip install neuralforecast  (installed legacy 0.1.0 - incompatible)`
- `python -m pip install statsforecast  (failed - scipy source build needs C compiler not present)`
- `python -m pip install darts  (succeeded)`
- `python -m pip install neuralforecast==1.7.6  (failed - requires ray>=2.2.0 with no Python 3.14 wheel)`

## Packages Installed Successfully

- statsmodels, pmdarima, lightgbm, xgboost (prebuilt cp314 wheels)
- torch 2.12.0+cpu
- darts 0.44.1 (+ scikit-learn, scipy 1.17.1, statsmodels, xarray, shap)

## Packages Failed / Unresolved

- **statsforecast**: build aborted - its dependency resolution pulled scipy 1.15.3 as a source tarball, which needs a C/Fortran compiler (MSVC) that is not installed. Optional: AutoARIMA/ETS/Theta are covered by pmdarima / statsmodels / darts respectively.
- **neuralforecast (modern)**: 1.7.6 requires `ray>=2.2.0`, which has no Python 3.14 wheel. Pip backtracked to the legacy 0.1.0, which is incompatible with the installed pytorch-lightning 2.6.5 (`pytorch_lightning.utilities.distributed` removed). NHITS depends only on neuralforecast, so it remains blocked.

## Important Warnings

- Console-script shims were installed to a Scripts dir not on PATH (cosmetic; imports unaffected).
- hyperopt emits a `pkg_resources` deprecation warning (cosmetic).

## Final Import Status

| dependency | available | version | status |
| --- | --- | --- | --- |
| darts | True | 0.44.1 | available |
| lightgbm | True | 4.6.0 | available |
| neuralforecast | False | - | installed_but_broken |
| pmdarima | True | 2.1.1 | available |
| statsforecast | False | - | missing |
| statsmodels | True | 0.14.6 | available |
| torch | True | 2.12.0+cpu | available |
| xgboost | True | 3.2.0 | available |
