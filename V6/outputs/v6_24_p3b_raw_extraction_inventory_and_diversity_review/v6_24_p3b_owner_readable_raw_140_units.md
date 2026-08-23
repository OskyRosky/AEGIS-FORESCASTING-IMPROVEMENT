# V6.24-P3B — Owner-Readable: 140 Raw Extraction Units

**These are the 140 physical units inside the raw Parquet files.** This is the file-level truth, not the product count.

The reconciliation is exact:

```
140 physical units
-  50 SSD LVNE units  (duplicate physical variant: identical Mean_Actual to LVWE)
=  90 observed series
```

| Group | Units | Raw file | Observed? | Notes |
|---|---:|---|---|---|
| SSD LVWE | **50** | `ssd_lvwe_raw.parquet` | YES | Carries the observed actual series |
| SSD LVNE | **50** | `ssd_lvne_raw.parquet` | NO | Forecast variant only. Mean_Actual duplicates LVWE exactly |
| CPU  | **20** | `cpu_actuals_raw.parquet` | YES | 1:1 with observed series |
| IOPS  | **20** | `iops_actuals_raw.parquet` | YES | 1:1 with observed series |
| **Total** | **140** | 4 files | | |

---

## SSD LVWE — 50 raw units

| Metric | DB Type | Variant | Scenario | Gran. | Key | Raw file | Rows | Min date | Max date | Observed? | Fcst variant? | Dup physical? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | APCP150 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | APCPRD01 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | APCPRD02 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | AREP273 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | AUSP282 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | AUSP300 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | AUSPRD01 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | AUTP296 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | BRAP284 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | CANP288 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | CANPRD01 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | CHEP278 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | CHLP298 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | DEUP281 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | DNKP307 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | ESPP292 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | EURP107 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | EURP119 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | EURP120 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | FRAP264 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | GBRP123 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | GBRP265 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | GBRP267 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | IDNP305 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | INDP287 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | INDPRD01 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | ISRP290 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | ITAP293 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | JPNP286 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | JPNP301 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | JPNPRD01 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | KORP216 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | LAMP152 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | LAMP215 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | LAMPRD80 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | MEXP297 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | MYSP306 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NAMP100 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NAMP101 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NAMP104 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NAMPRD07 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NAMPRD08 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NORP279 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | NZLP299 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | POLP291 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | QATP289 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | SGPP274 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | SWEP280 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | TWNP295 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |
| SSD | Phoenix | LVWE | NOT_APPLICABLE | Forest | ZAFP275 | ssd_lvwe_raw.parquet | 131 | 2026-04-13 | 2026-08-22 | TRUE | TRUE | FALSE |

## SSD LVNE — 50 raw units

> **Do not load this group's `actual_value` as actuals.** Every row's `is_duplicate_physical_variant` is TRUE and `is_observed_series` is FALSE. P4 must take SSD actuals from LVWE only.

| Metric | DB Type | Variant | Scenario | Gran. | Key | Raw file | Rows | Min date | Max date | Observed? | Fcst variant? | Dup physical? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | APCP150 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | APCPRD01 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | APCPRD02 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | AREP273 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | AUSP282 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | AUSP300 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | AUSPRD01 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | AUTP296 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | BRAP284 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | CANP288 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | CANPRD01 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | CHEP278 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | CHLP298 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | DEUP281 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | DNKP307 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | ESPP292 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | EURP107 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | EURP119 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | EURP120 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | FRAP264 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | GBRP123 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | GBRP265 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | GBRP267 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | IDNP305 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | INDP287 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | INDPRD01 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | ISRP290 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | ITAP293 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | JPNP286 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | JPNP301 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | JPNPRD01 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | KORP216 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | LAMP152 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | LAMP215 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | LAMPRD80 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | MEXP297 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | MYSP306 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NAMP100 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NAMP101 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NAMP104 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NAMPRD07 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NAMPRD08 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NORP279 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | NZLP299 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | POLP291 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | QATP289 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | SGPP274 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | SWEP280 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | TWNP295 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |
| SSD | Phoenix | LVNE | NOT_APPLICABLE | Forest | ZAFP275 | ssd_lvne_raw.parquet | 132 | 2026-04-09 | 2026-08-22 | FALSE | TRUE | TRUE |

## CPU — 20 raw units

| Metric | DB Type | Variant | Scenario | Gran. | Key | Raw file | Rows | Min date | Max date | Observed? | Fcst variant? | Dup physical? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | APC-Multitenant | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | ARE-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | AUS-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | BRA-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | CAN-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | CHE-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | CHN-Gallatin | cpu_actuals_raw.parquet | 556 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | DEU-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | EUR-MSIT | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Consumed | Region | FRA-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | APC-Multitenant | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | ARE-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | AUS-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | BRA-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | CAN-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | CHE-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | CHN-Gallatin | cpu_actuals_raw.parquet | 556 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | DEU-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | EUR-MSIT | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |
| CPU | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NOT_APPLICABLE | Failover | Region | FRA-Go Local | cpu_actuals_raw.parquet | 562 | 2022-01-04 | 2023-07-20 | TRUE | FALSE | FALSE |

## IOPS — 20 raw units

| Metric | DB Type | Variant | Scenario | Gran. | Key | Raw file | Rows | Min date | Max date | Observed? | Fcst variant? | Dup physical? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | APC-Multitenant | iops_actuals_raw.parquet | 1103 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | ARE-Go Local | iops_actuals_raw.parquet | 1101 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | AUS-Go Local | iops_actuals_raw.parquet | 1103 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | BRA-Go Local | iops_actuals_raw.parquet | 1009 | 2020-09-22 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | CAN-Go Local | iops_actuals_raw.parquet | 1101 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | CHE-Go Local | iops_actuals_raw.parquet | 1101 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | CHN-Gallatin | iops_actuals_raw.parquet | 429 | 2022-05-10 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | DEU-Go Local | iops_actuals_raw.parquet | 1100 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | EUR-Multitenant | iops_actuals_raw.parquet | 1102 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Consumed | Region | FRA-Go Local | iops_actuals_raw.parquet | 1102 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | APC-Multitenant | iops_actuals_raw.parquet | 1102 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | ARE-Go Local | iops_actuals_raw.parquet | 1101 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | AUS-Go Local | iops_actuals_raw.parquet | 1103 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | BRA-Go Local | iops_actuals_raw.parquet | 1009 | 2020-09-22 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | CAN-Go Local | iops_actuals_raw.parquet | 1101 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | CHE-Go Local | iops_actuals_raw.parquet | 1101 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | CHN-Gallatin | iops_actuals_raw.parquet | 429 | 2022-05-10 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | DEU-Go Local | iops_actuals_raw.parquet | 1100 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | EUR-Multitenant | iops_actuals_raw.parquet | 1102 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
| IOPS | NOT_APPLICABLE | NOT_APPLICABLE | Failover | Region | FRA-Go Local | iops_actuals_raw.parquet | 1102 | 2020-06-23 | 2023-07-20 | TRUE | FALSE | FALSE |
