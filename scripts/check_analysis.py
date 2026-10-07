"""Check raw-data preservation, session selection, counts, repeats, and maps."""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results/sweetspot'

def table(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def records(path):
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]

source = ROOT / 'data/raw/sweetspot/touch_results_2026-10-06-sweetspot.jsonl'
raw = records(source)
retained = records(ROOT / 'data/processed/sweetspot_valid.jsonl')
excluded = records(ROOT / 'data/excluded/sweetspot_excluded.jsonl')
assert len(raw) == 177 and len(retained) == 163 and len(excluded) == 14
assert {r['event_id'] for r in retained}.isdisjoint({r['event_id'] for r in excluded})
assert sorted(retained + excluded, key=lambda r: r['event_id']) == sorted(raw, key=lambda r: r['event_id'])
manifest = json.loads((RESULTS / 'manifest.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['source_sha256'] == '290accd48b1739358913f6846d241b868f7a73a8317a14dd1b178490747f67f5'
sessions = table(RESULTS / 'tables/sessions.csv')
excluded_numbers = {3, 4, 6, 7, 9}
assert {int(s['session_number']) for s in sessions} == set(range(1, 21)) - excluded_numbers
assert {int(s['session_number']) for s in table(ROOT / 'data/annotations/exclusions.csv')} == excluded_numbers
assert sum(int(s['effective_target_count']) for s in sessions) == 135
assert sum(int(s['logged_target_count']) for s in sessions) == 141
for number in (12, 13):
    s = next(s for s in sessions if int(s['session_number']) == number)
    assert s['effective_target_count'] == '6' and s['logged_target_count'] == '9'
    assert s['completion_basis'] == 'operator_confirmed'
assert len([r for r in retained if r['actual_touch_x'] is not None]) == 132
metrics = table(RESULTS / 'tables/metrics.csv')
assert abs(float(metrics[0]['fraction']) - 111 / 132) < 1e-12
assert abs(float(metrics[1]['fraction']) - 111 / 135) < 1e-12
assert abs(float(metrics[2]['fraction']) - 111 / 141) < 1e-12
pairs = table(RESULTS / 'tables/repeated_contacts.csv')
assert len(pairs) == 4 and {int(p['session_number']) for p in pairs} == {5, 14, 15, 19}
assert all(p['rapid_repeated_contact_candidate'] == 'True' for p in pairs)
assert len(list((RESULTS / 'maps').glob('session_[0-9][0-9].png'))) == 15
assert len(list((RESULTS / 'maps/excluded').glob('session_[0-9][0-9].png'))) == 5
assert len(re.findall(rb'/Type\s*/Page\b', (RESULTS / 'maps/all_sessions.pdf').read_bytes())) == 15
print('Checks passed: original records, decisions, fractions, repeated contacts, and maps reconciled.')
