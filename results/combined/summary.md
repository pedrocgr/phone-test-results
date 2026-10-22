# Overall recorded contacts: Sweet Spot + Random Poses + Horizontal Tests

This section pools **all recorded contacts from retained sessions** in all three conditions.
Archived sessions remain excluded. Source dataset, session number, UUID and event ID are kept in every row.
The pooled population reflects the recorded mix of sizes/poses; it is not a balanced experiment.

| Condition | Sessions | Events | Contacts | App hits | App misses | no_touch events | Expected targets | Targets with records |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sweetspot | 15 | 163 | 132 | 111 | 21 | 31 | 135 | 135 |
| random_poses | 7 | 107 | 105 | 101 | 4 | 2 | 102 | 92 |
| horizontal_tests | 18 | 247 | 220 | 204 | 16 | 27 | 228 | 228 |
| combined | 40 | 517 | 457 | 416 | 41 | 60 | 465 | 455 |

Pooled app-recorded contact hit fraction: **416/457 = 91.03%**, including repeats.
This is not independent robot-action accuracy. The target inventory and unknown/censoring categories remain separate.
`outcome_sensitivity.csv` and `target_tendency.csv` contain repeat-flag sensitivities and first-per-circle placement.
The latter is conditional on in-circle recording, while all assigned contacts retain outside contacts and assignment artifacts.
Contacts and sessions are not deduplicated across conditions; dataset/session identity prevents target-ID collisions.
All results remain descriptive. Per-condition analyses should accompany any pooled percentage.
The signed offsets in pooled tables use the original phone/app axes. The region-tendency figure
separates conditions and rotates the horizontal view to match its mounting; see the section below.

# combined: screen region and target size

Regions are fixed thirds of **logged screen height**, assigned using the **target center**:
upper [0, 1/3), middle [1/3, 2/3), lower [2/3, 1]. They are not thirds of the app's target-placement area.
Contacts never change region merely because their touch coordinate crosses a boundary.
The tables below retain phone/app axes: offsets are in dp (not mm) and target radii;
negative app-y offset means toward the phone's original top edge.

## Region tendency in the displayed phone orientation

`region_tendency.png` shows each condition separately in the phone-plane view.
Sweet Spot and Random Poses thirds run top to bottom. Horizontal Tests has the phone's top
pointing left, as confirmed by the operator: its app upper/middle/lower thirds are displayed
left/center/right. Both the panel placement and touch offsets are rotated: view dx = app dy,
view dy = -app dx. Positive view x points right; positive view y points down.
These are display directions, not calibrated robot/world axes.
`region_tendency_view.csv` records the transformed regional summaries in dp and target radii.
All other tables and figures retain the original app axes, making their coordinate basis explicit.

## First contact per uniquely containing circle

This population describes recorded in-circle placement, not all intended robot attempts.
Outside contacts are kept separately in the app-assigned populations below.

| Region | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Median y (dp) | Median distance (dp) | Median distance / radius | Above center |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lower | 102 | 37 | -0.45 | +10.19 | +12.12 | 15.95 | 0.433 | 11.8% |
| middle | 195 | 40 | +0.02 | -2.18 | -1.35 | 11.47 | 0.360 | 56.4% |
| upper | 103 | 37 | -2.48 | -17.12 | -15.93 | 23.35 | 0.653 | 98.1% |

## All app-assigned contacts (hits and misses)

| Region | Contacts | Sessions | Mean y (dp) | Median y (dp) | Median distance / radius |
|---|---:|---:|---:|---:|---:|
| lower | 109 | 37 | +12.59 | +12.38 | 0.447 |
| middle | 206 | 40 | -7.16 | -1.66 | 0.369 |
| upper | 142 | 40 | -13.37 | -17.32 | 0.743 |

App assignments can differ from the physically containing circle after repeated touches.
`region_size_contacts.csv` includes sensitivities removing rapid-repeat second events,
explicit completed-target repeats, or either repeat flag. All original contacts remain available.

## Target outcomes by region

Each target is counted once within its original dataset/session. Unknown/censoring outcomes are kept separate.
`no_touch` is an app observation, not proof of a physical failure. Missing geometry receives region `unknown`.

| Region | Targets | App-assigned hit | Assigned miss without hit | no_touch only | Unknown/censoring |
|---|---:|---:|---:|---:|---:|
| upper | 132 | 103 | 23 | 5 | 1 |
| middle | 210 | 195 | 6 | 9 | 0 |
| lower | 113 | 102 | 4 | 3 | 4 |
| unknown | 10 | 0 | 0 | 0 | 10 |

## Region × size

`region_by_size.png` shows median vertical offset in dp and median radial distance divided by radius,
with contact/session counts for each combination. `region_size_outcomes.csv` provides the corresponding
target inventory. `target_outcomes_region_by_size.png` also includes combinations with zero recorded hits,
showing target-level app outcomes, no-touch observations and unknown/censoring separately.
White placement cells are explicitly labeled with available target outcomes; they are not zero error.
The main placement plots show only first in-circle contacts. `app_assignment_diagnostics.png`
keeps all app-assigned contacts, including misses and repeats, with no outliers removed.
A smaller target tolerates less of the same absolute error. Compare dp offsets and normalized distances
together before interpreting any size association. In-circle distributions are boundary-truncated.
Region/size cells with few sessions are descriptive; contacts within sessions are not independent trials.
Random Poses contributes only radius 40 dp. Pooled counts reflect the observed mix of conditions,
not a balanced experiment or causal size/pose effect. The per-condition reports must accompany pooled results.
