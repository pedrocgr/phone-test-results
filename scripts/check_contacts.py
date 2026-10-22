"""Small regression checks for reassigned double contacts, missing targets, and IMU wrapping."""
from copy import deepcopy
import hashlib
import json
from struct import unpack

from analyze_contacts import (ROOT, analyze_session, circular_summary, outcome_sensitivity,
                             read_csv, read_jsonl, tendency, screen_region, regional_outcomes, phone_view_offset)


def event(identifier, target, cx, x, time, result="hit"):
    return dict(event_id=identifier, session_id="session", target_id=target, date_time=time,
                target_center_x=cx, target_center_y=100, actual_touch_x=x,
                actual_touch_y=100 if x is not None else None, target_radius=20, target_radius_dp=10,
                distance_to_center=abs(x-cx) if x is not None else None,
                inside_target=result == "hit", result=result, configuration={"target_count": 2},
                screen_width=1080, screen_height=2400)


a = event("a", "trio-001-red", 100, 100, "2026-10-06T12:00:00Z")
b = event("b", "trio-001-blue", 500, 102, "2026-10-06T12:00:00.070Z", "miss")
c = event("c", "trio-001-blue", 500, None, "2026-10-06T12:00:01Z", "no_touch")
events = [a, b, c]
snapshot = deepcopy(events)
contacts, session, targets, pairs = analyze_session(events, 1, {a['target_id'], b['target_id']}, "sweetspot")
assert events == snapshot  # Source labels/coordinates must not change.
assert len(contacts) == 2 and len(pairs) == 1
assert contacts[1]["app_result"] == "miss" and contacts[1]["assignment_disagrees"]
assert contacts[1]["unique_containing_target_id"] == a["target_id"]
assert contacts[1]["rapid_repeat_candidate"] and not contacts[1]["first_contact_in_circle"]
assert session["legacy_ceiling_compatible"]
assert targets[1]["target_id"] == a["target_id"]  # IDs sorted blue, red.
assert targets[0]["possible_ceiling_censoring"] and targets[0]["outcome_unknown"]
assert next(r for r in tendency(contacts) if r["population"] == "first_contact_per_circle" and r["stratum"] == "all")["contacts"] == 1

# Same contact twice in Random Poses is explicit repetition, not two targets hit.
updated = [deepcopy(a), deepcopy(a)]
updated[1].update(event_id="d", date_time="2026-10-06T12:00:00.070Z", target_already_completed=True)
cs, ss, ts, ps = analyze_session(updated, 1, {a['target_id'], b['target_id']}, "random_poses")
assert ss["assigned_targets_with_hit"] == 1 and ss["app_completed_repeat_contacts"] == 1
assert ss["target_ids_without_records"] == 1 and not ss["all_expected_ids_recorded"]
assert not ss["legacy_ceiling_compatible"] and ts[0]["outcome_unknown"]
assert next(r for r in outcome_sensitivity([ss], cs) if r['contact_population'] == 'without_app_completed_repeats')['contacts'] == 1

# Overlapping circles must not invent a unique geometric target.
overlap = deepcopy(b)
overlap.update(target_center_x=110, actual_touch_x=102, distance_to_center=8, result="hit", inside_target=True)
cs, *_ = analyze_session([a, overlap], 1, {a['target_id'], b['target_id']}, "sweetspot")
assert all(c["containing_target_count"] == 2 and not c["unique_containing_target_id"] for c in cs)
mean, resultant, spread = circular_summary([179, -179])
assert abs(abs(mean)-180) < 1e-9 and resultant > .99 and abs(spread-1) < 1e-9
assert circular_summary([]) == (None, None, None)
assert circular_summary([0, 180])[0] is None

