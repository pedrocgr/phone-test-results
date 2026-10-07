# Smartphone touch experiments: Sweet Spot

This repository contains raw smartphone touch logs and an executable, descriptive analysis intended to support a scientific article. Repository documentation, code, tables, figure labels, and derived filenames are in English. Raw measurement values and identifiers are preserved.

## Main files

| File | Role |
|---|---|
| [sweetspot_analysis.ipynb](sweetspot_analysis.ipynb) | Executed analysis, methods, audit tables, and coordinate maps. |
| [sweetspot_analysis/summary.md](sweetspot_analysis/summary.md) | Results, denominators, provenance, and limitations. |
| [sweetspot_analysis/touch_results_sweetspot_valid.jsonl](sweetspot_analysis/touch_results_sweetspot_valid.jsonl) | Main retained log: 15 operator-selected sessions, 163 events, 132 contacts. A verbatim subset of the raw source. |
| [touch_results_2026-10-06-sweetspot.jsonl](touch_results_2026-10-06-sweetspot.jsonl) | Unmodified raw Sweet Spot input: 20 sessions and 177 events. |
| [sweetspot_analysis/excluded_sessions/original_events.jsonl](sweetspot_analysis/excluded_sessions/original_events.jsonl) | Five excluded sessions, preserving all 14 original event rows. |
| [sweetspot_analysis/operator_annotations.csv](sweetspot_analysis/operator_annotations.csv) | Explicit operator corrections and metadata discrepancies. |
| [sweetspot_analysis/analysis_manifest.json](sweetspot_analysis/analysis_manifest.json) | Source/subset hashes, parameters, population, and execution environment. |
| [sweetspot_analysis/all_session_maps.pdf](sweetspot_analysis/all_session_maps.pdf) | Coordinate maps for the 15 retained sessions. |
| [sweetspot_analysis/05_session_overview.png](sweetspot_analysis/05_session_overview.png) | Overview of retained sessions. |

Summary figures are also exported as vector PDFs. English PNG maps for individual retained sessions are in `sweetspot_analysis/session_maps/`. Maps for excluded trials are in `sweetspot_analysis/excluded_sessions/maps/` and are labeled as excluded.

The root `touch_results_after_app_update_2026-10-06.jsonl` is empty. Additional populated after-update exports are present under `fixed-touch-results-after-app-update/fixed-touch-results-after-app-update/` in JSONL, JSON, and CSV formats. The JSON and JSONL each contain 116 events; these are export representations, not three independent experiments. They are preserved and inventoried but **not analyzed by the Sweet Spot notebook**.

## Population and operator annotations

Session numbers are assigned by the first recorded event in chronological order. They remain stable after exclusions; they are not renumbered from 1 to 15.

The operator retrospectively identified **sessions 3, 4, 6, 7, and 9** as interrupted, invalid trials. These are excluded from primary summaries and retained in the archive. No automated contact-count threshold determines exclusion.

The operator confirmed that **sessions 12 and 13 were completed trials with six displayed targets (two trios)**. Their JSON configuration reports nine targets and three trios. The effective target count is six in the primary analysis, while the logged count remains unchanged in the source and retained JSONL.

The count correction is external information, not a fact independently reconstructed from the logs. The six recorded identifiers are retained: session 12 uses trios 1 and 3, and session 13 has three green, two red, and one blue identifiers. The identifiers do not independently confirm two complete RGB trios. The cause of this metadata discrepancy is unresolved. Do not silently replace or renumber these identifiers.

For the retained population, the effective target denominator is **135**; the raw configuration denominator is **141**. Both are reported in `target_count_sensitivity.csv`. No target-count correction is inferred for any other session.

## Measurement units and definitions

An **event** is one JSONL row. A **recorded contact** is an event with non-null `actual_touch_x` and `actual_touch_y`. A `no_touch` event contains no contact coordinates and is not a detected touch.

Screen coordinates are pixels, relative to the application test surface, with origin at the top left and y increasing downward. The logged surface is 1080 × 2400 px. Logged density is 2.5 px/dp. Display units must not be interpreted as millimeters without independent calibration.

Raw `date_time` values are UTC. Derived tables also provide America/Recife local time (UTC−03:00). Session event span is first-to-last recorded event, not full trial duration. `response_time_ms` is an app timer and may include setup, waiting, and operator intervention.

App-reported `hit` and `miss` outcomes refer to the **assigned target**, which need not be the target intended by the robot. App outcomes are preserved, even when geometric inspection indicates a contact lies inside a different target.

