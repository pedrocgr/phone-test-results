# Smartphone touch experiments

A simple, reproducible analysis of recorded touchscreen contacts for a scientific article. All documentation and derived artifacts are in English. Raw measurements are preserved.

## Repository layout

```text
data/
  raw/sweetspot/           Original Sweet Spot JSONL (20 sessions)
  raw/random_poses/        Original Random Poses exports (11 sessions)
  raw/horizontal_tests/    Original Horizontal Tests exports (30 sessions; 13 October)
  annotations/            Operator exclusions and target-count corrections
  processed/              Retained Sweet Spot and Random Poses JSONL
  excluded/               Original events from archived trials
notebooks/
  sweetspot.ipynb          Baseline outcomes, repeated contacts, maps
  contact_analysis.ipynb   Three conditions: tendency, region × size, IMU and map review
scripts/
  run_analysis.py         Execute both notebooks
  analyze_contacts.py     Extended analysis; can also run directly
  analyze_touch_repeats.py Two counting views, reusing the existing figures and maps
  check_analysis.py       Check data preservation and results
  check_contacts.py       Check geometry, censoring flags, IMU and extended outputs
  check_touch_repeats.py   Check grouping, unchanged sources and both figure sets
results/
  README.md                  Start here: counting rules and combined results
  double_touch_comparison.csv Counts for both rules and all conditions
  with_double_touches/       Every contact, including repeats; original reports and source tables
  without_double_touches/    One any-hit outcome per target/session
    sweetspot/               Each view contains these same four condition folders
    random_poses/
    horizontal_tests/
    combined/
      figures/               PNG figures for this view
      tables/                Reproducible numerical summaries
archive/detailed_analysis/ Previous detailed notebook and outputs
archive/random_poses_before_exclusions/ Previous results including the four archived sessions
```

## Start here

- [Results index: choose a counting rule](results/README.md)
- [Without double-touch penalties: one result per target/session](results/without_double_touches/README.md)
- [With double touches: every recorded contact](results/with_double_touches/README.md)
- [Side-by-side counts for both rules (CSV)](results/double_touch_comparison.csv)
- [Original contact overview and detailed reports](results/with_double_touches/overview.md)
- [Horizontal Tests: numbered session maps and review table](results/with_double_touches/horizontal_tests/session_review.md)
- [Main notebook](notebooks/sweetspot.ipynb)
- [Main retained JSONL](data/processed/sweetspot_valid.jsonl)
- [Target tendency notebook](notebooks/contact_analysis.ipynb)
- [Archived Random Poses events](data/excluded/random_poses_excluded.jsonl)
- [Comparison with shared target-radius strata](results/with_double_touches/comparison.md)

Choose `with_double_touches/` or `without_double_touches/` before selecting a condition.
Both have the full figure sets. Original detailed reports, source tables and excluded-session maps
live in `with_double_touches/`; the former `results/sweetspot/`, `random_poses/`, `horizontal_tests/`
and `combined/` copies were removed. Regenerating the notebooks uses this same layout.

## Screen region, target size, and overall results

The 13 October **Horizontal Tests** export is now analyzed separately in
`results/with_double_touches/horizontal_tests/`. At the operator's request on 21 October, sessions
**5, 10, 11, 12, 13, 14, 15, 16, 18, 26, 28 and 29** were archived and excluded.
Their 25 original events remain in `data/excluded/horizontal_tests_excluded.jsonl`
and their maps in `results/with_double_touches/horizontal_tests/maps/excluded/`. Original session
numbers are preserved. The retained 18 sessions contain 247 events, 220 contacts,
204 app hits and 27 no-touch records. All configured target IDs have records,
which does not independently confirm robot completion. The 272 original events
remain unchanged under `data/raw/horizontal_tests/`; JSON, JSONL and CSV are copies
of the same events, not three datasets. Exclusion IDs and provenance are recorded
in `data/annotations/horizontal_tests_exclusions.csv`.

