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
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NEARBY_DP = 8
REPEAT_MS = 300
COLORS = {"red": "#e53935", "green": "#43a047", "blue": "#1e88e5"}
REGIONS = ("upper", "middle", "lower")
DATASETS = ("sweetspot", "random_poses", "horizontal_tests")
DATASET_LABELS = {"sweetspot": "Sweet Spot", "random_poses": "Random Poses",
                  "horizontal_tests": "Horizontal Tests", "combined": "Sweet Spot + Random Poses + Horizontal Tests"}
DATASET_COLORS = {"sweetspot": "#1565c0", "random_poses": "#d84315", "horizontal_tests": "#00796b"}
PLACEMENT_NOTE = ("One point per uniquely matched target: its first recorded in-target touch.\n"
                  "Outside / ambiguous contacts and extra touches excluded; this is placement, not success rate.")


def screen_region(y_fraction):
    """Fixed thirds of the logged screen; classify by target center, not touch."""
    if not math.isfinite(y_fraction) or not 0 <= y_fraction <= 1:
        raise ValueError("Target center must be within the logged screen height")
    return REGIONS[min(int(y_fraction * 3), 2)]


def phone_view_offset(dataset, dx, dy):
    """Operator-confirmed horizontal mounting: phone top points left, viewed from the front."""
    return (dy, -dx) if dataset == "horizontal_tests" else (dx, dy)


def plot_region_tendency(output, first):
    """Arrange each phone's thirds in its displayed orientation, with matching offset axes."""
    conditions = [dataset for dataset in DATASETS if any(c["dataset"] == dataset for c in first)]
    combined = output.name == "combined"
    horizontal = output.name == "horizontal_tests"
    if combined:
        fig = plt.figure(figsize=(10, 14))
        grid = fig.add_gridspec(4, 6, hspace=.85, wspace=.8)
        panels = [(dataset, region, fig.add_subplot(grid[row, col*3:(col+1)*3]))
                  for col, dataset in enumerate(("sweetspot", "random_poses"))
                  for row, region in enumerate(REGIONS)]
        panels += [("horizontal_tests", region, fig.add_subplot(grid[3, col*2:(col+1)*2]))
                   for col, region in enumerate(REGIONS)]
    else:
        fig, axs = plt.subplots(1 if horizontal else 3, 3 if horizontal else 1,
                                figsize=(12, 5.5) if horizontal else (6.5, 12))
        panels = [(conditions[0], region, ax) for region, ax in zip(REGIONS, np.ravel(axs))]
    view_rows = []
    horizontal_labels = {"upper": "Left (phone top)", "middle": "Center", "lower": "Right (phone bottom)"}
    for dataset, region, ax in panels:
        cs = [c for c in first if c["dataset"] == dataset and c["geometric_region"] == region]
        is_horizontal = dataset == "horizontal_tests"
        label = horizontal_labels[region] if is_horizontal else f"{region.title()} (phone {'top' if region == 'upper' else 'bottom' if region == 'lower' else 'center'})"
        if cs:
            dx, dy = phone_view_offset(dataset, np.array([c["geometric_dx_r"] for c in cs]),
                                      np.array([c["geometric_dy_r"] for c in cs]))
            ax.scatter(dx, dy, color=DATASET_COLORS[dataset], s=23, alpha=.7)
            ax.scatter(np.median(dx), np.median(dy), color="black", marker="+", s=110)
            dx_dp, dy_dp = phone_view_offset(dataset, np.array([c["geometric_dx_dp"] for c in cs]),
                                            np.array([c["geometric_dy_dp"] for c in cs]))
            view_rows.append(dict(dataset=dataset, app_region=region, viewer_region=label,
                                  phone_top_direction="left" if is_horizontal else "up",
                                  contacts=len(cs), sessions=len({c["session_id"] for c in cs}),
                                  mean_view_dx_dp=float(np.mean(dx_dp)), mean_view_dy_dp=float(np.mean(dy_dp)),
                                  median_view_dx_dp=float(np.median(dx_dp)), median_view_dy_dp=float(np.median(dy_dp)),
                                  median_view_dx_r=float(np.median(dx)), median_view_dy_r=float(np.median(dy)),
                                  median_radial_error_dp=float(np.median(np.hypot(dx_dp, dy_dp)))))
        ax.add_patch(Circle((0, 0), 1, fill=False, color="black"))
        ax.axhline(0, color="gray", linewidth=.7)
        ax.axvline(0, color="gray", linewidth=.7)
        ax.set(xlim=(-1.15, 1.15), ylim=(1.15, -1.15), aspect="equal",
               xticks=[-1, 0, 1], yticks=[-1, 0, 1],
               title=f"{DATASET_LABELS[dataset]}\n{label}: {len(cs)} touches")
        ax.title.set_fontsize(10)
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.tick_params(labelsize=8)
    write_csv(output / "tables/region_tendency_view.csv", view_rows)
    fig.subplots_adjust(left=.11, right=.98, top=.78 if horizontal else .89,
                        bottom=.17 if horizontal else .11)
    fig.supxlabel("Viewer left ← touch offset (% of target radius) → Viewer right", fontsize=10,
                  y=.1 if horizontal else .055)
    fig.supylabel("Viewer above ← touch offset (% of target radius) → Viewer below", fontsize=10, x=.025)
    heading = fig.suptitle("Where do contacts land?\n" +
                 ("Horizontal Tests — phone top points LEFT" if horizontal else
                  "Phone top points UP in Sweet Spot / Random Poses; LEFT in Horizontal Tests" if combined else
                  f"{DATASET_LABELS[output.name]} — phone top points UP"), fontsize=12, y=.98)
    note = (PLACEMENT_NOTE + "\nCircle = target edge; crosshair = target center; black + = median in each panel.\n"
            "Horizontal view: (dx, dy) = (app dy, -app dx). This is a phone-plane view, not robot/world coordinates.")
    if combined:
        # The article supplies its own caption; retain the same panels and transformed data.
        fig.supxlabel("")
        fig.supylabel("")
        heading.set_text("")
        fig.set_size_inches(7, 10)
        fig.savefig(output / "figures/region_tendency_article.png", dpi=300, bbox_inches="tight",
                    metadata={"Description": note + " Blue: Sweet Spot; orange: Random Poses; teal: Horizontal Tests."})
        fig.set_size_inches(10, 14)
        fig.supxlabel("Viewer left ← touch offset (% of target radius) → Viewer right", fontsize=10, y=.055)
        fig.supylabel("Viewer above ← touch offset (% of target radius) → Viewer below", fontsize=10, x=.025)
        fig.suptitle("Where do contacts land?\nPhone top points UP in Sweet Spot / Random Poses; LEFT in Horizontal Tests",
                     fontsize=12, y=.98)
    save(fig, output, "region_tendency", note)


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


