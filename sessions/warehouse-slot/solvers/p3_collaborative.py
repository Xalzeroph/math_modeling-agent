"""
P3: 入库-出库协同优化 — 分阶段：货位选择 + 二分图最大权匹配

阶段1: 入库货位贪心分配（按空位距离+频率加权）
阶段2: DC配对 — Hungarian算法精确求解二分图最大权匹配

行程时间:
  SC = linear_travel_time + T_load  (往返)
  DC = one_way(out) + T_load + one_way(between) + T_load + one_way(in_ret)
      ↑三段均为单程，不用 linear_travel_time
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


def hungarian_dc_pairing(out_nodes, in_nodes, time_window=7200):
    """Hungarian算法求解 DC 配对（单巷道最大权匹配）

    Args:
        out_nodes: list of dicts with keys [time, t_sc, hd, vd]
        in_nodes:  list of dicts with keys [time, t_sc, t_one_way, hd, vd]
        time_window: 时间窗(s), 默认2h

    Returns:
        pairs: list of (i, j, saving) paired indices
        unpaired_out: set of unmatched outbound indices
        unpaired_in: set of unmatched inbound indices
    """
    n_out, n_in = len(out_nodes), len(in_nodes)
    if n_out == 0 or n_in == 0:
        return [], set(range(n_out)), set(range(n_in))

    # 构建节省量矩阵
    savings = np.zeros((n_out, n_in))
    for i, o in enumerate(out_nodes):
        for j, p in enumerate(in_nodes):
            td = abs((o['time'] - p['time']).total_seconds())
            if td > time_window:
                savings[i, j] = -1e9  # 无效边
            else:
                # T_DC = one_way(out) + T_load + one_way(between) + T_load + one_way(in)
                hd_btw = abs(o['hd'] - p['hd'])
                vd_btw = abs(o['vd'] - p['vd'])
                t_btw = one_way_travel_time(hd_btw, vd_btw, V_H_EMPTY, V_V_EMPTY)
                t_out_one = one_way_travel_time(o['hd'], o['vd'], V_H_EMPTY, V_V_EMPTY)
                t_dc = t_out_one + T_LOAD_UNLOAD + t_btw + T_LOAD_UNLOAD + p['t_one_way']
                t_sc_both = o['t_sc'] + p['t_sc']  # 两次SC
                savings[i, j] = t_sc_both - t_dc

    # Hungarian只做方阵且最小化 → 补零行列
    n = max(n_out, n_in)
    cost = np.zeros((n, n))
    cost[:n_out, :n_in] = -savings
    # 填充无效边为大数
    cost[cost > 1e8] = 1e9

    from scipy.optimize import linear_sum_assignment
    row_ind, col_ind = linear_sum_assignment(cost)

    pairs = []
    paired_out = set()
    paired_in = set()
    for i, j in zip(row_ind, col_ind):
        if i < n_out and j < n_in and savings[i, j] > 0:
            pairs.append((i, j, savings[i, j]))
            paired_out.add(i)
            paired_in.add(j)

    unpaired_out = set(range(n_out)) - paired_out
    unpaired_in = set(range(n_in)) - paired_in
    return pairs, unpaired_out, unpaired_in


def simulate_dc(df_orders, df_inbound, assign, df_slots, slot_occupied, f_norm_map):
    """分阶段求解 P3：货位选择 + DC 配对优化"""
    slot_info = df_slots.set_index('slot_id')
    occupied_set = set(slot_occupied.keys())
    empty_slots = df_slots[~df_slots['slot_id'].isin(occupied_set)].copy()

    # 预计算空位的 one_way 时间（P3统一使用空载速度）
    empty_slots['one_way'] = np.maximum(
        empty_slots['h_dist'] / V_H_EMPTY,
        empty_slots['v_dist'] / V_V_EMPTY)
    # 按 allowed_types + travel_time 预排序
    empty_slots = empty_slots.sort_values(['allowed_types', 'travel_time'])

    # === 阶段1: 入库货位分配（频率三级梯队） ===
    # 高频率(f>0.01): 近端梯队(T1)，中频率(0.001<f≤0.01): 中端梯队(T2)
    # 低频率(f≤0.001): 远端梯队(T3)
    # 按箱型预分组避免逐次扫描
    slot_by_type = {}
    for t in ['E1', 'E1E3', 'E1E3E4']:
        s = empty_slots[empty_slots['allowed_types'] == t].copy()
        n = len(s)
        # 三等分梯队
        s['tier'] = 'T1'
        s.iloc[:max(1, n//3), s.columns.get_loc('tier')] = 'T1'
        s.iloc[max(1, n//3):max(2, 2*n//3), s.columns.get_loc('tier')] = 'T2'
        s.iloc[max(2, 2*n//3):, s.columns.get_loc('tier')] = 'T3'
        slot_by_type[t] = s

    inbound_list = []
    in_nodes_by_aisle = {k: [] for k in range(1, 8)}
    # 每个梯队独立指针
    tier_ptr = {t: {r: 0 for r in ['T1','T2','T3']} for t in ['E1','E1E3','E1E3E4']}

    for _, row in df_inbound.iterrows():
        mat = row['原材料编号']
        bt = row['箱子类型']
        qty = int(row['入库数量/箱'])
        f = f_norm_map.get(mat, 0.001)
        # 确定梯队
        if f > 0.01:
            tier = 'T1'
        elif f > 0.001:
            tier = 'T2'
        else:
            tier = 'T3'

        type_key = {'E4': 'E1E3E4', 'E3': 'E1E3', 'E1': 'E1'}[bt]
        if tier == 'T3':
            # T3溢出可用T2
            tier_keys = ['T3', 'T2']
        else:
            tier_keys = [tier]

        for _ in range(qty):
            found = None
            found_tier = None
            for tk in tier_keys:
                pool = slot_by_type.get(type_key)
                if pool is None:
                    continue
                ptr = tier_ptr[type_key][tk]
                mask = pool['tier'] == tk
                tier_pool = pool[mask]
                if ptr < len(tier_pool):
                    found = tier_pool.iloc[ptr]
                    found_tier = tk
                    tier_ptr[type_key][tk] = ptr + 1
                    break
            if found is None and tier == 'T3':
                # 从T2溢出
                pool = slot_by_type.get(type_key)
                if pool is not None:
                    ptr = tier_ptr[type_key]['T2']
                    mask = pool['tier'] == 'T2'
                    tier_pool = pool[mask]
                    if ptr < len(tier_pool):
                        found = tier_pool.iloc[ptr]
                        found_tier = 'T2'
                        tier_ptr[type_key]['T2'] = ptr + 1
            if found is None:
                break
            t_sc_in = found['travel_time'] + T_LOAD_UNLOAD
            entry = {
                'time': row['入库时间'], 'aisle': found['aisle'],
                'hd': found['h_dist'], 'vd': found['v_dist'],
                't_one_way': found['one_way'], 't_sc': t_sc_in
            }
            inbound_list.append(entry)
            in_nodes_by_aisle[int(found['aisle'])].append(entry)

    # === 阶段2: DC 配对（每巷道 Hungarian） ===
    out_nodes_by_aisle = {k: [] for k in range(1, 8)}
    out_tasks_done = 0
    for _, order in df_orders.iterrows():
        mat = order['原材料号']
        if mat not in assign or not assign[mat]:
            continue
        # 遍历材料的所有货位，选最优（最短时间，深位同材料免倒腾）
        best_time = float('inf')
        best_s = None
        for sid in assign[mat]:
            if sid not in slot_info.index:
                continue
            s = slot_info.loc[sid]
            tt = s['travel_time'] + T_LOAD_UNLOAD
            if s['depth'] == 2:
                shallow_sid = sid.rsplit('_', 1)[0] + '_01'
                if slot_occupied.get(shallow_sid) != mat:
                    tt += T_LOAD_UNLOAD
            if tt < best_time:
                best_time = tt
                best_s = s
        if best_s is None:
            continue
        out_nodes_by_aisle[best_s['aisle']].append({
            'time': order['时间'], 'hd': best_s['h_dist'], 'vd': best_s['v_dist'],
            't_sc': best_time
        })
        out_tasks_done += 1

    dc_pairs = 0
    dc_work = 0.0
    sc_work = 0.0

    for aisle in range(1, 8):
        out_nodes = out_nodes_by_aisle[aisle]
        in_nodes = in_nodes_by_aisle[aisle]
        pairs, unp_out, unp_in = hungarian_dc_pairing(out_nodes, in_nodes, 7200)
        dc_pairs += len(pairs)

        for i, j, saving in pairs:
            o = out_nodes[i]
            p = in_nodes[j]
            t_out_one = one_way_travel_time(o['hd'], o['vd'], V_H_EMPTY, V_V_EMPTY)
            hd_btw = abs(o['hd'] - p['hd'])
            vd_btw = abs(o['vd'] - p['vd'])
            t_btw = one_way_travel_time(hd_btw, vd_btw, V_H_EMPTY, V_V_EMPTY)
            t_dc = t_out_one + T_LOAD_UNLOAD + t_btw + T_LOAD_UNLOAD + p['t_one_way']
            dc_work += t_dc

        # 未配对的出库 → SC
        for i in unp_out:
            dc_work += out_nodes[i]['t_sc']

        # 未配对的入库 → SC
        for j in unp_in:
            dc_work += in_nodes[j]['t_sc']

    # SC baseline: 全部独立SC
    sc_work = sum(o['t_sc'] for nodes in out_nodes_by_aisle.values() for o in nodes)
    sc_work += sum(p['t_sc'] for p in inbound_list)
    # 如果有未被分配的入库箱（空位不足），不计数

    return sc_work, dc_work, dc_pairs, out_tasks_done


def main():
    print("=" * 60)
    print("P3: 入库-出库协同优化 (Hungarian DC配对)")
    print("=" * 60)

    print("[1/2] 加载与计算...")
    from data_loader import get_sorted_inventory, build_cell_index, load_inventory
    df_inv = get_sorted_inventory()
    df_orders = load_orders()
    df_inbound = load_inbound()
    df_slots = build_slot_index()
    df_cells = build_cell_index(df_slots)

    # 预加载 f_norm 映射
    df_inv_full = load_inventory()
    f_norm_map = dict(zip(df_inv_full['原材料编号'], df_inv_full['f_norm']))

    assign, slot_occ, et_base, _ = greedy_assignment(df_inv, df_slots, df_cells)

    print("\n[2/2] 分阶段求解（Hungarian 配对）...")
    sc_work, dc_work, dc_pairs, total_possible = simulate_dc(
        df_orders, df_inbound, assign, df_slots, slot_occ, f_norm_map)

    sc_h = sc_work / 3600
    dc_h = dc_work / 3600
    sc_actual = sc_h / 7
    dc_actual = dc_h / 7
    saving = (sc_actual - dc_actual) / sc_actual * 100 if sc_actual > 0 else 0

    print(f"  出库任务总数: {total_possible}")
    print(f"  入库箱总数: {df_inbound['入库数量/箱'].sum():.0f}")
    print(f"  DC 配对成功 (Hungarian): {dc_pairs}")
    print(f"  单作业总工时: {sc_h:.2f}h, 实际运营: {sc_actual:.2f}h")
    print(f"  复合作业总工时: {dc_h:.2f}h, 实际运营: {dc_actual:.2f}h")
    print(f"  节省: {saving:.1f}%")

    # 图
    fig, ax = plt.subplots(figsize=(8, 5))
    heights = [sc_actual, dc_actual]
    bars = ax.bar(['单作业模式', '复合作业模式(Hungarian)'], heights,
                  color=['#2171B5', '#238B45'], edgecolor='white')
    for bar, h in zip(bars, heights):
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.1, f'{h:.2f}h',
                ha='center', fontsize=11)
    ax.set_ylabel('完成时间 (h)', fontsize=11)
    ax.set_title('单作业 vs 复合作业(Hungarian)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, max(heights) * 1.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig9_dual_vs_single.pdf'), format='pdf', bbox_inches='tight')
    plt.close()

    with open(os.path.join(RES_DIR, 'p3_results.txt'), 'w') as f:
        f.write(f"方法: Hungarian 二分图最大权匹配\n")
        f.write(f"单作业总工时: {sc_h:.2f}h\n")
        f.write(f"复合作业总工时: {dc_h:.2f}h\n")
        f.write(f"DC配对: {dc_pairs}/{total_possible}\n")
        f.write(f"实际运营(SC): {sc_actual:.2f}h\n")
        f.write(f"实际运营(DC): {dc_actual:.2f}h\n")
        f.write(f"节省: {saving:.1f}%\n")

    print(f"  -> fig9_dual_vs_single.pdf")
    print("=" * 60)
    return saving


if __name__ == "__main__":
    main()
