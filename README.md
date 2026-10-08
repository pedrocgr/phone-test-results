# Smartphone touch experiments

A simple, reproducible analysis of recorded touchscreen contacts for a scientific article. All documentation and derived artifacts are in English. Raw measurements are preserved.

## Repository layout

```text
data/
  raw/sweetspot/           Original Sweet Spot JSONL (20 sessions)
  raw/random_poses/        Original Random Poses exports (11 sessions)
  annotations/            Operator exclusions and target-count corrections
  processed/              Retained Sweet Spot and Random Poses JSONL
  excluded/               Original events from archived trials
notebooks/
  sweetspot.ipynb          Baseline outcomes, repeated contacts, maps
  contact_analysis.ipynb   Both datasets and pooled results: tendency, region × size, IMU
scripts/
  run_analysis.py         Execute both notebooks
  analyze_contacts.py     Extended analysis; can also run directly
  check_analysis.py       Check data preservation and results
  check_contacts.py       Check geometry, censoring flags, IMU and extended outputs
results/sweetspot/
  summary.md              Short results and limitations
  tables/                 Sessions, outcome fractions, repeated contacts
  figures/                Contact outcome chart (PNG)
  maps/                   Individual maps, overview, and combined PDF
archive/detailed_analysis/ Previous detailed notebook and outputs
results/random_poses/      Extended reports, tables, figures and 7 retained session maps
results/combined/          Overall Sweet Spot + Random Poses contacts and region × size analysis
archive/random_poses_before_exclusions/ Previous results including the four archived sessions
```

## Start here

- [Main notebook](notebooks/sweetspot.ipynb)
- [Main retained JSONL](data/processed/sweetspot_valid.jsonl)
- [Short results](results/sweetspot/summary.md)
- [All retained session maps](results/sweetspot/maps/all_sessions.pdf)
- [Session overview](results/sweetspot/maps/session_overview.png)
- [Target tendency notebook](notebooks/contact_analysis.ipynb)
- [Sweet Spot target tendency](results/sweetspot/figures/target_tendency.png)
- [Random Poses analysis](results/random_poses/contact_analysis.md)
- [Random Poses target tendency](results/random_poses/figures/target_tendency.png)
- [Random Poses session maps](results/random_poses/maps/all_sessions.pdf)
- [Archived Random Poses events](data/excluded/random_poses_excluded.jsonl)
- [Comparison with shared target-radius strata](results/comparison.md)
- [Overall contacts: Sweet Spot + Random Poses](results/combined/summary.md)
- [Sweet Spot region × size](results/sweetspot/region_size_analysis.md)
- [Random Poses region × size](results/random_poses/region_size_analysis.md)
- [Pooled region × size figure](results/combined/figures/region_by_size.png)

## Screen region, target size, and overall results

Targets are classified into **upper, middle and lower thirds of the logged screen height**, using their centers, not the eventual touch coordinates. Missing target geometry has region `unknown`; it is not placed into any third. Region/radius tables show contact and session counts, signed mean/median offsets in dp, radial error in dp and target radii, and target-level app outcomes with `no_touch` and unknown/censoring separated.

Each condition has `region_tendency`, `vertical_bias_by_height`, `region_by_size` and `target_outcomes_region_by_size` PNG figures. The heatmaps show first recorded in-circle contacts, with `n` contacts and `s` sessions in each cell; blank means no in-circle contacts, even if outside contacts were recorded. The outcome chart includes zero-hit combinations and separates app hits, assigned misses, no-touch and unknown/censoring. The height plot additionally shows all app-assigned contacts, including outside contacts and assignment artifacts, with a symlog scale so no outliers are removed. In-circle placement is conditional on recorded success; its boundary truncation matters when comparing sizes.

Individual figures are saved only as PNG. The remaining PDFs combine multiple session maps and have no single equivalent PNG. Duplicate single-figure PDFs were removed from current and archived results.

`results/combined/` pools **all 237 recorded contacts from 22 retained sessions** (270 events). It preserves each contact's dataset, session UUID/number and event ID, keeps archived trials excluded, and includes per-condition counts alongside the overall results. This recorded mix is not a balanced experiment; Random Poses contributes only radius 40 dp. Use per-condition results and the repeat-flag sensitivities alongside pooled fractions. No unlogged physical contact or intended robot action is inferred.

The baseline notebook covers recorded hits/misses, nearby repeated contacts, and session maps. The extended notebook adds target-relative tendency, repeat/censoring sensitivities, Random Poses and exploratory contact-time IMU summaries. Raw measurements are preserved. The archive remains a historical snapshot outside the current workflow.

## Target tendency and logging limitations

The unit-circle plots center each target at `(0, 0)` and divide x/y offsets by its radius; positive x points right and positive y points down. Tables also report dp, radius/color strata, quadrant fractions, median/p90 radial error and means weighted equally by session. dp is a display unit, not millimeters.

