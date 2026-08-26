"""P9J | Read-only inspection of the LEGACY Models artifacts.
Nothing is written. This only reports what the old Models pages consume.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
files = {
 "tournament_standings": "outputs/model_lab/tournament_engine/tournament_preliminary_standings.csv",
 "tournament_scorecard": "outputs/model_lab/tournament_engine/tournament_model_scorecard.csv",
 "tournament_pairwise": "outputs/model_lab/tournament_engine/tournament_pairwise_evidence.csv",
 "tournament_evidence_summary": "outputs/model_lab/tournament_engine/tournament_model_evidence_summary.csv",
 "challenger_metrics": "outputs/model_lab/challenger_metrics/challenger_metrics_by_model_diagnostic.csv",
 "champion_conditions": "outputs/governance/6_3_champion_conditions/champion_conditions_protocol.csv",
 "champion_dashboard_language": "outputs/governance/6_3_champion_conditions/champion_dashboard_language.csv",
}
for name, rel in files.items():
    p = ROOT / rel
    print("=" * 78)
    print(name, "->", rel)
    if not p.exists():
        print("  MISSING")
        continue
    try:
        d = pd.read_csv(p)
    except Exception as e:
        print("  read error:", e); continue
    print(f"  rows={len(d)}  cols={len(d.columns)}")
    print("  columns:", list(d.columns))
    for c in ("model_name", "metric", "entity_key", "series_key", "scope", "grain"):
        if c in d.columns:
            u = d[c].dropna().unique()
            print(f"  {c}: n={len(u)} -> {list(u)[:18]}")
    if len(d) <= 6:
        print(d.to_string()[:1600])
    else:
        print("  head:"); print(d.head(4).to_string()[:1400])