## Metrics and exploratory flags

| Quantity | Numerator / definition | Denominator / limitation |
|---|---|---|
| Recorded-contact hit rate | Hit events: 111 | Coordinate-bearing events: 132; **84.09%**. Includes repeats and is not independent robot-action accuracy. |
| Observed target hit coverage | Distinct targets with at least one hit: 111 | Effective targets: 135; **82.22%**. Uses the operator annotations. |
| Raw-count sensitivity | Same target-hit numerator: 111 | Logged configuration count: 141; **78.72%**. |
| Nearby contact pair | Euclidean separation ≤ 8 dp (20 px here) | All within-session pairs of recorded contacts; exploratory threshold. |
| Rapid repeated-contact candidate | Nearby pair with event timestamp interval ≤ 300 ms | Consistent with repeated contact/double click; physical cause is not verified. |
| Same target region | Same nearest logged target, both within radius + 20 dp | Geometric grouping, independent of assigned target IDs. |
| Count-ceiling flag | Contacts equal effective target count, at least one miss, and fewer targets with hits than the target count | A descriptive pattern compatible with the reported ceiling, not evidence of proven censoring. |

All four rapid-repeat pairs occur in sessions **5, 14, 15, and 19**. They persist at spatial thresholds of 5, 20, 50, and 100 px. In three pairs, the app assigns different target IDs to almost coincident contacts.

Primary metrics retain all contacts, including these pairs and extreme spatial errors. No events are deduplicated, trimmed, or imputed. Target states are mutually exclusive (`hit`, `miss_without_hit`, `no_touch_only`, `unrecorded`), with separate history flags such as `hit_and_no_touch`. Such a flag is not an additional failed target.

## Table guide

- `sessions.csv`: original session number and UUID; effective/logged target counts; count source; completion basis; contact/event totals; target states; descriptive flags.
- `targets.csv`: one row per expected target under the documented count assumptions, including its result history.
- `events.csv`: source line number, event/session UUIDs, UTC/local timestamps, original outcome and target assignment, coordinates, displacement, and normalized error.
- `touch_pairs.csv`: every within-session contact pair, including event UUIDs, source lines, timestamps, distance, interval, both assignments, and proximity flags.
- `nearby_touch_pairs.csv`: pairs meeting the nearby-contact or same-region criterion.
- `sample_metrics.csv` and `radius_metrics.csv`: descriptive fractions and integer counts. Fractions are stored numerically, without percent rounding.
- `target_count_sensitivity.csv`: both target denominators.
- `count_ceiling_flags.csv`, `missing_target_flags.csv`, and `targets_with_hit_and_no_touch.csv`: audit subsets. A zero-row table still has its header.
- `operator_annotations.csv` and `excluded_sessions/sessions.csv`: operator decisions and their stated basis.

## Scientific scope and limitations

The Sweet Spot label and operator decisions describe experimental context; raw logs do not contain robot poses or joint angles. Current neighboring app/robot source is optional context and is not proof of the installed APK's behavior.

Target size, session time, and target count vary together. Trials are not randomized or balanced, and repeated contacts are clustered within sessions. No causal size/software comparison or significance test based on independent contacts is reported. Timing and event-sampled IMU data do not establish robot latency, trajectories, impacts, or the cause of a repeated contact.

No session records more coordinate-bearing contacts than its effective target count. The logs cannot identify when a capture ceiling was removed or how many contacts were never logged. The number of genuinely censored contacts is unknown. Operator-confirmed completion must not be mistaken for independently verified logging completeness.

Claims in the article should distinguish **measured events**, **operator annotations**, **derived classifications**, and **hypotheses**. For stronger claims, collect APK/build identity, explicit start/end and termination reason, independent touchscreen contacts, and synchronized ROS/contact-sensor data.

## Reproduction

Use Python 3.12 from the repository root. The actual versions used for the stored notebook execution are recorded in `sweetspot_analysis/analysis_manifest.json`; `requirements.txt` lists the direct dependencies rather than a fully locked environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --prefix "$PWD/.venv" --name sweetspot --display-name "Python (Sweet Spot)"
python run_analysis.py
python check_analysis.py
```

Alternatively, open the notebook in Jupyter or VS Code, select the Sweet Spot kernel, and run all cells in order. Existing `.venv` users can run the final two commands directly. Generated artifacts are overwritten; raw inputs are only read. Optional neighboring repositories are not needed for the numeric analysis.
