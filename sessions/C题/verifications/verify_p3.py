import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import json, numpy as np

with open(os.path.join(os.path.dirname(__file__), '..', 'results', 'p3_summary.json')) as f:
    peaks = json.load(f)['peak_analysis']

for sn, p in peaks.items():
    y, v = p['peak_year'], p['peak_value']
    print(f"[V-P3-1] {sn}: peak {y} at {v:.1f}Mt")
    assert isinstance(y, int) and 2026 <= y <= 2045, f"FAIL: year {y} out of range"
    assert v > 0 and v < 50000, f"FAIL: value {v} unrealistic"
    print(f"  PASS")

# Check BAU > CR > ER
bau_v = peaks['Baseline (BAU)']['peak_value']
cr_v = peaks['Carbon Reduction']['peak_value']
er_v = peaks['Enhanced Reduction']['peak_value']
print(f"[V-P3-2] Peak ordering BAU({bau_v:.0f}) >= CR({cr_v:.0f}) >= ER({er_v:.0f})")
assert bau_v >= cr_v >= er_v, f"FAIL: peak ordering incorrect"
print(f"  PASS")

# Check CSV files exist
for fname in ['baseline_bau.csv', 'carbon_reduction.csv', 'enhanced_reduction.csv']:
    path = os.path.join(os.path.dirname(__file__), '..', 'results', fname)
    assert os.path.exists(path), f"FAIL: {fname} not found"
    print(f"[V-P3-3] {fname} exists: PASS")

print(f"\nAll P3 checks PASS")
