import sys, os
p = os.path.join(os.path.dirname(__file__), '..', 'results', 'p2_kaya_summary.txt')
with open(p) as f:
    lines = [l.strip() for l in f if l.strip()]
vals = {}
for line in lines:
    k, v = line.split(':')
    vals[k.strip()] = float(v.strip().replace('Mt',''))
co2_chg = vals['CO2 change']
pop_c = vals['Pop contribution']
aff_c = vals['Affluence contribution']
tech_c = vals['Tech contribution']
res = vals['Residual']
print(f"[V-P2-1] CO2 change: {co2_chg:.1f}Mt")
assert 0 < co2_chg < 2000
print("  PASS")
print(f"[V-P2-2] Affluence: +{aff_c:.1f}Mt > 0")
assert aff_c > 0
print("  PASS")
print(f"[V-P2-3] Technology: {tech_c:.1f}Mt < 0")
assert tech_c < 0
print("  PASS")
print(f"[V-P2-4] LMDI residual: {res:.2f}Mt ~= 0")
assert abs(res) < 1
print("  PASS")
print("\nAll P2 checks PASS")
