# Analysis results

Choose the counting rule first; each folder contains Sweet Spot, Random Poses, Horizontal Tests and Combined.

| View | Counting rule | Combined result |
|---|---|---|
| [Without double-touch penalties](without_double_touches/README.md) | One outcome per target/session: any hit = hit; only misses = miss | 400/434 = 92.17% |
| [All contacts](with_double_touches/README.md) | Every recorded contact, including repeats | 416/457 = 91.03% |

[Comparison table (CSV)](double_touch_comparison.csv)

The original contact analysis, detailed reports, input tables, IMU summaries and excluded-session maps live under `with_double_touches/`; there is no third copy at this level. Plots within each view belong to that view. First-in-circle placement and target-inventory plots already counted each target once, so their samples agree between views. No-touch and missing records stay separate from the hit/miss denominators. Raw data and exclusions are unchanged.
