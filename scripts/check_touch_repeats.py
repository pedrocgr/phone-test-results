"""Check any-hit target grouping, source preservation and both complete figure sets."""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json

from analyze_contacts import ROOT, DATASETS, read_csv
from analyze_touch_repeats import make_units, MODES


def contact(event, target, result, time, dataset="sweetspot", session="session"):
    return dict(event_id=event, dataset=dataset, session_id=session, session_number="1",
                assigned_target_id=target, assigned_radius_dp="40", assigned_region="upper",
                app_result=result, date_time=f"2026-10-06T12:00:{time}Z")


source = [contact("a", "A", "miss", "00"), contact("b", "A", "hit", "00.070"),
          contact("c", "A", "miss", "20"), contact("d", "B", "miss", "30"),
          contact("e", "B", "miss", "30.050")]
snapshot = deepcopy(source)
units, membership = make_units(source, "without_double_touches")
assert [(u["target_id"], u["result"], u["source_contacts"]) for u in units] == [("A", "hit", 3), ("B", "miss", 2)]
assert units[0]["representative_event_id"] == "b" and units[1]["representative_event_id"] == "d"
assert source == snapshot and [c["app_result"] for c in membership] == [c["app_result"] for c in source]
raw, _ = make_units(source, "with_double_touches")
assert len(raw) == 5 and sum(u["result"] == "hit" for u in raw) == 1
isolated = [source[0], dict(source[0], event_id="other", session_id="another"),
            dict(source[0], dataset="random_poses")]
assert len(make_units(isolated, "without_double_touches")[0]) == 3
rapid, _ = make_units(source, "rapid_repeat_sensitivity", [dict(
    dataset="sweetspot", session_id="session", event_id_a="a", event_id_b="b")])
assert len(rapid) == 4 and next(u for u in rapid if u["source_contacts"] == 2)["result"] == "hit"
try:
    make_units(source, "unknown")
except ValueError:
    pass
else:
    raise AssertionError("Unknown counting rule accepted")

contacts = read_csv(ROOT / "results/combined/tables/contacts_extended.csv")
original = {(c["dataset"], c["event_id"]): c for c in contacts}
expected = {
    "with_double_touches": [(132, 111), (105, 101), (220, 204), (457, 416)],
    "without_double_touches": [(127, 111), (91, 88), (216, 201), (434, 400)],
}
for mode in MODES:
    folder = ROOT / "results" / mode
    rows = read_csv(folder / "summary.csv")
    assert [(int(r["counted_units"]), int(r["hits"])) for r in rows] == expected[mode]
    assert int(rows[-1]["no_touch_events"]) == 60 and int(rows[-1]["unrecorded_targets"]) == 10
    units = {u["unit_id"]: u for u in read_csv(folder / "units.csv")}
    members = read_csv(folder / "contact_membership.csv")
    assert len(members) == len(original) == 457
    assert {(c["dataset"], c["event_id"]) for c in members} == set(original)
    groups = defaultdict(list)
    for c in members:
        assert all(c[k] == v for k, v in original[(c["dataset"], c["event_id"])].items())
        groups[c["counting_unit_id"]].append(c)
    for uid, cs in groups.items():
        assert units[uid]["result"] == ("hit" if any(c["app_result"] == "hit" for c in cs) else "miss")
        assert units[uid]["source_event_ids"].split(";") == [c["event_id"] for c in cs]
        assert int(units[uid]["source_contacts"]) == len(cs)
    if mode == "without_double_touches":
        assert len({(u["dataset"], u["session_id"], u["target_id"]) for u in units.values()}) == len(units)
    for name, sha in json.loads((folder / "manifest.json").read_text())["input_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, name
    rapid_summary = read_csv(folder / "rapid_repeat_sensitivity.csv")[-1]
    assert (int(rapid_summary["counted_units"]), int(rapid_summary["hits"])) == (449, 412)
    for ds, counts in zip((*DATASETS, "combined"), expected[mode]):
        output = folder / ds
        representatives = read_csv(output / "tables/representative_contacts.csv")
        assert len(representatives) == counts[0]
        assert sum(c["app_result"] == "hit" for c in representatives) == counts[1]
        us = [u for u in units.values() if ds == "combined" or u["dataset"] == ds]
        assert {(c["dataset"], c["event_id"]) for c in representatives} == {
            (u["dataset"], u["representative_event_id"]) for u in us}
        outcomes = read_csv(output / "tables/counted_outcomes_region_by_size.csv")
        assert sum(int(r["counted_units"]) for r in outcomes) == counts[0]
        assert sum(int(r["hits"]) for r in outcomes) == counts[1]
        sessions = read_csv(output / "tables/session_outcomes.csv")
        assert sum(int(r["counted_units"]) for r in sessions) == counts[0]
        assert sum(int(r["hits"]) for r in sessions) == counts[1]
        for name in ("target_tendency", "region_tendency", "vertical_bias_by_height", "region_by_size",
                     "target_outcomes_region_by_size", "app_assignment_diagnostics", "contact_outcomes_region_by_size",
                     "outcomes_by_size", "hit_fraction_by_condition"):
            png = (output / f"figures/{name}.png").read_bytes()
            assert png.startswith(b"\x89PNG") and b"Description" in png, (mode, ds, name)
        if ds != "combined":
            assert (output / "figures/contact_outcomes.png").is_file()
            assert (output / "maps/session_overview.png").is_file()
            assert len(list((output / "maps").glob("session_[0-9][0-9].png"))) == {"sweetspot": 15, "random_poses": 7, "horizontal_tests": 18}[ds]
        # First-contact placement is already deduplicated: count/coordinates must not change with mode.
        assert read_csv(output / "tables/region_tendency_view.csv") == read_csv(ROOT / f"results/{ds}/tables/region_tendency_view.csv")
        old_figures = {p.name for p in (ROOT / f"results/{ds}/figures").glob("*.png")}
        assert old_figures <= {p.name for p in (output / "figures").glob("*.png")}, (mode, ds, old_figures)

assert (ROOT / "results/with_double_touches/target_inventory.csv").read_bytes() == (ROOT / "results/without_double_touches/target_inventory.csv").read_bytes()
assert len(read_csv(ROOT / "results/double_touch_comparison.csv")) == 8
print("Repeat-analysis checks passed: any-hit rule, 457 unchanged source contacts, full figures/maps, counts and hashes.")