def save(fig, output, name, caption=""):
    mode = output.parent.name
    if mode in ("with_double_touches", "without_double_touches"):
        rule = ("Every contact counted separately, including repeats." if mode == "with_double_touches" else
                "One outcome per session/target: any hit = hit; only misses = miss.")
        caption = rule + "\n" + caption
    if caption:
        fig.text(.5, -.015, caption, ha="center", va="top", fontsize=9, linespacing=1.5)
    fig.savefig(output / "figures" / f"{name}.png", dpi=180, bbox_inches="tight", metadata={"Description": caption})
    plt.close(fig)


def analyze_regions(output, contacts, targets, placement_contacts=None):
    """Use the same summaries and definitions for each condition and pooled records."""
    rows = tendency(contacts)
    if placement_contacts is not None:
        # Placement already uses one contact per geometric circle, independently of app-outcome grouping.
        rows = [r for r in rows if r["population"] != "first_contact_per_circle"] + [
            r for r in tendency(placement_contacts) if r["population"] == "first_contact_per_circle"]
    outcomes = regional_outcomes(targets)
    write_csv(output / "tables/region_size_contacts.csv", [r for r in rows if r["stratum"] in ("region", "radius_dp", "region_radius_dp")])
    write_csv(output / "tables/region_size_outcomes.csv", outcomes)
    first = [c for c in (contacts if placement_contacts is None else placement_contacts) if c["first_contact_in_circle"]]
    conditions = sorted({c["dataset"] for c in contacts})
    title = DATASET_LABELS[output.name]

    plot_region_tendency(output, first)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for dataset in conditions:
        cs = [c for c in first if c["dataset"] == dataset]
        ax.scatter([c["target_y_fraction"] for c in cs], [c["geometric_dy_dp"] for c in cs], s=28, alpha=.7,
                   color=DATASET_COLORS[dataset], label=f"{DATASET_LABELS[dataset]}: {len(cs)} touches")
    for border in (1/3, 2/3):
        ax.axvline(border, color="gray", linestyle="--", linewidth=.8)
    for position, label in zip((1/6, .5, 5/6), ("Phone-top third", "Middle third", "Phone-bottom third")):
        ax.text(position, .98, label, ha="center", va="top", transform=ax.get_xaxis_transform(), fontsize=9)
    ax.axhline(0, color="black", linewidth=.8, label="Target center (zero offset)")
    ax.set(xlim=(0, 1), xlabel="Target position along app y (0% = phone top; 100% = phone bottom)",
           ylabel="App-y touch offset (dp)\nNegative = toward phone top; positive = toward phone bottom",
           title=f"{title}\nDoes the offset along app y change with target position?")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(fontsize=9, loc="upper left", bbox_to_anchor=(0, -.18), ncol=2)
    fig.tight_layout()
    save(fig, output, "vertical_bias_by_height", PLACEMENT_NOTE +
         "\nApp y points DOWN in the upright view, but RIGHT in Horizontal Tests (phone top pointing left).\n"
         "This plot compares phone/app axes, not a shared viewer-vertical error. dp = display units, not millimeters.")

    radii = sorted({t["radius_dp"] for t in targets if t["radius_dp"] is not None})
    outcome_cells = {r["value"]: r for r in outcomes if r["stratum"] == "region_radius_dp"}
    fig, axs = plt.subplots(2, 1, figsize=(max(8, len(radii)*1.55), 10))
    for ax, metric, panel_title, cmap in [
        (axs[0], "median_dy_dp", "Typical vertical offset (median, dp)", "coolwarm"),
        (axs[1], "median_radial_error_r", "Typical distance from center (median, % of target radius)", "viridis")]:
        cells = np.full((3, len(radii)), np.nan)
        counts = {}
        for r in rows:
            if r["population"] == "first_contact_per_circle" and r["stratum"] == "region_radius_dp":
                region, radius = r["value"].split(":")
                index = REGIONS.index(region), radii.index(float(radius))
                cells[index] = r[metric] * (100 if metric == "median_radial_error_r" else 1)
                counts[index] = r
        valid = cells[np.isfinite(cells)]
        scale = max([1, *np.abs(valid)])
        im = ax.imshow(np.ma.masked_invalid(cells), aspect="auto", cmap=cmap,
                       vmin=-scale if metric == "median_dy_dp" else 0,
                       vmax=scale if metric == "median_dy_dp" else 100)
        for index, r in counts.items():
            value = f"{r[metric]:+.1f} dp" if metric == "median_dy_dp" else f"{r[metric]:.0%} of radius"
            ax.text(index[1], index[0], f"{value}\nTouches: {r['contacts']}\nSessions: {r['sessions']}",
                    ha="center", va="center", fontsize=8, bbox=dict(facecolor="white", alpha=.8, edgecolor="none"))
        for i, region in enumerate(REGIONS):
            for j, radius in enumerate(radii):
                if (i, j) in counts:
                    continue
                row = outcome_cells.get(f"{region}:{radius:g}")
                text = "No targets\nwith known\nposition" if not row else f"0 matched inside\nTargets: {row['targets']}"
                if row:
                    for key, label in (("assigned_hit_targets", "app hits"),
                                       ("assigned_miss_without_hit_targets", "app misses"),
                                       ("no_touch_only_targets", "no-touch only"), ("unknown_outcome_targets", "unknown")):
                        if row[key]:
                            text += f"\n{row[key]} {label}"
                ax.text(j, i, text, ha="center", va="center", fontsize=8)
        ax.set(xticks=range(len(radii)), xticklabels=[f"{r:g}" for r in radii], yticks=range(3),
               yticklabels=[f"{r.title()} third" for r in REGIONS], xlabel="Target radius (dp)", title=panel_title)
        bar = fig.colorbar(im, ax=ax, shrink=.85)
        if metric == "median_dy_dp":
            bar.set_label("Negative = above; positive = below", fontsize=9)
        else:
            bar.set_ticks([0, 25, 50, 75, 100])
            bar.set_ticklabels(["0% (center)", "25%", "50%", "75%", "100% (edge)"])
    fig.suptitle(f"{title}\nHow do screen region and target size relate to touch placement?", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .94), h_pad=3)
    save(fig, output, "region_by_size", PLACEMENT_NOTE +
         "\nWhite cells have no in-target sample—not zero error. Counts show the available records. dp is not mm.")

    # Include zero-hit size/region cells: they are absent from in-circle placement plots.
    outcome_radii = sorted({t["radius_dp"] for t in targets if t["radius_dp"] is not None})
    categories = [("assigned_hit_targets", "Hit recorded", "#43a047"),
                  ("assigned_miss_without_hit_targets", "Miss recorded; no hit", "#e53935"),
                  ("no_touch_only_targets", "No-touch records only", "#ffb300"),
                  ("unknown_outcome_targets", "Outcome unknown", "#9e9e9e")]
    fig, axs = plt.subplots(3, 1, figsize=(6.5, 12), sharex=True, sharey=True)
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
            ax.text(i, 1.01, f"Targets: {row['targets']}\nSessions: {row['sessions']}" if row else "No targets",
                    ha="center", va="bottom", fontsize=8)
        ax.set(xticks=range(len(outcome_radii)), xticklabels=[f"{r:g}" for r in outcome_radii],
               ylim=(0, 1.2), yticks=[0, .25, .5, .75, 1], title=f"{region.title()} screen third")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
    axs[-1].set_xlabel("Target radius (dp)")
    fig.supylabel("Percentage of targets")
    handles, labels_legend = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels_legend, loc="lower center", bbox_to_anchor=(.5, .05), ncol=2, fontsize=8)
    fig.suptitle(f"{title}\nWhat did the app record for each target?", fontsize=13)
    fig.tight_layout(rect=(.02, .12, 1, .95))
    missing = sum(not t["geometry_available"] for t in targets)
    save(fig, output, "target_outcomes_region_by_size",
         "Each target counted once; outcomes follow app labels, not the robot's intended target.\n"
         "No-touch = records without contact coordinates; unknown = missing records / possible app-limit effects.\n"
         f"{missing} targets without known screen position omitted. dp = display units, not millimeters.")

    report = f"""# {output.name}: screen region and target size

Regions are fixed thirds of **logged screen height**, assigned using the **target center**:
upper [0, 1/3), middle [1/3, 2/3), lower [2/3, 1]. They are not thirds of the app's target-placement area.
Contacts never change region merely because their touch coordinate crosses a boundary.
The tables below retain phone/app axes: offsets are in dp (not mm) and target radii;
negative app-y offset means toward the phone's original top edge.

## Region tendency in the displayed phone orientation

`region_tendency.png` shows each condition separately in the phone-plane view.
Sweet Spot and Random Poses thirds run top to bottom. Horizontal Tests has the phone's top
pointing left, as confirmed by the operator: its app upper/middle/lower thirds are displayed
left/center/right. Both the panel placement and touch offsets are rotated: view dx = app dy,
view dy = -app dx. Positive view x points right; positive view y points down.
These are display directions, not calibrated robot/world axes.
`region_tendency_view.csv` records the transformed regional summaries in dp and target radii.
All other tables and figures retain the original app axes, making their coordinate basis explicit.

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
White placement cells are explicitly labeled with available target outcomes; they are not zero error.
The main placement plots show only first in-circle contacts. `app_assignment_diagnostics.png`
keeps all app-assigned contacts, including misses and repeats, with no outliers removed.
A smaller target tolerates less of the same absolute error. Compare dp offsets and normalized distances
together before interpreting any size association. In-circle distributions are boundary-truncated.
Region/size cells with few sessions are descriptive; contacts within sessions are not independent trials.
Random Poses contributes only radius 40 dp. Pooled counts reflect the observed mix of conditions,
not a balanced experiment or causal size/pose effect. The per-condition reports must accompany pooled results.
"""
    (output / "region_size_analysis.md").write_text(report, encoding="utf-8")
    return report


