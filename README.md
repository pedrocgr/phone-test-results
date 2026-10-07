# Smartphone touch experiments

A simple, reproducible analysis of recorded touchscreen contacts for a scientific article. All documentation and derived artifacts are in English. Raw measurements are preserved.

## Repository layout

```text
data/
  raw/sweetspot/           Original Sweet Spot JSONL (20 sessions)
  raw/after_app_update/    Later exports; not analyzed yet
  annotations/            Operator exclusions and target-count corrections
  processed/              Main retained log (15 sessions)
  excluded/               Original events from excluded trials
notebooks/
  sweetspot.ipynb          Main analysis: outcomes, repeated contacts, maps
scripts/
  run_analysis.py         Execute the notebook
  check_analysis.py       Check data preservation and results
results/sweetspot/
  summary.md              Short results and limitations
  tables/                 Sessions, outcome fractions, repeated contacts
  figures/                Contact outcome chart (PNG and vector PDF)
  maps/                   Individual maps, overview, and combined PDF
archive/detailed_analysis/ Previous detailed notebook and outputs
```

## Start here

- [Main notebook](notebooks/sweetspot.ipynb)
- [Main retained JSONL](data/processed/sweetspot_valid.jsonl)
- [Short results](results/sweetspot/summary.md)
- [All retained session maps](results/sweetspot/maps/all_sessions.pdf)
- [Session overview](results/sweetspot/maps/session_overview.png)

The current analysis covers **recorded hits/misses, nearby repeated contacts, and session maps**. IMU, application timing, calibration, and software-history analyses are not performed. Raw IMU fields are retained. The archive is a historical snapshot of the previous analysis and is outside the current workflow.

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

The later JSON, JSONL, and CSV exports represent the same 116 events, not three independent experiments. They are preserved under `data/raw/after_app_update/` for a future analysis. The empty earlier export is preserved in its `empty_export/` subfolder.

## Run

From the repository root, using the existing environment:

```bash
source .venv/bin/activate
python scripts/run_analysis.py
python scripts/check_analysis.py
```

For a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --prefix "$PWD/.venv" --name sweetspot --display-name "Python (Sweet Spot)"
```

Then run the two scripts above, or open the notebook in Jupyter/VS Code and run all cells with the Sweet Spot kernel. The notebook supports execution from the repository root or `notebooks/`. Generated results are overwritten; raw files are only read. The manifest records the actual dependency versions used; `requirements.txt` is not a fully locked environment.
