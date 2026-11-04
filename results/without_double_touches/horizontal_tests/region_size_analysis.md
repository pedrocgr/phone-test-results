Counting rule: one outcome per session/target; first hit, otherwise first miss, supplies the representative coordinate. First-in-circle placement retains its original, already unique samples.

# horizontal_tests: screen region and target size

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
| lower | 48 | 18 | -6.49 | +14.95 | +15.48 | 18.23 | 0.634 | 0.0% |
| middle | 109 | 18 | +3.17 | +2.91 | +3.62 | 9.40 | 0.324 | 33.0% |
| upper | 44 | 17 | +10.78 | -10.27 | -10.69 | 15.98 | 0.527 | 97.7% |

## Representative app-assigned contacts (one per session/target)

| Region | Contacts | Sessions | Mean y (dp) | Median y (dp) | Median distance / radius |
|---|---:|---:|---:|---:|---:|
| lower | 51 | 18 | +15.04 | +15.55 | 0.661 |
| middle | 112 | 18 | +3.31 | +3.76 | 0.327 |
| upper | 53 | 18 | -10.07 | -10.35 | 0.566 |

App assignments can differ from the physically containing circle after repeated touches.
`region_size_contacts.csv` includes sensitivities removing rapid-repeat second events,
explicit completed-target repeats, or either repeat flag. All original contacts remain available.

## Target outcomes by region

Each target is counted once within its original dataset/session. Unknown/censoring outcomes are kept separate.
`no_touch` is an app observation, not proof of a physical failure. Missing geometry receives region `unknown`.

| Region | Targets | App-assigned hit | Assigned miss without hit | no_touch only | Unknown/censoring |
|---|---:|---:|---:|---:|---:|
| upper | 58 | 44 | 9 | 5 | 0 |
| middle | 117 | 109 | 3 | 5 | 0 |
| lower | 53 | 48 | 3 | 2 | 0 |

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
