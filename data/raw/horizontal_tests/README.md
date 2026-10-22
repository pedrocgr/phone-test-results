# Horizontal Tests — 13 October 2026

Original exports copied byte-for-byte from
`/home/pcgr/Desktop/logs13-10/horizontal_tests/` on 19 October 2026.
JSON, JSONL and CSV describe the same 272 events, not independent experiments.
Only JSONL enters the analysis; the other exports are retained for reconciliation.

The folder and operator identify the holder condition as horizontal. The app
still reports portrait coordinates (1080 × 2179 px). All targets are RGB circles;
`captcha_enabled` is false throughout. The random-position setting describes
target placement and does not establish a random robot pose.

On 21 October the operator confirmed that, when looking at the screen from the
front, the phone's top pointed LEFT (90 degrees counterclockwise from portrait).
The region-tendency view uses `(view dx, view dy) = (app dy, -app dx)` and arranges
the original upper/middle/lower app bands as left/center/right. This display
rotation does not change any raw coordinates or calibrate a robot/world frame.

The raw export preserves all 30 chronological sessions. On 21 October the operator
requested excluding sessions 5, 10, 11, 12, 13, 14, 15, 16, 18, 26, 28 and 29.
Their original events are archived separately; the analysis retains 18 sessions
with original numbering. Decisions are recorded in
`data/annotations/horizontal_tests_exclusions.csv`; raw events stay unchanged.

Source SHA-256 values:

- JSONL: `a081ca9553b7c576d90724a0f50369f85cef2639c71126e54e2fa7c85ca8fbcf`
- JSON: `6ab85a6c1bbc79dd0e509942eacbc2a135380f343eb8c176ee00f2e005d39519`
- CSV: `b52065f7d087ff4143d3c3ba4d56ecd35aa959ee598757f29f17630de4891caa`
