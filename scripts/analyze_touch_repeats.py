"""Compare individual app contacts with one any-hit outcome per session/target."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import hashlib
import json

import matplotlib
if __name__ == "__main__":
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

from analyze_contacts import (ROOT, DATASETS, DATASET_LABELS, DATASET_COLORS, read_csv, write_csv, save,
                              plot_dataset, analyze_regions, tendency)

MODES = ("with_double_touches", "without_double_touches")


def make_units(contacts, mode, pairs=()):
    """Retain original labels; any recorded hit makes its target/group a hit."""
    if mode not in (*MODES, "rapid_repeat_sensitivity"):
        raise ValueError(f"Unknown counting mode: {mode}")
    ordered = sorted(contacts, key=lambda c: (c["dataset"], c["session_id"],
                     datetime.fromisoformat(c["date_time"].replace("Z", "+00:00")), c["event_id"]))
    keys = {(c["dataset"], c["event_id"]): c for c in ordered}
    assert len(keys) == len(ordered)
    parents = {key: key for key in keys}

    def find(key):
        while parents[key] != key:
            key = parents[key]
        return key

    if mode == "rapid_repeat_sensitivity":
        for pair in pairs:
            a, b = (pair["dataset"], pair["event_id_a"]), (pair["dataset"], pair["event_id_b"])
            assert keys[a]["session_id"] == keys[b]["session_id"] == pair["session_id"]
            parents[find(b)] = find(a)
    groups = defaultdict(list)
    for c in ordered:
        assert c["app_result"] in ("hit", "miss")
        key = (c["dataset"], c["session_id"], c["assigned_target_id"]) if mode == "without_double_touches" else find((c["dataset"], c["event_id"]))
        groups[key].append(c)
    units, membership = [], []
    for index, members in enumerate(groups.values(), 1):
        hits = [c for c in members if c["app_result"] == "hit"]
        representative = (hits or members)[0]
        unit_id = f"{mode}:{index:04d}"
        if mode == "without_double_touches":
            assert len({(c["assigned_radius_dp"], c["assigned_region"]) for c in members}) == 1
        units.append(dict(unit_id=unit_id, dataset=representative["dataset"],
                          session_id=representative["session_id"], session_number=representative["session_number"],
                          target_id=representative["assigned_target_id"], radius_dp=float(representative["assigned_radius_dp"]),
                          app_region=representative["assigned_region"], result="hit" if hits else "miss",
                          source_contacts=len(members), source_hits=len(hits), source_misses=len(members)-len(hits),
                          first_contact_time=members[0]["date_time"], last_contact_time=members[-1]["date_time"],
                          contact_span_sec=(datetime.fromisoformat(members[-1]["date_time"].replace("Z", "+00:00")) -
                                            datetime.fromisoformat(members[0]["date_time"].replace("Z", "+00:00"))).total_seconds(),
                          representative_event_id=representative["event_id"],
                          source_event_ids=";".join(c["event_id"] for c in members)))
        for c in members:
            membership.append(dict(c, counting_unit_id=unit_id, counting_unit_result="hit" if hits else "miss"))
    return units, membership


def summarize(units, contacts, sessions, dataset):
    us = [u for u in units if dataset == "combined" or u["dataset"] == dataset]
    cs = [c for c in contacts if dataset == "combined" or c["dataset"] == dataset]
    ss = [s for s in sessions if dataset == "combined" or s["dataset"] == dataset]
    hits = sum(u["result"] == "hit" for u in us)
    return dict(dataset=dataset, sessions=len(ss), source_contact_records=len(cs), counted_units=len(us),
                hits=hits, misses=len(us)-hits, hit_fraction=hits/len(us) if us else None,
                extra_contact_records_grouped=len(cs)-len(us), multi_contact_units=sum(u["source_contacts"] > 1 for u in us),
                no_touch_events=sum(int(s["no_touch"]) for s in ss),
                configured_targets=sum(int(s["effective_targets"]) for s in ss),
                unrecorded_targets=sum(int(s["target_ids_without_records"]) for s in ss))


def plot_outcomes(output, units, summary):
    grouped = output.name == "without_double_touches" or output.parent.name == "without_double_touches"
    if output.name in MODES:
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(range(len(summary)), [r["hit_fraction"] for r in summary],
                      color=[DATASET_COLORS.get(r["dataset"], "#455a64") for r in summary])
        for bar, r in zip(bars, summary):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.02,
                    f"{r['hits']}/{r['counted_units']}\n{r['hit_fraction']:.1%}", ha="center", fontsize=10)
        ax.set(xticks=range(len(summary)), xticklabels=["Combined" if r["dataset"] == "combined" else DATASET_LABELS[r["dataset"]] for r in summary],
               ylim=(0, 1.17), yticks=[0, .25, .5, .75, 1], ylabel="Recorded hit fraction")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.set_title("Individual contact records" if not grouped else
                     "One outcome per target in each session\nAny hit = hit; only misses = miss")
        fig.tight_layout()
        save(fig, output, "hit_fraction_by_condition", "Labels = hits / counted units. no-touch and unrecorded targets are excluded from this denominator.\n"
             "Conditions differ in target size, app behavior and mounting; fractions are descriptive.")
        return  # The pooled size chart lives only in combined/figures/.

    fig, ax = plt.subplots(figsize=(10, 5.5))
    radii = sorted({u["radius_dp"] for u in units})
    for index, dataset in enumerate(DATASETS):
        if not any(u["dataset"] == dataset for u in units):
            continue
        for i, radius in enumerate(radii):
            selected = [u for u in units if u["dataset"] == dataset and u["radius_dp"] == radius]
            if not selected:
                continue
            hits = sum(u["result"] == "hit" for u in selected)
            x = i+(index-1)*.26
            ax.bar(x, hits/len(selected), width=.25, color=DATASET_COLORS[dataset],
                   label=DATASET_LABELS[dataset] if radius == min(u["radius_dp"] for u in units if u["dataset"] == dataset) else None)
            ax.text(x, hits/len(selected)+.015, f"{hits}/{len(selected)}", ha="center", fontsize=7)
    ax.set(xticks=range(len(radii)), xticklabels=[f"{r:g}" for r in radii], ylim=(0, 1.15),
           yticks=[0, .25, .5, .75, 1], xlabel="Target radius (dp)", ylabel="Recorded hit fraction",
           title="Individual contacts by target size" if not grouped else
                 "Target-level outcomes by size — any hit counts as a hit")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.15), ncol=3, fontsize=9)
    fig.tight_layout()
    save(fig, output, "outcomes_by_size", "Labels = hits / counted units; dp is not millimeters.\n"
         "Blank positions have no observations. The horizontal 15 dp condition has one session.")


def plot_region_outcomes(output, units):
    """Use the chosen counting unit in every size/region denominator, including zero-hit cells."""
    from analyze_contacts import REGIONS
    radii = sorted({u["radius_dp"] for u in units})
    fig, axs = plt.subplots(3, 1, figsize=(7, 11), sharex=True, sharey=True)
    rows = []
    for region, ax in zip(REGIONS, axs):
        for i, radius in enumerate(radii):
            selected = [u for u in units if u["app_region"] == region and u["radius_dp"] == radius]
            if not selected:
                ax.text(i, .5, "No records", ha="center", fontsize=8, rotation=90)
                continue
            hits = sum(u["result"] == "hit" for u in selected)
            fraction = hits / len(selected)
            ax.bar(i, fraction, color="#43a047", label="Hit" if i == 0 else None)
            ax.bar(i, 1-fraction, bottom=fraction, color="#e53935", label="Miss" if i == 0 else None)
            ax.text(i, 1.02, f"{hits}/{len(selected)}", ha="center", fontsize=9)
            rows.append(dict(region=region, radius_dp=radius, counted_units=len(selected), hits=hits,
                             misses=len(selected)-hits, hit_fraction=fraction))
        ax.set(title=f"{region.title()} phone third", ylim=(0, 1.15), yticks=[0, .25, .5, .75, 1])
        ax.yaxis.set_major_formatter(PercentFormatter(1))
    axs[-1].set(xticks=range(len(radii)), xticklabels=[f"{r:g}" for r in radii], xlabel="Target radius (dp)")
    fig.supylabel("Fraction of counted units with contact")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color="#43a047", label="Hit"), Patch(color="#e53935", label="Miss")],
               loc="lower center", bbox_to_anchor=(.5, .025), ncol=2)
    fig.suptitle(f"{DATASET_LABELS[output.name]}\nRecorded outcomes by phone region and target size")
    fig.tight_layout(rect=(.02, .09, 1, .95))
    save(fig, output, "contact_outcomes_region_by_size", "Labels = hits / counted units. No-touch and unrecorded targets are separate.\n"
         "Regions use app axes; the horizontal phone's top third is viewer-left. dp is not mm.")
    write_csv(output / "tables/counted_outcomes_region_by_size.csv", rows)


def plot_session_outcomes(output, rows):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    x = np.arange(len(rows))
    ax.bar(x, [s["hits"] for s in rows], label="Hit", color="#43a047")
    ax.bar(x, [s["misses"] for s in rows], bottom=[s["hits"] for s in rows], label="Miss", color="#e53935")
    for position, s in zip(x, rows):
        ax.text(position, s["counted_units"]+.15, str(s["counted_units"]), ha="center", fontsize=8)
    ax.set(xticks=x, xticklabels=[s["session_number"] for s in rows],
           xlabel="Original session number (retained sessions)", ylabel="Counted units with contact",
           ylim=(0, max(s["counted_units"] for s in rows)+3),
           title=f"{DATASET_LABELS[output.name]}\nRecorded outcomes in each session")
    ax.legend(loc="upper left", ncol=2)
    fig.tight_layout()
    save(fig, output, "contact_outcomes", "Numbers = counted units; no-touch and unrecorded targets are excluded.\n"
         "Individual-contact mode includes repeats; target mode counts one any-hit outcome per session/target.")


def run(root, contacts, sessions, targets, groups):
    root = Path(root)
    baseline = root / "results/with_double_touches"
    base = baseline / "combined"
    pairs = [dict(p, dataset=ds) for ds in DATASETS
             for p in read_csv(baseline / ds / "tables/rapid_repeat_pairs.csv")]
    paths = [base / f"tables/{name}.csv" for name in ("contacts_extended", "sessions_extended", "targets_extended")]
    paths += [baseline / ds / "tables/rapid_repeat_pairs.csv" for ds in DATASETS]
    paths += [root / "scripts/analyze_touch_repeats.py"]
    baseline_manifest = json.loads((base / "contact_manifest.json").read_text())
    source_hashes = baseline_manifest["input_sha256"]
    assert all(hashlib.sha256((root / path).read_bytes()).hexdigest() == sha for path, sha in source_hashes.items())
    input_hashes = dict(source_hashes, **{str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    rapid, _ = make_units(contacts, "rapid_repeat_sensitivity", pairs)
    comparisons = []
    for mode in MODES:
        output = root / "results" / mode
        (output / "figures").mkdir(parents=True, exist_ok=True)
        units, membership = make_units(contacts, mode)
        summary = [summarize(units, contacts, sessions, ds) for ds in (*DATASETS, "combined")]
        for name, rows in (("summary", summary), ("units", units), ("contact_membership", membership)):
            write_csv(output / f"{name}.csv", rows)
        strata = []
        for dimension, field in (("radius_dp", "radius_dp"), ("app_region", "app_region")):
            for ds in (*DATASETS, "combined"):
                us = [u for u in units if ds == "combined" or u["dataset"] == ds]
                for value in sorted({u[field] for u in us}):
                    selected = [u for u in us if u[field] == value]
                    hits = sum(u["result"] == "hit" for u in selected)
                    strata.append(dict(dataset=ds, stratum=dimension, value=value, counted_units=len(selected),
                                       hits=hits, misses=len(selected)-hits, hit_fraction=hits/len(selected)))
        write_csv(output / "size_and_region_outcomes.csv", strata)
        write_csv(output / "rapid_repeat_sensitivity.csv", [summarize(rapid, contacts, sessions, ds) for ds in (*DATASETS, "combined")])
        # Inventory categories do not change with the choice of contact-counting unit.
        inventory = []
        for ds in (*DATASETS, "combined"):
            ts = [t for t in targets if ds == "combined" or t["dataset"] == ds]
            inventory.append(dict(dataset=ds, configured_targets=len(ts),
                                  targets_with_any_hit=sum(t["assigned_status"] == "hit" for t in ts),
                                  targets_with_contact_misses_only=sum(t["assigned_status"] == "miss_recorded" for t in ts),
                                  targets_with_no_touch_records_only=sum(t["assigned_status"] == "no_touch_only" for t in ts),
                                  targets_without_records=sum(t["assigned_status"] == "unrecorded" for t in ts),
                                  possible_ceiling_censoring=sum(t["possible_ceiling_censoring"] for t in ts)))
        write_csv(output / "target_inventory.csv", inventory)
        plot_outcomes(output, units, summary)
        representatives = {(u["dataset"], u["representative_event_id"]) for u in units}
        selected_contacts = [c for c in contacts if (c["dataset"], c["event_id"]) in representatives]
        for ds in (*DATASETS, "combined"):
            folder = output / ds
            for name in ("figures", "tables", "maps"):
                (folder / name).mkdir(parents=True, exist_ok=True)
            original = [c for c in contacts if ds == "combined" or c["dataset"] == ds]
            selected = [c for c in selected_contacts if ds == "combined" or c["dataset"] == ds]
            ss = [s for s in sessions if ds == "combined" or s["dataset"] == ds]
            ts = [t for t in targets if ds == "combined" or t["dataset"] == ds]
            us = [u for u in units if ds == "combined" or u["dataset"] == ds]
            plot_dataset(folder, selected, ss, groups.get(ds, []), placement_contacts=original,
                         contact_event_ids={c["event_id"] for c in selected})
            region_report = analyze_regions(folder, selected, ts, placement_contacts=original)
            region_report = ("Counting rule: " + ("individual contacts, including repeats." if mode == "with_double_touches" else
                             "one outcome per session/target; first hit, otherwise first miss, supplies the representative coordinate.") +
                             " First-in-circle placement retains its original, already unique samples.\n\n" + region_report)
            if mode == "without_double_touches":
                region_report = region_report.replace("## All app-assigned contacts (hits and misses)",
                                                      "## Representative app-assigned contacts (one per session/target)")
                region_report = region_report.replace("keeps all app-assigned contacts, including misses and repeats, with no outliers removed.",
                                                      "shows one representative per session/target: first hit, otherwise first miss. No coordinates are corrected.")
            (folder / "region_size_analysis.md").write_text(region_report, encoding="utf-8")
            if mode == "without_double_touches":
                write_csv(folder / "tables/representative_contacts.csv", selected)
            spatial_rows = [r for r in tendency(selected) if r["population"] != "first_contact_per_circle"]
            spatial_rows += [r for r in tendency(original) if r["population"] == "first_contact_per_circle"]
            write_csv(folder / "tables/target_tendency.csv", spatial_rows)
            plot_outcomes(folder, us, [r for r in summary if r["dataset"] == ds])
            plot_region_outcomes(folder, us)
            session_rows = []
            for s in ss:
                su = [u for u in us if (u["dataset"], u["session_id"]) == (s["dataset"], s["session_id"])]
                hits = sum(u["result"] == "hit" for u in su)
                session_rows.append(dict(dataset=s["dataset"], session_id=s["session_id"],
                                         session_number=s["session_number"], counted_units=len(su), hits=hits,
                                         misses=len(su)-hits, no_touch_events=s["no_touch"],
                                         unrecorded_targets=s["target_ids_without_records"]))
            write_csv(folder / "tables/session_outcomes.csv", session_rows)
            if ds != "combined":
                plot_session_outcomes(folder, session_rows)
            rule = "One representative per target: first hit, otherwise first miss." if mode == "without_double_touches" else "Every recorded contact retained."
            (folder / "README.md").write_text(
                f"# {DATASET_LABELS[ds]}\n\n{rule}\n\n"
                "[Outcome fractions by size](figures/outcomes_by_size.png) · "
                "[Outcomes by region and size](figures/contact_outcomes_region_by_size.png) · "
                "[Region tendency](figures/region_tendency.png) · "
                "[Placement by region and size](figures/region_by_size.png) · "
                "[Target tendency](figures/target_tendency.png) · "
                "[Offset along the phone](figures/vertical_bias_by_height.png) · "
                "[Assignment diagnostics](figures/app_assignment_diagnostics.png) · "
                "[Target inventory outcomes](figures/target_outcomes_region_by_size.png)\n\n"
                "Placement figures retain the original first in-circle contact per geometric target: they already "
                "exclude extra touches and therefore do not change between counting modes. Outcome fractions, "
                "assigned-contact diagnostics and session map markers use the selected counting rule. The target-inventory "
                "chart already uses any-hit outcomes and retains its no-touch/unknown categories. "
                "IMU summaries retain all original sensor readings; they are not touch outcomes. "
                "No source position or app label is corrected. All session exclusions remain unchanged.\n\n"
                + ("[Session outcomes](figures/contact_outcomes.png) · [Session maps](maps/session_overview.png) · [All maps (PDF)](maps/all_sessions.pdf)\n" if ds != "combined" else "") +
                "\n[Counting method and aggregate results](../README.md)\n", encoding="utf-8")
        description = ("Every recorded contact is counted separately, including repeated hits and misses. "
                       "This reproduces the original contact-level metric." if mode == "with_double_touches" else
                       "Each app-assigned target in each session contributes at most one outcome: any recorded hit means hit; "
                       "contacts with only misses mean miss. This also collapses later retries on the same target, "
                       "not only rapid double touches. Session and dataset identity keep reused target IDs separate.")
        report = (f"# {'With double touches: individual contacts' if mode == 'with_double_touches' else 'Without double-touch penalties: one outcome per target'}\n\n"
                  f"{description}\n\n"
                  "| Condition | Sessions | Counted units | Hits | Misses | Hit fraction | Extra contact records grouped |\n"
                  "|---|---:|---:|---:|---:|---:|---:|\n")
        for r in summary:
            report += (f"| {DATASET_LABELS[r['dataset']]} | {r['sessions']} | {r['counted_units']} | "
                       f"{r['hits']} | {r['misses']} | {r['hit_fraction']:.2%} | {r['extra_contact_records_grouped']} |\n")
        report += ("\n## What is and is not counted\n\n"
                   "The denominator includes only units with recorded contact coordinates. no-touch entries and targets "
                   "without records remain separate in `target_inventory.csv` and `summary.csv`; they are not imputed as hits or misses. "
                   "The same operator-requested session exclusions apply in both folders.\n\n"
                   "Original app labels, coordinates and event IDs remain unchanged in `contact_membership.csv`. "
                   "`units.csv` links every counted unit to all source events. A grouped result is a derived classification, "
                   "not a modification of a raw contact or proof of the robot's intended target. Old Sweet Spot app assignment "
                   "and count-ceiling limitations remain; no missing contact can be recovered by grouping.\n\n"
                   "`rapid_repeat_sensitivity.csv` separately counts temporal/spatial groups using the existing <=300 ms "
                   "and <=8 dp candidate pairs. This stricter rule retains later retries as separate outcomes and is not "
                   "the main target-level metric requested by the operator.\n\n"
                   "## Figures and reproducibility\n\n"
                   "[Fractions by condition](figures/hit_fraction_by_condition.png) · [Fractions by target size](combined/figures/outcomes_by_size.png)\n\n"
                   "Full figure sets and session maps: [Sweet Spot](sweetspot/README.md), "
                   "[Random Poses](random_poses/README.md), [Horizontal Tests](horizontal_tests/README.md), "
                   "[Combined](combined/README.md). Each includes the same tendency, region, size and diagnostic figures as the original analysis.\n\n"
                   "Placement plots already use the first recorded in-target contact per geometric circle, so their "
                   "positions are unchanged. Maps and assigned-contact diagnostics use the first hit per session/target "
                   "(or first miss if no hit) in the target-level mode; contact mode keeps all source contacts. "
                   "A representative is an actual recorded coordinate, not a spatial correction.\n\n"
                   "Run `python scripts/analyze_contacts.py` to regenerate both views with the baseline analysis. Input hashes and "
                   "the grouping rule are in `manifest.json`. dp is a display unit, not millimeters; these fractions are "
                   "descriptive and do not establish independent-attempt accuracy or a causal orientation effect.\n")
        (output / "README.md").write_text(report, encoding="utf-8")
        manifest = dict(mode=mode, unit="contact" if mode == "with_double_touches" else "session_target",
                        grouped_outcome="any_hit_else_miss", input_sha256=input_hashes,
                        representative_coordinate="first_hit_else_first_miss" if mode == "without_double_touches" else "each_contact",
                        placement_population="original_first_contact_per_geometric_circle",
                        source_contacts=len(contacts), counted_units=len(units),
                        hits=sum(u["result"] == "hit" for u in units), session_exclusions_preserved=True,
                        rapid_sensitivity_thresholds=dict(max_interval_ms=300, max_separation_dp=8),
                        numpy=np.__version__, matplotlib=matplotlib.__version__)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
        comparisons.extend(dict(mode=mode, **r) for r in summary)
        print(f"{mode}: {summary[-1]['hits']}/{summary[-1]['counted_units']} = {summary[-1]['hit_fraction']:.2%}")
    write_csv(root / "results/double_touch_comparison.csv", comparisons)
    combined = {r["mode"]: r for r in comparisons if r["dataset"] == "combined"}
    def fraction(mode):
        row = combined[mode]
        return f"{row['hits']}/{row['counted_units']} = {row['hit_fraction']:.2%}"
    (root / "results/README.md").write_text(
        "# Analysis results\n\n"
        "Choose the counting rule first; each folder contains Sweet Spot, Random Poses, Horizontal Tests and Combined.\n\n"
        "| View | Counting rule | Combined result |\n|---|---|---|\n"
        f"| [Without double-touch penalties](without_double_touches/README.md) | One outcome per target/session: any hit = hit; only misses = miss | {fraction('without_double_touches')} |\n"
        f"| [All contacts](with_double_touches/README.md) | Every recorded contact, including repeats | {fraction('with_double_touches')} |\n\n"
        "[Comparison table (CSV)](double_touch_comparison.csv)\n\n"
        "The original contact analysis, detailed reports, input tables, IMU summaries and excluded-session maps "
        "live under `with_double_touches/`; there is no third copy at this level. "
        "Plots within each view belong to that view. First-in-circle placement and target-inventory plots "
        "already counted each target once, so their samples agree between views. "
        "No-touch and missing records stay separate from the hit/miss denominators. Raw data and exclusions are unchanged.\n",
        encoding="utf-8")
    return comparisons


if __name__ == "__main__":
    from analyze_contacts import run as run_analysis
    run_analysis()
