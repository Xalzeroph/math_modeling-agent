import numpy as np, pandas as pd, matplotlib, sys, os, json
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_loader import get_national_stats, get_national_emissions
plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
RESULTS = os.path.join(os.path.dirname(__file__), '..', 'results')
FIGURES = os.path.join(os.path.dirname(__file__), '..', 'figures')

def main():
    print("="*60)
    print("Problem 3: Kaya Scenario Prediction 2026-2045")
    print("="*60)
    stats = get_national_stats()
    yearly_co2 = get_national_emissions()
    yearly_co2 = yearly_co2[yearly_co2.index <= 2023]
    data = stats[stats['Year'].isin(yearly_co2.index)].copy()
    data['CO2'] = yearly_co2.values
    data['GDP_per_cap'] = data['GDP'] * 1e4 / data['Pop']
    data['C_intensity'] = data['CO2'] * 100 / data['GDP']

    hist_gdp_g = float(np.mean(np.diff(np.log(data['GDP'].values))))
    hist_pop_g = float(np.mean(np.diff(np.log(data['Pop'].values))))
    hist_ci_c = float(np.mean(np.diff(np.log(data['C_intensity'].values))))

    base = data.iloc[-1]
    base_pop = base['Pop']; base_gdp_pc = base['GDP_per_cap']; base_ci = base['C_intensity']; base_co2 = base['CO2']
    print(f"Historical: GDP={hist_gdp_g*100:.2f}%/yr, Pop={hist_pop_g*100:.2f}%/yr, CI={hist_ci_c*100:.2f}%/yr")
    print(f"Base 2023: CO2={base_co2:.1f}Mt")

    # Extend historical 2024-2025
    t_yrs = np.arange(len(data))
    trend = np.polyfit(t_yrs, np.log(data['CO2'].values), 1)
    hist_years = list(range(2019, 2026))
    hist_co2_full = list(data['CO2'].values)
    hist_co2_full.append(float(np.exp(np.polyval(trend, len(data)))))
    hist_co2_full.append(float(np.exp(np.polyval(trend, len(data)+1))))

    # Time-varying rate scenarios
    years = np.arange(2026, 2046)
    scenarios = {
        'Baseline (BAU)': {
            'gdp_s': hist_gdp_g*0.95, 'gdp_e': hist_gdp_g*0.85,
            'ci_s': hist_ci_c, 'ci_e': hist_ci_c*1.1,
            'pop': hist_pop_g
        },
        'Carbon Reduction': {
            'gdp_s': hist_gdp_g*0.85, 'gdp_e': hist_gdp_g*0.65,
            'ci_s': hist_ci_c*1.15, 'ci_e': hist_ci_c*1.45,
            'pop': hist_pop_g
        },
        'Enhanced Reduction': {
            'gdp_s': hist_gdp_g*0.70, 'gdp_e': hist_gdp_g*0.45,
            'ci_s': hist_ci_c*1.30, 'ci_e': hist_ci_c*1.80,
            'pop': hist_pop_g*0.95
        }
    }

    results = {}
    peak_results = {}
    print("\n====== Scenario Forecast ======")
    for sn, sp in scenarios.items():
        n = len(years)
        gdp_r = np.linspace(sp['gdp_s'], sp['gdp_e'], n)
        ci_r = np.linspace(sp['ci_s'], sp['ci_e'], n)
        p, a, t = base_pop, base_gdp_pc, base_ci
        co2_list = []
        for i in range(n):
            p *= np.exp(sp['pop'])
            a *= np.exp(gdp_r[i])
            t *= np.exp(ci_r[i])
            co2_list.append(p * a * t / 1e6)
        results[sn] = pd.DataFrame({'Year': years, 'CO2_Mt': co2_list})
        pi = int(np.argmax(co2_list))
        msg = 'peak' if 0 < pi < n-1 else 'monotonic'
        peak_results[sn] = {'peak_year': int(years[pi]), 'peak_value': float(co2_list[pi]), 'type': msg}
        print(f"  {sn}: peak at {years[pi]} ({co2_list[pi]:.0f}Mt) [{msg}]")

    # Plot
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.5))
    colors = {'Baseline (BAU)': '#2171B5', 'Carbon Reduction': '#FEC44F', 'Enhanced Reduction': '#D73027'}
    a1.plot(hist_years, hist_co2_full, 'o-', color='gray', lw=2.5, label='Historical')
    a1.plot(2023, base_co2, 'o', color='black', ms=8)
    for sn in results:
        df = results[sn]; p = peak_results[sn]
        a1.plot(df['Year'], df['CO2_Mt'], color=colors[sn], lw=2.5, label=sn)
        if p['type'] == 'peak':
            a1.scatter(p['peak_year'], p['peak_value'], color=colors[sn], s=150, marker='*', edgecolors='black', zorder=5)
            a1.annotate(f"{p['peak_year']}\n{p['peak_value']:.0f}Mt", xy=(p['peak_year'],p['peak_value']), fontsize=8, xytext=(8,8), textcoords='offset points')
    a1.axhline(y=base_co2, color='gray', ls=':', alpha=0.5)
    a1.set_xlabel('Year'); a1.set_ylabel('CO2 (Mt)')
    a1.set_title('China CO2 Emission Scenarios (Time-varying Kaya)')
    a1.legend(fontsize=9); a1.grid(alpha=0.25); a1.set_xlim(2018, 2046)

    for sn in scenarios:
        sp = scenarios[sn]
        ci_r = np.linspace(sp['ci_s'], sp['ci_e'], len(years))
        ci_vec = base_ci * np.exp(np.cumsum(np.concatenate([[0], ci_r[:-1]])))
        a2.plot(years, ci_vec, color=colors[sn], lw=2.5, label=sn)
    a2.set_xlabel('Year'); a2.set_ylabel('Carbon Intensity (t/10k yuan)')
    a2.set_title('Carbon Intensity Scenarios')
    a2.legend(fontsize=9); a2.grid(alpha=0.25); a2.set_xlim(2025, 2046)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES, 'p3_scenarios.pdf'), format='pdf', bbox_inches='tight')
    plt.close()

    # Save
    for sn, df in results.items():
        fname = sn.lower().replace(' ','_').replace('(','').replace(')','') + '.csv'
        df.to_csv(os.path.join(RESULTS, fname), index=False)
    with open(os.path.join(RESULTS, 'p3_summary.json'), 'w') as f:
        json.dump({'peak_analysis': peak_results}, f, indent=2)

    print("\n====== Policy Recommendations ======")
    for sn, p in peak_results.items():
        print(f"  {sn}: {p['type']} at {p['peak_year']} ({p['peak_value']:.0f}Mt)")
    print("  Accelerating CI decline + moderating GDP growth is key to early peak.")

if __name__ == '__main__':
    main()
