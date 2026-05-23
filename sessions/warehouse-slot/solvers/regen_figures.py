"""Regenerate figures with updated titles"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use('Agg')
from data_loader import *
from p1_slot_assignment import greedy_assignment_cell, plot_heatmap, plot_comparison
from p3_collaborative import simulate_dc, main as p3_main

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')

print("Loading data...", flush=True)
df_inv = get_sorted_inventory()
df_slots = build_slot_index()
df_cells = build_cell_index(df_slots)
df_inv_full = load_inventory()
f_norm_map = dict(zip(df_inv_full['原材料编号'], df_inv_full['f_norm']))

print("P1 assignment...", flush=True)
assign, slot_occ, et, _, _ = greedy_assignment_cell(df_inv, df_slots, df_cells)

# fig1: heatmap
print("fig1...", flush=True)
plot_heatmap(df_slots, slot_occ, os.path.join(FIG_DIR, 'fig1_slot_heatmap.pdf'))
print("fig1 done", flush=True)

# fig3: comparison
print("fig3...", flush=True)
plot_comparison(df_inv, assign, assign, os.path.join(FIG_DIR, 'fig3_greedy_vs_ga.pdf'))
print("fig3 done", flush=True)

# P2-P5 figure generation via their main functions
print("fig9 (P3)...", flush=True)
p3_main()
print("fig9 done", flush=True)
