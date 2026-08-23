import json, _p1_sql as S
from pathlib import Path
OUT=Path(".").resolve(); S.append_ledger_from(OUT/"v6_24_p1_query_ledger.csv")
rep={}
for metric,tbl,tcol,dcol,kcol in [("CPU","forecast_substrateBE_cpu","type","datadate","Forest_SKU"),
                                  ("IOPS","forecast_substrateBE_iops","type","datadate","Forest_SKU"),
                                  ("CPU","forecast_substrateBE_cpu_byDB_forest","ModelVersion","DateTime","Key"),
                                  ("SSD","forecast_substrateBE_ssd","","","")]:
    if not tcol:
        continue
    r=S.run(f"SELECT [{tcol}],COUNT(*),MIN([{dcol}]),MAX([{dcol}]),COUNT(DISTINCT [{kcol}]) FROM dbo.[{tbl}] WHERE [{tcol}] LIKE '%actual%' GROUP BY [{tcol}]",
            metric=metric,obj=tbl,purpose="Direct probe for Forest-level actual marker",qtype="aggregate")
    out=[[str(x[0]),int(x[1]),str(x[2]),str(x[3]),int(x[4])] for x in r]
    print(f"{metric}|{tbl}|{out if out else 'NO_ACTUAL_MARKER'}")
    rep[tbl]=out
# HDD forest combinations over 50
r=S.run("""SELECT LOWER(LTRIM(RTRIM(data_type))) AS dt, COUNT(*) AS combos,
           SUM(CASE WHEN obs>50 THEN 1 ELSE 0 END) AS over50, MIN(obs), MAX(obs)
           FROM (SELECT data_type, forest_name, COUNT(*) AS obs FROM dbo.[forecast_substrateBE_hdd]
                 WHERE LTRIM(RTRIM(type))='actual' GROUP BY data_type, forest_name) t
           GROUP BY LOWER(LTRIM(RTRIM(data_type)))""",
        metric="HDD",obj="forecast_substrateBE_hdd",purpose="Forest combinations over 50 real observations",qtype="aggregate")
print("HDD_FOREST_COMBOS:")
for x in r: print(f"   {x[0]} combos={x[1]} over50={x[2]} obs={x[3]}..{x[4]}")
rep["hdd_forest_combos"]=[[str(x[0]),int(x[1]),int(x[2]),int(x[3]),int(x[4])] for x in r]
Path("_stepI_forest_actuals.json").write_text(json.dumps(rep,indent=1),encoding="utf-8")
S.save_ledger()
