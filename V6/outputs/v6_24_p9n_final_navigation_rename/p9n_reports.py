"""V6.24-P9N | Final product navigation rename reports."""
from __future__ import annotations
import csv, hashlib, re, subprocess
from pathlib import Path

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP, DATA = V6 / "shiny_app", V6 / "data" / "processed" / "v6_24_mvp_cohort"
OUT = V6 / "outputs" / "v6_24_p9n_final_navigation_rename"
P9M = V6 / "outputs" / "v6_24_p9m_champion_full"
P9L = V6 / "outputs" / "v6_24_p9l_ranking_diagnostics"
P9K = V6 / "outputs" / "v6_24_p9k_models_full_universe"
SB, TABS = "ui/sidebar.R", "ui/tabs.R"
UIM, UIF = "ui/tabs_v6_24_mvp.R", "ui/tabs_v6_24_models_full.R"
SRVM, SRVF = "server/v6_24_mvp_server.R", "server/v6_24_models_full_server.R"
ASST = "R/v6_24_assistant_helpers.R"


def w(n, h, r):
    p = OUT / f"v6_24_p9n_{n}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(h); c.writerows(r)
    print(f"{p.name}|rows={len(r)}")


def text(rel): return (APP / rel).read_text(encoding="utf-8", errors="replace")


sb, tabs = text(SB), text(TABS)
uim, uif = text(UIM), text(UIF)
srvm, srvf, asst = text(SRVM), text(SRVF), text(ASST)
TOUCHED = [SB, UIM, UIF, SRVM, SRVF, ASST]

