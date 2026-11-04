Counting rule: one outcome per session/target; first hit, otherwise first miss, supplies the representative coordinate. First-in-circle placement retains its original, already unique samples.

# random_poses: screen region and target size

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
| lower | 22 | 6 | +9.39 | +2.68 | +3.81 | 12.45 | 0.311 | 40.9% |
| middle | 35 | 7 | -0.65 | -9.86 | -11.32 | 15.54 | 0.389 | 77.1% |
| upper | 31 | 7 | -9.58 | -21.77 | -24.82 | 29.17 | 0.729 | 96.8% |

## Representative app-assigned contacts (one per session/target)

| Region | Contacts | Sessions | Mean y (dp) | Median y (dp) | Median distance / radius |
|---|---:|---:|---:|---:|---:|
| lower | 22 | 6 | +2.68 | +3.81 | 0.311 |
| middle | 37 | 7 | -16.74 | -13.83 | 0.414 |
| upper | 32 | 7 | -22.38 | -25.02 | 0.738 |

App assignments can differ from the physically containing circle after repeated touches.
`region_size_contacts.csv` includes sensitivities removing rapid-repeat second events,
explicit completed-target repeats, or either repeat flag. All original contacts remain available.

## Target outcomes by region

Each target is counted once within its original dataset/session. Unknown/censoring outcomes are kept separate.
`no_touch` is an app observation, not proof of a physical failure. Missing geometry receives region `unknown`.

| Region | Targets | App-assigned hit | Assigned miss without hit | no_touch only | Unknown/censoring |
|---|---:|---:|---:|---:|---:|
| upper | 32 | 31 | 1 | 0 | 0 |
| middle | 38 | 35 | 2 | 1 | 0 |
| lower | 22 | 22 | 0 | 0 | 0 |
| unknown | 10 | 0 | 0 | 0 | 10 |

## Region × size

`region_by_size.png` shows median vertical offset in dp and median radial distance divided by radius,
with contact/session counts for each combination. `region_size_outcomes.csv` provides the corresponding
target inventory. `target_outcomes_region_by_size.png` also includes combinations with zero recorded hits,
showing target-level app outcomes, no-touch observations and unknown/censoring separately.
White placement cells are explicitly labeled with available target outcomes; they are not zero error.
The main placement plots show only first in-circle contacts. `app_assignment_diagnostics.png`
shows one representative per session/target: first hit, otherwise first miss. No coordinates are corrected.
A smaller target tolerates less of the same absolute error. Compare dp offsets and normalized distances
together before interpreting any size association. In-circle distributions are boundary-truncated.
Region/size cells with few sessions are descriptive; contacts within sessions are not independent trials.
Random Poses contributes only radius 40 dp. Pooled counts reflect the observed mix of conditions,
not a balanced experiment or causal size/pose effect. The per-condition reports must accompany pooled results.