def plot_dataset(output, contacts, sessions, groups, placement_contacts=None, contact_event_ids=None):
    title = DATASET_LABELS[output.name]
    first = [c for c in (contacts if placement_contacts is None else placement_contacts) if c["first_contact_in_circle"]]
    conditions = sorted({c["dataset"] for c in contacts})
    fig, ax = plt.subplots(figsize=(7, 7.5))
    for dataset in conditions:
        cs = [c for c in first if c["dataset"] == dataset]
        ax.scatter([c["geometric_dx_r"] for c in cs], [c["geometric_dy_r"] for c in cs],
                   color=DATASET_COLORS[dataset], s=28, alpha=.7,
                   label=f"{DATASET_LABELS[dataset]}: {len(cs)} touches")
    if first:
        ax.scatter(np.mean([c["geometric_dx_r"] for c in first]), np.mean([c["geometric_dy_r"] for c in first]),
                   color="black", marker="+", s=130, label="Average touch position")
    ax.add_patch(Circle((0, 0), 1, fill=False, color="black", linewidth=1.5))
    ax.axhline(0, color="gray", linewidth=.7)
    ax.axvline(0, color="gray", linewidth=.7)
    ax.set(xlim=(-1.15, 1.15), ylim=(1.15, -1.15), aspect="equal",
           xticks=[-1, -.5, 0, .5, 1], yticks=[-1, -.5, 0, .5, 1],
           xlabel="Left ← horizontal offset (% of target radius) → Right",
           ylabel="Above ← vertical offset (% of target radius) → Below")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    fig.suptitle(f"{title}\nWhere do touches land inside the target?", fontsize=13)
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], marker="o", markerfacecolor="none", markeredgecolor="black", linestyle="none", markersize=10))
    labels.append("Target edge")
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .04), ncol=2, fontsize=9)
    fig.tight_layout(rect=(0, .17, 1, .92))
    save(fig, output, "target_tendency", PLACEMENT_NOTE +
         "\nCrosshair = target center; 100% of the radius = one center-to-edge distance.")

    # Keep app-label outliers visible, without compressing the main placement plots.
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
    for dataset in conditions:
        cs = [c for c in contacts if c["dataset"] == dataset]
        label = f"{DATASET_LABELS[dataset]}: {len(cs)} touches"
        axs[0].scatter([c["assigned_dx_r"] for c in cs], [c["assigned_dy_r"] for c in cs],
                       color=DATASET_COLORS[dataset], s=24, alpha=.7, label=label)
        axs[1].scatter([c["assigned_y_fraction"] for c in cs], [c["assigned_dy_dp"] for c in cs],
                       color=DATASET_COLORS[dataset], s=24, alpha=.7, label=label)
    axs[0].add_patch(Circle((0, 0), 1, fill=False, color="black", label="App-assigned target edge"))
    extent = max([1.2] + [abs(c[f"assigned_{a}_r"]) + .1 for c in contacts for a in ("dx", "dy")])
    axs[0].set(xlim=(-extent, extent), ylim=(extent, -extent), aspect="equal",
               xlabel="Horizontal offset (target radii)", ylabel="Vertical offset (target radii; down)",
               title="Touch location relative to the app's target")
    axs[0].axvline(0, color="gray", linewidth=.7)
    axs[1].set(xlim=(0, 1), xlabel="App target position (0% = top; 100% = bottom)",
               ylabel="Vertical offset (dp; negative = above)", title="All offsets; large values compressed")
    axs[1].xaxis.set_major_formatter(PercentFormatter(1))
    axs[1].set_yscale("symlog", linthresh=10)
    for ax in axs:
        ax.axhline(0, color="gray", linewidth=.7)
        ax.legend(fontsize=8)
    diagnostic = ("one representative contact per session/target" if output.parent.name == "without_double_touches"
                  else "all contacts, including misses and repeats")
    fig.suptitle(f"{title}\nApp-label diagnostics: {diagnostic}", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .93))
    save(fig, output, "app_assignment_diagnostics",
         "App labels may associate a repeat touch with a different target; they do not prove robot intent.\n"
         "Right panel has a nonlinear vertical scale; no outliers removed. dp = display units, not millimeters.")

    if output.name not in ("random_poses", "horizontal_tests") and contact_event_ids is None:
        return  # Reuse the baseline Sweet Spot session maps.
    if output.name == "combined":
        return

    if output.name in ("random_poses", "horizontal_tests"):
        fig, axs = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        for axis, ax in enumerate(axs):
            valid = [s for s in sessions if s[f"imu_axis{axis}_mean_deg"] is not None]
            ax.scatter([s["session_number"] for s in valid], [s[f"imu_axis{axis}_mean_deg"] for s in valid])
            ax.set(ylabel="Mean angle (degrees)", ylim=(-185, 185), yticks=[-180, -90, 0, 90, 180],
                   title=f"Phone sensor component {axis} — {len(valid)} sessions with readings")
            ax.axhline(0, color="gray", linewidth=.7)
        axs[-1].set(xlabel="Original session number", xticks=[s["session_number"] for s in sessions])
        fig.suptitle(f"{title}\nHow did phone orientation vary between sessions?", fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, .93), h_pad=2)
        save(fig, output, "phone_orientation_by_session",
             "Each point = circular mean of phone IMU angles at recorded contacts in one retained session.\n"
             "Exporter components are unverified—not calibrated robot roll, pitch or yaw.\n"
             "This plot does not establish an effect on accuracy; session selection is documented in the report.")

    map_rows = math.ceil(len(groups) / 4)
    fig, axs = plt.subplots(map_rows, 4, figsize=(13, max(8, map_rows * 3.8)), squeeze=False)
    with PdfPages(output / "maps/all_sessions.pdf") as pdf:
        for panel, (number, events) in zip(axs.flat, groups):
            individual, ax = plt.subplots(figsize=(5, 9))
            for view in (panel, ax):
                geo = {e["target_id"]: e for e in events}
                for tid, e in geo.items():
                    color = COLORS[tid.rsplit("-", 1)[-1]]
                    view.add_patch(Circle((e["target_center_x"], e["target_center_y"]), e["target_radius"], color=color, alpha=.2))
                    if output.name == "horizontal_tests":
                        view.text(e["target_center_x"], e["target_center_y"], tid.split("-")[1].lstrip("0"),
                                  ha="center", va="center", fontsize=6, color="dimgray")
                        ev = [r for r in events if r["target_id"] == tid]
                        if all(not has_contact(r) for r in ev):
                            view.scatter(e["target_center_x"], e["target_center_y"], s=35,
                                         marker="s", facecolors="none", edgecolors="#b77900")
                for e in events:
                    if has_contact(e) and (contact_event_ids is None or e["event_id"] in contact_event_ids):
                        view.scatter(e["actual_touch_x"], e["actual_touch_y"], s=14,
                                     marker="x" if e["result"] == "miss" else "o", color="black")
                        if output.name == "horizontal_tests" and e.get("target_already_completed"):
                            view.scatter(e["actual_touch_x"], e["actual_touch_y"], s=55,
                                         marker="o", facecolors="none", edgecolors="#8e24aa")
                view.set(xlim=(0, events[0]["screen_width"]), ylim=(events[0]["screen_height"], 0), aspect="equal",
                         title=f"Session {number}: {len(geo)}/{events[0]['configuration']['target_count']} targets located")
            ax.set(xlabel="Screen x (pixels; left → right)", ylabel="Screen y (pixels; top → bottom)")
            individual.suptitle(f"{title} — session {number}", fontsize=13)
            map_note = "Colored circles = targets; dots = app hits; crosses = app misses.\n"
            if output.name == "horizontal_tests":
                shown = [e for e in events if has_contact(e) and (contact_event_ids is None or e["event_id"] in contact_event_ids)]
                count = len(shown)
                hits = sum(e["result"] == "hit" for e in shown)
                label = "Contacts" if contact_event_ids is None else "Shown contacts"
                map_note += (f"{label}: {count} ({hits} hits); no-touch records: {sum(not has_contact(e) for e in events)}.\n"
                             "Hollow square = no-touch only; purple ring = completed-target repeat.\n")
            map_note += "Only recorded positions shown; missing targets not reconstructed."
            if output.parent.name == "without_double_touches":
                map_note += "\nOne marker per session/target: first hit, otherwise first miss."
            individual.text(.5, .015, map_note, ha="center", fontsize=8)
            individual.tight_layout(rect=(0, .12, 1, .94))
            individual.savefig(output / "maps" / f"session_{number:02d}.png", dpi=180, bbox_inches="tight")
            pdf.savefig(individual, bbox_inches="tight")
            plt.close(individual)
        for ax in axs.flat[len(groups):]:
            ax.set_visible(False)
    fig.suptitle(f"{title}: where were targets and touches recorded?", fontsize=13)
    fig.text(.5, .01, ("One marker per session/target: first hit, otherwise first miss.\n" if output.parent.name == "without_double_touches" else "") +
             "Colored circles = targets; dots = app hits; crosses = app misses.\n"
             "Screen coordinates in pixels: top-left origin. Only retained sessions; missing targets not reconstructed.",
             ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .05, 1, .96))
    fig.savefig(output / "maps/session_overview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def horizontal_summary(output, contacts, sessions, targets, groups, exclusions):
    """Describe the retained population and keep operator exclusions traceable."""
    review = []
    for s, (number, events) in zip(sessions, groups):
        assert s["session_number"] == number
        review.append(dict(session_number=number, session_id=s["session_id"],
                           first_event_utc=events[0]["date_time"], last_event_utc=events[-1]["date_time"],
                           radius_dp=events[0]["target_radius_dp"], contacts=s["contacts"],
                           hits=s["hits"], misses=s["misses"], no_touch=s["no_touch"],
                           targets_with_records=s["target_ids_recorded"], configured_targets=s["effective_targets"],
                           all_target_ids_recorded=s["all_expected_ids_recorded"],
                           completed_target_repeat_contacts=s["app_completed_repeat_contacts"],
                           map=f"maps/session_{number:02d}.png"))
    write_csv(output / "tables/session_review.csv", review)
    review_text = ("# Horizontal Tests: retained sessions and archived maps\n\n"
                   f"Retained sessions: {len(sessions)}; operator-requested exclusions: {len(exclusions)}. "
                   "Original session numbering is preserved. Full-ID means every configured target has an event, "
                   "not independently confirmed robot completion. Timestamps below follow the export's UTC labels.\n\n"
                   "Maps use the logged app axes (1080 × 2179 px, x right, y down), even though the holder is horizontal. "
                   "Dots = app hits; crosses = app misses; hollow squares = targets with only no-touch records; "
                   "purple rings = completed-target repeats. Unlogged target positions cannot be drawn.\n\n"
                   "| Session / map | First event (UTC) | Radius (dp) | Contacts | Hits | Misses | no_touch | Targets with records | Full-ID |\n"
                   "|---|---|---:|---:|---:|---:|---:|---:|---|\n")
    for r in review:
        review_text += (f"| [{r['session_number']:02d}]({r['map']}) | {r['first_event_utc']} | {r['radius_dp']:g} | "
                        f"{r['contacts']} | {r['hits']} | {r['misses']} | {r['no_touch']} | "
                        f"{r['targets_with_records']}/{r['configured_targets']} | "
                        f"{'yes' if r['all_target_ids_recorded'] else 'review: partial IDs'} |\n")
    if exclusions:
        review_text += "\n## Archived sessions\n\nOriginal events remain in `data/excluded/horizontal_tests_excluded.jsonl`.\n\n"
        for r in exclusions:
            number = int(r["session_number"])
            review_text += f"- [Session {number:02d}](maps/excluded/session_{number:02d}.png): {r['reason']}.\n"
    (output / "session_review.md").write_text(review_text, encoding="utf-8")

    sizes = sorted({r["radius_dp"] for r in review})
    size_rows = []
    for population in ("all_sessions", "all_expected_ids_recorded"):
        for radius in sizes:
            selected = [r for r in review if r["radius_dp"] == radius and
                        (population == "all_sessions" or r["all_target_ids_recorded"])]
            ids = {r["session_id"] for r in selected}
            cs = [c for c in contacts if c["session_id"] in ids]
            ts = [t for t in targets if t["session_id"] in ids]
            hits = sum(c["app_result"] == "hit" for c in cs)
            first = [c for c in cs if c["first_contact_in_circle"]]
            size_rows.append(dict(session_population=population, radius_dp=radius, sessions=len(selected),
                                  contacts=len(cs), hits=hits, misses=len(cs)-hits,
                                  contact_hit_fraction=hits / len(cs) if cs else None,
                                  configured_targets=len(ts), hit_targets=sum(t["assigned_status"] == "hit" for t in ts),
                                  no_touch_only_targets=sum(t["assigned_status"] == "no_touch_only" for t in ts),
                                  targets_without_records=sum(not t["geometry_available"] for t in ts),
                                  first_circle_contacts=len(first),
                                  median_first_circle_error_dp=float(np.median([
                                      math.hypot(c["geometric_dx_dp"], c["geometric_dy_dp"]) for c in first])) if first else None))
    write_csv(output / "tables/outcomes_by_size.csv", size_rows)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    populations = [("all_sessions", "Retained sessions", "#00796b")]
    if not all(r["all_target_ids_recorded"] for r in review):
        populations.append(("all_expected_ids_recorded", "Sessions with all target IDs recorded", "#80cbc4"))
    width = .65 if len(populations) == 1 else .38
    for index, (population, label, color) in enumerate(populations):
        rows = [r for r in size_rows if r["session_population"] == population]
        bars = ax.bar(np.arange(len(sizes)) + (index-(len(populations)-1)/2)*width,
                      [100*r["contact_hit_fraction"] if r["contact_hit_fraction"] is not None else 0 for r in rows],
                      width=width, label=label, color=color)
        for bar, r in zip(bars, rows):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2, f"{r['hits']}/{r['contacts']}",
                    ha="center", va="bottom", fontsize=9)
    ax.set(xticks=range(len(sizes)), xticklabels=[f"{r:g}" for r in sizes], ylim=(0, 115),
           yticks=[0, 25, 50, 75, 100], xlabel="Target radius (dp)", ylabel="Recorded contacts classified as hits (%)",
           title="Horizontal Tests\nHow does recorded contact success vary with target size?")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.16), fontsize=9)
    fig.tight_layout()
    save(fig, output, "outcomes_by_size", "Labels = hits / recorded contacts; repeats included. no-touch records are not contacts.\n"
         "Full target-ID coverage does not prove completion. Contacts within sessions are not independent; dp is not mm.")

    full = next(r for r in outcome_sensitivity(sessions, contacts)
                if r["session_population"] == "all_expected_ids_recorded" and r["contact_population"] == "all_contacts")
    report = ("# Horizontal Tests — results from 13 October 2026\n\n"
              f"The source contains RGB circles only, not CAPTCHA. There are {len(sessions)} retained sessions; "
              f"{len(exclusions)} sessions were archived at the operator's request. "
              "Original numbering and raw events are preserved. Horizontal mounting is an operator annotation, "
              "not inferred from the app's random-target setting or screen dimensions.\n\n"
              "[Review each session and its map](session_review.md) · [Map overview](maps/session_overview.png) · "
              "[All session maps, one PDF](maps/all_sessions.pdf)\n\n"
              f"The {full['sessions']} full-ID sessions contain {full['hits']}/{full['contacts']} app-hit contacts "
              f"({full['contact_hit_fraction']:.2%}, including repeats) and hits on "
              f"{full['assigned_hit_targets']}/{full['expected_targets']} distinct configured targets "
              f"({full['recorded_hit_coverage_of_expected']:.2%}). These use different denominators.\n\n"
              "## Target size and contact outcomes\n\n"
              "Full-ID sessions have records for every configured target; this is a sensitivity subset, not a validated completion label. "
              "Each cell shows hits / recorded contacts, including repeat touches.\n\n"
              "| Radius (dp) | Sessions (all / full-ID) | All sessions | Full-ID sessions | Unrecorded targets (all sessions) |\n"
              "|---|---:|---:|---:|---:|\n")
    for a, b in zip(size_rows[:len(sizes)], size_rows[len(sizes):]):
        rate = lambda r: f"{r['hits']}/{r['contacts']} ({r['contact_hit_fraction']:.1%})" if r["contacts"] else "no contacts"
        report += (f"| {a['radius_dp']:g} | {a['sessions']} / {b['sessions']} | {rate(a)} | {rate(b)} | "
                   f"{a['targets_without_records']} |\n")
    report += ("\nSmall-target samples are limited and target counts/collection conditions differ. "
               "The 15 dp radius occurs in one session; these data do not isolate a causal size or orientation effect. "
               "Unrecorded targets and no-touch entries are not automatically classified as robot misses.\n\n"
               "## Contact placement across the screen\n\n"
               "These are first recorded in-target contacts, one per uniquely containing circle. "
               "They describe placement conditional on a recorded in-circle contact.\n\n"
               "| App screen third | Contacts | Mean x (dp) | Mean y (dp) | Median distance from center (dp) |\n"
               "|---|---:|---:|---:|---:|\n")
    for region in REGIONS:
        row = next((r for r in tendency(contacts) if r["population"] == "first_contact_per_circle"
                    and r["stratum"] == "region" and r["value"] == region), None)
        if row:
            report += (f"| {region.title()} | {row['contacts']} | {row['mean_dx_dp']:+.2f} | "
                       f"{row['mean_dy_dp']:+.2f} | {row['median_radial_error_dp']:.2f} |\n")
    report += ("\nThe aggregate mean can conceal opposing regional offsets. A single constant translation cannot "
               "fully cancel a position-dependent pattern; these observations alone do not identify its calibration or mapping cause.\n\n"
               "## Region tendency as seen from the front\n\n"
               "The operator confirmed that the phone's top pointed LEFT. The three panels in "
               "[region_tendency.png](figures/region_tendency.png) therefore run left to right: "
               "phone top, middle, phone bottom. Offsets rotate with the phone: view dx = app dy, view dy = -app dx. "
               "Positive view x means right; positive view y means down. The following table uses this view.\n\n"
               "| Viewed region | Contacts | Mean right/left offset (dp) | Mean down/up offset (dp) |\n"
               "|---|---:|---:|---:|\n")
    for row in read_csv(output / "tables/region_tendency_view.csv"):
        report += (f"| {row['viewer_region']} | {row['contacts']} | "
                   f"{float(row['mean_view_dx_dp']):+.2f} | {float(row['mean_view_dy_dp']):+.2f} |\n")
    report += ("\n"
               "## Coordinates and IMU\n\n"
               "The app exports portrait coordinates (1080 × 2179 px) despite the horizontal holder. "
               "Upper/middle/lower mean thirds of the app's logged y axis; in the displayed horizontal view these become left/center/right. "
               "dx is positive right; dy is positive down. IMU components remain in the exporter's unverified axes; "
               "they are not calibrated robot roll/pitch/yaw. dp values use the logged px/dp ratio, not millimeters.\n")
    return report