# Region uses the target center even when the touch crosses a third boundary.
assert [screen_region(y) for y in (0, .2, 1/3, .5, 2/3, 1)] == ['upper', 'upper', 'middle', 'middle', 'lower', 'lower']
for bad in (-.01, 1.01, float('nan')):
    try:
        screen_region(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid screen fraction accepted')
crossing = dict(a, screen_height=300, actual_touch_y=10, distance_to_center=90, result='miss', inside_target=False)
cross_cs, cross_ss, cross_ts, _ = analyze_session([crossing], 1, {a['target_id'], b['target_id']}, 'sweetspot')
assert cross_cs[0]['assigned_region'] == 'middle' and cross_cs[0]['geometric_region'] == ''
assert {t['region'] for t in cross_ts} == {'middle', 'unknown'}
regional = regional_outcomes(cross_ts)
assert next(r for r in regional if r['stratum'] == 'region' and r['value'] == 'unknown')['unknown_outcome_targets'] == 1
# Reused target/session names in different datasets must remain separate.
copy_cs = [dict(c, dataset='random_poses') for c in cross_cs]
assert next(r for r in tendency(cross_cs + copy_cs) if r['stratum'] == 'all')['sessions'] == 2

# With the phone top pointing left, app-up becomes viewer-left and app-right becomes viewer-up.
assert phone_view_offset('horizontal_tests', 0, -1) == (-1, 0)
assert phone_view_offset('horizontal_tests', 1, 0) == (0, -1)
assert phone_view_offset('horizontal_tests', 3, 4) == (4, -3)
assert phone_view_offset('sweetspot', 3, 4) == (3, 4)
assert phone_view_offset('random_poses', -2, 7) == (-2, 7)

source_contact_keys = set()
source_target_keys = set()

for dataset, expected in [("sweetspot", (15, 132, 111)), ("random_poses", (7, 105, 88)),
                          ("horizontal_tests", (18, 220, 201))]:
    output = ROOT / "results" / dataset
    manifest = json.loads((output / "contact_manifest.json").read_text())
    assert (manifest["sessions"], manifest["contacts"], manifest["first_circle_contacts"]) == expected
    for name, sha in manifest["input_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha
    contacts = read_csv(output / "tables/contacts_extended.csv")
    sessions = read_csv(output / "tables/sessions_extended.csv")
    assert len(contacts) == expected[1] and len(sessions) == expected[0]
    assert sum(c["first_contact_in_circle"] == "True" for c in contacts) == expected[2]
    assert all((c['unique_containing_target_id'] != '') == (c['containing_target_count'] == '1') for c in contacts)
    source_contact_keys.update((c['dataset'], c['event_id']) for c in contacts)
    targets = read_csv(output / 'tables/targets_extended.csv')
    source_target_keys.update((t['dataset'], t['session_id'], t['target_id']) for t in targets)
    region_rows = read_csv(output / 'tables/region_size_contacts.csv')
    for population in {r['population'] for r in region_rows}:
        regions = [r for r in region_rows if r['population'] == population and r['stratum'] == 'region']
        cells = [r for r in region_rows if r['population'] == population and r['stratum'] == 'region_radius_dp']
        assert sum(int(r['contacts']) for r in regions) == sum(int(r['contacts']) for r in cells)
    if dataset == "random_poses":
        interrupted = next(s for s in sessions if s['session_number'] == '6')
        assert interrupted['operator_unexecuted_targets'] == '10'
        assert interrupted['operator_interruption_reason'] == 'Execution stopped after a touch-sensor connection error'
        assert interrupted['operator_annotation_source']
        assert all(s['operator_unexecuted_targets'] == '0' for s in sessions if s['session_number'] != '6')
        assert sum(c['app_target_already_completed'] == 'True' for c in contacts) == 13
        assert sum(int(s['target_ids_without_records']) for s in sessions) == 10
        assert {int(s['session_number']) for s in sessions if s['all_expected_ids_recorded'] == 'False'} == {6}
        assert {int(s['session_number']) for s in sessions} == {1, 3, 4, 5, 6, 9, 11}
        source = next((ROOT / 'data/raw/random_poses').glob('*.jsonl'))
        raw = read_jsonl(source)
        valid = read_jsonl(ROOT / 'data/processed/random_poses_valid.jsonl')
        archived = read_jsonl(ROOT / 'data/excluded/random_poses_excluded.jsonl')
        assert len(raw) == 116 and len(valid) == 107 and len(archived) == 9
        assert hashlib.sha256(source.read_bytes()).hexdigest() == '5cd7f5f138de816b5d531899aba79af099fd35f56c46bd3becde4af49c1c8bff'
        assert {e['event_id'] for e in valid}.isdisjoint({e['event_id'] for e in archived})
        assert sorted(valid + archived, key=lambda e: e['event_id']) == sorted(raw, key=lambda e: e['event_id'])
        annotations = read_csv(ROOT / 'data/annotations/random_poses_exclusions.csv')
        assert {int(s['session_number']) for s in annotations} == {2, 7, 8, 10}
        assert {e['session_id'] for e in archived} == {s['session_id'] for s in annotations}
        assert {p.stem for p in (output / 'maps').glob('session_[0-9][0-9].png')} == {f'session_{i:02d}' for i in (1, 3, 4, 5, 6, 9, 11)}
    for name in ("target_tendency", "region_tendency", "vertical_bias_by_height", "region_by_size", "target_outcomes_region_by_size", "app_assignment_diagnostics"):
        image = (output / "figures" / f"{name}.png").read_bytes()
        assert len(image) > 1000 and b'Description\x00' in image
    assert (output / 'figures/phone_orientation_by_session.png').exists() == (dataset in ('random_poses', 'horizontal_tests'))
    assert ('## Phone orientation' in (output / 'contact_analysis.md').read_text()) == (dataset == 'random_poses')

output = ROOT / 'results/combined'
combined_contacts = read_csv(output / 'tables/contacts_extended.csv')
combined_targets = read_csv(output / 'tables/targets_extended.csv')
combined_sessions = read_csv(output / 'tables/sessions_extended.csv')
assert len(combined_contacts) == 457 and len(combined_sessions) == 40 and len(combined_targets) == 465
assert {(c['dataset'], c['event_id']) for c in combined_contacts} == source_contact_keys
assert {(t['dataset'], t['session_id'], t['target_id']) for t in combined_targets} == source_target_keys
assert sum(c['app_result'] == 'hit' for c in combined_contacts) == 416
assert sum(c['first_contact_in_circle'] == 'True' for c in combined_contacts) == 400
assert sum(int(s['events']) for s in combined_sessions) == 517
article_image = output / 'figures/region_tendency_article.png'
assert b'Description\x00' in article_image.read_bytes()
article_width, article_height = unpack('>II', article_image.read_bytes()[16:24])
assert article_height > article_width and article_width >= 800
assert article_image.stat().st_size > 1000
manifest = json.loads((output / 'contact_manifest.json').read_text())
assert set(manifest['source_datasets']) == {'sweetspot', 'random_poses', 'horizontal_tests'}
for name, sha in manifest['input_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha
outcomes = read_csv(output / 'tables/region_size_outcomes.csv')
assert sum(int(r['targets']) for r in outcomes if r['stratum'] == 'region') == 465
assert next(r for r in outcomes if r['stratum'] == 'region' and r['value'] == 'unknown')['targets'] == '10'
assert not list((ROOT / 'results').glob('*/figures/screen_bias.png'))
assert not (output / 'figures/imu_and_bias.png').exists()
for dataset in ('sweetspot', 'random_poses', 'combined'):
    for name in ('region_tendency', 'target_outcomes_region_by_size'):
        image = ROOT / 'results' / dataset / 'figures' / f'{name}.png'
        width, height = unpack('>II', image.read_bytes()[16:24])
        assert height > width, f'{dataset}: screen-region chart must be portrait'
    assert not (ROOT / 'results' / dataset / 'figures/imu_and_bias.png').exists()
zero_hit = next(r for r in read_csv(ROOT / 'results/sweetspot/tables/region_size_outcomes.csv')
                if r['stratum'] == 'region_radius_dp' and r['value'] == 'upper:25')
assert zero_hit['targets'] == '3' and zero_hit['assigned_hit_targets'] == '0'
assert zero_hit['assigned_miss_without_hit_targets'] == '3'
print("Contact checks passed: double contact assignments, censoring flags, unknown targets, source hashes, and circular IMU statistics.")

# New horizontal exports are preserved as one dataset, not counted three times.
source = ROOT / 'data/raw/horizontal_tests/touch_results.jsonl'
raw = read_jsonl(source)
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'a081ca9553b7c576d90724a0f50369f85cef2639c71126e54e2fa7c85ca8fbcf'
assert raw == json.loads(source.with_suffix('.json').read_text())
csv_export = read_csv(source.with_suffix('.csv'))
assert [r['event_id'] for r in csv_export] == [r['event_id'] for r in raw]
for csv_row, event_row in zip(csv_export, raw):
    assert json.loads(csv_row['configuration']) == event_row['configuration']
    assert json.loads(csv_row['imu']) == event_row['imu']
    for field in ('target_center_x', 'target_center_y', 'target_radius'):
        assert float(csv_row[field]) == event_row[field]
assert len(raw) == len({r['event_id'] for r in raw}) == 272
assert all(r['target_shape'] == 'circle' and not r['configuration']['captcha_enabled'] for r in raw)
assert {(r['screen_width'], r['screen_height']) for r in raw} == {(1080, 2179)}
valid = read_jsonl(ROOT / 'data/processed/horizontal_tests_valid.jsonl')
excluded = read_jsonl(ROOT / 'data/excluded/horizontal_tests_excluded.jsonl')
assert sorted(valid + excluded, key=lambda r: r['event_id']) == sorted(raw, key=lambda r: r['event_id'])
excluded_numbers = {5, 10, 11, 12, 13, 14, 15, 16, 18, 26, 28, 29}
retained_numbers = set(range(1, 31)) - excluded_numbers
annotations = read_csv(ROOT / 'data/annotations/horizontal_tests_exclusions.csv')
assert {int(r['session_number']) for r in annotations} == excluded_numbers
assert len(valid) == 247 and len(excluded) == 25
assert {r['session_id'] for r in excluded} == {r['session_id'] for r in annotations}
assert {r['event_id'] for r in valid}.isdisjoint({r['event_id'] for r in excluded})
output = ROOT / 'results/horizontal_tests'
manifest = json.loads((output / 'contact_manifest.json').read_text())
assert (manifest['events'], manifest['contacts'], manifest['sessions'], manifest['first_circle_contacts']) == (247, 220, 18, 201)
assert set(manifest['excluded_session_numbers']) == excluded_numbers
for name, sha in manifest['input_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha
contacts = read_csv(output / 'tables/contacts_extended.csv')
sessions = read_csv(output / 'tables/sessions_extended.csv')
targets = read_csv(output / 'tables/targets_extended.csv')
assert len(contacts) == 220 and len(sessions) == 18 and len(targets) == 228
assert sum(r['app_result'] == 'hit' for r in contacts) == 204
assert sum(r['app_target_already_completed'] == 'True' for r in contacts) == 3
assert sum(r['first_contact_in_circle'] == 'True' for r in contacts) == 201
assert sum(int(r['no_touch']) for r in sessions) == 27
assert sum(int(r['target_ids_without_records']) for r in sessions) == 0
assert sum(r['all_expected_ids_recorded'] == 'True' for r in sessions) == 18
review = read_csv(output / 'tables/session_review.csv')
assert {int(r['session_number']) for r in review} == retained_numbers
assert {int(p.stem.split('_')[1]) for p in (output / 'maps').glob('session_[0-9][0-9].png')} == retained_numbers
assert {int(p.stem.split('_')[1]) for p in (output / 'maps/excluded').glob('session_[0-9][0-9].png')} == excluded_numbers
for r in review:
    assert (output / r['map']).is_file()
import re
assert len(re.findall(rb'/Type\s*/Page\b', (output / 'maps/all_sessions.pdf').read_bytes())) == 18
size_rows = read_csv(output / 'tables/outcomes_by_size.csv')
for population, expected in (('all_sessions', (220, 204)), ('all_expected_ids_recorded', (220, 204))):
    rows = [r for r in size_rows if r['session_population'] == population]
    assert {float(r['radius_dp']) for r in rows} == {15, 20, 25, 30, 35, 40}
    assert (sum(int(r['contacts']) for r in rows), sum(int(r['hits']) for r in rows)) == expected
for name in ('target_tendency', 'region_tendency', 'vertical_bias_by_height', 'region_by_size',
             'target_outcomes_region_by_size', 'outcomes_by_size', 'phone_orientation_by_session'):
    image = (output / 'figures' / f'{name}.png').read_bytes()
    assert len(image) > 1000 and b'Description\x00' in image
overview = read_csv(ROOT / 'results/overview.csv')
total = next(r for r in overview if r['dataset'] == 'all')
assert (int(total['sessions']), int(total['events']), int(total['contacts']), int(total['app_hits'])) == (40, 517, 457, 416)
assert abs(float(total['contact_hit_fraction']) - 416/457) < 1e-12
assert not list(output.glob('figures/*.pdf'))
view = read_csv(output / 'tables/region_tendency_view.csv')
assert [r['viewer_region'] for r in view] == ['Left (phone top)', 'Center', 'Right (phone bottom)']
assert sum(int(r['contacts']) for r in view) == 201
app_rows = read_csv(output / 'tables/region_size_contacts.csv')
for r in view:
    app = next(a for a in app_rows if a['population'] == 'first_contact_per_circle'
               and a['stratum'] == 'region' and a['value'] == r['app_region'])
    assert abs(float(r['mean_view_dx_dp']) - float(app['mean_dy_dp'])) < 1e-10
    assert abs(float(r['mean_view_dy_dp']) + float(app['mean_dx_dp'])) < 1e-10
    assert abs(float(r['median_radial_error_dp']) - float(app['median_radial_error_dp'])) < 1e-10
image = (output / 'figures/region_tendency.png').read_bytes()
width, height = unpack('>II', image[16:24])
assert width > height
combined_view = read_csv(ROOT / 'results/combined/tables/region_tendency_view.csv')
assert sum(int(r['contacts']) for r in combined_view) == 400
assert {r['dataset'] for r in combined_view} == {'sweetspot', 'random_poses', 'horizontal_tests'}
assert [r for r in combined_view if r['dataset'] == 'horizontal_tests'] == view
assert {r['event_id'] for r in combined_contacts if r['dataset'] == 'horizontal_tests'} == {r['event_id'] for r in contacts}
print('Horizontal checks passed: original exports, 18 retained sessions, 12 archived sessions, maps and updated totals.')
