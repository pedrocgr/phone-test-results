# Recorded contact tendency: Sweet Spot, Random Poses and Horizontal Tests

First recorded contact per uniquely containing circle; conditional on recorded in-circle contact.
Offsets are in phone screen axes (x right, y down), in dp rather than physical millimeters.
Equal-session means help distinguish contact weighting from session weighting.

| Dataset | Radius (dp) | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Equal-session x (dp) | Equal-session y (dp) | Above center |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sweetspot | all | 111 | 15 | -6.25 | -6.95 | -6.39 | -6.82 | 70.3% |
| sweetspot | 25 | 5 | 1 | -1.84 | -2.81 | -1.84 | -2.81 | 60.0% |
| sweetspot | 30 | 27 | 4 | -6.51 | -2.98 | -6.37 | -2.84 | 59.3% |
| sweetspot | 35 | 34 | 5 | -8.97 | -9.43 | -9.35 | -10.05 | 76.5% |
| sweetspot | 40 | 18 | 2 | -6.60 | -6.95 | -6.60 | -6.95 | 72.2% |
| sweetspot | 45 | 10 | 1 | -8.22 | -12.73 | -8.22 | -12.73 | 80.0% |
| sweetspot | 50 | 17 | 2 | -0.13 | -6.08 | -0.17 | -5.65 | 70.6% |
| random_poses | all | 88 | 7 | -1.28 | -10.92 | -1.89 | -10.70 | 75.0% |
| random_poses | 40 | 88 | 7 | -1.28 | -10.92 | -1.89 | -10.70 | 75.0% |
| horizontal_tests | all | 201 | 18 | +2.53 | +2.90 | +2.85 | +3.14 | 39.3% |
| horizontal_tests | 15 | 10 | 1 | +1.95 | +1.87 | +1.95 | +1.87 | 40.0% |
| horizontal_tests | 20 | 24 | 2 | +2.77 | +3.14 | +2.69 | +3.16 | 37.5% |
| horizontal_tests | 25 | 45 | 4 | +2.49 | +4.35 | +2.59 | +4.41 | 35.6% |
| horizontal_tests | 30 | 38 | 4 | +2.97 | +6.50 | +4.27 | +6.70 | 28.9% |
| horizontal_tests | 35 | 24 | 2 | +1.30 | +2.52 | +1.30 | +2.52 | 37.5% |
| horizontal_tests | 40 | 60 | 5 | +2.77 | -0.24 | +2.77 | -0.24 | 50.0% |

Both full populations and every available radius stratum are shown; compare matching radii across conditions. Even at the same radius,
app behavior, holder pose, session completeness and collection conditions differ.
These samples do not establish a causal effect of robot pose or recording conditions.
Sweet Spot and Random Poses have an aggregate tendency above target center; Horizontal Tests instead
has opposing regional offsets. Camera-to-tip extrinsics and coordinate mapping warrant a controlled check;
these logs alone do not identify the cause or justify an automatic offset correction.

Legacy double-contact consequences are flagged in `sweetspot/contact_analysis.md`;
missing outcomes are not imputed. New repeated contacts and partial sessions remain visible in
`random_poses/contact_analysis.md`. See their sensitivity tables before quoting an accuracy percentage.

Horizontal Tests applies the operator-requested exclusions in `data/annotations/horizontal_tests_exclusions.csv`. Its app coordinates stay portrait even when the holder is horizontal. The horizontal radius 15 dp condition has one session. See `horizontal_tests/summary.md` for all-session versus full-ID size strata.
