# Sweet Spot: descriptive analysis for a scientific article

## Data provenance and analysis population

Raw input: `touch_results_2026-10-06-sweetspot.jsonl`. SHA-256: `290accd48b1739358913f6846d241b868f7a73a8317a14dd1b178490747f67f5`.
The source has 177 events in 20 sessions.
Sessions 3, 4, 6, 7, 9 were excluded retrospectively because the operator identified interrupted trials.
The retained dataset contains **15 sessions, 163 events, and 132 coordinate-bearing contact events**.
Session numbers and all raw measurements remain unchanged. Events are not synonymous with contacts.
The retained JSONL is a verbatim subset of the original source; target-count corrections are annotations, not edits to the measurements.

## Operator annotations and metadata discrepancies

Sessions 12 and 13 are completed six-target trials according to the operator, who reported two displayed trios.
Their JSON configuration states nine targets and three trios. The primary effective count is six for each; the unmodified JSON count is retained separately.
Session 12 logs identifiers from trios 1 and 3. Session 13 logs three green, two red, and one blue identifiers.
These identifiers do not independently verify two complete RGB trios. The reported six-target count is an external annotation, and the cause of the metadata discrepancy remains unresolved.
See `operator_annotations.csv` for identifiers and annotation source.

## Observed outcomes and denominators

- Recorded hits: **111**; recorded misses: **21**; manual no_touch events: **31**.
- Recorded-contact hit rate: **111/132 = 84.09%**.
- Distinct targets with a hit: **111**.
- Observed target hit coverage using effective target counts: **111/135 = 82.22%**.
- Sensitivity using unmodified JSON configuration counts: **111/141 = 78.72%**.
- Median assigned-target distance: **44.04 px**; mean: **81.87 px**.
- Median displacement: **dx = -19.84 px**, **dy = -24.08 px**.

All contacts are retained in these metrics, including rapid repeat candidates and extreme distances.
The target-level numerator counts a target once if any hit was recorded. The contact-level numerator counts hit events.
The metrics describe recorded app outcomes; they are not independent robot-action success rates or estimates of unlogged outcomes.

## Spatial repetition

4 nearby pairs occur in sessions 5, 14, 15, 19.
Their distances range from 2.35 to 3.83 px,
and their timestamp intervals range from 60.5 to 73.3 ms.
All meet the exploratory rapid-repeat threshold of 8 dp and 300 ms.
In three pairs the app assigns the second contact to a different target. Physical double-click causation is unverified.
The same four pairs are found at distance thresholds of 5, 20, 50, and 100 px.

## Capture limitation

No retained session records more coordinate-bearing contacts than its effective target count.
The session where a logging ceiling was removed cannot be identified, and the number of truly censored contacts is unknown.
The count-ceiling flag applies to sessions 1, 5, 11, 12, 14, 15, 18, 20; it is a descriptive pattern, not proof of loss.
8 targets have both hit and no_touch events; those histories are preserved rather than counted as separate failed targets.

## Limitations and scope of claims

Exclusions and count corrections are retrospective operator annotations.
Raw target-count discrepancies and logged identifiers require clarification before making stronger claims about target layout.
App assignments may differ from intended robot targets. Repeated contacts are not independent trials.
Target size, time, and target count vary together; no causal size comparison or software improvement claim is supported.
Application timers include waiting and intervention; sparse IMU samples do not reconstruct motion or impact.
There are no robot poses, synchronized contact-sensor logs, or installed APK/build identifiers in the dataset.
The after-update input contains 0 bytes. Populated after-update exports are also available in fixed-touch-results-after-app-update/; they are outside the current analysis, and no before/after comparison is made.

## Reproduction and artifacts

Run `sweetspot_analysis.ipynb` from the repository root. The execution environment, input hash, and analysis parameters are recorded in `analysis_manifest.json`.
English per-session PNG maps and the 15-page primary PDF are exported; excluded trials have separate maps.
CSV tables retain event identifiers, source line numbers, original assignments, and UTC timestamps for repeated-contact pairs.

# Repeated contacts: Sweet Spot

4 nearby pairs in 4 retained sessions; 4 rapid-repeat candidates.

| Session | Contacts | Distance (px) | Interval (ms) | Nearest target | App outcomes |
|---|---|---:|---:|---|---|
| 5 | 5 and 6 | 2.35 | 73.3 | trio-001-green | hit → miss |
| 14 | 3 and 4 | 2.74 | 60.5 | trio-001-red | hit → miss |
| 15 | 2 and 3 | 3.83 | 72.1 | trio-003-green | hit → miss |
| 19 | 1 and 2 | 3.02 | 67.7 | trio-003-red | miss → miss |

In sessions 5, 14, and 15, the second contact was attributed to a different target although the positions nearly coincide. In session 19, both contacts lie just outside the same circle.

These are recorded-contact observations, consistent with repeated contact; physical cause is unverified. App outcomes remain unmodified.