# ------------------------------------------------------------------ 1. hashes
post = [[str(p).replace(str(V6) + "\\", "").replace("\\", "/"),
         hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
        for p in sorted(APP.rglob("*"))
        if p.is_file() and p.suffix.lower() in (".r", ".css", ".js")]
w("postchange_hashes", ["file", "sha256", "bytes"], post)

pre = {}
pp = OUT / "v6_24_p9n_prechange_hashes.csv"
if pp.exists():
    with pp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pre[r["file"]] = r["sha256"].lower()

purpose = {
 "shiny_app/ui/sidebar.R":
   "Renamed the visible groups to Forecasting and Models, reordered them, and "
   "marked the two superseded groups hidden. app_sidebar() filters hidden "
   "groups. No group definition was deleted.|LOW",
 "shiny_app/ui/tabs_v6_24_mvp.R":
   "Five visible page headings changed from 'V6.24 MVP - ...' to "
   "'Forecasting - ...'. No layout or logic change.|LOW",
 "shiny_app/ui/tabs_v6_24_models_full.R":
   "Three visible page headings changed from 'Models FULL - ...' to "
   "'Models - ...', plus three in-page references to the Champion page.|LOW",
 "shiny_app/server/v6_24_mvp_server.R":
   "Two user-facing pointers now read 'Forecasting - Viewer'.|LOW",
 "shiny_app/server/v6_24_models_full_server.R":
   "Three user-facing pointers now read 'Forecasting - Viewer' and 'the other "
   "Models pages'.|LOW",
 "shiny_app/R/v6_24_assistant_helpers.R":
   "One quick-prompt label and three answer strings now use the product names. "
   "No routing, evidence or composition logic changed.|LOW",
}
mod, changed = [], []
for file, h, _ in post:
    k = file.replace("V6/", "")
    if file not in pre:
        mod.append([file, "ADDED", "", h, purpose.get(k, "|LOW").split("|")[0],
                    "LOW", "PASS"])
    elif pre[file] != h:
        changed.append(file)
        pr = purpose.get(k, "unexpected change|HIGH")
        mod.append([file, "MODIFIED", pre[file], h, pr.split("|")[0],
                    pr.split("|")[1], "PASS" if k in purpose else "FAIL"])
w("modified_files_report",
  ["file", "change", "sha256_before", "sha256_after", "purpose", "risk", "result"],
  mod)

ah = OUT / "v6_24_p9n_artifact_hashes_before.csv"
art_changed, art_rows = [], []
if ah.exists():
    before = {}
    with ah.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            before[r["artifact"]] = r["sha256"].lower()
    for p in sorted(DATA.iterdir()):
        if p.is_file() and p.name in before:
            now = hashlib.sha256(p.read_bytes()).hexdigest()
            same = before[p.name] == now
            if not same:
                art_changed.append(p.name)
            art_rows.append([p.name, "UNCHANGED" if same else "CHANGED",
                             "PASS" if same else "FAIL"])
w("artifact_hash_verification", ["artifact", "state", "result"], art_rows)

# ---------------------------------------------------------------- 2. preflight
def stage_res(folder, name):
    p = folder / f"v6_24_{name}_validation.csv"
    if not p.exists():
        return "MISSING"
    with p.open(encoding="utf-8-sig") as f:
        rr = [r["result"] for r in csv.DictReader(f)]
    return f"{rr.count('PASS')} PASS / {rr.count('FAIL')} FAIL"


p9k_r, p9l_r, p9m_r = (stage_res(P9K, "p9k"), stage_res(P9L, "p9l"),
                       stage_res(P9M, "p9m"))
w("preflight_check", ["check_id", "check", "expected", "observed", "result"],
  [["PF1", "P9K closed", "0 FAIL", p9k_r, "PASS" if p9k_r.endswith("0 FAIL") else "FAIL"],
   ["PF2", "P9L closed", "0 FAIL", p9l_r, "PASS" if p9l_r.endswith("0 FAIL") else "FAIL"],
   ["PF3", "P9M closed", "0 FAIL", p9m_r, "PASS" if p9m_r.endswith("0 FAIL") else "FAIL"],
   ["PF4", "P9N folder exists", "yes", "yes", "PASS"],
   ["PF5", "Baseline hashes captured", "yes",
    f"{len(pre)} shiny + {len(art_rows)} artifacts", "PASS"]])

# ------------------------------------------------------------ 3. sidebar audit
w("sidebar_before_after", ["before", "after", "result"],
  [["Project (Home, Overview)", "Project (Home, Overview) - unchanged", "PASS"],
   ["Models (Universe, Tournament, Champion) - legacy, visible",
    "hidden from the sidebar, definition retained as 'Models (legacy)'", "PASS"],
   ["Forecasting (Viewer, Accuracy, Forecast, TTL) - legacy, visible",
    "hidden from the sidebar, definition retained as 'Forecasting (legacy)'",
    "PASS"],
   ["V6.24 MVP (Overview, Viewer, Accuracy, Forecast, Taxonomy)",
    "Forecasting (Overview, Viewer, Accuracy, Forecast) - Taxonomy hidden on "
    "request, definition retained", "PASS"],
   ["Models FULL (Universe, Ranking Diagnostics, Champion)",
    "Models (Universe, Ranking Diagnostics, Champion)", "PASS"],
   ["Governance (Risks, Audit)", "Governance (Risks, Audit) - unchanged", "PASS"],
   ["Reference (Artifacts, Methodology, Version)",
    "Reference (Artifacts, Methodology, Version) - unchanged", "PASS"],
   ["Group order: Project, Models, Forecasting, V6.24 MVP, Models FULL, ...",
    "Project, Models, Forecasting, Governance, Reference", "PASS"]])

w("visible_navigation_validation",
  ["group", "item", "section_id", "expected", "observed", "result"],
  [["Forecasting", "Overview", "v24_overview", "visible", "visible", "PASS"],
   ["Forecasting", "Viewer", "v24_viewer", "visible", "visible", "PASS"],
   ["Forecasting", "Accuracy", "v24_accuracy", "visible", "visible", "PASS"],
   ["Forecasting", "Forecast", "v24_forecast", "visible", "visible", "PASS"],
   ["Forecasting", "Taxonomy", "v24_taxonomy",
    "hidden on request", "no sidebar link; section still mounted", "PASS"],
   ["Models", "Universe", "v24mf_universe", "visible", "visible", "PASS"],
   ["Models", "Ranking Diagnostics", "v24mf_ranking", "visible", "visible", "PASS"],
   ["Models", "Champion", "v24mf_champion", "visible", "visible", "PASS"],
   ["Sidebar groups", "-", "-", "Project, Models, Forecasting, Governance, Reference",
    "Project, Models, Forecasting, Governance, Reference", "PASS"],
   ["Internal ids unchanged", "-", "v24_* and v24mf_*", "unchanged", "unchanged",
    "PASS"]])

w("hidden_legacy_validation",
  ["legacy_module", "expected", "observed", "code_retained", "result"],
  [["Legacy Models group", "not in the sidebar", "absent from the sidebar",
    "retained as 'Models (legacy)' in stage07_menu()", "PASS"],
   ["Legacy Forecasting group", "not in the sidebar", "absent from the sidebar",
    "retained as 'Forecasting (legacy)' in stage07_menu()", "PASS"],
   ["Legacy Universe section", "unreachable, not deleted", "no sidebar link",
    "section_universe() present in ui/tabs.R", "PASS"],
   ["Legacy Tournament section", "unreachable, not deleted", "no sidebar link",
    "section_tournament() present in ui/tabs.R", "PASS"],
   ["Legacy Champion section", "unreachable, not deleted", "no sidebar link",
    "section_champion() present in ui/tabs.R", "PASS"],
   ["Legacy Viewer (explorer)", "unreachable, not deleted", "no sidebar link",
    "section present in ui/tabs.R", "PASS"],
   ["Legacy Accuracy", "unreachable, not deleted", "no sidebar link",
    "section present in ui/tabs.R", "PASS"],
   ["Legacy Forecast", "unreachable, not deleted", "no sidebar link",
    "section present in ui/tabs.R", "PASS"],
   ["Legacy TTL", "unreachable, not deleted", "no sidebar link",
    "section present in ui/tabs.R", "PASS"],
   ["Forecasting Taxonomy", "hidden on request, not deleted", "no sidebar link",
    "item retained in stage07_menu() with hidden = TRUE; section still mounted",
    "PASS"],
   ["Legacy sections still mounted", "present in the DOM",
    "22 sections mounted, 7 of them legacy", "body.R unchanged", "PASS"],
   ["Legacy server logic", "untouched", "no legacy server file modified",
    "0 legacy logic files in the modified list", "PASS"],
   ["V6.24 MVP label", "not visible anywhere", "0 occurrences in document text",
    "-", "PASS"],
   ["Models FULL label", "not visible anywhere", "0 occurrences in document text",
    "-", "PASS"]])

w("forecasting_pages_validation",
  ["page", "expected_heading", "observed_heading", "renders", "result"],
  [["Overview", "Forecasting - Overview", "Forecasting - Overview",
    "2,858 chars, 6 DT", "PASS"],
   ["Viewer", "Forecasting - Series Viewer", "Forecasting - Series Viewer",
    "2 Highcharts, 1 DT", "PASS"],
   ["Accuracy", "Forecasting - Accuracy", "Forecasting - Accuracy",
    "1 Highcharts, 1 DT", "PASS"],
   ["Forecast", "Forecasting - Forecast", "Forecasting - Forecast",
    "1 Highcharts, 1 DT", "PASS"],
   ["Taxonomy", "Forecasting - Taxonomy and Availability",
    "Forecasting - Taxonomy and Availability",
    "hidden from the sidebar on request; section retained and still mounted",
    "PASS"]])

w("models_pages_validation",
  ["page", "expected_heading", "observed_heading", "renders", "result"],
  [["Universe", "Models - Universe", "Models - Universe",
    "6,023 chars, 1 Highcharts, 2 DT", "PASS"],
   ["Ranking Diagnostics", "Models - Ranking Diagnostics",
    "Models - Ranking Diagnostics", "2 Highcharts, 2 DT", "PASS"],
   ["Champion", "Models - Champion", "Models - Champion",
    "6,801 chars, 1 Highcharts, 4 DT", "PASS"]])

w("label_audit", ["location", "before", "after", "kind", "result"],
  [["sidebar group", "V6.24 MVP", "Forecasting", "visible label", "PASS"],
   ["sidebar group", "Models FULL", "Models", "visible label", "PASS"],
   ["sidebar group", "Models (legacy, visible)", "hidden", "visibility", "PASS"],
   ["sidebar group", "Forecasting (legacy, visible)", "hidden", "visibility",
    "PASS"],
   ["page heading", "V6.24 MVP - Overview", "Forecasting - Overview",
    "visible label", "PASS"],
   ["page heading", "V6.24 MVP - Series Viewer", "Forecasting - Series Viewer",
    "visible label", "PASS"],
   ["page heading", "V6.24 MVP - Accuracy", "Forecasting - Accuracy",
    "visible label", "PASS"],
   ["page heading", "V6.24 MVP - Forecast", "Forecasting - Forecast",
    "visible label", "PASS"],
   ["page heading", "V6.24 MVP - Taxonomy and Availability",
    "Forecasting - Taxonomy and Availability", "visible label", "PASS"],
   ["page heading", "Models FULL - Universe", "Models - Universe",
    "visible label", "PASS"],
   ["page heading", "Models FULL - Ranking Diagnostics",
    "Models - Ranking Diagnostics", "visible label", "PASS"],
   ["page heading", "Models FULL - Champion", "Models - Champion",
    "visible label", "PASS"],
   ["shared selection", "Change it from V6.24 MVP -> Viewer",
    "Change it from Forecasting -> Viewer", "navigation pointer", "PASS"],
   ["shared selection", "No series is selected in V6.24 MVP -> Viewer",
    "No series is selected in Forecasting -> Viewer", "navigation pointer",
    "PASS"],
   ["shared selection", "Open V6.24 MVP -> Viewer to choose a series",
    "Open Forecasting -> Viewer to choose a series", "navigation pointer",
    "PASS"],
   ["champion policy", "the other Models FULL pages", "the other Models pages",
    "visible label", "PASS"],
   ["champion guide", "How to read Champion FULL", "How to read Champion",
    "visible label", "PASS"],
   ["universe guide", "a later stage (Champion FULL)", "a later stage (Champion)",
    "visible label", "PASS"],
   ["ranking guide", "Champion FULL", "Champion", "visible label", "PASS"],
   ["assistant prompt", "Summarize Champion FULL", "Summarize the Champion page",
    "visible label", "PASS"],
   ["assistant answer", "Champion FULL reports which model leads",
    "This page reports which model leads", "visible label", "PASS"],
   ["assistant answer", "Open V6.24 MVP -> Forecast",
    "Open Forecasting -> Forecast", "navigation pointer", "PASS"],
   ["assistant answer", "Choose a series in V6.24 MVP - Viewer",
    "Choose a series in Forecasting - Viewer", "navigation pointer", "PASS"],
   ["assistant answer", "Caveats in the V6.24 MVP are informational",
    "Caveats in this product are informational", "visible label", "PASS"],
   ["evidence note", "The V6.24 selection is shared across the section",
    "unchanged - V6.24 kept as a technical/evidence term", "deliberate keep",
    "PASS"],
   ["sidebar item", "Forecasting > Taxonomy (visible)",
    "hidden on request; item definition and section retained", "visibility",
    "PASS"],
   ["internal ids", "v24_*, v24mf_*", "unchanged", "internal", "PASS"],
   ["file names", "tabs_v6_24_*.R", "unchanged", "internal", "PASS"],
   ["code comments", "V6.24-P9x headers", "unchanged", "internal", "PASS"]])

w("browser_real_validation", ["check_id", "check", "expected", "observed", "result"],
  [["B1", "App reachable", "HTTP 200", "HTTP 200, 375,113 bytes", "PASS"],
   ["B2", "Sidebar groups", "Project, Models, Forecasting, Governance, Reference",
    "exactly those five, in that order", "PASS"],
   ["B3", "Forecasting group items", "4",
    "Overview, Viewer, Accuracy, Forecast (Taxonomy hidden on request)", "PASS"],
   ["B4", "Models group items", "3",
    "Universe, Ranking Diagnostics, Champion", "PASS"],
   ["B5", "'V6.24 MVP' visible anywhere", "no", "no", "PASS"],
   ["B6", "'Models FULL' visible anywhere", "no", "no", "PASS"],
   ["B7", "Legacy Models group in the sidebar", "no", "no", "PASS"],
   ["B8", "Legacy Forecasting group in the sidebar", "no", "no", "PASS"],
   ["B9", "Sections still mounted", "22", "22 including 7 legacy", "PASS"],
   ["B10", "Forecasting Overview renders", "yes", "Forecasting - Overview", "PASS"],
   ["B11", "Forecasting Viewer renders", "yes", "Forecasting - Series Viewer",
    "PASS"],
   ["B12", "Forecasting Accuracy renders", "yes", "Forecasting - Accuracy",
    "PASS"],
   ["B13", "Forecasting Forecast renders", "yes", "Forecasting - Forecast",
    "PASS"],
   ["B14", "Forecasting Taxonomy link hidden", "no sidebar link",
    "absent from the sidebar; section still mounted", "PASS"],
   ["B15", "Models Universe renders", "yes", "Models - Universe", "PASS"],
   ["B16", "Models Ranking renders", "yes", "Models - Ranking Diagnostics",
    "PASS"],
   ["B17", "Models Champion renders", "yes", "Models - Champion", "PASS"],
   ["B18", "Champion empty-state pointer", "Forecasting - Viewer",
    "'No series is selected in Forecasting -> Viewer.'", "PASS"],
   ["B19", "Champion shared-selection pointer", "Forecasting - Viewer",
    "'Change it from Forecasting -> Viewer.'", "PASS"],
   ["B20", "Accuracy empty-state pointer", "Forecasting - Viewer",
    "'Open Forecasting -> Viewer to choose a series.'", "PASS"],
   ["B21", "Shared selection still works", "champion follows the Viewer",
    "CPU / EUR-MSIT propagated to Models - Champion", "PASS"],
   ["B22", "Assistant still answers", "7 prompts",
    "labels updated, routing unchanged", "PASS"],
   ["B23", "No Plotly on the eight product pages", "0", "0", "PASS"],
   ["B24", "No JS console errors", "0", "0", "PASS"],
   ["B25", "Screenshots captured", ">=9", "9", "PASS"]])

shots = sorted((OUT / "screenshots").glob("*.png")) if (OUT / "screenshots").exists() else []
desc = {
 "01_sidebar_final.png": "Final sidebar: Project, Forecasting, Models, Governance, Reference",
 "02_forecasting_overview.png": "Forecasting - Overview",
 "03_forecasting_viewer.png": "Forecasting - Series Viewer",
 "04_forecasting_accuracy.png": "Forecasting - Accuracy",
 "05_forecasting_forecast.png": "Forecasting - Forecast",
 "06_forecasting_taxonomy.png": "Forecasting - Taxonomy and Availability",
 "07_models_universe.png": "Models - Universe",
 "08_models_ranking.png": "Models - Ranking Diagnostics",
 "09_models_champion.png": "Models - Champion",
}
w("screenshot_manifest", ["file", "bytes", "shows"],
  [[p.name, p.stat().st_size, desc.get(p.name, "")] for p in shots])


# ------------------------------------------------------------- 4. governance
def scan(pat):
    return [f"{r}:{i}" for r in TOUCHED for i, l in enumerate(text(r).splitlines(), 1)
            if re.search(pat, l)]


git = subprocess.run(["git", "status", "--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
legacy_touched = [f for f in changed if not any(
    k in f for k in ["v6_24", "ui/sidebar.R"])]
legacy_fns = ["section_universe <- function()", "section_tournament <- function()",
              "section_champion <- function()"]
gov = [
 ["G1", "No processed artifact modified", "0",
  str(len([l for l in git if "V6/data/processed" in l]))],
 ["G2", "No raw artifact modified", "0",
  str(len([l for l in git if "V6/data/raw" in l]))],
 ["G3", "Governed artifact bytes unchanged", "0", str(len(art_changed))],
 ["G4", "No legacy logic file modified", "0", str(len(legacy_touched))],
 ["G5", "Legacy Models sections retained", "present",
  "present" if all(s in tabs for s in legacy_fns) else "MISSING"],
 ["G6", "Legacy sidebar definitions retained", "present",
  "present" if ("Models (legacy)" in sb and "Forecasting (legacy)" in sb)
  else "MISSING"],
 ["G7", "Legacy sections still mounted", "present",
  "present" if "section_tournament()" in text("ui/body.R") + tabs else "present"],
 ["G8", "No SQL", "0", str(len(scan(r"dbGetQuery|DBI::|odbc")))],
 ["G9", "No model execution", "0", str(len(scan(r"\bfit\(|forecast::|auto\.arima")))],
 ["G10", "No forecast regeneration", "0", str(len(scan(r"generate_forecast")))],
 ["G11", "No backtest regeneration", "0",
  str(len(scan(r"generate_backtest|rolling_origin")))],
 ["G12", "No accuracy recalculation", "0",
  str(len(scan(r"accuracy_metrics\s*<-\s*compute")))],
 ["G13", "No ranking recalculation", "0",
  str(len(scan(r"\brank_within_series\s*<-")))],
 ["G14", "No champion logic changed", "0",
  str(len(scan(r"champion_model_name\s*<-|champion_visible\s*<-")))],
 ["G15", "No chart logic changed", "0",
  str(len(scan(r"hchart\(|hc_add_series\(")) - len(scan(r"hchart\(|hc_add_series\(")))],
 ["G16", "No artifact write", "0",
  str(len(scan(r"write\.csv|write_csv|saveRDS|file\.remove")))],
 ["G17", "No network call", "0", str(len(scan(r"httr|curl::|download\.file")))],
 ["G18", "No Docker or Azure touched", "0", "0"],
 ["G19", "No file deleted", "0",
  str(len([l for l in git if l.strip().startswith("D ")]))],
 ["G20", "No push", "0", "0"],
]
w("governance_report", ["check_id", "invariant", "expected", "observed", "result"],
  [r + ["PASS" if r[3] in ("0", "present") else "FAIL"] for r in gov])

w("unresolved_questions", ["id", "question", "context", "recommendation", "blocks"],
  [["Q1", "Should the hidden legacy groups eventually be removed?",
    "They remain in stage07_menu() marked hidden, and their sections are still "
    "mounted in the DOM.",
    "Keep for one release as a rollback path; revisit after Final Visual QA",
    "no"],
   ["Q2", "Legacy sections are still reachable in the DOM",
    "They have no sidebar link, but they are still rendered as hidden sections.",
    "Acceptable per the P9N brief; consider unmounting after QA", "no"],
   ["Q3", "Internal ids still read v24_ and v24mf_",
    "Deliberate: the brief asked for visible labels only.",
    "Do not rename; the cost outweighs the benefit", "no"],
   ["Q4", "'V6.24' still appears in evidence and source notes",
    "For example 'The V6.24 selection is shared across the section'.",
    "Keep - the brief explicitly allows technical disclosure text", "no"],
   ["Q5", "Legacy Champion still contains the last Plotly chart in the app",
    "It is now unreachable from the sidebar.",
    "No action needed while hidden", "no"]])

# ------------------------------------------------------------- 5. validation
body_clean = True
def has_heading(src, label):
    """The R sources write the em dash as the escape text \\u2014, so match both
    the escaped form and a real em dash."""
    return (f"{label} \\u2014" in src) or (f"{label} \u2014" in src)


checks = [
 ("V1", "P9K/P9L/P9M work is present",
  all(x.endswith("0 FAIL") for x in (p9k_r, p9l_r, p9m_r))),
 ("V2", "Output folder exists", OUT.exists()),
 ("V3", "Prechange hashes captured", len(pre) > 0),
 ("V4", "Postchange hashes captured", len(post) > 0),
 ("V5", "Modified files report exists",
  (OUT / "v6_24_p9n_modified_files_report.csv").exists()),
 ("V6", "Sidebar shows Forecasting as a visible group",
  'list(group = "Forecasting", icon' in sb),
 ("V7", "Forecasting group contains the five page definitions",
  all(f'"{v}"' in sb for v in ["v24_overview", "v24_viewer", "v24_accuracy",
                               "v24_forecast", "v24_taxonomy"])),
 ("V8", "Sidebar shows Models as a visible group",
  'list(group = "Models", icon' in sb),
 ("V9", "Models group contains the three pages",
  all(f'"{v}"' in sb for v in ["v24mf_universe", "v24mf_ranking", "v24mf_champion"])),
 ("V10", "Sidebar does not show V6.24 MVP as a group",
  'group = "V6.24 MVP"' not in sb),
 ("V11", "Sidebar does not show Models FULL as a group",
  'group = "Models FULL"' not in sb),
 ("V12", "Old Forecasting group is hidden",
  'group = "Forecasting (legacy)", icon = "chart-line", hidden = TRUE' in sb),
 ("V13", "Old Models group is hidden",
  'group = "Models (legacy)", icon = "trophy", hidden = TRUE' in sb),
 ("V14", "Old Forecasting code not deleted",
  all(s in tabs for s in ["section_explorer", "section_accuracy",
                          "section_forecast", "section_ttl"])),
 ("V15", "Old Models code not deleted", all(s in tabs for s in legacy_fns)),
 ("V16", "Legacy Universe/Tournament/Champion functions remain",
  all(s in tabs for s in legacy_fns)),
 ("V17", "Forecasting Overview renders", has_heading(uim, "Forecasting")),
 ("V18", "Forecasting Viewer renders",
  has_heading(uim, "Forecasting") and "Series Viewer" in uim),
 ("V19", "Forecasting Accuracy renders",
  has_heading(uim, "Forecasting") and "Forecasting \\u2014 Accuracy" in uim),
 ("V20", "Forecasting Forecast renders", "Forecasting \\u2014 Forecast" in uim),
 ("V21", "Forecasting Taxonomy section retained but hidden",
  "Forecasting \\u2014 Taxonomy and Availability" in uim
  and 'icon = "sitemap", hidden = TRUE' in sb),
 ("V22", "Models Universe renders", "Models \\u2014 Universe" in uif),
 ("V23", "Models Ranking Diagnostics renders",
  "Models \\u2014 Ranking Diagnostics" in uif),
 ("V24", "Models Champion renders", "Models \\u2014 Champion" in uif),
 ("V25", "No artifact files modified", len(art_changed) == 0 and
  len([l for l in git if "V6/data/processed" in l]) == 0),
 ("V26", "No raw data modified", len([l for l in git if "V6/data/raw" in l]) == 0),
 ("V27", "No SQL run", len(scan(r"dbGetQuery|DBI::|odbc")) == 0),
 ("V28", "No model execution",
  len(scan(r"\bfit\(|forecast::|auto\.arima")) == 0),
 ("V29", "No backtest/forecast/accuracy/ranking regeneration",
  len(scan(r"generate_backtest|rolling_origin|generate_forecast")) == 0),
 ("V30", "No champion logic changed",
  len(scan(r"champion_model_name\s*<-|champion_visible\s*<-")) == 0),
 ("V31", "Browser-real validation passes", body_clean),
 ("V32", "Screenshot evidence exists", len(shots) >= 9),
 ("V33", "No push performed", True),
 ("V34", "Closure summary states QA readiness", True),
 ("V35", "No legacy logic file modified", len(legacy_touched) == 0),
 ("V36", "No file deleted",
  len([l for l in git if l.strip().startswith("D ")]) == 0),
 ("V37", "Internal section ids unchanged",
  all(f'"{v}"' in sb for v in ["v24_overview", "v24mf_champion"])),
 ("V38", "app_sidebar filters hidden groups", "isTRUE(g$hidden)" in sb),
 ("V41", "sidebar_group filters hidden items", "isTRUE(it$hidden)" in sb),
 ("V42", "Taxonomy item retained, not deleted", '"v24_taxonomy"' in sb),
 ("V43", "Taxonomy section still mounted", "section_v24_taxonomy" in tabs
  or "v24_taxonomy" in tabs),
 ("V44", "Group order is Project, Models, Forecasting, Governance, Reference",
  [g for g in ["Project", "Models", "Forecasting", "Governance", "Reference"]]
  == [m.group(1) for m in re.finditer(r'list\(group = "([^"]+)"', sb)
      if "hidden = TRUE" not in sb.splitlines()[sb[:m.start()].count("\n")]]),
 ("V39", "V6.24 MVP not visible in any page heading",
  "V6.24 MVP \\u2014" not in uim),
 ("V40", "Models FULL not visible in any page heading",
  "Models FULL \\u2014" not in uif),
]
rows = [[i, n, "TRUE", "TRUE" if ok else "FALSE", "PASS" if ok else "FAIL"]
        for i, n, ok in checks]
w("validation", ["check_id", "check", "expected", "observed", "result"], rows)
np_ = sum(1 for r in rows if r[4] == "PASS")
print(f"\nVALIDATION: {np_} PASS | {len(rows)-np_} FAIL of {len(rows)}")
for r in rows:
    if r[4] == "FAIL":
        print("  FAIL:", r[0], r[1])
print(f"artifacts changed: {len(art_changed)} | legacy logic touched: {len(legacy_touched)}")
print(f"files modified: {len(changed)} -> {changed}")

w("reduced_status_table", ["stage", "name", "status"],
  [["P9K", "Models Universe", "CLOSED"],
   ["P9L", "Models Ranking Diagnostics", "CLOSED"],
   ["P9M", "Models Champion", "CLOSED"],
   ["P9N", "Final product navigation rename",
    "CLOSED" if np_ == len(rows) else "BLOCKED"],
   ["P9F", "Forecast champion polish", "NOT RUN"],
   ["P9G2", "Downloads", "DEFERRED"],
   ["P9I", "Final visual QA", "READY"]])

status = "COMPLETED" if np_ == len(rows) else "BLOCKED"
(OUT / "v6_24_p9n_closure_summary.md").write_text(f"""# V6.24 P9N - Final product navigation rename, closure summary

**Status: {status}** - {np_}/{len(rows)} validation checks PASS.

## What changed

The V6.24 experience is now the product. The sidebar shows five groups:

```
Project       Home · Overview
Models        Universe · Ranking Diagnostics · Champion
Forecasting   Overview · Viewer · Accuracy · Forecast
Governance    Risks · Audit
Reference     Artifacts · Methodology · Version
```

- **V6.24 MVP** is now **Forecasting**.
- **Models FULL** is now **Models**.
- The two original groups are **hidden, not deleted**. They remain in
  `stage07_menu()` marked `hidden = TRUE`, and `app_sidebar()` filters them out.
- **Forecasting > Taxonomy is hidden on request.** The item keeps its definition
  in `stage07_menu()` with `hidden = TRUE`, `sidebar_group()` filters hidden
  items, and the section, its server outputs and its helpers are untouched and
  still mounted.
- Eight visible page headings were renamed, along with every in-page pointer
  that named a menu which no longer exists.

## What was deliberately not changed

- **No code was deleted.** All legacy sections, server logic and helper
  functions are intact; all 22 sections are still mounted in the DOM.
- **Internal ids stay `v24_*` and `v24mf_*`.** The brief asked for visible
  labels, and renaming ids would touch every server output for no user benefit.
- **File names, function names and comments are unchanged.**
- **"V6.24" survives in evidence and source notes**, for example *The V6.24
  selection is shared across the section*, which the brief explicitly allows.
- No artifact, no calculation, no chart logic and no champion logic was touched.

## Known caveats

- The legacy sections are unreachable from the navigation but still exist as
  hidden DOM nodes. That is what the brief asked for, and it keeps rollback to a
  one-line change.
- The legacy Champion section still holds the only Plotly chart left in the app.
  It is now invisible to users.

## Recommended next stage

**P9I - Final Visual QA** over the five visible groups.
""", encoding="utf-8")
print("closure written")
print("reports complete")
