#!/usr/bin/env python3
"""Problem 2: Carbon emission factor analysis — Kaya + proper LMDI."""
import numpy as np, pandas as pd, matplotlib, sys, os
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_loader import get_national_stats, get_national_emissions

plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
RESULTS = os.path.join(os.path.dirname(__file__), '..', 'results')
FIGURES = os.path.join(os.path.dirname(__file__), '..', 'figures')

def log_mean(x, y):
    """Logarithmic mean L(x,y) = (x-y)/(ln x - ln y)"""
    if abs(x - y) < 1e-10:
        return x
    return (x - y) / (np.log(x) - np.log(y))

def lmdi_decompose(base, current):
    """LMDI additive decomposition of CO2 change."""
    P0, A0, T0, I0 = base
    Pt, At, Tt, It = current
    # Logarithmic mean weights
    w = log_mean(It, I0)
    dP = w * np.log(Pt/P0)
    dA = w * np.log(At/A0)
    dT = w * np.log(Tt/T0)
    return dP, dA, dT

def main():
    print("="*60)
    print("Problem 2: Carbon Emission Factor Analysis (Kaya + LMDI)")
    print("="*60)
    stats = get_national_stats()
    yearly_co2 = get_national_emissions()
    yearly_co2 = yearly_co2[yearly_co2.index <= 2023]
    data = stats[stats['Year'].isin(yearly_co2.index)].copy()
    data['CO2'] = yearly_co2.values
    data['Pop_idx'] = data['Pop'] / data['Pop'].iloc[0]
    data['GDP_per_cap'] = data['GDP'] * 1e4 / data['Pop']
    data['C_intensity'] = data['CO2'] * 100 / data['GDP']
    data['A_idx'] = data['GDP_per_cap'] / data['GDP_per_cap'].iloc[0]
    data['T_idx'] = data['C_intensity'] / data['C_intensity'].iloc[0]
    data['I_idx'] = data['CO2'] / data['CO2'].iloc[0]

    print(data[['Year','CO2','Pop','GDP_per_cap','C_intensity']].round(2).to_string(index=False))

    # Correlation
    print("\nCorrelation with CO2:")
    for f in ['Pop','GDP_per_cap','C_intensity']:
        print(f"  {f}: {data['CO2'].corr(data[f]):.4f}")

    # Kaya decomposition
    print("\nKaya Factor Index (2019=1.0):")
    print(data[['Year','Pop_idx','A_idx','T_idx','I_idx']].round(4).to_string(index=False))

    # LMDI decomposition
    base_vals = (data['Pop'].iloc[0], data['GDP_per_cap'].iloc[0], data['C_intensity'].iloc[0], data['CO2'].iloc[0])
    contribs = []
    for i in range(len(data)):
        cur = (data['Pop'].iloc[i], data['GDP_per_cap'].iloc[i], data['C_intensity'].iloc[i], data['CO2'].iloc[i])
        dP, dA, dT = lmdi_decompose(base_vals, cur)
        contribs.append({'Year':data['Year'].iloc[i], 'dCO2':cur[3]-base_vals[3], 'Pop':dP, 'Affluence':dA, 'Tech':dT})
    cdf = pd.DataFrame(contribs)

    print("\nLMDI Decomposition (Mt CO2 change from 2019):")
    print(cdf.round(1).to_string(index=False))

    last = cdf.iloc[-1]
    total_chg = last['dCO2']
    print(f"\nCumulative 2019->2023: +{total_chg:.1f} Mt")
    print(f"  Population: +{last['Pop']:.1f} Mt ({last['Pop']/total_chg*100:.1f}%)")
    print(f"  Affluence:  +{last['Affluence']:.1f} Mt ({last['Affluence']/total_chg*100:.1f}%)")
    print(f"  Technology: {last['Tech']:.1f} Mt ({last['Tech']/total_chg*100:.1f}%)")
    res = total_chg - (last['Pop']+last['Affluence']+last['Tech'])
    print(f"  Residual:   {res:.2f} Mt (should be ~0 for LMDI)")

    # Plot
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
    yrs = data['Year'].values
    a1.plot(yrs, data['CO2'], 'o-', color='#2171B5', lw=2.5, ms=8, label='CO2 Emissions')
    a1.set_xlabel('Year'); a1.set_ylabel('CO2 (Mt)')
    a1.set_title('China Carbon Emissions 2019-2023')
    a1.grid(alpha=0.25)

    a2.bar(cdf['Year'], cdf['Pop'], label='Population', color='#6BAED6', edgecolor='black')
    b = cdf['Pop'].values
    a2.bar(cdf['Year'], cdf['Affluence'], bottom=b, label='GDP/cap', color='#FEC44F', edgecolor='black')
    b += cdf['Affluence'].values
    a2.bar(cdf['Year'], cdf['Tech'], bottom=b, label='Carbon Intensity', color='#D73027', edgecolor='black')
    a2.plot(cdf['Year'], cdf['dCO2'], 'o-', color='black', lw=2.5, ms=8, label='Total Change')
    a2.axhline(y=0, color='gray', ls='--')
    a2.set_xlabel('Year'); a2.set_ylabel('CO2 Change from 2019 (Mt)')
    a2.set_title('LMDI Factor Decomposition')
    a2.legend(fontsize=8); a2.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, 'p2_kaya.pdf'), format='pdf', bbox_inches='tight')
    plt.close()

    with open(os.path.join(RESULTS, 'p2_kaya_summary.txt'), 'w') as f:
        f.write(f"CO2 change: {total_chg:.1f} Mt\n")
        f.write(f"Pop contribution: {last['Pop']:.1f} Mt\n")
        f.write(f"Affluence contribution: {last['Affluence']:.1f} Mt\n")
        f.write(f"Tech contribution: {last['Tech']:.1f} Mt\n")
        f.write(f"Residual: {res:.2f} Mt\n")

if __name__ == '__main__':
    main()
