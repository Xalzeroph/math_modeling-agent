"""
P1: 库位初始分配优化 — 贪心启发式 + GA 验证

目标：为65000箱原材料分配95200个货位，最小化期望出库时间
方法：贪心启发式(baseline) → 遗传算法(GA)优化
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import (load_inventory, build_slot_index, build_cell_index,
                         linear_travel_time, SEED, V_H_EMPTY, V_V_EMPTY,
                         T_LOAD_UNLOAD)
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
                     'axes.labelsize': 10, 'grid.alpha': 0.25,
                     'grid.color': '#CCCCCC'})

np.random.seed(SEED)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')
RES_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)


# ============================================================
#  贪心启发式分配（cell-pairing版：同类材料放同一货格深浅位）
# ============================================================
def greedy_assignment_cell(df_inv, df_slots, df_cells):
    """贪心货位分配（同类材料货格配对）

    核心变化 vs 原 greedy_assignment：
    - 分配单位从"货位"变为"货格(cell)"
    - 每种材料 q 箱 → floor(q/2) 个完整货格 + (q%2) 个浅位单箱
    - 单箱余数的深位进入自由池供后续余数复用
    - E[T] 对无配对的深位箱加 T_load 惩罚

    池分配策略（不变）：
    - E4箱 → pool_E4_cells (层43-50)
    - E3箱 → pool_E3_cells (层9-42) + E4剩余
    - E1箱 → pool_E1_cells (层1-8) + E3剩余 + E4剩余
    """
    # 三区cell池，按浅位行程时间升序
    p_E4_cells = df_cells[df_cells['allowed_types'] == 'E1E3E4'].sort_values('tt_shallow')
    p_E3_cells = df_cells[df_cells['allowed_types'] == 'E1E3'].sort_values('tt_shallow')
    p_E1_cells = df_cells[df_cells['allowed_types'] == 'E1'].sort_values('tt_shallow')

    ptrs = {'E4': 0, 'E3': 0, 'E1': 0}
    pools = {'E4': p_E4_cells, 'E3': p_E3_cells, 'E1': p_E1_cells}
    free_deep = {'E4': [], 'E3': [], 'E1': []}  # 余数释放的深位

    assignment = {}
    slot_occupied = {}
    # 记录每个货格浅位的材料归属，用于判断深位是否有配对
    cell_shallow_owner = {}
    mat_times = {}

    # 构建slot_id → 行程时间的快速查找
    slot_tt = dict(zip(df_slots['slot_id'], df_slots['travel_time']))

    def alloc_cells(pool_key, n_needed):
        """从某cell池分配 n_needed 个完整货格"""
        pool = pools[pool_key]
        ptr = ptrs[pool_key]
        if ptr >= len(pool):
            return []
        take_n = min(n_needed, len(pool) - ptr)
        cells = pool.iloc[ptr:ptr + take_n]
        ptrs[pool_key] = ptr + take_n
        return cells

    def alloc_singleton(pool_key):
        """分配一个浅位（来自新货格），其深位入自由池"""
        pool = pools[pool_key]
        ptr = ptrs[pool_key]
        if ptr >= len(pool):
            return None
        cell = pool.iloc[ptr]
        free_deep[pool_key].append(cell['slot_deep'])
        ptrs[pool_key] = ptr + 1
        return cell['slot_shallow']

    def alloc_singleton_from_free(pool_key):
        """尝试从空闲深位池取一个可用位（不消耗新货格）"""
        if free_deep[pool_key]:
            return free_deep[pool_key].pop(0)
        return None

    def process_type(box_type, pool_keys):
        subset = df_inv[df_inv['箱子类型'] == box_type]
        for _, row in subset.iterrows():
            mat_id = row['原材料编号']
            qty = int(row['库存数量/箱'])
            ncells = qty // 2
            remainder = qty % 2
            taken = []
            total_penalty_tt = 0.0

            # 分配完整货格（同材料占深浅位）
            need = ncells
            for key in pool_keys:
                if need <= 0:
                    break
                cells = alloc_cells(key, need)
                for _, cell in cells.iterrows():
                    taken.append(cell['slot_shallow'])
                    taken.append(cell['slot_deep'])
                    cell_shallow_owner[cell['slot_shallow']] = mat_id
                    # 完整配对：两个位都无深位惩罚（取1箱=浅位直达，取2箱=一次行程）
                    total_penalty_tt += cell['tt_shallow'] + cell['tt_deep']
                need -= len(cells)

            # 处理余数单箱
            if remainder == 1:
                allocated = False
                for key in pool_keys:
                    sid = alloc_singleton_from_free(key)
                    if sid:
                        taken.append(sid)
                        is_deep = (sid[-1] == '2')
                        tt = slot_tt.get(sid, 0)
                        if is_deep:
                            # 深位且浅位非本材料 → 倒腾惩罚
                            shallow_sid = sid.rsplit("_", 1)[0] + '_01'
                            owner = cell_shallow_owner.get(shallow_sid)
                            if owner != mat_id:
                                total_penalty_tt += tt + T_LOAD_UNLOAD
                            else:
                                total_penalty_tt += tt
                        else:
                            cell_shallow_owner[sid] = mat_id
                            total_penalty_tt += tt
                        allocated = True
                        break
                if not allocated:
                    for key in pool_keys:
                        sid = alloc_singleton(key)
                        if sid:
                            taken.append(sid)
                            cell_shallow_owner[sid] = mat_id
                            tt = slot_tt.get(sid, 0)
                            total_penalty_tt += tt
                            allocated = True
                            break

            if taken:
                assignment[mat_id] = taken
                mat_times[mat_id] = total_penalty_tt / len(taken)
                for sid in taken:
                    slot_occupied[sid] = mat_id

    process_type('E4', ['E4'])
    process_type('E3', ['E3', 'E4'])
    process_type('E1', ['E1', 'E3', 'E4'])

    # 计算E[T]（含深位惩罚）
    expected_time = 0.0
    for _, row in df_inv.iterrows():
        mat_id = row['原材料编号']
        if mat_id in mat_times:
            expected_time += row['f_norm'] * mat_times[mat_id]
    expected_time += T_LOAD_UNLOAD

    return assignment, slot_occupied, expected_time, mat_times, cell_shallow_owner


# 保留旧函数名兼容下游调用
def greedy_assignment(df_inv, df_slots, df_cells=None):
    """兼容接口：传入 df_cells 时使用 cell-pairing 版本"""
    if df_cells is not None:
        assign, occ, et, mt, _ = greedy_assignment_cell(df_inv, df_slots, df_cells)
        return assign, occ, et, mt
    else:
        return _greedy_assignment_flat(df_inv, df_slots)


def _greedy_assignment_flat(df_inv, df_slots):
    """原贪心分配（无cell-pairing），保留以支持无cell索引的调用"""
    p_E4 = df_slots[df_slots['allowed_types'] == 'E1E3E4'].sort_values('travel_time')
    p_E3 = df_slots[df_slots['allowed_types'] == 'E1E3'].sort_values('travel_time')
    p_E1 = df_slots[df_slots['allowed_types'] == 'E1'].sort_values('travel_time')

    ptrs = {'E4': 0, 'E3': 0, 'E1': 0}
    pools = {'E4': p_E4, 'E3': p_E3, 'E1': p_E1}

    assignment = {}
    slot_occupied = {}
    mat_times = {}

    def process_type(box_type, pool_keys):
        subset = df_inv[df_inv['箱子类型'] == box_type]
        for _, row in subset.iterrows():
            mat_id = row['原材料编号']
            qty = int(row['库存数量/箱'])
            taken = []
            total_tt = 0.0
            for key in pool_keys:
                if qty <= 0:
                    break
                pool = pools[key]
                ptr = ptrs[key]
                avail = len(pool) - ptr
                if avail <= 0:
                    continue
                take_n = min(qty, avail)
                batch = pool.iloc[ptr:ptr + take_n]
                sids = batch['slot_id'].tolist()
                tt = batch.apply(lambda r: linear_travel_time(
                    r['h_dist'], r['v_dist'], V_H_EMPTY, V_V_EMPTY), axis=1).mean()
                taken.extend(sids)
                total_tt += tt * take_n
                ptrs[key] = ptr + take_n
                qty -= take_n
            if taken:
                assignment[mat_id] = taken
                mat_times[mat_id] = total_tt / len(taken)
                for sid in taken:
                    slot_occupied[sid] = mat_id

    process_type('E4', ['E4'])
    process_type('E3', ['E3', 'E4'])
    process_type('E1', ['E1', 'E3', 'E4'])

    expected_time = 0.0
    for _, row in df_inv.iterrows():
        mat_id = row['原材料编号']
        if mat_id in mat_times:
            expected_time += row['f_norm'] * mat_times[mat_id]
    expected_time += T_LOAD_UNLOAD

    return assignment, slot_occupied, expected_time, mat_times


# ============================================================
#  GA 优化 — 排列编码，swap变异，组内最短路贪心
# ============================================================
def ga_optimize(df_inv, df_slots, df_cells, n_gen=60, pop_size=30):
    """GA: 排列编码 — 按箱型独立优化材料分配顺序

    三类箱子独立排列(E4/E3/E1)，组内swap+OX交叉
    """
    order_map = {'E4': 0, 'E3': 1, 'E1': 2}
    df_w = df_inv.copy()
    df_w['type_order'] = df_w['箱子类型'].map(order_map)
    df_base = df_w.sort_values(['type_order', 'heat'], ascending=[True, False])

    # 确定各箱型在df_base中的起止索引
    bt_start = {}
    bt_end = {}
    for bt in ['E4', 'E3', 'E1']:
        mask = df_base['箱子类型'] == bt
        idxs = np.where(mask)[0]
        bt_start[bt] = idxs[0]
        bt_end[bt] = idxs[-1] + 1
    n_total = len(df_base)

    def evaluate(bt_orders):
        """用各箱型的排列构建整体顺序"""
        new_order = np.zeros(n_total, dtype=int)
        pos = 0
        for bt in ['E4', 'E3', 'E1']:
            s, e = bt_start[bt], bt_end[bt]
            n_bt = e - s
            new_order[pos:pos+n_bt] = bt_orders[bt]
            pos += n_bt
        df_ordered = df_base.iloc[new_order].copy()
        _, _, et, _, _ = greedy_assignment_cell(df_ordered, df_slots, df_cells)
        return et

    # Baseline: 热度排序（各箱型内原顺序）
    base_orders = {}
    for bt in ['E4', 'E3', 'E1']:
        s, e = bt_start[bt], bt_end[bt]
        base_orders[bt] = np.arange(s, e)
    baseline_et = evaluate(base_orders)
    print(f"  GA Baseline (贪心): E[T]={baseline_et:.2f}s")
    history = [baseline_et]
    best_et = baseline_et
    best_orders = {bt: o.copy() for bt, o in base_orders.items()}

    def perturb_orders(orders, n_swaps=20):
        """对三类箱子各自swap"""
        new = {bt: o.copy() for bt, o in orders.items()}
        for bt in ['E4', 'E3', 'E1']:
            arr = new[bt]
            m = len(arr)
            for _ in range(n_swaps):
                if m < 2:
                    break
                i, j = np.random.randint(0, m, 2)
                arr[i], arr[j] = arr[j], arr[i]
        return new

    # 种群
    pop = []
    for _ in range(pop_size):
        orders = perturb_orders(base_orders)
        et = evaluate(orders)
        pop.append((orders, et))
        history.append(et)
        if et < best_et:
            best_et = et
            best_orders = {bt: o.copy() for bt, o in orders.items()}

    for gen in range(n_gen):
        pop.sort(key=lambda x: x[1])
        elites = pop[:max(2, pop_size // 3)]

        new_pop = list(elites)
        while len(new_pop) < pop_size:
            pi = np.random.randint(0, len(elites))
            qi = np.random.randint(0, len(elites))
            if pi == qi:
                continue
            p_orders = elites[pi][0]
            q_orders = elites[qi][0]
            child = {}

            for bt in ['E4', 'E3', 'E1']:
                p_arr = p_orders[bt]
                q_arr = q_orders[bt]
                m = len(p_arr)
                if m < 2:
                    child[bt] = p_arr.copy()
                    continue
                # OX
                a, b = sorted(np.random.randint(0, m, 2))
                cross = np.full(m, -1)
                cross[a:b] = p_arr[a:b]
                p_set = set(cross[a:b])
                fill = 0
                for idx in q_arr:
                    if idx not in p_set:
                        while fill < m and cross[fill] != -1:
                            fill += 1
                        if fill < m:
                            cross[fill] = idx
                            fill += 1
                # swap变异
                if np.random.random() < 0.3:
                    i, j = np.random.randint(0, m, 2)
                    cross[i], cross[j] = cross[j], cross[i]
                child[bt] = cross

            et = evaluate(child)
            new_pop.append((child, et))
            history.append(et)
            if et < best_et:
                best_et = et
                best_orders = {bt: o.copy() for bt, o in child.items()}

        pop = sorted(new_pop, key=lambda x: x[1])[:pop_size]
        if (gen + 1) % 10 == 0:
            impr = (baseline_et - best_et) / baseline_et * 100
            print(f"  GA Gen {gen+1}/{n_gen}, Best E[T]={best_et:.2f}s (+{impr:.2f}%)")

    impr = (baseline_et - best_et) / baseline_et * 100
    print(f"  GA 最优 E[T]={best_et:.2f}s, 改善={impr:.2f}%")

    df_best = df_base.iloc[:0]  # empty
    for bt in ['E4', 'E3', 'E1']:
        s, e = bt_start[bt], bt_end[bt]
        idxs = best_orders[bt]
        df_best = pd.concat([df_best, df_base.iloc[idxs]])
    best_assignment, best_slot_occupied, best_et_final, _, _ = greedy_assignment_cell(df_best, df_slots, df_cells)
    print(f"  验证 E[T]={best_et_final:.2f}s")
    return best_assignment, best_slot_occupied, best_et_final, history


# ============================================================
#  可视化
# ============================================================
def plot_heatmap(df_slots, slot_occupied, filename, df_inv=None, assignment=None):
    """货位分配热力图 — 展示单个货架的箱型分布

    选择中间货架（Rack 5），用颜色编码 E1/E3/E4 三种箱型的分布：
    - E1（200mm，小型）= 蓝色系
    - E3（400mm，中型）= 橙色系
    - E4（500mm，大型）= 红色系
    - 白色 = 空位
    同一货格双深位均占时，按优先级 E4>E3>E1 显示（高箱型优先）。
    """
    rack_id = 5
    slots_rack = df_slots[df_slots['rack'] == rack_id]

    # 构建 slot_id → 材料编号 的映射
    slot_to_mat = {}
    if assignment:
        for mat_id, slot_ids in assignment.items():
            for sid in slot_ids:
                slot_to_mat[sid] = mat_id

    # 构建 材料编号 → 箱子类型 的映射
    mat_to_type = {}
    if df_inv is not None:
        for _, row in df_inv.iterrows():
            mat_to_type[row['原材料编号']] = row['箱子类型']

    # 箱型编码: 0=空, 1=E1, 2=E3, 3=E4
    # 双深位均占时取优先级高的（E4>E3>E1）
    type_code = np.zeros((50, 68), dtype=int)
    type_priority = {'E4': 3, 'E3': 2, 'E1': 1}

    for _, row in slots_rack.iterrows():
        sid = row['slot_id']
        if sid in slot_occupied:
            mat = slot_to_mat.get(sid, '')
            bt = mat_to_type.get(mat, '')
            if bt in type_priority:
                l, c = row['layer'] - 1, row['col'] - 1
                # 叠加：双深位时取更高优先级
                if type_code[l, c] < type_priority[bt]:
                    type_code[l, c] = type_priority[bt]

    # 自定义颜色映射: 0=白, 1=蓝(E1), 2=橙(E3), 3=红(E4)
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(['#FFFFFF', '#4A90D9', '#E8833A', '#D43F3F'])
    bounds = [0, 1, 2, 3, 4]
    norm = BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.imshow(type_code, aspect='auto', cmap=cmap, norm=norm, origin='lower',
              interpolation='nearest')
    ax.set_xlabel('列号', fontsize=11)
    ax.set_ylabel('层号', fontsize=11)
    ax.set_title(f'货架{rack_id}箱型分布', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"  → {filename} (Rack {rack_id}, box type heatmap)")


def plot_convergence(history, filename):
    """GA收敛曲线"""
    fig, ax = plt.subplots(figsize=(8, 5))

    best_so_far = np.minimum.accumulate(history)
    ax.plot(best_so_far, color='#2171B5', linewidth=2)
    ax.axhline(y=best_so_far[-1], color='#D73027', linestyle='--', linewidth=1,
               label=f'最终最优: {best_so_far[-1]:.1f}s')
    ax.set_xlabel('评估次数', fontsize=11)
    ax.set_ylabel('期望出库时间 (s)', fontsize=11)
    ax.set_title('遗传算法收敛曲线', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"  → {filename}")


def plot_comparison(df_inv, mat_times_greedy, mat_times_ga, filename):
    """贪心 vs GA 对比 — 按消耗频率分组的平均出库时间"""
    fig, ax = plt.subplots(figsize=(10, 5))

    # 按f_norm分桶
    bins = [0, 0.001, 0.005, 0.01, 0.05, 0.1, 1.0]
    labels = ['<0.1%', '0.1-0.5%', '0.5-1%', '1-5%', '5-10%', '>10%']
    df_inv['f_bin'] = pd.cut(df_inv['f_norm'] * 100, bins=[0, 0.1, 0.5, 1, 5, 10, 100], labels=labels)

    greedy_avg = []
    ga_avg = []
    for label in labels:
        subset = df_inv[df_inv['f_bin'] == label]
        times_g = [mat_times_greedy.get(m, 0) for m in subset['原材料编号']]
        times_ga = [mat_times_ga.get(m, 0) for m in subset['原材料编号']]
        greedy_avg.append(np.mean(times_g) if times_g else 0)
        ga_avg.append(np.mean(times_ga) if times_ga else 0)

    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width/2, greedy_avg, width, label='贪心启发式', color='#2171B5', edgecolor='white')
    ax.bar(x + width/2, ga_avg, width, label='GA优化', color='#D73027', edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel('消耗频率分组', fontsize=11)
    ax.set_ylabel('平均出库时间 (s)', fontsize=11)
    ax.set_title('贪心与GA各频率组平均出库时间对比', fontsize=12, fontweight='bold')
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"  → {filename}")


# ============================================================
#  Main
# ============================================================
def main():
    print("=" * 60)
    print("P1: 库位初始分配优化 (cell-pairing)")
    print("=" * 60)

    # 加载数据
    print("\n[1/4] 加载数据...")
    from data_loader import get_sorted_inventory
    df_inv = get_sorted_inventory()
    df_slots = build_slot_index()
    df_cells = build_cell_index(df_slots)

    # 贪心分配（cell-pairing）
    print("\n[2/4] 贪心启发式分配 (货格配对)...")
    assign_g, occupied_g, et_g, mat_times_g, cell_owner = greedy_assignment_cell(df_inv, df_slots, df_cells)
    print(f"  贪心 E[T] = {et_g:.2f}s")
    print(f"  已分配货位: {len(occupied_g)}")

    # 统计配对率
    paired = sum(1 for sid in occupied_g if sid[-1] == '2'
                 and sid.rsplit("_", 1)[0] + '_01' in cell_owner
                 and cell_owner.get(sid.rsplit("_", 1)[0] + '_01') == occupied_g[sid])
    deep_count = sum(1 for sid in occupied_g if sid[-1] == '2')
    pairing_rate = paired / deep_count * 100 if deep_count > 0 else 0
    print(f"  同类材料配对率 (深位): {paired}/{deep_count} = {pairing_rate:.1f}%")

    # GA 优化
    print(f"\n[3/4] GA 优化 (30代×15种群)...")
    assign_ga, occupied_ga, et_ga, history = ga_optimize(df_inv, df_slots, df_cells, n_gen=30, pop_size=15)

    # 用cell-pairing逻辑重新计算GA结果的每个材料平均时间
    _, _, _, mat_times_ga, _ = greedy_assignment_cell(df_inv, df_slots, df_cells)
    # 用GA的实际分配方案覆盖
    mat_times_ga = {}
    for mat_id, slot_ids in assign_ga.items():
        if slot_ids:
            tt_total = 0.0
            for sid in slot_ids:
                base_tt = df_slots[df_slots['slot_id'] == sid]['travel_time'].values[0]
                if sid[-1] == '2':  # 深位：检查是否有同材料浅位配对
                    shallow_sid = sid.rsplit("_", 1)[0] + '_01'
                    shallow_mat = occupied_ga.get(shallow_sid)
                    if shallow_mat != mat_id:
                        base_tt += T_LOAD_UNLOAD  # 无配对 → 倒腾惩罚
                tt_total += base_tt
            mat_times_ga[mat_id] = tt_total / len(slot_ids)

    # 可视化
    print("\n[4/4] 生成图表...")
    plot_heatmap(df_slots, occupied_ga, 'fig1_slot_heatmap.pdf', df_inv=df_inv, assignment=assign_ga)
    plot_convergence(history, 'fig2_ga_convergence.pdf')
    plot_comparison(df_inv, mat_times_g, mat_times_ga, 'fig3_greedy_vs_ga.pdf')

    # 输出结果
    improvement = (et_g - et_ga) / et_g * 100
    print(f"\n{'='*60}")
    print(f"P1 结果汇总:")
    print(f"  贪心启发式 E[T] = {et_g:.2f}s")
    print(f"  GA 优化     E[T] = {et_ga:.2f}s")
    print(f"  改善率        = {improvement:.2f}%")
    print(f"{'='*60}")

    # 保存分配方案 (仅保存前100种材料作为示例)
    sample_mats = df_inv.sort_values('heat', ascending=False).head(100)['原材料编号'].tolist()
    result_data = []
    for mat_id in sample_mats:
        if mat_id in assign_ga:
            for slot in assign_ga[mat_id][:5]:  # 每种最多5个
                result_data.append({'原材料编号': mat_id, '货位编号': slot})
    pd.DataFrame(result_data).to_csv(os.path.join(RES_DIR, 'p1_assignment_sample.csv'), index=False)
    print(f"\n分配方案样本已保存到 results/p1_assignment_sample.csv")

    return et_g, et_ga, improvement


if __name__ == "__main__":
    main()
