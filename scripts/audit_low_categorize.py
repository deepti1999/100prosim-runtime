"""Categorise the 206 LOW rows — are they aggregates, UI-only, or real gaps?"""
import csv, json, re
from collections import Counter

with open('seed/sqlite_seed.json', encoding='utf-8') as f:
    seed = json.load(f)

# Read all LOW rows from final_map CSVs
LOW_MARKERS = ['LOW']
all_low = []
for short in ('landuse', 'renewabledata', 'verbrauchdata', 'gebaeudewaermedata'):
    with open(f'scripts/audit_out/final_map_{short}.csv', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['confidence'] == 'LOW':
                all_low.append((short, row))

print(f'Total LOW: {len(all_low)}')
print()

# Heuristic categories
def categorise(model, row):
    code = row['our_code']
    label = row['our_label'].lower()
    s = row.get('status_ours', '')
    z = row.get('ziel_ours', '')

    # Aggregate / sum indicators
    if re.match(r'^\d+\.$', code) or code in ('0', ''):
        return 'AGGREGATE (top-level code)'
    if any(w in label for w in ['gesamt', 'summe', 'total', 'alle', 'insgesamt']):
        return 'AGGREGATE (label says total)'

    # Computed / derived
    if label.startswith('nach ') or 'anpassung' in label:
        return 'COMPUTED (derived from another row)'

    # UI-only
    if model == 'renewabledata' and re.match(r'^[123]\.\d*$', code):
        return 'UI-GROUP (renewable top categories 1./2./3.)'

    # Solar/wind subtotals (LU_1.X.X)
    if model == 'landuse' and code.count('.') >= 2:
        return 'LU SUB-LEVEL (may aggregate)'

    # Could be genuine source-gap
    return 'POSSIBLE-GAP'

buckets = Counter()
by_model = {'landuse': Counter(), 'renewabledata': Counter(),
            'verbrauchdata': Counter(), 'gebaeudewaermedata': Counter()}

for model, row in all_low:
    cat = categorise(model, row)
    buckets[cat] += 1
    by_model[model][cat] += 1

print('===== LOW row categorisation =====')
for cat, n in buckets.most_common():
    print(f'  {cat}: {n}')

print()
print('===== Per model =====')
for m, c in by_model.items():
    print(f'{m}: {dict(c)}')

print()
print('===== 15 sample POSSIBLE-GAP rows (ones that might actually be drift) =====')
shown = 0
for model, row in all_low:
    if categorise(model, row) == 'POSSIBLE-GAP':
        print(f'  [{model}] {row["our_code"]} "{row["our_label"][:40]}" '
              f'status={row["status_ours"]} ziel={row["ziel_ours"]}')
        shown += 1
        if shown >= 15: break
