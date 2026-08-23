# V6.24-P3B — Owner-Readable: UI/UX Filter Paths

How the filter tree renders from the downloaded data. Planning artifact only, not Shiny implementation.

---

## SSD — 50 observed series

```
Metric = SSD
  └─ DB Type = Phoenix                    (single value)
      └─ Variant = LVWE | LVNE            (FORECAST variant)
          └─ Granularity = Forest         (single value)
              └─ Key = 50 forest keys
```

> **Selecting a Variant must change the forecast line, never the actual line.** LVWE and LVNE hold an identical `Mean_Actual`. If the observed curve moves when you switch variant, that is a bug.

**Scenario and Segment are `NOT_APPLICABLE`** — neither axis exists in the SSD source. Do not render them.

**The 50 forest keys:**

```
  APCP150, APCPRD01, APCPRD02, AREP273, AUSP282, AUSP300, AUSPRD01, AUTP296
  BRAP284, CANP288, CANPRD01, CHEP278, CHLP298, DEUP281, DNKP307, ESPP292
  EURP107, EURP119, EURP120, FRAP264, GBRP123, GBRP265, GBRP267, IDNP305
  INDP287, INDPRD01, ISRP290, ITAP293, JPNP286, JPNP301, JPNPRD01, KORP216
  LAMP152, LAMP215, LAMPRD80, MEXP297, MYSP306, NAMP100, NAMP101, NAMP104
  NAMPRD07, NAMPRD08, NORP279, NZLP299, POLP291, QATP289, SGPP274, SWEP280
  TWNP295, ZAFP275
```

---

## CPU — 20 observed series over 10 keys

```
Metric = CPU
  (DB Type = UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE   <- DO NOT RENDER)
  └─ Scenario = Consumed | Failover
      └─ Granularity = Region             (single value)
          └─ Key = 10 region-environment keys
```

> **All 10 keys exist under BOTH scenarios.** The Key list does not change when the Scenario filter changes. This enables a Consumed-vs-Failover comparison on the same region.

**Caveat: `STALE_ACTUALS_SOURCE`, latest date 2023-07-20.**

**The 10 keys:**

```
  APC-Multitenant, ARE-Go Local, AUS-Go Local, BRA-Go Local
  CAN-Go Local, CHE-Go Local, CHN-Gallatin, DEU-Go Local
  EUR-MSIT, FRA-Go Local
```

---

## IOPS — 20 observed series over 10 keys

```
Metric = IOPS
  (DB Type = NOT_APPLICABLE                         <- IOPS has no DB Type axis)
  └─ Scenario = Consumed | Failover
      └─ Granularity = Region             (single value)
          └─ Key = 10 region-environment keys
```

> **All 10 keys exist under BOTH scenarios.** The Key list does not change when the Scenario filter changes. This enables a Consumed-vs-Failover comparison on the same region.

**Caveat: `STALE_ACTUALS_SOURCE`, latest date 2023-07-20.**

**The 10 keys:**

```
  APC-Multitenant, ARE-Go Local, AUS-Go Local, BRA-Go Local
  CAN-Go Local, CHE-Go Local, CHN-Gallatin, DEU-Go Local
  EUR-Multitenant, FRA-Go Local
```

---

## HDD — context only, 50 series

```
Metric = HDD
  └─ DB Type = EDB | Basilisk
      └─ Segment = Consumer | Enterprise      (EDB ONLY; NOT_APPLICABLE under Basilisk)
          └─ Granularity = Forest | Region
              └─ Key = forest or region key
```

> **The only CONDITIONAL segment axis in the whole cohort.** It applies under EDB and must disappear under Basilisk.

HDD is `ALREADY_LOCAL_NOT_EXTRACTED`. It is the only metric that already has actuals, all 15 governed backtests and forecast, so it is the only one with `ui_visible_now = TRUE`.

---

## Memory — NOT RENDERED

`BLOCKED_NO_USEFUL_ACTUALS_SOURCE`. The governed `vw_SubstrateBE_Demand_Memory_*` views exist with the correct contract but return 0 rows. Awareness gap only; it must not appear in the selector.

---

## Axis rendering rules

| Metric | Axis | Value | Render in UI? | Count | Notes |
|---|---|---|---|---|---|
| SSD | db_type | Phoenix | YES | 50 | Rendered only for SSD. CPU and IOPS carry an explicit placeholder that must never become a selectable filter option. |
| SSD | variant | LVWE | YES | 6550 | Forecast variant. |
| SSD | scenario | NOT_APPLICABLE | NO | 50 | SSD has no scenario axis in source. |
| SSD | granularity | Forest | YES | 1 | Single value, so informational rather than selectable. |
| SSD | key | 50 distinct keys | YES | 50 | The only high-cardinality axis. |
| CPU | db_type | UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE | NO | 10 | Rendered only for SSD. CPU and IOPS carry an explicit placeholder that must never become a selectable filter option. |
| CPU | variant | NOT_APPLICABLE | NO | 11228 | No variant axis for this metric. |
| CPU | scenario | Consumed | YES | 10 | 10 keys available under this scenario. |
| CPU | scenario | Failover | YES | 10 | 10 keys available under this scenario. |
| CPU | granularity | Region | YES | 1 | Single value, so informational rather than selectable. |
| CPU | key | 10 distinct keys | YES | 10 | The only high-cardinality axis. |
| IOPS | db_type | NOT_APPLICABLE | NO | 10 | Rendered only for SSD. CPU and IOPS carry an explicit placeholder that must never become a selectable filter option. |
| IOPS | variant | NOT_APPLICABLE | NO | 20501 | No variant axis for this metric. |
| IOPS | scenario | Consumed | YES | 10 | 10 keys available under this scenario. |
| IOPS | scenario | Failover | YES | 10 | 10 keys available under this scenario. |
| IOPS | granularity | Region | YES | 1 | Single value, so informational rather than selectable. |
| IOPS | key | 10 distinct keys | YES | 10 | The only high-cardinality axis. |
| SSD | variant | LVNE | YES | 50 | Second forecast variant over the same 50 observed series. |

---

## Current visibility

| Metric | Series | `ui_visible_now` | `ui_visible_after_p5_p6_p7` | Blocker |
|---|---:|---|---|---|
| HDD | 50 | **TRUE** | TRUE | None |
| SSD | 50 | FALSE | TRUE | 15 governed backtests missing (P5) |
| CPU | 20 | FALSE | TRUE | 15 governed backtests missing (P5) |
| IOPS | 20 | FALSE | TRUE | 15 governed backtests missing (P5) |
| Memory | 0 | FALSE | FALSE | No actuals source at all |

> Only **50 of 140** series could legitimately render in the Viewer today. The P7 gate must derive `navigation_contract` and `taxonomy_counts` AFTER checking completeness, so a series that lacks its backtests cannot reach the selector.
