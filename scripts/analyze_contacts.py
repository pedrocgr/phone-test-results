"""Target-relative contacts, logging limitations, and exploratory phone IMU summaries."""
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
import csv
import hashlib
import json
import math
import platform

import matplotlib
if __name__ == "__main__":
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NEARBY_DP = 8
REPEAT_MS = 300
COLORS = {"red": "#e53935", "green": "#43a047", "blue": "#1e88e5"}
REGIONS = ("upper", "middle", "lower")


def screen_region(y_fraction):
    """Fixed thirds of the logged screen; classify by target center, not touch."""
    if not math.isfinite(y_fraction) or not 0 <= y_fraction <= 1:
        raise ValueError("Target center must be within the logged screen height")
    return REGIONS[min(int(y_fraction * 3), 2)]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def timestamp(event):
    return datetime.fromisoformat(event["date_time"].replace("Z", "+00:00"))


def has_contact(event):
    return event["actual_touch_x"] is not None and event["actual_touch_y"] is not None


def distance(event, target):
    return math.hypot(event["actual_touch_x"] - target["target_center_x"],
                      event["actual_touch_y"] - target["target_center_y"])


def circular_summary(values):
    """Mean, concentration, and largest deviation; do not average across +/-180."""
    if not values:
        return None, None, None
    z = np.mean(np.exp(1j * np.radians(values)))
    if abs(z) < 1e-8:
        return None, float(abs(z)), None
    mean = float(np.degrees(np.angle(z)))
    deviation = max(abs((v - mean + 180) % 360 - 180) for v in values)
    return mean, float(abs(z)), float(deviation)