Two spatial views are kept separate: **all contacts relative to the app-assigned target**, including misses, and **first recorded contact per uniquely containing circle**. The latter describes where successful recorded contacts land and prevents multiple contacts in the same circle from dominating the plot. It excludes outside/ambiguous contacts and cannot reconstruct robot intent or independent actions. Raw event IDs and app outcomes remain in `contacts_extended.csv`.

The old app could consume another target after a double contact. `sessions_extended.csv` flags sessions with rapid repeated coordinates, a contact count at the effective target-count ceiling, and unresolved target hit coverage as **ceiling-compatible**, not proven censored. Affected unresolved target rows carry `possible_ceiling_censoring`. No lost contacts are filled in, and `no_touch` is not automatically interpreted as a robot miss. `outcome_sensitivity.csv` shows alternative populations and repeat exclusions without replacing the original observed fractions.

Random Poses has an explicit `target_already_completed` flag. The original export contains 116 events in 11 sessions. The operator requested archiving incomplete sessions **2, 7, 8 and 10**; their 9 original events are preserved in `data/excluded/random_poses_excluded.jsonl`, with reasons and session IDs in `data/annotations/random_poses_exclusions.csv`. The 7 retained sessions keep their original numbers (1, 3, 4, 5, 6, 9, 11): 107 events, 105 contacts and 13 contacts with the repeat flag. Session 6 remains included because it was not requested for exclusion; its 10 targets without records are unknown outcomes. The original full export and previous result snapshot remain archived. The fraction over configured targets is observed coverage, not a robot failure rate.

IMU summaries use circular means of the three logged `orientation_deg` components, concentration and maximum circular deviation, using contact snapshots only. Axis conventions and the phone-to-holder/world transform have not been verified, so labels remain `orientation[0..2]`. Euler singularities and contact-time motion limit interpretation. Random robot pose is a dataset-level operator annotation, not inferred from the app's `random_position` setting (which randomizes targets). No causal comparison between Sweet Spot and random poses is claimed.

## Data decisions and scientific interpretation

Session numbers follow the first recorded event chronologically and retain their original numbering after exclusions.
The operator retrospectively identified **3, 4, 6, 7, and 9** as interrupted, invalid trials. Their original events are preserved separately.

The operator confirmed **six displayed targets (two trios) and completed execution in sessions 12 and 13**. Their JSON configuration reports nine targets. The analysis uses six as the effective count and preserves the logged count. [Operator annotations](data/annotations/operator_target_counts.csv) document the discrepancy. Logged identifiers, particularly the uneven RGB counts in session 13, do not independently verify two complete RGB trios; they remain unchanged.

The retained population contains **15 sessions, 163 events, and 132 recorded contacts**. An event is a JSONL row; a contact has non-null touch coordinates. A `no_touch` row is not a detected contact. App-reported outcomes refer to the app's assigned target, not necessarily the robot's intended target.

- Recorded-contact hit fraction: **111/132 = 84.09%**, including repeated contacts.
- Observed target hit coverage: **111/135 = 82.22%**, using operator-corrected target counts.
- Raw-count sensitivity: **111/141 = 78.72%**, using the unmodified configuration counts.

Targets with any hit are counted once in target coverage. No contacts are deduplicated, trimmed, or imputed. These descriptive fractions do not estimate independent robot-action accuracy or contacts never logged.

Nearby pairs use a threshold of **8 dp (20 px here)**. A rapid-repeat candidate also has a timestamp interval ≤ **300 ms**. Four pairs occur in **5, 14, 15, and 19**; they are consistent with repeated contact but do not establish its physical cause. Coordinates use the logged 1080 × 2400 px surface, with origin at the top left and y increasing downward. Display units are not physical millimeters.

For article reporting, distinguish **raw observations**, **operator annotations**, and **derived classifications**. The trial conditions vary over time and contacts are clustered within sessions; no causal or independent-trial inference is made. The source hash, parameters, and environment versions are in [manifest.json](results/sweetspot/manifest.json).

The Random Poses JSON, JSONL, and CSV exports represent the same 116 original events, not three independent experiments. Only JSONL is analyzed; JSON equality is checked. Export paths were renamed to `data/raw/random_poses/` without changing their contents. The empty export is preserved in its `empty_export/` subfolder. Extended manifests record input/annotation/code hashes and environment versions.

## Run

From the repository root, using the existing environment:

```bash
source .venv/bin/activate
python scripts/run_analysis.py
python scripts/check_analysis.py
python scripts/check_contacts.py
```

For a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --prefix "$PWD/.venv" --name sweetspot --display-name "Python (Sweet Spot)"
```

Then run the scripts above, or open both notebooks in Jupyter/VS Code and run all cells with the Sweet Spot kernel. The notebooks support execution from the repository root or `notebooks/`. To regenerate only the extensions, run `python scripts/analyze_contacts.py`. Generated results are overwritten; raw files are only read. Manifests record dependency versions; `requirements.txt` is not a fully locked environment.
