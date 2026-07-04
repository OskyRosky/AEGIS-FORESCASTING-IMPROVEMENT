# AEGIS V6.0B — Azure Permissions Checklist (prerequisite for V6.1+)

> Confirm these BEFORE V6.1 creates anything. Track A items are needed first;
> Track B items only after the hard gate. Nothing here is executed in V6.0B.

## Track A (V6.1–V6.4) — required to proceed
- [ ] Create **Resource Group** (or use an approved existing one).
- [ ] Create **Azure Container Registry (ACR)**.
- [ ] Create **Azure Container Apps** environment + app.
- [ ] Create **User-assigned Managed Identity**.
- [ ] Create **Key Vault**.
- [ ] Create **Storage Account + Azure Files** share.
- [ ] Assign **RBAC** roles (needs **User Access Administrator** or **Owner** on the scope):
      AcrPull, Key Vault Secrets User, Storage File Data SMB Share Reader.
- [ ] Configure **internal/private ingress** for the dashboard.
- [ ] (If required) **VNet integration** for the ACA environment.

## Track B (V6.5+) — required only after the hard gate
- [ ] **VNet / Private Link** to Azure SQL.
- [ ] **SQL DB Reader** (or minimum) role for the refresh identity.
- [ ] **Blob Storage** containers (staging/productive/backups) + roles.
- [ ] **Log Analytics / App Insights** workspace.
- [ ] Firewall / allowed-networks configuration for SQL.
- [ ] (If Azure OpenAI) **Cognitive Services OpenAI User** role (optional, V6.8).

## General
- [ ] Confirm **subscription** + **region** to use.
- [ ] Confirm **naming / tagging** conventions and cost center.
- [ ] Confirm whether **public exposure** is ever allowed (default: no) + legal
      sign-off for Highcharts before any public exposure.

**Blocker note:** if RBAC-assignment rights or resource-creation rights are not
available, Track A cannot proceed past V6.0B. Report and stop.
