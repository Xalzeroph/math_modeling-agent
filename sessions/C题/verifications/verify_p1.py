import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, numpy as np

results = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'results', 'p1_evaluation.csv'))
n = len(results)
print(f"[V-P1-1] Provinces evaluated: {n} (expect 30)")
assert n == 30, f"FAIL: expected 30, got {n}"
print(f"  PASS")

C = results['Closeness'].values
print(f"[V-P1-2] Closeness range: [{C.min():.4f}, {C.max():.4f}] (expect [0,1])")
assert C.min() >= 0 and C.max() <= 1.0, f"FAIL: closeness out of range"
print(f"  PASS")

C_sorted = sorted(C, reverse=True)
print(f"[V-P1-3] Closeness monotonic: all sorted descending (check)")
is_monotonic = all(C_sorted[i] >= C_sorted[i+1] for i in range(len(C_sorted)-1))
assert is_monotonic, "FAIL: not monotonic"
print(f"  PASS")

print(f"[V-P1-4] Rank column exists: {'Rank' in results.columns}")
assert 'Rank' in results.columns, "FAIL: no Rank column"
print(f"  PASS")

print(f"\nAll P1 checks PASS")