These are RGB-circle tests (radii 15–40 dp), not CAPTCHA logs. Horizontal refers
to the operator-described mounting; app coordinates remain portrait at
1080 × 2179 px. The operator confirmed that the phone's top pointed left when
viewing the screen. `region_tendency.png` now displays the horizontal thirds
left-to-right (phone top / middle / bottom), rotating offsets by
`view dx = app dy`, `view dy = -app dx`. Other figures and statistical tables keep
the original app axes; `region_tendency_view.csv` gives the rotated summaries.
These are phone-plane display directions, not calibrated world coordinates.

Each view's `combined/` includes all three retained conditions. The original contact overview is in
`results/with_double_touches/overview.md` and `overview.csv`. The combined region-tendency figure
uses separate condition panels: vertical columns for Sweet Spot/Random Poses
and a horizontal row for Horizontal Tests. Do not interpret differences between
conditions as an isolated orientation effect.

Targets are classified into **upper, middle and lower thirds of the logged screen height**, using their centers, not the eventual touch coordinates. Missing target geometry has region `unknown`; it is not placed into any third. Region/radius tables show contact and session counts, signed mean/median offsets in dp, radial error in dp and target radii, and target-level app outcomes with `no_touch` and unknown/censoring separated.

Figures have plain-English question titles, written-out counts, units, and captions describing which records are included. Blue means Sweet Spot and orange means Random Poses in placement figures; green/red/yellow/gray describe app outcomes, not test conditions. The archived figures remain historical snapshots.

| Figure | What it shows |
|---|---|
| `target_tendency.png` | Where the first recorded in-target touches land. Crosshair = center; circle = target edge. Offsets are percentages of target radius. |
| `region_tendency.png` | First in-target contacts in the displayed phone orientation: vertical thirds for Sweet Spot/Random Poses, left/center/right for Horizontal Tests. Offsets rotate with the horizontal phone. |
| `combined/figures/region_tendency_article.png` | Compact export of the same regional points for the paper; colors, sampling rule, and median marker are explained in the LaTeX caption instead of inside the image. |
| `vertical_bias_by_height.png` | App-y offset versus app-y target position. Negative = toward phone top, positive = toward phone bottom; this is vertical for upright phones and horizontal for the top-left mounting. |
| `region_by_size.png` | Median vertical offset and center distance for each screen-third/target-radius combination. White cells state why no in-target sample is available. |
| `target_outcomes_region_by_size.png` | App-recorded target outcomes in each region/size group, as percentages. Targets are counted once; unknown outcomes stay separate. |
| `phone_orientation_by_session.png` | Random Poses and Horizontal Tests separately: mean phone IMU angles by original session. Components are not verified roll/pitch/yaw. |
| `horizontal_tests/figures/outcomes_by_size.png` | Hits / recorded contacts at each radius, comparing all horizontal sessions with the subset recording every configured target ID. |
| `app_assignment_diagnostics.png` | Supplementary checks using all app-assigned contacts, including misses, repeated contacts and assignment artifacts. The height panel has a nonlinear scale; no outliers removed. |

Placement plots describe first recorded contacts inside uniquely identifiable targets, not all intended robot attempts. Outside/ambiguous contacts and extra contacts are excluded from these plots, but remain in the tables and app-label diagnostics. In-circle placement is conditional and boundary-truncated, which matters when comparing target sizes. dp means phone display units, not millimeters.

The overlapping-arrow `screen_bias` figure was removed, including its pre-exclusion archived copy. Use `region_tendency` to see where contacts land relative to the target center in each screen third, and `vertical_bias_by_height` to see how vertical offset changes with target height. The underlying coordinates and statistical tables are unchanged.

Target-outcome charts retain app-screen thirds. Region-tendency charts arrange panels in the displayed phone orientation; the combined figure keeps the conditions separate. Counts are written out as touches, targets or sessions rather than unexplained `n`/`s` abbreviations.

Individual figures are saved only as PNG. The remaining PDFs combine multiple session maps and have no single equivalent PNG. Duplicate single-figure PDFs were removed from current and archived results.

