#!/usr/bin/env python3
"""
Problem 1: 省域碳排放综合评价
方法: 熵权法 + TOPSIS + K-Means
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_loader import load_province_emissions, get_province_gdp_population, province_name_map

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

RESULTS = os.path.join(os.path.dirname(__file__), '..', 'results')
FIGURES = os.path.join(os.path.dirname(__file__), '..', 'figures')

def entropy_weight(X, directions=None):
    X = np.array(X, dtype=float)
    m, n = X.shape
    if directions is None:
        directions = np.ones(n)
    directions = np.array(directions)
    norm = np.zeros_like(X)
    for j in range(n):
        mn, mx = X[:, j].min(), X[:, j].max()
        rng = mx - mn
        if rng == 0:
            norm[:, j] = 1
        else:
            if directions[j] == 1:
                norm[:, j] = (X[:, j] - mn) / rng
            else:
                norm[:, j] = (mx - X[:, j]) / rng
    shift = norm + 0.001
    p = shift / shift.sum(axis=0)
    e = -1 / np.log(m) * np.sum(p * np.log(p), axis=0)
    d = 1 - e
    w = d / d.sum()
    return w, e, d, norm

def topsis(X, weights, directions=None):
    X = np.array(X, dtype=float)
    m, n = X.shape
    if directions is None:
        directions = np.ones(n)
    norm = X / np.sqrt((X**2).sum(axis=0))
    V = norm * weights
    Vplus, Vminus = np.zeros(n), np.zeros(n)
    for j in range(n):
        if directions[j] == 1:
            Vplus[j], Vminus[j] = V[:, j].max(), V[:, j].min()
        else:
            Vplus[j], Vminus[j] = V[:, j].min(), V[:, j].max()
    Dplus = np.sqrt(((V - Vplus)**2).sum(axis=1))
    Dminus = np.sqrt(((V - Vminus)**2).sum(axis=1))
    C = Dminus / (Dplus + Dminus + 1e-10)
    return C, Dplus, Dminus, V

def plot_results(df, weights, info_entropy, indicators_short):
    df_sorted = df.sort_values('Closeness', ascending=True)
    n = len(df)
    # 1. 权重
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ['#2171B5', '#6BAED6', '#74C476', '#FEC44F', '#D73027']
    bars = ax.bar(indicators_short, weights, color=colors, edgecolor='black', width=0.6)
    for bar, w in zip(bars, weights):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                f'{w:.4f}', ha='center', va='bottom', fontsize=10)
    ax.set_ylabel('Weight', fontsize=12)
    ax.set_title('Indicator Weights (Entropy Method)', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(weights)*1.3)
    ax.grid(True, alpha=0.25, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, 'p1_weight.pdf'), format='pdf', bbox_inches='tight')
    plt.close()

    # 2. 排名
    fig, ax = plt.subplots(figsize=(10, 7))
    colors_c = plt.cm.RdYlGn(df_sorted['Closeness'].values)
    ax.barh(range(n), df_sorted['Closeness'].values, color=colors_c, edgecolor='black', height=0.7)
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        ax.text(row['Closeness']+0.005, i, f"{row['Closeness']:.4f}", va='center', fontsize=8)
    ax.set_yticks(range(n))
    ax.set_yticklabels(df_sorted['Province_cn'].values, fontsize=9)
    ax.set_xlabel('TOPSIS Closeness C', fontsize=12)
    ax.set_title('Provincial Carbon Emission Ranking', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 1.05)
    ax.grid(True, alpha=0.25, axis='x')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, 'p1_ranking.pdf'), format='pdf', bbox_inches='tight')
    plt.close()

    # 3. 聚类结果
    fig, ax = plt.subplots(figsize=(10, 5))
    cats = sorted(df_sorted['Category'].unique())
    cmap = plt.cm.Set2(np.linspace(0, 1, len(cats)))
    cc = {c: cmap[i] for i, c in enumerate(cats)}
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        ax.barh(i, 1, color=cc[row['Category']], edgecolor='black', height=0.7, alpha=0.8)
        ax.text(0.5, i, row['Province_cn'], ha='center', va='center', fontsize=8, fontweight='bold')
    ax.set_yticks([])
    ax.set_title('Provincial Carbon Emission Clusters', fontsize=13, fontweight='bold')
    handles = [plt.Rectangle((0,0),1,1, color=cc[c]) for c in cats]
    ax.legend(handles, cats, loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, 'p1_cluster.pdf'), format='pdf', bbox_inches='tight')
    plt.close()

def main():
    print("="*60)
    print("Problem 1: Provincial Carbon Emission Evaluation")
    print("="*60)

    pdf = load_province_emissions()
    name_map = province_name_map()
    pdf['Province_cn'] = pdf['Province'].map(name_map)
    gdp_pop = get_province_gdp_population()
    merged = pdf.merge(gdp_pop, left_on='Province_cn', right_on='Province', how='inner')
    merged.drop(columns=['Province_y'], inplace=True)
    merged.rename(columns={'Province_x': 'Province'}, inplace=True)
    merged.reset_index(drop=True, inplace=True)
    print(f"Valid provinces: {len(merged)}")

    merged['C_Total'] = merged['CO2_Mt']
    merged['C_PerCap'] = merged['CO2_Mt'] * 1e4 / merged['Pop']  # t/person
    merged['C_Intensity'] = merged['CO2_Mt'] / (merged['GDP'] * 0.01)  # t/万元, normalized
    merged['C_Productivity'] = merged['GDP'] / merged['CO2_Mt']
    merged['C_Coord'] = (merged['GDP']/merged['GDP'].sum()) / (merged['CO2_Mt']/merged['CO2_Mt'].sum())

    indicators = ['C_Total', 'C_PerCap', 'C_Intensity', 'C_Productivity', 'C_Coord']
    indicator_names = ['Total CO2', 'Per Capita CO2', 'Intensity', 'Productivity', 'Coord Ratio']
    directions = [-1, -1, -1, 1, 1]
    X = merged[indicators].values

    w, e, d, norm = entropy_weight(X, directions)
    print("\nEntropy Weights:")
    for nm, wi, ei in zip(indicator_names, w, e):
        print(f"  {nm}: weight={wi:.4f}, entropy={ei:.4f}")

    C, Dp, Dm, V = topsis(X, w, directions)
    merged['Closeness'] = C

    # K-Means with silhouette
    sil_scores = []
    K_range = range(2, 8)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(norm * w)
        sil_scores.append(silhouette_score(norm * w, labels))
    best_k = K_range[np.argmax(sil_scores)]
    print(f"\nBest K={best_k} (silhouette={max(sil_scores):.4f})")

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    merged['Cluster'] = km.fit_predict(norm * w)

    cat_order = merged.groupby('Cluster')['Closeness'].mean().sort_values(ascending=False).index.tolist()
    labels = ['High-High', 'Medium-High', 'Medium-Low', 'Low-Efficient', 'Category5', 'Category6', 'Category7']
    for idx, c in enumerate(cat_order):
        merged.loc[merged['Cluster']==c, 'Category'] = labels[idx] if idx < len(labels) else f'C{idx+1}'

    result = merged[['Province_cn', 'CO2_Mt', 'GDP', 'Pop', 'Closeness', 'Category']].copy()
    result['Rank'] = result['Closeness'].rank(ascending=False).astype(int)
    result.sort_values('Rank', inplace=True)
    print("\n====== Provincial Carbon Emission Ranking ======")
    print(result[['Rank', 'Province_cn', 'CO2_Mt', 'Closeness', 'Category']].to_string(index=False))
    result.to_csv(os.path.join(RESULTS, 'p1_evaluation.csv'), index=False, encoding='utf-8-sig')
    print(f"\nSaved: results/p1_evaluation.csv")

    plot_results(merged, w, e, indicator_names)

    print("\n====== Cluster Analysis ======")
    for cat in sorted(merged['Category'].unique()):
        sub = merged[merged['Category']==cat]
        print(f"  {cat} (avg C={sub['Closeness'].mean():.4f}): {', '.join(sub['Province_cn'].values)}")
    return merged

if __name__ == '__main__':
    main()