def analyze_session(events, number, expected_ids, dataset):
    events = sorted(events, key=timestamp)
    geometry = {}
    for e in events:
        assert (e["actual_touch_x"] is None) == (e["actual_touch_y"] is None)
        assert e["target_radius"] > 0 and e["target_radius_dp"] > 0
        assert e["target_id"] in expected_ids
        if e["target_id"] in geometry:
            old = geometry[e["target_id"]]
            assert all(e[k] == old[k] for k in ("target_center_x", "target_center_y", "target_radius", "target_radius_dp"))
        geometry[e["target_id"]] = e
        if has_contact(e):
            d = distance(e, e)
            assert math.isclose(d, e["distance_to_center"], abs_tol=.001)
            assert e["inside_target"] == (d <= e["target_radius"])
            assert e["result"] == ("hit" if e["inside_target"] else "miss")
        else:
            assert e["result"] == "no_touch"
    touches = [e for e in events if has_contact(e)]
    pairs, repeat_ids = [], set()
    # ponytail: O(n²) matches the existing short-session analysis; index if logs grow large.
    for a, b in combinations(touches, 2):
        dt = (timestamp(b) - timestamp(a)).total_seconds() * 1000
        density = a["target_radius"] / a["target_radius_dp"]
        separation = math.hypot(a["actual_touch_x"] - b["actual_touch_x"], a["actual_touch_y"] - b["actual_touch_y"])
        if 0 <= dt <= REPEAT_MS and separation <= NEARBY_DP * density:
            repeat_ids.add(b["event_id"])
            pairs.append(dict(session_number=number, session_id=a["session_id"],
                              event_id_a=a["event_id"], event_id_b=b["event_id"],
                              interval_ms=dt, separation_dp=separation / density,
                              assigned_target_a=a["target_id"], assigned_target_b=b["target_id"],
                              assignment_changed=a["target_id"] != b["target_id"]))
    contacts, seen_spatial_targets = [], set()
    for e in touches:
        containing = [t for t in geometry.values() if distance(e, t) <= t["target_radius"]]
        target = containing[0] if len(containing) == 1 else None
        density = e["target_radius"] / e["target_radius_dp"]
        dx = e["actual_touch_x"] - e["target_center_x"]
        dy = e["actual_touch_y"] - e["target_center_y"]
        c = dict(dataset=dataset, session_number=number, session_id=e["session_id"],
                 event_id=e["event_id"], date_time=e["date_time"], assigned_target_id=e["target_id"],
                 app_result=e["result"], actual_x_px=e["actual_touch_x"], actual_y_px=e["actual_touch_y"],
                 assigned_radius_dp=e["target_radius_dp"], assigned_color=e["target_id"].rsplit("-", 1)[-1],
                 assigned_x_fraction=e["target_center_x"] / e["screen_width"],
                 assigned_y_fraction=e["target_center_y"] / e["screen_height"],
                 assigned_region=screen_region(e["target_center_y"] / e["screen_height"]),
                 assigned_dx_dp=dx / density, assigned_dy_dp=dy / density,
                 assigned_dx_r=dx / e["target_radius"], assigned_dy_r=dy / e["target_radius"],
                 unique_containing_target_id=target["target_id"] if target else "",
                 containing_target_count=len(containing),
                 assignment_disagrees=bool(target and target["target_id"] != e["target_id"]),
                 rapid_repeat_candidate=e["event_id"] in repeat_ids,
                 app_completed_flag_available="target_already_completed" in e,
                 app_target_already_completed=e.get("target_already_completed", False),
                 first_contact_in_circle=bool(target and target["target_id"] not in seen_spatial_targets),
                 geometric_radius_dp=None, geometric_color="", geometric_region="", geometric_dx_dp=None, geometric_dy_dp=None,
                 geometric_dx_r=None, geometric_dy_r=None, target_x_fraction=None, target_y_fraction=None,
                 screen_dx_fraction=None, screen_dy_fraction=None)
        if target:
            density = target["target_radius"] / target["target_radius_dp"]
            dx = e["actual_touch_x"] - target["target_center_x"]
            dy = e["actual_touch_y"] - target["target_center_y"]
            c.update(geometric_radius_dp=target["target_radius_dp"], geometric_color=target["target_id"].rsplit("-", 1)[-1],
                     geometric_region=screen_region(target["target_center_y"] / target["screen_height"]),
                     geometric_dx_dp=dx / density, geometric_dy_dp=dy / density,
                     geometric_dx_r=dx / target["target_radius"], geometric_dy_r=dy / target["target_radius"],
                     target_x_fraction=target["target_center_x"] / target["screen_width"],
                     target_y_fraction=target["target_center_y"] / target["screen_height"],
                     screen_dx_fraction=dx / target["screen_width"], screen_dy_fraction=dy / target["screen_height"])
            seen_spatial_targets.add(target["target_id"])
        contacts.append(c)
    hit_ids = {e["target_id"] for e in events if e["result"] == "hit"}
    legacy = dataset == "sweetspot"
    # A compatible pattern is evidence of a limitation, not proof of an unlogged hit.
    ceiling_compatible = legacy and bool(pairs) and len(touches) == len(expected_ids) and len(hit_ids) < len(expected_ids)
    target_rows = []
    for tid in sorted(expected_ids):
        ev = [e for e in events if e["target_id"] == tid]
        has_hit = tid in hit_ids
        spatial_hit = tid in seen_spatial_targets
        status = "hit" if has_hit else "miss_recorded" if any(e["result"] == "miss" for e in ev) else "no_touch_only" if ev else "unrecorded"
        geo = geometry.get(tid)
        target_rows.append(dict(dataset=dataset, session_number=number, session_id=events[0]["session_id"], target_id=tid,
                                region=screen_region(geo["target_center_y"] / geo["screen_height"]) if geo else "unknown",
                                radius_dp=geo["target_radius_dp"] if geo else None,
                                assigned_status=status, geometry_available=tid in geometry,
                                uniquely_contained_contact=spatial_hit,
                                possible_ceiling_censoring=ceiling_compatible and not spatial_hit,
                                outcome_unknown=not spatial_hit and (ceiling_compatible or not ev)))
    summary = dict(dataset=dataset, session_number=number, session_id=events[0]["session_id"],
                   events=len(events), contacts=len(touches), hits=sum(e["result"] == "hit" for e in touches),
                   misses=sum(e["result"] == "miss" for e in touches), no_touch=len(events) - len(touches),
                   logged_targets=events[0]["configuration"]["target_count"], effective_targets=len(expected_ids),
                   target_count_source="operator" if len(expected_ids) != events[0]["configuration"]["target_count"] else "JSON",
                   target_ids_recorded=len(geometry), target_ids_without_records=len(expected_ids) - len(geometry),
                   all_expected_ids_recorded=len(geometry) == len(expected_ids),
                   assigned_targets_with_hit=len(hit_ids), unique_circles_with_contact=len(seen_spatial_targets),
                   rapid_repeat_pairs=len(pairs), rapid_repeat_second_events=len(repeat_ids),
                   app_completed_repeat_contacts=sum(c["app_target_already_completed"] for c in contacts),
                   geometric_assignment_disagreements=sum(c["assignment_disagrees"] for c in contacts),
                   legacy_ceiling_compatible=ceiling_compatible,
                   contact_span_sec=(timestamp(touches[-1]) - timestamp(touches[0])).total_seconds() if touches else None)
    # Contact-time IMU snapshots are exploratory; manual no_touch events are excluded.
    for axis in range(3):
        vals = [(e.get("imu") or {}).get("orientation_deg") for e in touches]
        vals = [v[axis] for v in vals if v is not None and len(v) == 3 and all(math.isfinite(x) for x in v)]
        mean, concentration, spread = circular_summary(vals)
        summary.update({f"imu_axis{axis}_samples": len(vals), f"imu_axis{axis}_mean_deg": mean,
                        f"imu_axis{axis}_resultant": concentration, f"imu_axis{axis}_max_deviation_deg": spread})
    for field, label in [("accelerometer_mps2", "acceleration_norm_mps2"), ("gyroscope_rad_s", "gyro_norm_rad_s")]:
        vals = [(e.get("imu") or {}).get(field) for e in touches]
        norms = [math.sqrt(sum(x*x for x in v)) for v in vals if v is not None and len(v) == 3 and all(math.isfinite(x) for x in v)]
        summary[f"median_{label}"] = float(np.median(norms)) if norms else None
    first = [c for c in contacts if c["first_contact_in_circle"]]
    summary["first_circle_contacts"] = len(first)
    summary["first_circle_mean_dx_dp"] = float(np.mean([c["geometric_dx_dp"] for c in first])) if first else None
    summary["first_circle_mean_dy_dp"] = float(np.mean([c["geometric_dy_dp"] for c in first])) if first else None
    return contacts, summary, target_rows, pairs