`results/with_double_touches/combined/` pools **all 457 recorded contacts from 40 retained sessions** (517 events): **416 app hits / 457 contacts = 91.03%**, including repeats. It preserves each contact's dataset, session UUID/number and event ID, keeps archived trials excluded, and includes per-condition counts alongside the overall results. This recorded mix is not a balanced experiment; Random Poses contributes only radius 40 dp. Use per-condition results and the repeat-flag sensitivities alongside pooled fractions. No unlogged physical contact or intended robot action is inferred.

The baseline notebook covers recorded hits/misses, nearby repeated contacts, and session maps. The extended notebook adds target-relative tendency, repeat/censoring sensitivities, Random Poses and exploratory contact-time IMU summaries. Raw measurements are preserved. The archive remains a historical snapshot outside the current workflow.

## Target tendency and logging limitations

The two counting views above both contain **Sweet Spot, Random Poses, Horizontal Tests and Combined**
subfolders, each with the existing target-tendency, region-tendency, region/size, phone-height,
assignment-diagnostic and target-inventory figures, plus size/region hit fractions and session tables/maps.
`with_double_touches/` is also the canonical location for the original contact-level analysis.

**Without double-touch penalties** follows the operator-confirmed rule: group by dataset, session and
app-assigned target ID; any recorded hit makes the outcome a hit, and only recorded misses make it a miss.
This groups later retries too, not only rapid double contacts. It gives **400 hits / 434 touched targets
= 92.17%**, versus **416 / 457 contacts = 91.03%** in the individual-contact view. These are different
units, not an improvement in the robot's measured independent-attempt accuracy.

Maps and assigned-contact diagnostics use an actual representative: the first hit, otherwise the first miss.
First-in-circle placement figures already exclude extra touches and retain their original coordinates and
samples in both views. IMU summaries also retain all sensor samples. No-touch-only and unrecorded targets
stay separate; the target-inventory chart already uses any-hit target outcomes and is unchanged.
Every grouped result links to all unchanged source events in `contact_membership.csv` and `units.csv`.
The stricter rapid-repeat grouping (≤300 ms and ≤8 dp) is supplementary in `rapid_repeat_sensitivity.csv`.

The unit-circle plots center each target at `(0, 0)` and divide x/y offsets by its radius; positive x points right and positive y points down. Tables also report dp, radius/color strata, quadrant fractions, median/p90 radial error and means weighted equally by session. dp is a display unit, not millimeters.

Two spatial views are kept separate: **all contacts relative to the app-assigned target**, including misses, and **first recorded contact per uniquely containing circle**. The latter describes where successful recorded contacts land and prevents multiple contacts in the same circle from dominating the plot. It excludes outside/ambiguous contacts and cannot reconstruct robot intent or independent actions. Raw event IDs and app outcomes remain in `contacts_extended.csv`.

The old app could consume another target after a double contact. `sessions_extended.csv` flags sessions with rapid repeated coordinates, a contact count at the effective target-count ceiling, and unresolved target hit coverage as **ceiling-compatible**, not proven censored. Affected unresolved target rows carry `possible_ceiling_censoring`. No lost contacts are filled in, and `no_touch` is not automatically interpreted as a robot miss. `outcome_sensitivity.csv` shows alternative populations and repeat exclusions without replacing the original observed fractions.

Random Poses has an explicit `target_already_completed` flag. The original export contains 116 events in 11 sessions. The operator requested archiving incomplete sessions **2, 7, 8 and 10**; their 9 original events are preserved in `data/excluded/random_poses_excluded.jsonl`, with reasons and session IDs in `data/annotations/random_poses_exclusions.csv`. The 7 retained sessions keep their original numbers (1, 3, 4, 5, 6, 9, 11): 107 events, 105 contacts and 13 contacts with the repeat flag. Session 6 remains included; the operator confirmed that its 10 targets without records were not executed after a sensor connection error. The original full export and previous result snapshot remain archived. The fraction over configured targets is observed coverage, not a robot failure rate.

