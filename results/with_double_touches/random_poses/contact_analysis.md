# Random Poses: contact tendency and observation limitations

- Sessions analyzed: **7**; recorded contacts: **105**.
- Original session numbers preserved. Archived sessions: **[2, 7, 8, 10]**; see `data/annotations/random_poses_exclusions.csv`.
- App-reported hits: **101/105 = 96.19%**, including repeats.
- App-assigned target hit coverage: **88/102 = 86.27%**.
- Distinct circles uniquely containing a recorded contact: **88/102** (geometric observation, not intended-action accuracy).
- Targets with any event/geometry: **92/102**. Sessions without all expected target IDs: **[6]**.
- Targets without any record: **10** (unknown outcomes, not failures).
- Hit fraction among targets with a record: **88/92 = 95.65%** (selection-dependent).
- Sessions with all expected IDs recorded: **6**; target coverage **82/84** (not independently verified robot completion).
- Rapid repeated-location pairs: **2**; explicit app completed-target repeat contacts: **13**.
- Contacts inside exactly one different circle than the app-assigned target: **0**.
- Legacy count-ceiling-compatible sessions: **none**.

## Target tendency

First recorded contact per uniquely containing circle: **88** observations across **7** sessions.
Mean offset: **x -1.28 dp; y -10.92 dp**.
Session-balanced mean: **x -1.89 dp; y -10.70 dp**.
Contacts above center: **75.0%**; left of center: **53.4%**.
Median radial error: **0.495 radii**; 90th percentile: **0.820 radii**.

Positive x points right; positive y points down. The unit circle is the target boundary.
dp is derived from each target's logged px/dp ratio, not physical millimeters.
`target_tendency.csv` includes radius/color/region and region × radius strata, all app assignments (including misses),
all uniquely contained contacts, first-per-circle observations, and two repeat-exclusion sensitivities.
First-per-circle is a spatial sampling rule, not a reconstructed robot action or first intended attempt.
The in-circle tendency is conditional on recorded success; it excludes outside/ambiguous contacts and has boundary truncation.
Means are descriptive. Contacts are clustered by session; no independent-event significance test is applied.

## Double contacts and app censoring

Raw app outcomes are never overwritten. Geometry is only reconstructed from logged target circles.
A unique containing circle is identifiable spatially, but does not prove robot intent; missing circles cannot be reconstructed.
Legacy sessions with rapid repeated locations, a contact count equal to effective target count,
and incomplete hit coverage are marked **compatible with the count ceiling**, not confirmed censored trials.
Unresolved targets in those sessions are marked `possible_ceiling_censoring`; no later hit is imputed.
`no_touch` is an app/operator observation, not proof of a physical miss. Missing records in incomplete sessions are unknown.
Retain the original fractions as app-recorded outcomes. Use spatial coverage and repeat sensitivities alongside them;
do not report any corrected fraction as robot accuracy. Recover unlogged outcomes only with synchronized robot logs/video
or a separately attributed operator annotation. Neither is available in these exports.
`outcome_sensitivity.csv` additionally separates full-ID sessions and excludes ceiling-compatible sessions,
with all contacts versus rapid-repeat and explicit completed-target-repeat exclusions.
These alternative populations are sensitivities, not replacement truth or independent-action estimates.

## Operator-confirmed interruption

Session 6: Execution stopped after a touch-sensor connection error. The remaining 10 targets were not executed and are not counted as touch misses. Recorded contacts are retained; the interruption reason is an operator annotation, not inferred from the app export.


## Phone orientation (exploratory)

`sessions_extended.csv` summarizes contact-time `orientation_deg[0..2]` using circular means,
resultant concentration and largest circular deviation, plus accelerometer/gyroscope norm medians.
Null sensor samples are omitted. Manual no-touch timestamps are excluded from these summaries.
These are phone sensor axes as logged: the exporter axis convention, phone-to-holder extrinsic and
reference heading are not established here. They are not calibrated robot/world roll, pitch and yaw.
Near an Euler singularity, heading and roll may change even for a similar phone attitude;
contact-time acceleration includes motion/impact. The IMU plot describes sample variation only.
Random target placement in app configuration does not identify a random robot pose. The Random Poses
random-holder condition comes from the operator's description and remains a dataset-level annotation.
Sweet Spot radius, collection time, app behavior and holder conditions differ from the later dataset;
their fractions cannot demonstrate a causal improvement or deterioration.
