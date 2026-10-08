# sweetspot: screen region and target size

Regions are fixed thirds of **logged screen height**, assigned using the **target center**:
upper [0, 1/3), middle [1/3, 2/3), lower [2/3, 1]. They are not thirds of the app's target-placement area.
Contacts never change region merely because their touch coordinate crosses a boundary.
Offsets are in dp (not mm) and target radii; negative vertical offset means above the center.

## First contact per uniquely containing circle

This population describes recorded in-circle placement, not all intended robot attempts.
Outside contacts are kept separately in the app-assigned populations below.

| Region | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Median y (dp) | Median distance (dp) | Median distance / radius | Above center |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lower | 32 | 13 | +1.84 | +8.21 | +8.73 | 13.08 | 0.321 | 9.4% |
| middle | 51 | 15 | -6.26 | -7.78 | -8.24 | 14.74 | 0.390 | 92.2% |
| upper | 28 | 13 | -15.47 | -22.74 | -23.84 | 28.73 | 0.755 | 100.0% |

## All app-assigned contacts (hits and misses)

| Region | Contacts | Sessions | Mean y (dp) | Median y (dp) | Median distance / radius |
|---|---:|---:|---:|---:|---:|
| lower | 34 | 13 | +14.46 | +9.05 | 0.333 |
| middle | 54 | 15 | -17.42 | -8.39 | 0.394 |
| upper | 44 | 15 | -7.34 | -23.11 | 0.878 |

App assignments can differ from the physically containing circle after repeated touches.
`region_size_contacts.csv` includes sensitivities removing rapid-repeat second events,
explicit completed-target repeats, or either repeat flag. All original contacts remain available.

## Target outcomes by region

Each target is counted once within its original dataset/session. Unknown/censoring outcomes are kept separate.
`no_touch` is an app observation, not proof of a physical failure. Missing geometry receives region `unknown`.

| Region | Targets | App-assigned hit | Assigned miss without hit | no_touch only | Unknown/censoring |
|---|---:|---:|---:|---:|---:|
| upper | 42 | 28 | 13 | 0 | 1 |
| middle | 55 | 51 | 1 | 3 | 0 |
| lower | 38 | 32 | 1 | 1 | 4 |

## Region × size

`region_by_size.png` shows median vertical offset in dp and median radial distance divided by radius,
with contact/session counts for each combination. `region_size_outcomes.csv` provides the corresponding
target inventory. `target_outcomes_region_by_size.png` also includes combinations with zero recorded hits,
showing target-level app outcomes, no-touch observations and unknown/censoring separately.
Blank placement cells mean no in-circle observations, not zero error or zero success.
A smaller target tolerates less of the same absolute error. Compare dp offsets and normalized distances
together before interpreting any size association. In-circle distributions are boundary-truncated.
Region/size cells with few sessions are descriptive; contacts within sessions are not independent trials.
Random Poses contributes only radius 40 dp. Pooled counts reflect the observed mix of conditions,
not a balanced experiment or causal size/pose effect. The per-condition reports must accompany pooled results.
