import importlib.util, json, sys
from pathlib import Path
V6=Path(".").resolve().parents[1]
PILOT=V6/"outputs"/"v6_16_five_case_viewer_uiux_lab"/"build_v6_16_pilot_backtest.py"
print("pilot exists:", PILOT.exists())
spec=importlib.util.spec_from_file_location("pilot", PILOT); m=importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m); print("IMPORT_OK")
except Exception as e:
    print("IMPORT_FAILED:", type(e).__name__, str(e)[:200]); sys.exit(1)
base=list(getattr(m,"BASELINE_CLASSES",{}))
chal=list(getattr(m,"CHALLENGER_FORECASTERS",{}))
neu=list(getattr(m,"NEURAL_MODELS",()))
print("LAGS =", getattr(m,"LAGS",None), "| HORIZON_DAYS =", getattr(m,"HORIZON_DAYS",None))
print(f"\nBASELINE_CLASSES ({len(base)}):"); [print("  ",x) for x in base]
print(f"CHALLENGER_FORECASTERS ({len(chal)}):"); [print("  ",x) for x in chal]
print(f"NEURAL_MODELS ({len(neu)}):"); [print("  ",x) for x in neu]
allm=base+chal+list(neu)
print(f"\nTOTAL registered = {len(allm)}")
json.dump({"base":base,"chal":chal,"neural":list(neu),"LAGS":getattr(m,"LAGS",None),
           "HORIZON_DAYS":getattr(m,"HORIZON_DAYS",None),"all":allm},
          open("_p5a_models.json","w",encoding="utf-8"), indent=1)