def run(root=ROOT):
    reports = []
    comparisons = []
    pooled_contacts, pooled_sessions, pooled_targets = [], [], []
    all_sessions = []
    dataset_groups = {}
    interruption_path = root / "data/annotations/operator_session_interruptions.csv"
    interruptions = {(r["dataset"], r["session_id"]): r for r in read_csv(interruption_path)}
    for dataset in DATASETS:
        source = next((root / "data/raw" / dataset).glob("*.jsonl"))
        raw = read_jsonl(source)
        assert len({e["event_id"] for e in raw}) == len(raw)
        if dataset != "sweetspot":
            # JSON/JSONL are copies, not separate trials. CSV is retained, not appended.
            assert json.loads(source.with_suffix(".json").read_text()) == raw
        groups = defaultdict(list)
        for e in sorted(raw, key=timestamp):
            groups[e["session_id"]].append(e)
        exclusion_path = root / "data/annotations" / ("exclusions.csv" if dataset == "sweetspot" else f"{dataset}_exclusions.csv")
        exclusion_rows = read_csv(exclusion_path)
        exclusions = {s["session_id"] for s in exclusion_rows}
        assert exclusions <= set(groups)
        numbers = {sid: i for i, sid in enumerate(groups, 1)}
        assert all(numbers[s["session_id"]] == int(s["session_number"]) for s in exclusion_rows)
        if dataset != "sweetspot":
            lines = source.read_bytes().splitlines(keepends=True)
            for folder, selected in (("excluded", True), ("processed", False)):
                path = root / "data" / folder / f"{dataset}_{'excluded' if selected else 'valid'}.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"".join(line for line in lines if line.strip()
                                         and (json.loads(line)["session_id"] in exclusions) == selected))
        corrections = {s["session_id"]: s for s in read_csv(root / "data/annotations/operator_target_counts.csv")} if dataset == "sweetspot" else {}
        output = root / "results" / dataset
        for folder in ("tables", "figures", "maps"):
            (output / folder).mkdir(parents=True, exist_ok=True)
        for row in exclusion_rows:
            map_path = output / "maps" / f"session_{int(row['session_number']):02d}.png"
            if map_path.exists():
                archived = output / "maps/excluded" / map_path.name
                archived.parent.mkdir(parents=True, exist_ok=True)
                map_path.replace(archived)
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
            annotation = interruptions.get((dataset, sid))
            ss.update(operator_unexecuted_targets=0, operator_interruption_reason="",
                      operator_annotation_source="")
            if annotation:
                assert int(annotation["session_number"]) == number
                unexecuted = int(annotation["unexecuted_targets"])
                assert unexecuted > 0 and unexecuted == ss["target_ids_without_records"]
                ss.update(operator_unexecuted_targets=unexecuted,
                          operator_interruption_reason=annotation["reason"],
                          operator_annotation_source=annotation["annotation_source"])
            contacts.extend(cs)
            sessions.append(ss)
            targets.extend(ts)
            pairs.extend(ps)
            selected_groups.append((number, events))
        dataset_groups[dataset] = selected_groups
        tendency_rows = tendency(contacts)
        sensitivity = outcome_sensitivity(sessions, contacts)
        for name, rows in [("contacts_extended", contacts), ("sessions_extended", sessions),
                           ("targets_extended", targets), ("rapid_repeat_pairs", pairs), ("target_tendency", tendency_rows),
                           ("outcome_sensitivity", sensitivity)]:
            write_csv(output / "tables" / f"{name}.csv", rows)
        plot_dataset(output, contacts, sessions, selected_groups)
        regional_report = analyze_regions(output, contacts, targets)
        all_sessions.extend(sessions)
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
        report = f"""# {DATASET_LABELS[dataset]}: contact tendency and observation limitations

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
            for s in sessions:
                if s["operator_unexecuted_targets"]:
                    report += (f"\n## Operator-confirmed interruption\n\n"
                               f"Session {s['session_number']}: {s['operator_interruption_reason']}. "
                               f"The remaining {s['operator_unexecuted_targets']} targets were not executed "
                               "and are not counted as touch misses. Recorded contacts are retained; "
                               "the interruption reason is an operator annotation, not inferred from the app export.\n")
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
        if dataset == "horizontal_tests":
            detailed = report.split("## Double contacts and app censoring")[0]
            report = horizontal_summary(output, contacts, sessions, targets, selected_groups, exclusion_rows) + "\n" + detailed
            (output / "summary.md").write_text(report, encoding="utf-8")
        (output / "contact_analysis.md").write_text(report, encoding="utf-8")
        manifest_paths = [source, root / "scripts/analyze_contacts.py", exclusion_path]
        if dataset == "sweetspot":
            manifest_paths.append(root / "data/annotations/operator_target_counts.csv")
        else:
            manifest_paths.append(interruption_path)
            manifest_paths.extend([source.with_suffix(".json"), source.with_suffix(".csv")])
        if dataset == "horizontal_tests":
            manifest_paths.append(source.parent / "README.md")
        manifest = dict(dataset=dataset, input_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in manifest_paths},
                        nearby_dp=NEARBY_DP, repeat_ms=REPEAT_MS, events=sum(s["events"] for s in sessions),
                        contacts=len(contacts), sessions=len(sessions), first_circle_contacts=first["contacts"],
                        excluded_session_numbers=sorted(int(s["session_number"]) for s in exclusion_rows),
                        region_boundaries_y_fraction=[0, 1/3, 2/3, 1], region_basis="target_center",
                        python=platform.python_version(), numpy=np.__version__, matplotlib=matplotlib.__version__)
        (output / "contact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        reports.append(report + "\n" + regional_report)
        print(f"{dataset}: {len(sessions)} sessions, {len(contacts)} contacts, {first['contacts']} first-circle observations; results in {output}")
    comparison = """# Recorded contact tendency: Sweet Spot, Random Poses and Horizontal Tests

