# Recorded contact tendency: Sweet Spot and Random Poses

First recorded contact per uniquely containing circle; conditional on recorded in-circle contact.
Offsets are in phone screen axes (x right, y down), in dp rather than physical millimeters.
Equal-session means help distinguish contact weighting from session weighting.

| Dataset | Radius (dp) | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Equal-session x (dp) | Equal-session y (dp) | Above center |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sweetspot | all | 111 | 15 | -6.25 | -6.95 | -6.39 | -6.82 | 70.3% |
| sweetspot | 40 | 18 | 2 | -6.60 | -6.95 | -6.60 | -6.95 | 72.2% |
| random_poses | all | 88 | 7 | -1.28 | -10.92 | -1.89 | -10.70 | 75.0% |
| random_poses | 40 | 88 | 7 | -1.28 | -10.92 | -1.89 | -10.70 | 75.0% |

Both full populations and shared target-radius strata are shown. Even at the same radius,
app behavior, holder pose, session completeness and collection conditions differ.
These samples do not establish a causal effect of robot pose or recording conditions.
The consistent tendency above center warrants checking camera-to-tip extrinsics and coordinate mapping
in a new controlled experiment; these logs alone do not identify the cause or justify automatic offset correction.

Legacy double-contact consequences are flagged in `sweetspot/contact_analysis.md`;
missing outcomes are not imputed. New repeated contacts and partial sessions remain visible in
`random_poses/contact_analysis.md`. See their sensitivity tables before quoting an accuracy percentage.
