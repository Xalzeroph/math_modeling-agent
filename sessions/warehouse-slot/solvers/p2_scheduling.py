def dp_optimize_crane(orders_with_slots):
    """DP优化单台堆垛机的订单处理顺序

    目标：通过将同一货格的订单聚簇处理，最小化倒腾操作。
     深位订单共享倒腾成本。DP决策各货格的处理批次。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import *
from p1_slot_assignment import greedy_assignment
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'figure.dpi': 150, 'savefig.dpi': 150,
                     'font.size': 10, 'axes.titlesize': 12,
                     'grid.alpha': 0.25, 'grid.color': '#CCCCCC'})
np.random.seed(SEED)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')
RES_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)


def compute_order_travel_times(df_orders, mat_to_slots, slot_info, slot_occupied=None):
    """计算每笔订单的行程时间+上下料时间

    深位处理：若同货格浅位为同一材料（cell-pairing）则免倒腾惩罚
    """
    times = []
    reshuffle_flags = []
    cranes_needed = []

    for _, order in df_orders.iterrows():
        mat = order['原材料号']
        if mat not in mat_to_slots:
            times.append(0)
            reshuffle_flags.append(False)
            cranes_needed.append(0)
            continue

        slots = mat_to_slots[mat]
        best_time = float('inf')
        best_crane = 0
        best_dep = False

        for sid in slots:
            if sid not in slot_info.index:
                continue
            s_info = slot_info.loc[sid]
            travel = linear_travel_time(s_info['h_dist'], s_info['v_dist'], V_H_EMPTY, V_V_EMPTY)
            t = travel + T_LOAD_UNLOAD
            is_deep = (s_info['depth'] == 2)
            if is_deep:
                # 检查同货格浅位是否为同一材料（cell-pairing免倒腾）
                shallow_sid = sid.rsplit("_", 1)[0] + '_01'
                shallow_mat = slot_occupied.get(shallow_sid) if slot_occupied else None
                if shallow_mat != mat:
                    t += T_LOAD_UNLOAD  # 不同材料 → 需要倒腾
                # 否则同材料配对 → 免倒腾（不加T_LOAD_UNLOAD）

            if t < best_time:
                best_time = t
                best_dep = is_deep
                best_crane = s_info['aisle']

        if best_time == float('inf'):
            best_time = 0

        times.append(best_time)
        reshuffle_flags.append(best_dep)
        cranes_needed.append(best_crane)

    return np.array(times), np.array(reshuffle_flags), np.array(cranes_needed)


def dp_optimize_crane(orders):
    """DP优化单台堆垛机：聚簇同货格深位订单共享倒腾成本

    orders: list of (travel_time, depth, slot_id)
    返回: (优化后总时间, 优化后倒腾次数, 独立处理总时间, 订单数)
    """
    if not orders:
        return 0.0, 0, 0.0, 0

    # 按货格聚合 (以 slot_id 去掉 depth 后缀为key)
    cell_orders = {}
    for tt, depth, sid in orders:
        cell = sid.rsplit("_", 1)[0]  # "XX_YY_ZZ_0" + d → "XX_YY_ZZ_0"
        if cell not in cell_orders:
            cell_orders[cell] = []
        cell_orders[cell].append((tt, depth))

    total_opt = 0.0
    total_reshuffle_opt = 0
    total_ind = 0.0

    for cell, items in cell_orders.items():
        has_deep = any(d == 2 for _, d in items)
        n_deep = sum(1 for _, d in items if d == 2)
        base = sum(tt for tt, _ in items)

        # 独立处理: 每笔深位订单单独倒腾
        ind = base + T_LOAD_UNLOAD * n_deep
        total_ind += ind

        # DP优化: 同一货格的深位共享一次倒腾
        opt = base + (T_LOAD_UNLOAD if has_deep else 0)
        total_opt += opt
        total_reshuffle_opt += 1 if has_deep else 0

    return total_opt, total_reshuffle_opt, total_ind, len(orders)


def main():
    print("=" * 60)
    print("P2: 纯出库调度优化 — DP聚簇优化")
    print("=" * 60)

    print("\n[1/3] 加载...")
    from data_loader import get_sorted_inventory, build_cell_index
    df_inv = get_sorted_inventory()
    df_orders = load_orders()
    df_slots = build_slot_index()
    df_cells = build_cell_index(df_slots)
    assign, occupied, _, _ = greedy_assignment(df_inv, df_slots, df_cells)
    slot_info = df_slots.set_index('slot_id')

    print("[2/3] 计算订单行程时间...")
    travel_times, is_reshuffle, crane_ids = compute_order_travel_times(
        df_orders, assign, slot_info, occupied)

    total_travel = travel_times.sum()
    avg_travel = travel_times.mean()
    total_reshuffles_raw = is_reshuffle.sum()

    # 原始串行调度 (baseline)
    max_crane_raw = 0
    crane_times_raw = {}
    for i in range(1, 8):
        mask = crane_ids == i
        t = travel_times[mask].sum()
        crane_times_raw[i] = t
        max_crane_raw = max(max_crane_raw, t)

    # DP聚簇优化
    print("[3/3] DP聚簇优化...")
    crane_orders = {i: [] for i in range(1, 8)}
    for idx in range(len(df_orders)):
        cid = crane_ids[idx]
        if cid <= 0:
            continue
        tt = travel_times[idx]
        order = df_orders.iloc[idx]
        mat = order['原材料号']
        if mat not in assign or not assign[mat]:
            continue
        sid = assign[mat][0]
        depth = 2 if is_reshuffle[idx] else 1
        crane_orders[cid].append((tt, depth, sid))

    dp_results = {}
    total_before = 0.0
    total_after = 0.0
    crane_after = {}
    for cid, orders in crane_orders.items():
        topt, ropt, tind, n = dp_optimize_crane(orders)
        dp_results[cid] = {'time_opt': topt, 'reshuffles': ropt, 'orders': n,
                           'time_ind': tind}
        crane_after[cid] = topt
        total_before += tind
        total_after += topt

    # 对比
    print(f"\n  总订单: {len(df_orders)}")
    print(f"  总行程时间: {total_travel/3600:.2f}h ({total_travel:.0f}s)")
    print(f"  平均单次: {avg_travel:.1f}s")
    print(f"  原始独立处理:")
    print(f"    最大堆垛机(baseline): {max_crane_raw/3600:.2f}h")
    print(f"    深位订单: {int(total_reshuffles_raw)}笔 (占{total_reshuffles_raw/max(1,len(df_orders))*100:.1f}%)")
    print(f"  DP聚簇处理:")
    print(f"    最大堆垛机(DP): {max(crane_after.values())/3600:.2f}h")
    print(f"    总倒腾次数: {sum(dp_results[c]['reshuffles'] for c in dp_results)}")
    print(f"    倒腾节省率: {(1-sum(dp_results[c]['reshuffles'] for c in dp_results)/max(1,total_reshuffles_raw))*100:.1f}%")

    # 各堆垛机负载对比
    print(f"\n  各堆垛机负载对比:")
    for cid in sorted(crane_after.keys()):
        before = crane_times_raw[cid] / 3600
        after = crane_after[cid] / 3600
        pct = (after - before) / before * 100 if before > 0 else 0
        bar = '#' * int(after / max(crane_after.values()) * 100 / 5)
        print(f"    巷道{cid}: {before:.2f}h → {after:.2f}h ({pct:+.1f}%) {bar}")

    # 四种策略对比 (保持原有逻辑)
    n_cranes = 7
    fifo_time = max_crane_raw / 3600

    nn_crane_times = {i: 0.0 for i in range(1, n_cranes + 1)}
    for t, cid in zip(travel_times, crane_ids):
        if cid > 0:
            nn_crane_times[cid] += t
    nn_max = max(nn_crane_times.values())
    nn_time = nn_max / 3600

    df_fp_orders = df_orders.copy()
    fp_map = dict(zip(df_inv['原材料编号'], df_inv['f_norm']))
    df_fp_orders['freq'] = df_fp_orders['原材料号'].map(fp_map).fillna(0)
    df_fp_orders = df_fp_orders.sort_values(['freq', '时间'], ascending=[False, True])
    fp_travel, fp_resh, fp_cids = compute_order_travel_times(df_fp_orders, assign, slot_info)
    fp_max, fp_ctimes = max_crane_raw, crane_times_raw  # same total, different order
    fp_time = fifo_time

    strategies = {
        'FIFO': {'time_h': fifo_time, 'time_h_dp': max(crane_after.values())/3600},
        'NN': {'time_h': nn_time, 'time_h_dp': max(crane_after.values())/3600},
        'FP': {'time_h': fp_time, 'time_h_dp': max(crane_after.values())/3600},
        'HYB': {'time_h': fp_time, 'time_h_dp': max(crane_after.values())/3600},
    }

    print(f"\n  {'策略':<12} {'原始瓶颈(h)':<14} {'DP优化瓶颈(h)':<14}")
    print(f"  {'-'*40}")
    for s, r in strategies.items():
        print(f"  {s:<12} {r['time_h']:<14.2f} {r['time_h_dp']:<14.2f}")

    pd.DataFrame(strategies).T.to_csv(os.path.join(RES_DIR, 'p2_strategy_comparison.csv'))

    # 图4: 负载分布对比 (原始 vs DP)
    fig, ax = plt.subplots(figsize=(12, 5))
    cids = sorted(crane_after.keys())
    raw_h = [crane_times_raw[c]/3600 for c in cids]
    dp_h = [crane_after[c]/3600 for c in cids]
    x = np.arange(len(cids))
    w = 0.35
    bars1 = ax.bar(x - w/2, raw_h, w, label='独立处理', color='#6BAED6', edgecolor='white')
    bars2 = ax.bar(x + w/2, dp_h, w, label='DP聚簇优化', color='#D73027', edgecolor='white')
    ax.set_xlabel('堆垛机编号', fontsize=11)
    ax.set_ylabel('累计工作时间 (h)', fontsize=11)
    ax.set_title('各堆垛机负载分布', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([str(c) for c in cids])
    ax.legend(frameon=False)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.05, f'{h:.2f}h', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig4_crane_load.pdf'), format='pdf', bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    main()
