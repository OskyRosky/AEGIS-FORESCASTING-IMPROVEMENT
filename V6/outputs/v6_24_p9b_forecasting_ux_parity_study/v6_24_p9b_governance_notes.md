# V6.24-P9B — Governance Notes

P9B was a study. Nothing was built, and that claim is proved rather than asserted.

---

## 1. How "no code was modified" is proved

Before reading a single file, every Shiny file and every governed artifact was
fingerprinted with sha256:

```
_p9b_shiny_before.csv        56 files
_p9b_artifacts_before.csv    22 artifacts
```

At the end of the stage the same hashes are recomputed and compared. Checks V26,
V27 and V28 in `v6_24_p9b_validation.csv` carry the result. A study that only
*said* it changed nothing would be worth less than the fingerprints.

This mirrors the discipline used since P6C, where the frozen-artifact guarantee
moved from mtime comparison to full sha256.

## 2. What P9B was allowed to do, and did

Allowed and used: inspect Shiny sources, inspect governed artifacts, read P7 and
P8 reports, run the app locally for observation, and write study documents under
the P9B folder.

Allowed but not needed: screenshot capture. The app was already observed in a real
browser at the end of P8, and those observations are recorded in the P8 fix report.

Not permitted and not done: modifying Shiny code, CSS, UI, server, helpers or any
artifact; running SQL; executing models; regenerating forecasts; recalculating
accuracy or rankings; changing taxonomy; removing either section; pushing;
`git add .`.

## 3. Scope discipline

The temptation in a study like this is to fix something small while looking at it —
the `key_axis_status` label is a two-line change, and the `GOVERNED_30_STE...`
wrap is a CSS tweak. **Neither was made.** Rule 6 says step by step, and rule 7
says validate before moving on. A fix smuggled into a study is a fix nobody
validated.

Both are recorded in the parity map with their target stage.

## 4. The governance rules P9C onward inherits

| Rule | Enforcement |
|---|---|
| Forecasting is not removed | No legacy file appears in any stage's modify list |
| Both sections coexist | Sidebar keeps both groups |
| Forecasting is the UX reference | Every port is documented in the parity map |
| Governed artifacts are the only data source | Every element in the parity map names its artifact |
| Highcharts, not Plotly | Source scan after P9F must find zero plotly calls |
| Step by step | One area per stage |
| Validate before moving on | Each stage closes with technical **and browser** evidence |
| Shiny is read-only | Source scan plus sha256 immutability, every stage |

## 5. The validation lesson carried forward

P8 reported **48/48 validation checks and 56 smoke checks passing** on pages that
rendered **blank** in a browser. Two blind spots caused it:

- `shiny::testServer` has no DOM, so it cannot observe output suspension or
  widget initialisation.
- An HTTP `GET /` returns the server-rendered shell. Dynamic content arrives later
  over the websocket, which a single request never sees.

Both tests were correct about what they measured. Neither measured what the user
sees.

**Every P9x stage must therefore close with a real browser check that reads
values, not markup.** This is recorded as risk R13 with severity HIGH, and it is
the reason "screenshots required" appears on P9C through P9H.

## 6. Things this study deliberately did not decide

Eight open questions are recorded in `v6_24_p9b_unresolved_questions.csv`. Three
of them genuinely block work:

- **Q1** — the P9D/P9E ordering discrepancy between the two owner documents.
- **Q3** — whether to take the four-family display split from the legacy artifact.
- **Q5** — whether the assistant is selection-aware or section-level.

Deciding these unilaterally would be exactly the improvisation this stage exists
to prevent.

## 7. State of the working tree

The three V6.24 files created in P8 were committed by the owner (commits
`a158866` and `206e366`, 2026-08-23 17:14). The four files modified by the P8
browser-render fix remain uncommitted and were **not** altered by P9B.

P9B added only new files under
`V6/outputs/v6_24_p9b_forecasting_ux_parity_study/`.

No push was performed. `git add .`, `-A` and `--all` were not used.
