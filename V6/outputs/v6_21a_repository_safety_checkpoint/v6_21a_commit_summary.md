# V6.21A Repository Safety Checkpoint

## Repository facts

| Item | Value |
|---|---|
| Repository root | `AEGIS-FORESCASTING-IMPROVEMENT` |
| Branch | `main` |
| Commit count before checkpoint | 100 |
| Previous HEAD | `3d94b06` (also the remote tip `origin/main`) |
| Rejected checkpoint commits | `cae6955`, `8cafcd2`, `0a53d4b` (undone with `--soft`) |
| New checkpoint commit | `7502681` |
| Commit count after remediation | 101 |
| Commits ahead of origin/main | 1 |
| Backup of the rejected history | branch `v6_21a_pre_remediation` and tag `v6_21a_pre_remediation_tag` at `0a53d4b` |
| Pushed | NO, ready for Oscar to push from GitHub Desktop |
| Pull request | NO |
| Merge | NO |

## V6.21A-FIX: oversized file remediation

The first checkpoint was rejected by GitHub because six blobs exceeded the 100 MB
limit. The commit was redone rather than patched, since `.gitignore` does not
remove content that is already inside a commit.

Deviation from the prescribed procedure, and why:

- The prompt assumed **one** new commit and prescribed `git reset --soft HEAD~1`.
  The repository actually had **three** unpushed commits (`cae6955`, `8cafcd2`
  created by an external Git process, and `0a53d4b` created here).
- `HEAD~1` would have left the oversized blobs inside `cae6955` and the push
  would have failed again.
- The reset therefore targeted `3d94b06`, which is exactly the remote tip, so all
  unpushed history was rebuilt into a single clean commit.
- Before any reset, the rejected history was preserved in branch
  `v6_21a_pre_remediation` and in a tag. Nothing became unreachable.
- Only `--soft` was used. `--hard` was never used.

Bytes excluded by the new `.gitignore` rules: **2,110,959,226** (about 1.97 GiB)
across 17 files.

Largest file still committed: `forecast_viewer_model_outputs_v2_full.parquet`
at 14,280,896 bytes, well below both the 25 MB rule and the 100 MB GitHub limit.

### Pre-existing oversized blobs

Seven blobs between 45 MB and 66 MB remain in `HEAD`, all under
`V6/outputs/model_lab`, `v3_2g_...` and `v3_3_daily_refresh`. They were **already
tracked in `3d94b06`** and are already on GitHub, so they neither block the push
nor originate from this checkpoint. The new `.gitignore` patterns match them, but
ignore rules do not untrack existing files. Removing them would require
`git rm --cached`, which was not authorised in this stage.

### Files not deleted

No file was deleted from disk at any point. All six rejected artifacts were
verified as present, with their original byte sizes, with modification timestamps
predating this session, and with a readable first line.

### Files outside V6

The reset returned four root-level paths to an uncommitted state:
`About presentation 30 - 06 -2026.docx`, `Presentation.pptx`,
`MULTI_METRIC_EXPANSION_HANDOFF.md` and
`Escenario completo ---- Desde metricas hasta Keys ----/`. They were not staged,
as required. The discovery folder holds the Master Catalog used as evidence in
V6.19 and V6.20 and still deserves a separate protection decision.

## DEVIATION: an external Git process committed during staging