def tendency(contacts):
    rows = []
    for population, subset, basis in [
        ("all_assigned_contacts", contacts, "assigned"),
        ("assigned_without_rapid_repeat_second_events", [c for c in contacts if not c["rapid_repeat_candidate"]], "assigned"),
        ("assigned_without_app_completed_repeats", [c for c in contacts if not c["app_target_already_completed"]], "assigned"),
        ("assigned_without_repeat_flags", [c for c in contacts if not c["rapid_repeat_candidate"] and not c["app_target_already_completed"]], "assigned"),
        ("all_unique_circle_contacts", [c for c in contacts if c["unique_containing_target_id"]], "geometric"),
        ("first_contact_per_circle", [c for c in contacts if c["first_contact_in_circle"]], "geometric")]:
        strata = [("all", "all", subset)]
        for dimension in ("radius_dp", "color", "region"):
            for value in sorted({c[f"{basis}_{dimension}"] for c in subset}):
                strata.append((dimension, value, [c for c in subset if c[f"{basis}_{dimension}"] == value]))
        for region, radius in sorted({(c[f"{basis}_region"], c[f"{basis}_radius_dp"]) for c in subset}):
            strata.append(("region_radius_dp", f"{region}:{radius:g}",
                           [c for c in subset if c[f"{basis}_region"] == region and c[f"{basis}_radius_dp"] == radius]))
        for dimension, value, cs in strata:
            if not cs:
                continue
            dx, dy = (np.array([c[f"{basis}_{axis}_dp"] for c in cs]) for axis in ("dx", "dy"))
            radial = np.array([math.hypot(c[f"{basis}_dx_r"], c[f"{basis}_dy_r"]) for c in cs])
            session_vectors = defaultdict(list)
            for c in cs:
                session_vectors[(c["dataset"], c["session_id"])].append([c[f"{basis}_dx_dp"], c[f"{basis}_dy_dp"]])
            balanced = np.mean([np.mean(v, axis=0) for v in session_vectors.values()], axis=0)
            rows.append(dict(population=population, stratum=dimension, value=value, contacts=len(cs),
                             sessions=len(session_vectors), mean_dx_dp=float(dx.mean()), mean_dy_dp=float(dy.mean()),
                             median_dx_dp=float(np.median(dx)), median_dy_dp=float(np.median(dy)),
                             median_radial_error_dp=float(np.median(np.hypot(dx, dy))),
                             p90_radial_error_dp=float(np.percentile(np.hypot(dx, dy), 90)),
                             session_balanced_dx_dp=float(balanced[0]), session_balanced_dy_dp=float(balanced[1]),
                             median_radial_error_r=float(np.median(radial)), p90_radial_error_r=float(np.percentile(radial, 90)),
                             fraction_above_center=float(np.mean(dy < 0)), fraction_left_of_center=float(np.mean(dx < 0)),
                             upper_left_fraction=float(np.mean((dx < 0) & (dy < 0))),
                             upper_right_fraction=float(np.mean((dx > 0) & (dy < 0))),
                             lower_left_fraction=float(np.mean((dx < 0) & (dy > 0))),
                             lower_right_fraction=float(np.mean((dx > 0) & (dy > 0)))))
    return rows


def regional_outcomes(targets):
    """Target inventory denominators, with censored and unrecorded outcomes separate."""
    rows = []
    strata = [("all", "all", targets)]
    for region in (*REGIONS, "unknown"):
        strata.append(("region", region, [t for t in targets if t["region"] == region]))
    for radius in sorted({t["radius_dp"] for t in targets if t["radius_dp"] is not None}):
        strata.append(("radius_dp", radius, [t for t in targets if t["radius_dp"] == radius]))
        for region in REGIONS:
            strata.append(("region_radius_dp", f"{region}:{radius:g}",
                           [t for t in targets if t["region"] == region and t["radius_dp"] == radius]))
    for dimension, value, ts in strata:
        if not ts:
            continue
        hits = sum(t["assigned_status"] == "hit" for t in ts)
        unknown = sum(t["outcome_unknown"] for t in ts)
        misses = sum(t["assigned_status"] == "miss_recorded" and not t["outcome_unknown"] for t in ts)
        no_touch = sum(t["assigned_status"] == "no_touch_only" and not t["outcome_unknown"] for t in ts)
        assert hits + misses + no_touch + unknown == len(ts)
        rows.append(dict(stratum=dimension, value=value, targets=len(ts),
                         sessions=len({(t["dataset"], t["session_id"]) for t in ts}),
                         assigned_hit_targets=hits, assigned_miss_without_hit_targets=misses,
                         no_touch_only_targets=no_touch, unknown_outcome_targets=unknown,
                         possible_ceiling_censoring=sum(t["possible_ceiling_censoring"] for t in ts),
                         geometry_unavailable=sum(not t["geometry_available"] for t in ts),
                         observed_assigned_hit_coverage=hits / len(ts)))
    return rows


def outcome_sensitivity(sessions, contacts):
    rows = []
    for name, subset in [
        ("all_retained_sessions", sessions),
        ("all_expected_ids_recorded", [s for s in sessions if s["all_expected_ids_recorded"]]),
        ("without_ceiling_compatible_sessions", [s for s in sessions if not s["legacy_ceiling_compatible"]])]:
        ids = {(s["dataset"], s["session_id"]) for s in subset}
        cs = [c for c in contacts if (c["dataset"], c["session_id"]) in ids]
        for repeats in ("all_contacts", "without_rapid_repeat_second_events", "without_app_completed_repeats"):
            selected = [c for c in cs if (repeats != "without_rapid_repeat_second_events" or not c["rapid_repeat_candidate"])
                        and (repeats != "without_app_completed_repeats" or not c["app_target_already_completed"])]
            n = len(selected)
            hits = sum(c["app_result"] == "hit" for c in selected)
            expected = sum(s["effective_targets"] for s in subset)
            observed = sum(s["target_ids_recorded"] for s in subset)
            hit_targets = sum(s["assigned_targets_with_hit"] for s in subset)
            rows.append(dict(session_population=name, contact_population=repeats, sessions=len(subset),
                             contacts=n, hits=hits, contact_hit_fraction=hits / n if n else None,
                             assigned_hit_targets=hit_targets, expected_targets=expected, observed_targets=observed,
                             unrecorded_targets=expected-observed,
                             recorded_hit_coverage_of_expected=hit_targets / expected if expected else None,
                             hit_fraction_of_observed_targets=hit_targets / observed if observed else None))
    return rows