First recorded contact per uniquely containing circle; conditional on recorded in-circle contact.
Offsets are in phone screen axes (x right, y down), in dp rather than physical millimeters.
Equal-session means help distinguish contact weighting from session weighting.

| Dataset | Radius (dp) | Contacts | Sessions | Mean x (dp) | Mean y (dp) | Equal-session x (dp) | Equal-session y (dp) | Above center |
|---|---|---:|---:|---:|---:|---:|---:|---:|
"""
    for r in comparisons:
        comparison += (f"| {r['dataset']} | {r['value']} | {r['contacts']} | {r['sessions']} | "
                       f"{r['mean_dx_dp']:+.2f} | {r['mean_dy_dp']:+.2f} | {r['session_balanced_dx_dp']:+.2f} | "
                       f"{r['session_balanced_dy_dp']:+.2f} | {r['fraction_above_center']:.1%} |\n")
    comparison += """
Both full populations and every available radius stratum are shown; compare matching radii across conditions. Even at the same radius,
app behavior, holder pose, session completeness and collection conditions differ.
These samples do not establish a causal effect of robot pose or recording conditions.
Sweet Spot and Random Poses have an aggregate tendency above target center; Horizontal Tests instead
has opposing regional offsets. Camera-to-tip extrinsics and coordinate mapping warrant a controlled check;
these logs alone do not identify the cause or justify an automatic offset correction.

