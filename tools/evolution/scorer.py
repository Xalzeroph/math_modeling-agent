#!/usr/bin/env python3
"""
论文评分引擎 v2 — 91篇真实CUMCM论文基线 + 速度模式 + 问题类型加权

基于 mathmodel-skill 的 91 篇 p25/p50/p75 经验分布 + 4层反馈系统
+ LLM-MM-Agent 的 Actor-Critic 评估模式

用法:
  python tools/evolution/scorer.py --session "2026-数维杯-A-磁悬浮"                    # 标准评分
  python tools/evolution/scorer.py --session "2026-数维杯-A-磁悬浮" --mode fast       # 快速扫描
  python tools/evolution/scorer.py --session "2026-数维杯-A-磁悬浮" --mode championship # 冠军模式
  python tools/evolution/scorer.py --session "2026-数维杯-A-磁悬浮" --layer L2         # 跨阶段回溯
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def _load_empirical(root: Path) -> dict:
    f = root / "references" / "empirical_baselines.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _pct_score(value: float, empirical: dict) -> dict:
    """基于 p25/p50/p75 的百分位评分"""
    p25 = empirical.get("p25", 0)
    p50 = empirical.get("p50", 0)
    p75 = empirical.get("p75", 0)
    vmin = empirical.get("min", 0)
    vmax = empirical.get("max", 1)

    if value <= vmin:
        return {"score": 0.1, "label": "低于 p25", "pct": "<25%"}
    if value >= vmax:
        return {"score": 1.0, "label": "高于 p75", "pct": ">75%"}

    if value <= p25:
        pct = 0.25 * (value - vmin) / max(p25 - vmin, 1)
        return {"score": max(0.1, pct), "label": "低于 p25", "pct": f"约{int(pct*100)}%"}
    if value <= p50:
        pct = 0.25 + 0.25 * (value - p25) / max(p50 - p25, 1)
        return {"score": 0.3 + 0.2 * (value - p25) / max(p50 - p25, 1), "label": "p25-p50", "pct": f"约{int(pct*100)}%"}
    if value <= p75:
        pct = 0.50 + 0.25 * (value - p50) / max(p75 - p50, 1)
        return {"score": 0.5 + 0.3 * (value - p50) / max(p75 - p50, 1), "label": "p50-p75", "pct": f"约{int(pct*100)}%"}
    pct = 0.75 + 0.25 * (value - p75) / max(vmax - p75, 1)
    return {"score": 0.8 + 0.2 * (value - p75) / max(vmax - p75, 1), "label": "高于 p75", "pct": f"约{int(pct*100)}%"}


# ── 维度定义 + 权重 ────────────────
# 权重来源于 references/empirical_baselines.json 的 quality_signals
# O奖论文特征: 92%有灵敏度分析, 95%有量化摘要, 78%有交叉验证, 85%有多模型对比
# 高权重维度（验证/摘要/灵敏度）直接对应O奖论文的突出特征

DIMENSIONS = {
    "abstract_quality":      {"weight": 0.12, "desc": "摘要质量(长度+5段式结构+量化结果)"},
    "structure_completeness": {"weight": 0.10, "desc": "结构完整性(章节数+假设+符号表)"},
    "visual_richness":       {"weight": 0.10, "desc": "视觉丰富度(图+表)"},
    "formula_rigor":         {"weight": 0.10, "desc": "公式严谨性(数量+编号+出处)"},
    "verification_complete": {"weight": 0.20, "desc": "验证完整度(每solver有verify+指标多样性)"},
    "sensitivity_depth":     {"weight": 0.10, "desc": "灵敏度深度(定量+多参数+图表)"},
    "model_diversity":       {"weight": 0.08, "desc": "模型多样性(多方案对比+不同家族)"},
    "academic_norm":         {"weight": 0.08, "desc": "学术规范(引用+语言+格式)"},
    "code_documentation":    {"weight": 0.06, "desc": "代码文档(README+注释+数据检查)"},
    "ai_flavor_penalty":     {"weight": 0.06, "desc": "AI味惩罚(低分=好)"},
}

TYPE_WEIGHTS = {
    "optimization": {"model_diversity": 1.4, "verification_complete": 1.3, "sensitivity_depth": 1.3},
    "regression":   {"verification_complete": 1.4, "formula_rigor": 1.2, "sensitivity_depth": 1.2},
    "prediction":   {"verification_complete": 1.4, "visual_richness": 1.2, "sensitivity_depth": 1.3},
    "evaluation":   {"academic_norm": 1.3, "model_diversity": 1.2, "visual_richness": 1.2},
    "ode":          {"formula_rigor": 1.5, "verification_complete": 1.3, "sensitivity_depth": 1.3},
    "classification":{"verification_complete": 1.4, "model_diversity": 1.2, "visual_richness": 1.2},
    "network":      {"model_diversity": 1.3, "verification_complete": 1.2, "visual_richness": 1.3},
    "statistics":   {"verification_complete": 1.4, "formula_rigor": 1.3, "visual_richness": 1.2},
    "simulation":   {"verification_complete": 1.3, "sensitivity_depth": 1.4, "model_diversity": 1.3},
}


def check_abstract_5seg(text: str) -> int:
    """检查摘要是否有5段式结构: 问题+方法+模型+结果+结论"""
    patterns = [
        r'(问题|背景|本文研究)',
        r'(方法|采用|利用|基于)',
        r'(模型|建立|构建|推导)',
        r'(结果|表明|显示|计算)',
        r'(结论|验证|表明.*有效)',
    ]
    return sum(1 for p in patterns if re.search(p, text))


def count_ai_flavor(text: str) -> int:
    """统计 AI 味短语出现次数 — 基于论文手去AI味写作指南的 40+ 标记"""
    ai_markers = [
        # 过度强调重要性
        "标志着", "重要的里程碑", "关键作用", "突显了其重要性", "反映了更广泛的",
        "为...奠定基础", "代表了一个转折点", "不可磨灭的印记", "根深蒂固",
        # 过度强调知名度
        "独立报道", "由领先专家撰写", "获得了学术界的高度认可",
        # 带-ing的肤浅分析
        "突显了", "凸显了", "充分展示了", "体现了", "做出了.*贡献",
        # 宣传性语言
        "突破性的", "令人惊叹的", "丰富的理论内涵", "强大的实践价值",
        "充满活力的", "深刻的",
        # 模糊归因
        "专家认为", "观察者指出", "一些批评者认为", "几个来源",
        # 公式化挑战
        "尽管.*面临几个挑战", "挑战与展望", "尽管存在这些挑战",
        # 高频AI词汇
        "首先.*其次.*最后", "值得注意的是", "综上所述", "显著地", "极大地",
        "不容忽视", "毋庸置疑", "显而易见", "众所周知", "这样一来",
        "进而", "换言之", "也就是说",
        "此外", "与此同", "日益", "越来越", "持续地", "极为", "高度",
        "广阔的", "关键的", "深入探讨", "复杂的", "有价值的",
        # 否定平行结构
        "不仅.*而且",
        # 虚假范围
        "从.*到.*从.*到",
        # 通用积极结论
        "前景光明", "令人振奋", "迈向卓越",
    ]
    count = 0
    for m in ai_markers:
        count += len(re.findall(m, text))
    return count


def score_session(root: Path, session_name: str, mode: str = "standard",
                  problem_type: str = "unknown") -> dict:
    session_dir = root / "sessions" / session_name
    if not session_dir.exists():
        return {"status": "error", "message": f"Session 不存在: {session_name}"}

    empirical = _load_empirical(root)
    dims_data = empirical.get("dims", {})
    main_tex = session_dir / "paper" / "main.tex"
    tex_content = main_tex.read_text(encoding="utf-8") if main_tex.exists() else ""

    scores = {}

    # 1. 摘要质量
    abstract = ""
    m = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', tex_content, re.DOTALL)
    if m:
        abstract = m.group(1).strip()
    alen = len(abstract)
    segs = check_abstract_5seg(abstract)
    has_quant = bool(re.search(r'[0-9]+\.[0-9]+', abstract))
    scores["abstract_quality"] = {
        "value": f"{alen}字/{segs}段/{'有' if has_quant else '无'}量化",
        "raw": alen,
        "score": min(1.0, (0.3 * _pct_score(alen, dims_data.get("abstract_chars", {})).get("score", 0.3)
                           + 0.4 * (segs / 5)
                           + 0.3 * (1.0 if has_quant else 0.3)))
    }

    # 2. 结构
    secs = len(re.findall(r'\\section\{', tex_content))
    subs = len(re.findall(r'\\subsection\{', tex_content))
    has_assumptions = "假设" in tex_content
    has_notations = "符号" in tex_content
    scores["structure_completeness"] = {
        "value": f"{secs}章/{subs}节",
        "score": min(1.0, (0.4 * _pct_score(secs, dims_data.get("main_section_count", {"p50": 6})).get("score", 0.5)
                           + 0.2 * min(1.0, subs / 15)
                           + 0.2 * (1.0 if has_assumptions else 0.2)
                           + 0.2 * (1.0 if has_notations else 0.2)))
    }

    # 3. 视觉丰富度
    figs = len(re.findall(r'\\includegraphics', tex_content))
    fig_dir = session_dir / "figures"
    if fig_dir.exists():
        figs = max(figs, len(list(fig_dir.glob("*"))))
    tbls = len(re.findall(r'\\begin\{table\}', tex_content)) + len(re.findall(r'\\begin\{tabular\}', tex_content))
    scores["visual_richness"] = {
        "value": f"{figs}图/{tbls}表",
        "score": min(1.0, 0.6 * _pct_score(figs, dims_data.get("figure_count", {"p50": 8})).get("score", 0.5)
                           + 0.4 * _pct_score(tbls, dims_data.get("table_count", {"p50": 6})).get("score", 0.5))
    }

    # 4. 公式
    eqs = len(re.findall(r'\\begin\{equation', tex_content)) + len(re.findall(r'\$\$', tex_content)) // 2
    has_numbered = len(re.findall(r'\\label\{eq:', tex_content)) if eqs > 0 else 0
    scores["formula_rigor"] = {
        "value": f"{eqs}个({'有' if has_numbered else '无'}编号)",
        "score": min(1.0, 0.6 * _pct_score(eqs, dims_data.get("formula_count", {"p50": 24})).get("score", 0.5)
                           + 0.4 * min(1.0, has_numbered / max(eqs, 1) * 2))
    }

    # 5. 验证完整度
    sdir = session_dir / "solvers"
    vdir = session_dir / "verifications"
    n_s = len(list(sdir.glob("*.py"))) if sdir.exists() else 0
    n_v = len(list(vdir.glob("*.py"))) if vdir.exists() else 0
    verify_ratio = n_v / max(n_s, 1)
    # 检查验证指标的多样性
    indicator_count = 0
    if vdir.exists():
        for vf in vdir.glob("*.py"):
            code = vf.read_text(encoding="utf-8")
            for ind in ["r2_score", "RMSE", "accuracy", "precision", "recall", "f1",
                       "assert", "shapiro", "cross_val", "durbin", "bootstrap"]:
                if ind in code:
                    indicator_count += 1
    scores["verification_complete"] = {
        "value": f"{n_v}/{n_s} scripts, {indicator_count} indicators",
        "score": min(1.0, 0.5 * verify_ratio + 0.5 * min(1.0, indicator_count / 10))
    }

    # 6. 灵敏度
    has_sensitivity = "灵敏度" in tex_content or "敏感性" in tex_content
    has_sens_code = False
    if sdir.exists():
        has_sens_code = any("sensitivity" in p.name.lower() for p in sdir.glob("*.py"))
    sens_chars = len(re.findall(r'灵敏度.*?。', tex_content, re.DOTALL)) * 100
    scores["sensitivity_depth"] = {
        "value": f"{'定量' if has_sens_code else '定性' if has_sensitivity else '无'}",
        "score": 1.0 if has_sens_code else (0.6 if has_sensitivity else 0.0)
    }

    # 7. 模型多样性
    if sdir.exists():
        codes = [p.read_text(encoding="utf-8") for p in sdir.glob("*.py")]
        families = set()
        for c in codes:
            if "scipy.optimize" in c: families.add("optimization")
            if "sklearn" in c: families.add("ml")
            if "solve_ivp" in c: families.add("ode")
            if "networkx" in c: families.add("network")
            if "statsmodels" in c: families.add("statistics")
        scores["model_diversity"] = {
            "value": f"{n_s} solvers, {len(families)} families",
            "score": min(1.0, 0.4 * min(1.0, n_s / 3) + 0.6 * min(1.0, len(families) / 3))
        }
    else:
        scores["model_diversity"] = {"value": "0", "score": 0.0}

    # 8. 学术规范
    refs = len(re.findall(r'\\bibitem\{', tex_content)) + len(re.findall(r'\\cite\{', tex_content)) // 3
    scores["academic_norm"] = {
        "value": f"{refs} refs",
        "score": min(1.0, _pct_score(refs, dims_data.get("reference_count", {"p50": 28})).get("score", 0.5))
    }

    # 9. 代码文档
    has_readme = (session_dir / "README.md").exists()
    readme_score = 0.0
    if has_readme:
        r = (session_dir / "README.md").read_text(encoding="utf-8")
        if "模型" in r: readme_score += 0.3
        if "算法" in r: readme_score += 0.3
        if "结果" in r: readme_score += 0.2
        if "教训" in r: readme_score += 0.2
    scores["code_documentation"] = {"value": f"README:{'Y' if has_readme else 'N'}", "score": readme_score if has_readme else 0.0}

    # 10. AI 味惩罚 (越低越好，所以 score = 1 - 惩罚)
    ai_count = count_ai_flavor(tex_content)
    ai_penalty = min(1.0, ai_count / 20)  # 20次以上=满分惩罚
    scores["ai_flavor_penalty"] = {"value": f"{ai_count}处AI味", "score": 1.0 - ai_penalty}

    # ── 加权计算 ──────────────────────────────────
    if mode == "fast":
        active_dims = ["abstract_quality", "structure_completeness", "verification_complete"]
    elif mode == "championship":
        active_dims = list(DIMENSIONS.keys())
    else:
        active_dims = list(DIMENSIONS.keys())

    tw = TYPE_WEIGHTS.get(problem_type, {})
    weighted = 0.0
    total_w = 0.0
    details = []
    for dim in active_dims:
        base_w = DIMENSIONS[dim]["weight"]
        w = base_w * tw.get(dim, 1.0)
        w = max(0.5, min(2.0, w))  # clamp to [0.5, 2.0]
        s = scores.get(dim, {}).get("score", 0)
        weighted += s * w
        total_w += w
        details.append({
            "dimension": dim,
            "desc": DIMENSIONS[dim]["desc"],
            "value": scores[dim]["value"],
            "score": round(s, 2),
            "weight": round(w, 2),
        })

    overall = round(weighted / total_w * 100) if total_w > 0 else 0
    grade = ("A+" if overall >= 90 else "A" if overall >= 80 else "B+" if overall >= 70
             else "B" if overall >= 60 else "C" if overall >= 45 else "D")

    # 层和
    layer_summary = {
        "L1_stage_score": overall,
        "L2_cross_stage_note": "需要跨阶段回溯检查一致性" if mode == "championship" else "skipped",
        "L3_panel_note": "5视角评审团" if mode == "championship" else "skipped",
        "L4_calibration_note": "校准检查" if mode == "championship" else "skipped",
    }

    improvements = []
    for d in details:
        if d["score"] < 0.4:
            improvements.append(f"[CRITICAL] {d['dimension']}({d['desc']}): {d['score']:.2f}")
        elif d["score"] < 0.65:
            improvements.append(f"[WARN] {d['dimension']}({d['desc']}): {d['score']:.2f}")

    # 双层基线: vs_paper + vs_self
    self_pct = _self_percentile(root, problem_type, overall)
    paper_pct = _paper_percentile(root, problem_type, overall)

    return {
        "session": session_name,
        "mode": mode,
        "problem_type": problem_type,
        "overall_score": overall,
        "grade": grade,
        "details": details,
        "layers": layer_summary,
        "improvements": improvements,
        "vs_paper_pct": paper_pct,
        "vs_self_pct": self_pct,
        "baseline_source": "91篇CUMCM获奖论文(2023-2025) + MCM/ICM O奖论文",
    }


def _self_percentile(root, problem_type, score):
    """自身历史 baseline: 在同类 session 中的百分位"""
    sessions_dir = root / "sessions"
    if not sessions_dir.exists():
        return "N/A (无历史)"
    scores = []
    for d in sessions_dir.iterdir():
        if not d.is_dir():
            continue
        ef = d / "eval_report.json"
        if not ef.exists():
            continue
        try:
            data = json.loads(ef.read_text(encoding="utf-8"))
        except:
            continue
        if data.get("problem_type", "") == problem_type:
            scores.append(data.get("overall_score", 0))
    if not scores:
        return "N/A (无同类题型)"
    better = sum(1 for s in scores if s < score)
    pct = round(better / len(scores) * 100)
    return f">{pct}% (优于 {better}/{len(scores)} 次自身历史)"


def _paper_percentile(root, problem_type, score):
    """论文统计 baseline: 在论文基线中的百分位"""
    # 从 empirical_baselines.json 读取 319 篇统计
    baseline_file = root / "references" / "empirical_baselines.json"
    if not baseline_file.exists():
        return "N/A (无基线)"
    try:
        bl = json.loads(baseline_file.read_text(encoding="utf-8"))
    except:
        return "N/A (基线无法读取)"
    dims = bl.get("dims", {})
    if not dims:
        return "N/A (基线无数据)"
    # 用 main_section_count 和 abstract_chars 的 p50 作为参考
    # 简化: 取所有维度的 p50 加权平均做参照
    paper_scores = []
    for dim_name, dim_data in dims.items():
        paper_scores.append(dim_data.get("p50", 0))
    if not paper_scores:
        return "N/A (基线数据不足)"
    baseline_avg = sum(paper_scores) / len(paper_scores)
    pct = ">p50" if score > baseline_avg else "<=p50"
    return f"{pct} (vs 论文基线中位数)"


def main():
    parser = argparse.ArgumentParser(description="论文评分引擎 v2")
    parser.add_argument("--session", required=True)
    parser.add_argument("--mode", default="standard", choices=["fast", "standard", "championship"])
    parser.add_argument("--problem-type", default="unknown")
    parser.add_argument("--no-save", action="store_true", help="不保存到文件（仅stdout）")
    args = parser.parse_args()

    root = _resolve_root()
    result = score_session(root, args.session, args.mode, args.problem_type)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 自动保存到 session 目录供 evolver 读取
    if not args.no_save and "status" not in result.get("error", ""):
        session_dir = root / "sessions" / args.session
        session_dir.mkdir(parents=True, exist_ok=True)
        report_path = session_dir / "eval_report.json"
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[已保存到 {report_path.relative_to(root)}]", file=sys.stderr)


if __name__ == "__main__":
    main()
