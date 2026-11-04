# Horizontal Tests — results from 13 October 2026

The source contains RGB circles only, not CAPTCHA. There are 18 retained sessions; 12 sessions were archived at the operator's request. Original numbering and raw events are preserved. Horizontal mounting is an operator annotation, not inferred from the app's random-target setting or screen dimensions.

[Review each session and its map](session_review.md) · [Map overview](maps/session_overview.png) · [All session maps, one PDF](maps/all_sessions.pdf)

The 18 full-ID sessions contain 204/220 app-hit contacts (92.73%, including repeats) and hits on 201/228 distinct configured targets (88.16%). These use different denominators.

## Target size and contact outcomes

Full-ID sessions have records for every configured target; this is a sensitivity subset, not a validated completion label. Each cell shows hits / recorded contacts, including repeat touches.

| Radius (dp) | Sessions (all / full-ID) | All sessions | Full-ID sessions | Unrecorded targets (all sessions) |
|---|---:|---:|---:|---:|
| 15 | 1 / 1 | 10/20 (50.0%) | 10/20 (50.0%) | 0 |
| 20 | 2 / 2 | 24/28 (85.7%) | 24/28 (85.7%) | 0 |
| 25 | 4 / 4 | 46/46 (100.0%) | 46/46 (100.0%) | 0 |
| 30 | 4 / 4 | 40/41 (97.6%) | 40/41 (97.6%) | 0 |
| 35 | 2 / 2 | 24/24 (100.0%) | 24/24 (100.0%) | 0 |
| 40 | 5 / 5 | 60/61 (98.4%) | 60/61 (98.4%) | 0 |

Small-target samples are limited and target counts/collection conditions differ. The 15 dp radius occurs in one session; these data do not isolate a causal size or orientation effect. Unrecorded targets and no-touch entries are not automatically classified as robot misses.

## Contact placement across the screen

These are first recorded in-target contacts, one per uniquely containing circle. They describe placement conditional on a recorded in-circle contact.

| App screen third | Contacts | Mean x (dp) | Mean y (dp) | Median distance from center (dp) |
|---|---:|---:|---:|---:|
| Upper | 44 | +10.78 | -10.27 | 15.98 |
| Middle | 109 | +3.17 | +2.91 | 9.40 |
| Lower | 48 | -6.49 | +14.95 | 18.23 |

The aggregate mean can conceal opposing regional offsets. A single constant translation cannot fully cancel a position-dependent pattern; these observations alone do not identify its calibration or mapping cause.

## Region tendency as seen from the front

The operator confirmed that the phone's top pointed LEFT. The three panels in [region_tendency.png](figures/region_tendency.png) therefore run left to right: phone top, middle, phone bottom. Offsets rotate with the phone: view dx = app dy, view dy = -app dx. Positive view x means right; positive view y means down. The following table uses this view.

| Viewed region | Contacts | Mean right/left offset (dp) | Mean down/up offset (dp) |
|---|---:|---:|---:|
| Left (phone top) | 44 | -10.27 | -10.78 |
| Center | 109 | +2.91 | -3.17 |
| Right (phone bottom) | 48 | +14.95 | +6.49 |

## Coordinates and IMU

The app exports portrait coordinates (1080 × 2179 px) despite the horizontal holder. Upper/middle/lower mean thirds of the app's logged y axis; in the displayed horizontal view these become left/center/right. dx is positive right; dy is positive down. IMU components remain in the exporter's unverified axes; they are not calibrated robot roll/pitch/yaw. dp values use the logged px/dp ratio, not millimeters.

# Horizontal Tests: contact tendency and observation limitations

- Sessions analyzed: **18**; recorded contacts: **220**.
- Original session numbers preserved. Archived sessions: **[5, 10, 11, 12, 13, 14, 15, 16, 18, 26, 28, 29]**; see `data/annotations/horizontal_tests_exclusions.csv`.
- App-reported hits: **204/220 = 92.73%**, including repeats.
- App-assigned target hit coverage: **201/228 = 88.16%**.
- Distinct circles uniquely containing a recorded contact: **201/228** (geometric observation, not intended-action accuracy).
- Targets with any event/geometry: **228/228**. Sessions without all expected target IDs: **none**.
- Targets without any record: **0** (unknown outcomes, not failures).
- Hit fraction among targets with a record: **201/228 = 88.16%** (selection-dependent).
- Sessions with all expected IDs recorded: **18**; target coverage **201/228** (not independently verified robot completion).
- Rapid repeated-location pairs: **2**; explicit app completed-target repeat contacts: **3**.
- Contacts inside exactly one different circle than the app-assigned target: **0**.
- Legacy count-ceiling-compatible sessions: **none**.

## Target tendency

First recorded contact per uniquely containing circle: **201** observations across **18** sessions.
Mean offset: **x +2.53 dp; y +2.90 dp**.
Session-balanced mean: **x +2.85 dp; y +3.14 dp**.
Contacts above center: **39.3%**; left of center: **39.3%**.
Median radial error: **0.436 radii**; 90th percentile: **0.792 radii**.

Positive x points right; positive y points down. The unit circle is the target boundary.
dp is derived from each target's logged px/dp ratio, not physical millimeters.
`target_tendency.csv` includes radius/color/region and region × radius strata, all app assignments (including misses),
all uniquely contained contacts, first-per-circle observations, and two repeat-exclusion sensitivities.
First-per-circle is a spatial sampling rule, not a reconstructed robot action or first intended attempt.
The in-circle tendency is conditional on recorded success; it excludes outside/ambiguous contacts and has boundary truncation.
Means are descriptive. Contacts are clustered by session; no independent-event significance test is applied.