def save(fig, output, name):
    fig.savefig(output / "figures" / f"{name}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def analyze_regions(output, contacts, targets):
    """Use the same summaries and definitions for each condition and pooled records."""
    rows = tendency(contacts)
    outcomes = regional_outcomes(targets)
    write_csv(output / "tables/region_size_contacts.csv", [r for r in rows if r["stratum"] in ("region", "radius_dp", "region_radius_dp")])
    write_csv(output / "tables/region_size_outcomes.csv", outcomes)
    first = [c for c in contacts if c["first_contact_in_circle"]]
    conditions = sorted({c["dataset"] for c in contacts})
    colors = {"sweetspot": "#1565c0", "random_poses": "#d84315"}
    labels = {"sweetspot": "Sweet Spot", "random_poses": "Random Poses"}

    fig, axs = plt.subplots(1, 3, figsize=(14, 4.5), sharex=True, sharey=True)
    for region, ax in zip(REGIONS, axs):
        for dataset in conditions:
            cs = [c for c in first if c["geometric_region"] == region and c["dataset"] == dataset]
            if cs:
                ax.scatter([c["geometric_dx_r"] for c in cs], [c["geometric_dy_r"] for c in cs],
                           s=24, alpha=.65, color=colors[dataset], label=f"{labels[dataset]} n={len(cs)}")
        cs = [c for c in first if c["geometric_region"] == region]
        if cs:
            ax.scatter(np.median([c["geometric_dx_r"] for c in cs]), np.median([c["geometric_dy_r"] for c in cs]),
                       marker="+", s=130, color="black", label="Median offset")
        ax.add_patch(Circle((0, 0), 1, fill=False, color="black"))
        ax.axhline(0, color="gray", linewidth=.7)
        ax.axvline(0, color="gray", linewidth=.7)
        ax.set(title=f"{region.title()} third (n={len(cs)})", xlim=(-1.15, 1.15), ylim=(1.15, -1.15),
               aspect="equal", xlabel="x offset / target radius")
        ax.legend(fontsize=8)
    axs[0].set_ylabel("y offset / target radius (down)")
    fig.suptitle(f"{output.name}: first recorded contact per uniquely containing circle")
    save(fig, output, "region_tendency")

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, subset, basis, title in [
        (axs[0], contacts, "assigned", "All recorded contacts / app assignments"),
        (axs[1], first, "geometric", "First in-circle contacts / known geometry")]:
        for dataset in conditions:
            cs = [c for c in subset if c["dataset"] == dataset]
            xkey = "assigned_y_fraction" if basis == "assigned" else "target_y_fraction"
            ax.scatter([c[xkey] for c in cs], [c[f"{basis}_dy_dp"] for c in cs], s=22, alpha=.65,
                       color=colors[dataset], label=f"{labels[dataset]} n={len(cs)}")
        for border in (1/3, 2/3):
            ax.axvline(border, color="gray", linestyle="--", linewidth=.8)
        ax.axhline(0, color="black", linewidth=.8)
        ax.set(xlim=(0, 1), xlabel="Target center y / screen height (top 0 → bottom 1)",
               ylabel="Vertical offset (dp); negative = above target", title=title)
        ax.legend(fontsize=8)
    axs[0].set_yscale("symlog", linthresh=10)
    axs[0].set_title("All app assignments (symlog y; no outliers removed)")
    save(fig, output, "vertical_bias_by_height")

    radii = sorted({c["geometric_radius_dp"] for c in first})
    fig, axs = plt.subplots(1, 2, figsize=(max(10, len(radii)*1.8), 4))
    for ax, metric, title, cmap in [
        (axs[0], "median_dy_dp", "Median vertical offset (dp; negative = above)", "coolwarm"),
        (axs[1], "median_radial_error_r", "Median radial distance / radius (in-circle only)", "viridis")]:
        cells = np.full((3, len(radii)), np.nan)
        counts = {}
        for r in rows:
            if r["population"] == "first_contact_per_circle" and r["stratum"] == "region_radius_dp":
                region, radius = r["value"].split(":")
                index = REGIONS.index(region), radii.index(float(radius))
                cells[index] = r[metric]
                counts[index] = r
        scale = max(1, float(np.nanmax(np.abs(cells))))
        im = ax.imshow(np.ma.masked_invalid(cells), aspect="auto", cmap=cmap,
                       vmin=-scale if metric == "median_dy_dp" else 0,
                       vmax=scale if metric == "median_dy_dp" else 1)
        for index, r in counts.items():
            ax.text(index[1], index[0], f"{r[metric]:.2f}\nn={r['contacts']}\ns={r['sessions']}",
                    ha="center", va="center", fontsize=8, bbox=dict(facecolor="white", alpha=.8, edgecolor="none"))
        ax.set(xticks=range(len(radii)), xticklabels=[f"{r:g}" for r in radii], yticks=range(3),
               yticklabels=REGIONS, xlabel="Target radius (dp)", title=title)
        fig.colorbar(im, ax=ax, shrink=.8)
    fig.suptitle(f"{output.name}: region × size; blank = no observations, n = contacts, s = sessions")
    fig.tight_layout()
    save(fig, output, "region_by_size")

    # Include zero-hit size/region cells: they are absent from in-circle placement plots.
    outcome_radii = sorted({t["radius_dp"] for t in targets if t["radius_dp"] is not None})
    categories = [("assigned_hit_targets", "App-assigned hit", "#43a047"),
                  ("assigned_miss_without_hit_targets", "Assigned miss without hit", "#e53935"),
                  ("no_touch_only_targets", "no_touch only", "#ffb300"),
                  ("unknown_outcome_targets", "Unknown / possible censoring", "#9e9e9e")]
    fig, axs = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for region, ax in zip(REGIONS, axs):
        bottom = np.zeros(len(outcome_radii))
        cells = {r["value"]: r for r in outcomes if r["stratum"] == "region_radius_dp"}
        for key, label, color in categories:
            fractions = []
            for radius in outcome_radii:
                row = cells.get(f"{region}:{radius:g}")
                fractions.append(row[key] / row["targets"] if row else 0)
            ax.bar(range(len(outcome_radii)), fractions, bottom=bottom, color=color, label=label)
            bottom += fractions
        for i, radius in enumerate(outcome_radii):
            row = cells.get(f"{region}:{radius:g}")
            ax.text(i, 1.01, f"n={row['targets']}\ns={row['sessions']}" if row else "no data",
                    ha="center", va="bottom", fontsize=8)
        ax.set(xticks=range(len(outcome_radii)), xticklabels=[f"{r:g}" for r in outcome_radii],
               ylim=(0, 1.2), yticks=[0, .25, .5, .75, 1], title=region.title(), xlabel="Target radius (dp)")
    axs[0].set_ylabel("Fraction of target inventory")
    handles, labels_legend = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels_legend, loc="lower center", ncol=4, fontsize=8)
    fig.suptitle(f"{output.name}: app-recorded target outcomes; unknown geometry ungrouped")
    fig.tight_layout(rect=(0, .07, 1, .98))
    save(fig, output, "target_outcomes_region_by_size")

    report = f"""# {output.name}: screen region and target size

Regions are fixed thirds of **logged screen height**, assigned using the **target center**:
upper [0, 1/3), middle [1/3, 2/3), lower [2/3, 1]. They are not thirds of the app's target-placement area.
Contacts never change region merely because their touch coordinate crosses a boundary.
Offsets are in dp (not mm) and target radii; negative vertical offset means above the center.

## First contact per uniquely containing circle

This population describes recorded in-circle placement, not all intended robot attempts.
Outside contacts are kept separately in the app-assigned populations below.

| Region | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Median y (dp) | Median distance (dp) | Median distance / radius | Above center |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
"""
    for r in rows:
        if r["population"] == "first_contact_per_circle" and r["stratum"] == "region":
            report += (f"| {r['value']} | {r['contacts']} | {r['sessions']} | {r['mean_dx_dp']:+.2f} | "
                       f"{r['mean_dy_dp']:+.2f} | {r['median_dy_dp']:+.2f} | {r['median_radial_error_dp']:.2f} | "
                       f"{r['median_radial_error_r']:.3f} | {r['fraction_above_center']:.1%} |\n")
    report += """
## All app-assigned contacts (hits and misses)

| Region | Contacts | Sessions | Mean y (dp) | Median y (dp) | Median distance / radius |
|---|---:|---:|---:|---:|---:|
"""
    for r in rows:
        if r["population"] == "all_assigned_contacts" and r["stratum"] == "region":
            report += f"| {r['value']} | {r['contacts']} | {r['sessions']} | {r['mean_dy_dp']:+.2f} | {r['median_dy_dp']:+.2f} | {r['median_radial_error_r']:.3f} |\n"
    report += """
App assignments can differ from the physically containing circle after repeated touches.
`region_size_contacts.csv` includes sensitivities removing rapid-repeat second events,
explicit completed-target repeats, or either repeat flag. All original contacts remain available.

## Target outcomes by region

Each target is counted once within its original dataset/session. Unknown/censoring outcomes are kept separate.
`no_touch` is an app observation, not proof of a physical failure. Missing geometry receives region `unknown`.

| Region | Targets | App-assigned hit | Assigned miss without hit | no_touch only | Unknown/censoring |
|---|---:|---:|---:|---:|---:|
"""
    for r in outcomes:
        if r["stratum"] == "region":
            report += f"| {r['value']} | {r['targets']} | {r['assigned_hit_targets']} | {r['assigned_miss_without_hit_targets']} | {r['no_touch_only_targets']} | {r['unknown_outcome_targets']} |\n"
    report += """
## Region × size

`region_by_size.png` shows median vertical offset in dp and median radial distance divided by radius,
with contact/session counts for each combination. `region_size_outcomes.csv` provides the corresponding
target inventory. `target_outcomes_region_by_size.png` also includes combinations with zero recorded hits,
showing target-level app outcomes, no-touch observations and unknown/censoring separately.
Blank placement cells mean no in-circle observations, not zero error or zero success.
A smaller target tolerates less of the same absolute error. Compare dp offsets and normalized distances
together before interpreting any size association. In-circle distributions are boundary-truncated.
Region/size cells with few sessions are descriptive; contacts within sessions are not independent trials.
Random Poses contributes only radius 40 dp. Pooled counts reflect the observed mix of conditions,
not a balanced experiment or causal size/pose effect. The per-condition reports must accompany pooled results.
"""
    (output / "region_size_analysis.md").write_text(report, encoding="utf-8")
    return report