Legacy double-contact consequences are flagged in `sweetspot/contact_analysis.md`;
missing outcomes are not imputed. New repeated contacts and partial sessions remain visible in
`random_poses/contact_analysis.md`. See their sensitivity tables before quoting an accuracy percentage.
"""
    comparison += ("\nHorizontal Tests applies the operator-requested exclusions in `data/annotations/horizontal_tests_exclusions.csv`. "
                   "Its app coordinates stay portrait even when the holder is horizontal. "
                   "The horizontal radius 15 dp condition has one session. "
                   "See `horizontal_tests/summary.md` for all-session versus full-ID size strata.\n")
    (root / "results/comparison.md").write_text(comparison, encoding="utf-8")
    overview_rows = []
    for dataset in (*DATASETS, "all"):
        ss = [s for s in all_sessions if dataset == "all" or s["dataset"] == dataset]
        hits = sum(s["hits"] for s in ss)
        count = sum(s["contacts"] for s in ss)
        overview_rows.append(dict(dataset=dataset, sessions=len(ss), events=sum(s["events"] for s in ss),
                                  contacts=count, app_hits=hits, app_misses=count-hits,
                                  contact_hit_fraction=hits / count if count else None,
                                  no_touch=sum(s["no_touch"] for s in ss),
                                  configured_targets=sum(s["effective_targets"] for s in ss),
                                  unrecorded_targets=sum(s["target_ids_without_records"] for s in ss)))
    write_csv(root / "results/overview.csv", overview_rows)
    overview = ("# Recorded touchscreen contacts — all three conditions\n\n"
                "All three conditions apply their documented operator-requested exclusions. "
                "Original session numbering is preserved. Counts describe logged contacts, not independent robot attempts.\n\n"
                "| Condition | Sessions | Contacts | App hits | Hit fraction | no_touch | Targets without records |\n"
                "|---|---:|---:|---:|---:|---:|---:|\n")
    for r in overview_rows:
        overview += (f"| {DATASET_LABELS.get(r['dataset'], 'All conditions')} | {r['sessions']} | {r['contacts']} | "
                     f"{r['app_hits']} | {r['contact_hit_fraction']:.2%} | {r['no_touch']} | {r['unrecorded_targets']} |\n")
    overview += ("\n[Horizontal session maps and review table](horizontal_tests/session_review.md) · "
                 "[Horizontal size results](horizontal_tests/summary.md) · [Contact placement comparison](comparison.md)\n\n"
                 "The total is an unbalanced mixture of sizes, app versions, screen geometry and mounting conditions; "
                 "it does not estimate a causal orientation effect. Repeats are included; unknown targets remain separate. "
                 "`combined/` includes the same three retained conditions and their full contact/target tables and figures.\n")
    (root / "results/overview.md").write_text(overview, encoding="utf-8")
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
    summary = """# Overall recorded contacts: Sweet Spot + Random Poses + Horizontal Tests

This section pools **all recorded contacts from retained sessions** in all three conditions.
Archived sessions remain excluded. Source dataset, session number, UUID and event ID are kept in every row.
The pooled population reflects the recorded mix of sizes/poses; it is not a balanced experiment.

| Condition | Sessions | Events | Contacts | App hits | App misses | no_touch events | Expected targets | Targets with records |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
"""
    for dataset in (*DATASETS, "combined"):
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
The signed offsets in pooled tables use the original phone/app axes. The region-tendency figure
separates conditions and rotates the horizontal view to match its mounting; see the section below.
"""
    (output / "summary.md").write_text(summary + "\n" + regional_report, encoding="utf-8")
    manifests = [json.loads((root / f"results/{ds}/contact_manifest.json").read_text()) for ds in DATASETS]
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
    from analyze_touch_repeats import run as run_repeat_analysis
    run_repeat_analysis(root, pooled_contacts, pooled_sessions, pooled_targets, dataset_groups)
    return reports


if __name__ == "__main__":
    run()
