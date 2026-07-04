# V1 Active Root Policy

## Root Policy

The active project root is:

`C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V1`

The parent directory is only the project container and version root. It must not be treated as the active working root for Stage 07.

## Versioning Policy

V1 is the active version for the current blueprint/release. Future versions such as V2 or V3 may be created later, but work remains inside V1 until a later version is formally declared active.

## Codex Instruction Policy

Codex should treat V1 as the working root for implementation. New Stage 07 code and outputs must be created inside V1 unless a prompt explicitly authorizes another target.

## Claude Audit Instruction Policy

Claude Opus audits should inspect V1 as the active project root. Historical Stage 05, Stage 06, and Audit #6 artifacts should be treated as preserved evidence.

## Shiny Stage 07 Path Policy

Stage 07 Shiny work must use V1-relative paths or a root derived from the V1 project location. Shiny must be read-only and must not recompute metrics, rerun models, regenerate forecasts, or reinterpret champion decisions.

## Historical Artifacts Policy

Historical artifacts must not be rewritten solely to update old path text. Any required correction must be additive, governed, and traceable.

## .venv Portability Warning

`.venv` is non-portable and may contain internal absolute paths. If the environment breaks after migration, recreate or reinstall dependencies instead of manually rewriting `.venv` internals.

## Output Preservation Policy

`outputs/model_lab` and `outputs/governance` are historical/governed evidence areas. They must be preserved and not rewritten during V1 path formalization.
