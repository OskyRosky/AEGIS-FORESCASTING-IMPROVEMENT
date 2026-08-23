# V6.24-P5 work directory

Scratch space for the P5 backtest run. **Nothing here is a product artifact.**

| Folder | Contents |
|---|---|
| `checkpoints/` | Per-batch partial results, resumable |
| `logs/` | Runtime logs |
| `failures/` | Failure ledger: series_id, model_name, error_type, message, timestamp |
| `temp_outputs/` | Intermediate CSV before promotion |
| `runtime_ledger/` | Per-batch timing and row counts |

**Partial results must never be promoted to `processed/` and Shiny must never read this folder.** Promotion happens only after P5 validation passes.
