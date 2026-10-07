# Sweet Spot: simple descriptive analysis

## Selection and provenance

Source: `data/raw/sweetspot/touch_results_2026-10-06-sweetspot.jsonl`. SHA-256: `290accd48b1739358913f6846d241b868f7a73a8317a14dd1b178490747f67f5`.
The original file has 177 events in 20 sessions.
Sessions 3, 4, 6, 7, and 9 were excluded retrospectively by the operator as interrupted trials.
The retained population has **15 sessions, 163 events, and 132 recorded contacts**.
Source measurements and original session/target identifiers are preserved.

Sessions 12 and 13 are completed six-target trials according to the operator (two reported trios).
Their JSON configuration states nine targets. The correction is an external annotation, not a rewrite of the raw logs.
The six logged IDs, including an uneven RGB identifier distribution in session 13, do not independently verify two complete RGB trios. The metadata discrepancy remains unresolved.

## Observed outcomes

- App-reported hits: **111**; misses: **21**.
- Recorded-contact hit fraction: **111/132 = 84.09%**.
- Target hit coverage with operator-corrected counts: **111/135 = 82.22%**.
- Raw-configuration sensitivity: **111/141 = 78.72%**.

All registered contacts, including repeats, remain in the contact fraction. Targets with any hit are counted once in the target fraction.
Neither fraction estimates independent robot-action accuracy or unlogged outcomes.

## Repeated contacts

| Session | Contact indices | Separation (px) | Interval (ms) | App assignments |
|---|---|---:|---:|---|
| 5 | 5 and 6 | 2.35 | 73.3 | trio-001-green → trio-003-green |
| 14 | 3 and 4 | 2.74 | 60.5 | trio-001-red → trio-002-blue |
| 15 | 2 and 3 | 3.83 | 72.1 | trio-003-green → trio-002-blue |
| 19 | 1 and 2 | 3.02 | 67.7 | trio-003-red → trio-003-red |

There are 4 nearby pairs; 4 meet the exploratory rapid-repeat criterion.
The default thresholds are 8 dp and 300 ms. A close, rapid pair is consistent with repeated contact, without proving its physical cause.
App outcomes are preserved even when an assigned target differs from the nearby circle.

## Scope

This analysis covers recorded outcomes, contact repetition, and maps. IMU, application timing, calibration, and software-history analyses are not performed.
Target size and session conditions vary together; contacts are clustered within sessions. No causal or independent-trial inference is made.
The after-update raw exports are preserved but are not part of this Sweet Spot analysis.
See data/annotations/ for operator decisions and archive/detailed_analysis/ for the previous detailed snapshot.
