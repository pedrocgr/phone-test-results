# With double touches: individual contacts

Every recorded contact is counted separately, including repeated hits and misses. This reproduces the original contact-level metric.

| Condition | Sessions | Counted units | Hits | Misses | Hit fraction | Extra contact records grouped |
|---|---:|---:|---:|---:|---:|---:|
| Sweet Spot | 15 | 132 | 111 | 21 | 84.09% | 0 |
| Random Poses | 7 | 105 | 101 | 4 | 96.19% | 0 |
| Horizontal Tests | 18 | 220 | 204 | 16 | 92.73% | 0 |
| Sweet Spot + Random Poses + Horizontal Tests | 40 | 457 | 416 | 41 | 91.03% | 0 |

## What is and is not counted

The denominator includes only units with recorded contact coordinates. no-touch entries and targets without records remain separate in `target_inventory.csv` and `summary.csv`; they are not imputed as hits or misses. The same operator-requested session exclusions apply in both folders.

Original app labels, coordinates and event IDs remain unchanged in `contact_membership.csv`. `units.csv` links every counted unit to all source events. A grouped result is a derived classification, not a modification of a raw contact or proof of the robot's intended target. Old Sweet Spot app assignment and count-ceiling limitations remain; no missing contact can be recovered by grouping.

`rapid_repeat_sensitivity.csv` separately counts temporal/spatial groups using the existing <=300 ms and <=8 dp candidate pairs. This stricter rule retains later retries as separate outcomes and is not the main target-level metric requested by the operator.

## Figures and reproducibility

[Fractions by condition](figures/hit_fraction_by_condition.png) · [Fractions by target size](figures/hit_fraction_by_size.png)

Full figure sets and session maps: [Sweet Spot](sweetspot/README.md), [Random Poses](random_poses/README.md), [Horizontal Tests](horizontal_tests/README.md), [Combined](combined/README.md). Each includes the same tendency, region, size and diagnostic figures as the original analysis.

Placement plots already use the first recorded in-target contact per geometric circle, so their positions are unchanged. Maps and assigned-contact diagnostics use the first hit per session/target (or first miss if no hit) in the target-level mode; contact mode keeps all source contacts. A representative is an actual recorded coordinate, not a spatial correction.

Run `python scripts/analyze_contacts.py` to regenerate both views with the baseline analysis. Input hashes and the grouping rule are in `manifest.json`. dp is a display unit, not millimeters; these fractions are descriptive and do not establish independent-attempt accuracy or a causal orientation effect.