def plot_dataset(output, contacts, sessions, groups):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5))
    for ax, basis, subset, title in [
        (axs[0], "assigned", contacts, "All contacts / app-assigned target"),
        (axs[1], "geometric", [c for c in contacts if c["first_contact_in_circle"]], "First contact / uniquely containing circle")]:
        for color in COLORS:
            cs = [c for c in subset if c[f"{basis}_color"] == color]
            if cs:
                ax.scatter([c[f"{basis}_dx_r"] for c in cs], [c[f"{basis}_dy_r"] for c in cs],
                           color=COLORS[color], s=20, alpha=.65, label=f"{color} (n={len(cs)})")
        if subset:
            dx = np.mean([c[f"{basis}_dx_r"] for c in subset])
            dy = np.mean([c[f"{basis}_dy_r"] for c in subset])
            ax.scatter(dx, dy, color="black", marker="+", s=130, label="Mean offset")
        ax.add_patch(Circle((0, 0), 1, fill=False, color="black", linewidth=1.5))
        ax.axhline(0, color="gray", linewidth=.7)
        ax.axvline(0, color="gray", linewidth=.7)
        extent = max([1.2] + [abs(c[f"{basis}_{a}_r"]) + .1 for c in subset for a in ("dx", "dy")])
        ax.set(xlim=(-extent, extent), ylim=(extent, -extent), aspect="equal", title=title,
               xlabel="Touch x − center x / radius", ylabel="Touch y − center y / radius (down)")
        ax.legend(fontsize=8)
    fig.suptitle(f"{output.name}: target tendency (image coordinates)")
    save(fig, output, "target_tendency")

    if output.name != "random_poses":
        return  # IMU presentation is for Random Poses; reuse Sweet Spot session maps.

    fig, axs = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    for axis, ax in enumerate(axs[:3]):
        valid = [s for s in sessions if s[f"imu_axis{axis}_mean_deg"] is not None]
        ax.scatter([s["session_number"] for s in valid], [s[f"imu_axis{axis}_mean_deg"] for s in valid])
        ax.set(ylabel=f"orientation[{axis}] (deg)", ylim=(-185, 185))
    axs[0].set_title("Contact-time circular IMU means; per-axis values, not robot/world pose")
    for key, color in [("first_circle_mean_dx_dp", "#1565c0"), ("first_circle_mean_dy_dp", "#d84315")]:
        valid = [s for s in sessions if s[key] is not None]
        axs[3].plot([s["session_number"] for s in valid], [s[key] for s in valid], "o", color=color,
                    label="Mean x offset" if "dx" in key else "Mean y offset")
    axs[3].axhline(0, color="gray", linewidth=.7)
    axs[3].set(xlabel="Session number", ylabel="Mean circle offset (dp)")
    axs[3].legend(fontsize=8)
    save(fig, output, "imu_and_bias")

    fig, axs = plt.subplots(math.ceil(len(groups) / 4), 4, figsize=(13, 14), squeeze=False)
    with PdfPages(output / "maps/all_sessions.pdf") as pdf:
        for panel, (number, events) in zip(axs.flat, groups):
            individual, ax = plt.subplots(figsize=(5, 9))
            for view in (panel, ax):
                geo = {e["target_id"]: e for e in events}
                for tid, e in geo.items():
                    color = COLORS[tid.rsplit("-", 1)[-1]]
                    view.add_patch(Circle((e["target_center_x"], e["target_center_y"]), e["target_radius"], color=color, alpha=.2))
                for e in events:
                    if has_contact(e):
                        view.scatter(e["actual_touch_x"], e["actual_touch_y"], s=14,
                                     marker="x" if e["result"] == "miss" else "o", color="black")
                view.set(xlim=(0, events[0]["screen_width"]), ylim=(events[0]["screen_height"], 0), aspect="equal",
                         title=f"Session {number}: geometry {len(geo)}/{events[0]['configuration']['target_count']}")
            individual.savefig(output / "maps" / f"session_{number:02d}.png", dpi=180, bbox_inches="tight")
            pdf.savefig(individual, bbox_inches="tight")
            plt.close(individual)
        for ax in axs.flat[len(groups):]:
            ax.set_visible(False)
    fig.suptitle("Random Poses: recorded target geometry and contacts; missing targets not reconstructed")
    fig.tight_layout()
    fig.savefig(output / "maps/session_overview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def run(root=ROOT):
    reports = []
    comparisons = []
    pooled_contacts, pooled_sessions, pooled_targets = [], [], []
    for dataset in ("sweetspot", "random_poses"):
        source = next((root / "data/raw" / dataset).glob("*.jsonl"))
        raw = read_jsonl(source)
        assert len({e["event_id"] for e in raw}) == len(raw)
        if dataset == "random_poses":
            # JSON/JSONL are copies, not separate trials. CSV is retained, not appended.
            assert json.loads(source.with_suffix(".json").read_text()) == raw
        groups = defaultdict(list)
        for e in sorted(raw, key=timestamp):
            groups[e["session_id"]].append(e)
        exclusion_path = root / "data/annotations" / ("exclusions.csv" if dataset == "sweetspot" else "random_poses_exclusions.csv")
        exclusion_rows = read_csv(exclusion_path)
        exclusions = {s["session_id"] for s in exclusion_rows}
        assert exclusions <= set(groups)
        numbers = {sid: i for i, sid in enumerate(groups, 1)}
        assert all(numbers[s["session_id"]] == int(s["session_number"]) for s in exclusion_rows)
        if dataset == "random_poses":
            lines = source.read_bytes().splitlines(keepends=True)
            for folder, selected in (("excluded", True), ("processed", False)):
                path = root / "data" / folder / f"random_poses_{'excluded' if selected else 'valid'}.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"".join(line for line in lines if line.strip()
                                         and (json.loads(line)["session_id"] in exclusions) == selected))
        corrections = {s["session_id"]: s for s in read_csv(root / "data/annotations/operator_target_counts.csv")} if dataset == "sweetspot" else {}
        output = root / "results" / dataset
        for folder in ("tables", "figures", "maps"):
            (output / folder).mkdir(parents=True, exist_ok=True)
        contacts, sessions, targets, pairs, selected_groups = [], [], [], [], []
        for number, (sid, events) in enumerate(groups.items(), 1):
            if sid in exclusions:
                continue
            config = events[0]["configuration"]
            assert len({e["test_id"] for e in events}) == 1
            assert all(e["configuration"] == config for e in events)
            if sid in corrections:
                ids = set(corrections[sid]["target_ids"].split(";"))
                assert len(ids) == int(corrections[sid]["effective_target_count"])
            else:
                ids = {f"trio-{i:03d}-{color}" for i in range(1, config["rgb_trios_per_spawn"] + 1) for color in COLORS}
            cs, ss, ts, ps = analyze_session(events, number, ids, dataset)
            contacts.extend(cs)
            sessions.append(ss)
            targets.extend(ts)
            pairs.extend(ps)
            selected_groups.append((number, events))
        tendency_rows = tendency(contacts)
        sensitivity = outcome_sensitivity(sessions, contacts)
        for name, rows in [("contacts_extended", contacts), ("sessions_extended", sessions),
                           ("targets_extended", targets), ("rapid_repeat_pairs", pairs), ("target_tendency", tendency_rows),
                           ("outcome_sensitivity", sensitivity)]:
            write_csv(output / "tables" / f"{name}.csv", rows)
        plot_dataset(output, contacts, sessions, selected_groups)
        regional_report = analyze_regions(output, contacts, targets)
        pooled_contacts.extend(contacts)
        pooled_sessions.extend(sessions)
        pooled_targets.extend(targets)
        hits = sum(s["hits"] for s in sessions)
        assigned_hits = sum(s["assigned_targets_with_hit"] for s in sessions)
        n = sum(s["effective_targets"] for s in sessions)
        observed = sum(s["target_ids_recorded"] for s in sessions)
        spatial_hits = sum(s["unique_circles_with_contact"] for s in sessions)
        first = next(r for r in tendency_rows if r["population"] == "first_contact_per_circle" and r["stratum"] == "all")
        comparisons.extend(dict(dataset=dataset, **r) for r in tendency_rows
                           if r["population"] == "first_contact_per_circle" and r["stratum"] in ("all", "radius_dp"))
        flagged = [s["session_number"] for s in sessions if s["legacy_ceiling_compatible"]]
        incomplete = [s["session_number"] for s in sessions if not s["all_expected_ids_recorded"]]
        complete = next(s for s in sensitivity if s["session_population"] == "all_expected_ids_recorded" and s["contact_population"] == "all_contacts")
        report = f"""# {'Random Poses' if dataset == 'random_poses' else 'Sweet Spot'}: contact tendency and observation limitations

- Sessions analyzed: **{len(sessions)}**; recorded contacts: **{len(contacts)}**.
- Original session numbers preserved. Archived sessions: **{sorted(int(s['session_number']) for s in exclusion_rows)}**; see `data/annotations/{exclusion_path.name}`.
- App-reported hits: **{hits}/{len(contacts)} = {hits / len(contacts):.2%}**, including repeats.
- App-assigned target hit coverage: **{assigned_hits}/{n} = {assigned_hits / n:.2%}**.
- Distinct circles uniquely containing a recorded contact: **{spatial_hits}/{n}** (geometric observation, not intended-action accuracy).
- Targets with any event/geometry: **{observed}/{n}**. Sessions without all expected target IDs: **{incomplete or 'none'}**.
- Targets without any record: **{n-observed}** (unknown outcomes, not failures).
- Hit fraction among targets with a record: **{assigned_hits}/{observed} = {assigned_hits / observed:.2%}** (selection-dependent).
- Sessions with all expected IDs recorded: **{complete['sessions']}**; target coverage **{complete['assigned_hit_targets']}/{complete['expected_targets']}** (not independently verified robot completion).
- Rapid repeated-location pairs: **{len(pairs)}**; explicit app completed-target repeat contacts: **{sum(s['app_completed_repeat_contacts'] for s in sessions)}**.
- Contacts inside exactly one different circle than the app-assigned target: **{sum(s['geometric_assignment_disagreements'] for s in sessions)}**.
- Legacy count-ceiling-compatible sessions: **{flagged or 'none'}**.

## Target tendency

First recorded contact per uniquely containing circle: **{first['contacts']}** observations across **{first['sessions']}** sessions.
Mean offset: **x {first['mean_dx_dp']:+.2f} dp; y {first['mean_dy_dp']:+.2f} dp**.
Session-balanced mean: **x {first['session_balanced_dx_dp']:+.2f} dp; y {first['session_balanced_dy_dp']:+.2f} dp**.
Contacts above center: **{first['fraction_above_center']:.1%}**; left of center: **{first['fraction_left_of_center']:.1%}**.
Median radial error: **{first['median_radial_error_r']:.3f} radii**; 90th percentile: **{first['p90_radial_error_r']:.3f} radii**.

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
"""
        if dataset == "random_poses":
            report += """

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
"""
        (output / "contact_analysis.md").write_text(report, encoding="utf-8")
        manifest_paths = [source, root / "scripts/analyze_contacts.py", exclusion_path]
        if dataset == "sweetspot":
            manifest_paths.append(root / "data/annotations/operator_target_counts.csv")
        manifest = dict(dataset=dataset, input_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in manifest_paths},
                        nearby_dp=NEARBY_DP, repeat_ms=REPEAT_MS, events=sum(s["events"] for s in sessions),
                        contacts=len(contacts), sessions=len(sessions), first_circle_contacts=first["contacts"],
                        excluded_session_numbers=sorted(int(s["session_number"]) for s in exclusion_rows),
                        region_boundaries_y_fraction=[0, 1/3, 2/3, 1], region_basis="target_center",
                        python=platform.python_version(), numpy=np.__version__, matplotlib=matplotlib.__version__)
        (output / "contact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        reports.append(report + "\n" + regional_report)
        print(f"{dataset}: {len(sessions)} sessions, {len(contacts)} contacts, {first['contacts']} first-circle observations; results in {output}")
    common_radii = set.intersection(*({r["value"] for r in comparisons if r["dataset"] == dataset and r["stratum"] == "radius_dp"}
                                    for dataset in ("sweetspot", "random_poses")))
    comparison = """# Recorded contact tendency: Sweet Spot and Random Poses

First recorded contact per uniquely containing circle; conditional on recorded in-circle contact.
Offsets are in phone screen axes (x right, y down), in dp rather than physical millimeters.
Equal-session means help distinguish contact weighting from session weighting.

| Dataset | Radius (dp) | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Equal-session x (dp) | Equal-session y (dp) | Above center |
|---|---|---:|---:|---:|---:|---:|---:|---:|
"""
    for r in comparisons:
        if r["stratum"] == "all" or r["value"] in common_radii:
            comparison += (f"| {r['dataset']} | {r['value']} | {r['contacts']} | {r['sessions']} | "
                           f"{r['mean_dx_dp']:+.2f} | {r['mean_dy_dp']:+.2f} | {r['session_balanced_dx_dp']:+.2f} | "
                           f"{r['session_balanced_dy_dp']:+.2f} | {r['fraction_above_center']:.1%} |\n")
    comparison += """
Both full populations and shared target-radius strata are shown. Even at the same radius,
app behavior, holder pose, session completeness and collection conditions differ.
These samples do not establish a causal effect of robot pose or recording conditions.
The consistent tendency above center warrants checking camera-to-tip extrinsics and coordinate mapping
in a new controlled experiment; these logs alone do not identify the cause or justify automatic offset correction.

Legacy double-contact consequences are flagged in `sweetspot/contact_analysis.md`;
missing outcomes are not imputed. New repeated contacts and partial sessions remain visible in
`random_poses/contact_analysis.md`. See their sensitivity tables before quoting an accuracy percentage.
"""
    (root / "results/comparison.md").write_text(comparison, encoding="utf-8")
    output = root / "results/combined"
    for folder in ("tables", "figures"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    for name, rows in [("contacts_extended", pooled_contacts), ("sessions_extended", pooled_sessions),
                       ("targets_extended", pooled_targets), ("target_tendency", tendency(pooled_contacts)),
                       ("outcome_sensitivity", outcome_sensitivity(pooled_sessions, pooled_contacts))]:
        write_csv(output / "tables" / f"{name}.csv", rows)
    plot_dataset(output, pooled_contacts, pooled_sessions, [])
    regional_report = analyze_regions(output, pooled_contacts, pooled_targets)
    total_contacts = len(pooled_contacts)
    total_hits = sum(c["app_result"] == "hit" for c in pooled_contacts)
    summary = """# Overall recorded contacts: Sweet Spot + Random Poses

This section pools **all recorded contacts from retained sessions** in both conditions.
Archived sessions remain excluded. Source dataset, session number, UUID and event ID are kept in every row.
The pooled population reflects the recorded mix of sizes/poses; it is not a balanced experiment.

| Condition | Sessions | Events | Contacts | App hits | App misses | no_touch events | Expected targets | Targets with records |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
"""
    for dataset in ("sweetspot", "random_poses", "combined"):
        ss = [s for s in pooled_sessions if dataset == "combined" or s["dataset"] == dataset]
        summary += (f"| {dataset} | {len(ss)} | {sum(s['events'] for s in ss)} | {sum(s['contacts'] for s in ss)} | "
                    f"{sum(s['hits'] for s in ss)} | {sum(s['misses'] for s in ss)} | {sum(s['no_touch'] for s in ss)} | "
                    f"{sum(s['effective_targets'] for s in ss)} | {sum(s['target_ids_recorded'] for s in ss)} |\n")
    summary += f"""
Pooled app-recorded contact hit fraction: **{total_hits}/{total_contacts} = {total_hits / total_contacts:.2%}**, including repeats.
This is not independent robot-action accuracy. The target inventory and unknown/censoring categories remain separate.
`outcome_sensitivity.csv` and `target_tendency.csv` contain repeat-flag sensitivities and first-per-circle placement.
The latter is conditional on in-circle recording, while all assigned contacts retain outside contacts and assignment artifacts.
Contacts and sessions are not deduplicated across conditions; dataset/session identity prevents target-ID collisions.
All results remain descriptive. Per-condition analyses should accompany any pooled percentage.
"""
    (output / "summary.md").write_text(summary + "\n" + regional_report, encoding="utf-8")
    manifests = [json.loads((root / f"results/{ds}/contact_manifest.json").read_text()) for ds in ("sweetspot", "random_poses")]
    manifest = dict(dataset="combined", source_datasets=[m["dataset"] for m in manifests],
                    input_sha256={k: v for m in manifests for k, v in m["input_sha256"].items()},
                    events=sum(s["events"] for s in pooled_sessions), contacts=total_contacts,
                    sessions=len(pooled_sessions), first_circle_contacts=sum(c["first_contact_in_circle"] for c in pooled_contacts),
                    archived_sessions_excluded=True, region_boundaries_y_fraction=[0, 1/3, 2/3, 1],
                    region_basis="target_center", python=platform.python_version(),
                    numpy=np.__version__, matplotlib=matplotlib.__version__)
    (output / "contact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    reports.append(summary + "\n" + regional_report)
    print(f"combined: {len(pooled_sessions)} sessions, {total_contacts} recorded contacts; results in {output}")
    return reports


if __name__ == "__main__":
    run()