While explicit V6-scoped staging was in progress, an external Git process (the
editor's built-in Git integration, author "Oscar CENTENO MORA") acquired
`.git/index.lock` and created two commits, both with the message `add`:

| Commit | Time | Files |
|---|---|---:|
| `cae6955` | 2026-08-19 20:31:55 -06:00 | 325 |
| `8cafcd2` | 2026-08-19 20:32:02 -06:00 | 1 |

That process did **not** honour the V6.21A staging policy. It committed:

- **7 files outside `V6/`**: `About presentation 30 - 06 -2026.docx`,
  `Presentation.pptx`, `MULTI_METRIC_EXPANSION_HANDOFF.md` and the four files in
  `Escenario completo ---- Desde metricas hasta Keys ----/`.
- **9 files above the 25 MB limit**, totalling roughly 2.03 GB, including
  `forecast_viewer_model_outputs_v2_full.csv` (658 MiB) and
  `viewer_backtest_phase_a_nonneural.csv` (477 MiB).

Mitigating facts:

- **V1 through V5 were not touched**: zero files from those trees are in the commits.
- Nothing was pushed; the commits are local only.
- All intended V6.16-V6.20 content was captured.
- The out-of-scope root files are the Master Catalog evidence used by V6.19 and
  V6.20, which were previously unprotected.

Git history was deliberately **not** rewritten. A soft reset would have been
possible while the commits are local, but rewriting history that another active
process is writing to is unsafe, and the instruction set forbids destructive
operations. This is recorded as an owner decision instead.

Owner options:
A. accept the commits as they stand;
B. authorise a local history rewrite to enforce the 25 MB and V6-only rules;
C. keep the history and later purge the large duplicate CSVs once the
   Parquet-only decision is made.

## Correction to a stated assumption

The premise of a "single visible commit / no committed history" is **refuted at
repository level**. The repository has **100 commits** and **11,126 tracked files**
at HEAD.

The accurate statement is narrower: `V6/shiny_app` had received only one commit
(`0d573f4`, 2026-07-03), so all V6.16 through V6.20 work was uncommitted until this
checkpoint.

## Tracked files by top-level folder at HEAD

| Folder | Tracked files | Protected by Git | Changes detected | Action required |
|---|---:|---|---|---|
| V6 | 2,265 | YES | YES, now committed | None |
| V5 | 2,241 | YES | NO | None |
| V4 | 2,051 | YES | NO | None |
| V3 | 2,018 | YES | NO | None |
| V2 | 1,135 | YES | NO | None |
| V1 | 895 | YES | NO | None |
| BACKUP | 512 | YES | NO | None |
| Root files (docs, PDFs, README, setup.R) | 8 | YES | 2 modified | Reported, never staged |

**Finding: V1 through V5 are already protected by Git.** The hypothesis that the
frozen versions were unprotected is false. They were not touched in this stage.

## Changes outside V6 detected but not staged

- `About presentation 30 - 06 -2026.docx` (modified)
- `Presentation.pptx` (modified)
- `Escenario completo ---- Desde metricas hasta Keys ----/` (untracked)
- `MULTI_METRIC_EXPANSION_HANDOFF.md` (untracked)

None of these were staged. Note that the untracked discovery folder holds the
Master Catalog used as evidence in V6.19 and V6.20.

## OneDrive files on-demand

Placeholder scan under `V6`: **0 files** with `Offline` or `RecallOnDataAccess`
attributes. No hydration risk was present, so staging could not trigger large
cloud downloads.

## Files committed

| Measure | Value |
|---|---:|
| Candidate V6 files | 312 |
| Staged and committed | 299 |
| Excluded | 13 |
| Committed size | about 40.8 MiB |

Staging used `git add --pathspec-from-file` with 299 explicit paths. No
`git add .`, `-A` or `--all` was used, and no path outside `V6/` was staged.

Committed categories include Shiny source code, configuration, governance CSV and
Markdown, small metadata, both productive Parquet artifacts, and stage evidence
from V6.15 through V6.20.

## Files excluded

| Reason | Files | Approximate size |
|---|---:|---|
| Over the 25 MB limit | 9 | about 2.03 GB |
| Intermediate or binary run files above 5 MB | 4 | about 72 MB |

Largest exclusions: `forecast_viewer_model_outputs_v2_full.csv` (658 MiB),
`viewer_backtest_phase_a_nonneural.csv` (477 MiB),
`forecast_forward_outputs_v6_17_full.csv` (243 MiB), the three R6 phase-1
extraction CSVs, `viewer_backtest_phase_b_neural.csv`, `phase_a_console.log`, and
two DuckDB databases.

Both productive Parquet files were **below** 25 MB and were committed:
Viewer 14,280,896 bytes and Forward 6,210,430 bytes.

## Ignored dashboard data risk

`V6/.gitignore` line 4 ignores `data/processed/`.

`V6/data/processed` holds **24 files, 144,682,147 bytes (about 138 MiB)** and is
**NOT_PROTECTED_BY_GIT**. It is not protected by this commit and not protected by
the bundle.

It contains live dashboard inputs, including the sole Accuracy input
(`forecast_viewer_model_outputs.csv`, 204,300 rows, 39 keys) and both TTL inputs.

`.gitignore` was not modified and nothing was force-added, as required.

Owner decision remains open: A un-ignore selected small stable artifacts,
B keep ignored with an external backup, C migrate required runtime data into
governed Parquet or metadata outputs, or D temporarily accept the risk.

## Off-OneDrive backup

| Item | Value |
|---|---|
| Bundle path | `C:\Users\oscarau\Desktop\aegis_checkpoint_bundle\aegis_v6_checkpoint.bundle` |
| Scope | `--all` |
| Size | 214,674,401 bytes (about 205 MiB) |
| Outside OneDrive | YES |
| Verification | PASS: "The bundle records a complete history" |
| Tip recorded | `8cafcd2` |

The bundle protects committed Git history only. It does **not** protect the
ignored `V6/data/processed` files, nor the excluded large CSVs.

## Owner decision context recorded for the next stage

- Accuracy primary decision: **A, migrate Accuracy to the new V6 Parquet universe**.
- Fallback: **C, temporarily disable Accuracy with a clear unavailable state** if
  migration is not safe.
- Option B must not be chosen unless Oscar explicitly approves it later.

Nothing above was implemented in this stage.

## Next recommended stage

**V6.21B — Registry and Accuracy Hardening**, covering artifact registry Parquet
support, the Accuracy migration or temporary disablement, and restoration of the
Forward Forecast LLM panel.

The V6.19 cohort blockers and the V6.20 generation blockers remain open and are
unaffected by this checkpoint.
