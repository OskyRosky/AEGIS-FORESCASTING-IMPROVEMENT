TTL PROTOTYPE generated 2026-06-27
series: 45  resources: 1  snapshot_rows: 45  timeseries_rows: 2220
resources: ['HDD']  (multi-resource structure ready; HDD real only)
supply model: FLAT point-in-time (today); methods: intersection + eTTL
TTL bands: {'Cool': 33, 'Healthy': 10, 'Warning': 2}
methods: {'intersection': 42, 'eTTL': 3}
no-TTL (no pressure): 0
projection rows: 62
DEMAND=real forecast; SUPPLY+TTL=simulated (deterministic, flat).
outputs: C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V3\data\processed\ttl_supply_demand_timeseries.csv
         C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V3\data\processed\ttl_months_to_live_snapshot.csv
