# AEGIS V5.3 — Runtime Artifact Map

**Stage:** V5.3 — External Volumes / Artifact Mounts
**Method:** the governed loader (`shiny_app/R/data_loader.R` →
`build_artifact_registry()` / `load_governed_artifacts()`) defines every artifact
the dashboard reads at runtime. Presence was probed **from inside the running
container** (`docker exec ... Rscript _presence_probe2.R`), i.e. through the
external read-only mounts — not from the host.

## What the image contains vs what is mounted

- **Baked into the image (code + deps only):** `shiny_app/`, `config/`,
  `ACTIVE_PROJECT_ROOT.md`, `VERSION_INFO.md`, R runtime + packages, pandoc,
  TinyTeX. **No artifacts, no `data/`, no `outputs/` content baked.**
- **Mounted read-only at runtime:**
  - `./outputs` → `/app/outputs` (governed model_lab + governance + mock LLM JSON)
  - `./data/processed` → `/app/data/processed` (forecasts, actuals, viewer, TTL, model-eval, canonical universe)
- **NOT present anywhere:** `data/raw` (not baked, not mounted), `BACKUP`, `.env`, secrets.

## Runtime dependency summary (43 registry entries)

| group | source area | container path | required | present | missing | notes |
|-------|-------------|----------------|----------|---------|---------|-------|
| closure_pack | outputs | /app/outputs/model_lab/model_lab_closure_pack | 4 req + 4 opt | 8 | 0 | key_results, champion_summary, universe, risk_register required |
| tournament | outputs | /app/outputs/model_lab/tournament_engine | 2 req + 2 opt | 4 | 0 | standings + scorecard required |
| challenger | outputs | /app/outputs/model_lab/challenger_* | 0 req + 2 opt | 2 | 0 | diagnostics only |
| governance | outputs | /app/outputs/governance/6_3_champion_conditions | 2 req | 2 | 0 | champion conditions + language |
| audit | outputs | /app/outputs/model_lab + governance/audit_6 | 0 req + 5 opt | 5 | 0 | audit trail |
| methodology | outputs / docs | /app/outputs/model_lab/champion_decision + /app/docs | 0 req + 2 opt | 1 | 1 | benchmark_semantics (docs/, not mounted) missing — optional, page repurposed |
| forecasting | data/processed | /app/data/processed | 0 req + 11 opt | 11 | 0 | forecasts, intervals, viewer, actuals, entities, run_metadata |
| ttl | outputs / data/processed | /app/... | 0 req + 3 (1 roadmap) | 2 | 1 | ttl_capacity is a roadmap placeholder (never produced) |
| model_eval | data/processed | /app/data/processed | 0 req + 6 opt | 6 | 0 | model_universe_canonical drives the 15-model scope |
| llm | outputs | /app/outputs/v4_4_mock_provider/v4_4_mock_responses.json | 1 req | 1 | 0 | 10 mock assistants (read-only) |

**Required artifacts: 9 / 9 present in container.** The 2 "missing" entries are
`benchmark_semantics` (optional; `docs/` is neither baked nor mounted, page was
repurposed away from benchmark in V3) and `ttl_capacity` (roadmap placeholder,
never produced). Both are **non-blocking** and load gracefully as empty.

## data/raw — explicitly NOT a runtime dependency

No registry entry, and no `data_loader.R` / helpers reference, points to
`data/raw`. `data/raw` is an ingestion input consumed only by the (out-of-scope)
Python refresh pipeline. It is **not baked, not mounted, and not read** by the
dashboard. Confirmed absent inside the container (`test -d /app/data/raw` = no).

## Legacy / non-runtime artifacts present but unused

- `forecast_viewer_pilot` + `forecast_viewer_pilot_manifest` — superseded by the
  full viewer artifact; kept for provenance, the active viewer no longer reads them.
- `forecast_comparison.csv` — empty/unused stub.

These are read into the loader cache but not surfaced; harmless.