The IMU figure and orientation discussion focus on **Random Poses**, where orientation variation is relevant. Sweet Spot sensor summaries remain in the tables for traceability, without a separate IMU figure or section. IMU summaries use circular means of the three logged `orientation_deg` components, concentration and maximum circular deviation, using contact snapshots only. Axis conventions and the phone-to-holder/world transform have not been verified, so labels remain `orientation[0..2]`. Euler singularities and contact-time motion limit interpretation. Random robot pose is a dataset-level operator annotation, not inferred from the app's `random_position` setting (which randomizes targets). No causal comparison between Sweet Spot and random poses is claimed.

The operator subsequently confirmed that Random Poses session 6 stopped after a touch-sensor connection error; its remaining 10 targets were not executed. `data/annotations/operator_session_interruptions.csv` records this explanation separately from the raw events. Session tables retain its recorded contacts and identify the unexecuted targets; they are not classified as touch misses. Contact-based fractions are unchanged, while fractions over all configured targets must not be interpreted as failure rates.

## Data decisions and scientific interpretation

Session numbers follow the first recorded event chronologically and retain their original numbering after exclusions.
The operator retrospectively identified **3, 4, 6, 7, and 9** as interrupted, invalid trials. Their original events are preserved separately.

The operator confirmed **six displayed targets (two trios) and completed execution in sessions 12 and 13**. Their JSON configuration reports nine targets. The analysis uses six as the effective count and preserves the logged count. [Operator annotations](data/annotations/operator_target_counts.csv) document the discrepancy. Logged identifiers, particularly the uneven RGB counts in session 13, do not independently verify two complete RGB trios; they remain unchanged.

The retained population contains **15 sessions, 163 events, and 132 recorded contacts**. An event is a JSONL row; a contact has non-null touch coordinates. A `no_touch` row is not a detected contact. App-reported outcomes refer to the app's assigned target, not necessarily the robot's intended target.

- Recorded-contact hit fraction: **111/132 = 84.09%**, including repeated contacts.
- Observed target hit coverage: **111/135 = 82.22%**, using operator-corrected target counts.
- Raw-count sensitivity: **111/141 = 78.72%**, using the unmodified configuration counts.

Targets with any hit are counted once in target coverage. The original contact-level analysis retains every contact; the separate target-level view groups contacts as described above. No source coordinates or labels are changed and no missing contacts are imputed. These descriptive fractions do not estimate independent robot-action accuracy or contacts never logged.

Nearby pairs use a threshold of **8 dp (20 px here)**. A rapid-repeat candidate also has a timestamp interval ≤ **300 ms**. Four pairs occur in **5, 14, 15, and 19**; they are consistent with repeated contact but do not establish its physical cause. Coordinates use the logged 1080 × 2400 px surface, with origin at the top left and y increasing downward. Display units are not physical millimeters.

For article reporting, distinguish **raw observations**, **operator annotations**, and **derived classifications**. The trial conditions vary over time and contacts are clustered within sessions; no causal or independent-trial inference is made. The source hash, parameters, and environment versions are in [manifest.json](results/with_double_touches/sweetspot/manifest.json).

The Random Poses JSON, JSONL, and CSV exports represent the same 116 original events, not three independent experiments. Only JSONL is analyzed; JSON equality is checked. Export paths were renamed to `data/raw/random_poses/` without changing their contents. The empty export is preserved in its `empty_export/` subfolder. Extended manifests record input/annotation/code hashes and environment versions.

## Run

From the repository root, using the existing environment:

```bash
source .venv/bin/activate
python scripts/run_analysis.py
python scripts/check_analysis.py
python scripts/check_contacts.py
python scripts/check_touch_repeats.py
```

For a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --prefix "$PWD/.venv" --name sweetspot --display-name "Python (Sweet Spot)"
```

Then run the scripts above, or open both notebooks in Jupyter/VS Code and run all cells with the Sweet Spot kernel. The notebooks support execution from the repository root or `notebooks/`. To regenerate only the extensions, run `python scripts/analyze_contacts.py`. Generated results are overwritten; raw files are only read. Manifests record dependency versions; `requirements.txt` is not a fully locked environment.
