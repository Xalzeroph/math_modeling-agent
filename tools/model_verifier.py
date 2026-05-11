#!/usr/bin/env python3
"""模型验证协议 — 执行验证脚本并结构化输出结果"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "verifications").exists():
            return d
        d = d.parent
    return Path.cwd()


VERIFICATION_TEMPLATES = {
    "regression": '''"""回归模型验证脚本"""

import numpy as np
from scipy import stats
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score

# ============================================================
# 验证数据（请替换为实际数据）
# ============================================================
# y_true = ...
# y_pred = ...
# X = ...

checks = []

# [V-REG-1] 残差正态性检验
# residuals = y_true - y_pred
# stat, p = stats.shapiro(residuals)
# checks.append(("V-REG-1", p > 0.05, f"Shapiro-Wilk p={p:.4f}"))

# [V-REG-2] 异方差性检验 (Breusch-Pagan)
# from statsmodels.stats.diagnostic import het_breuschpagan
# _, p_bp, _, _ = het_breuschpagan(residuals, X)
# checks.append(("V-REG-2", p_bp > 0.05, f"Breusch-Pagan p={p_bp:.4f}"))

# [V-REG-3] 自相关检验 (Durbin-Watson)
# from statsmodels.stats.stattools import durbin_watson
# dw = durbin_watson(residuals)
# checks.append(("V-REG-3", 1.5 < dw < 2.5, f"Durbin-Watson={dw:.4f}"))

# [V-REG-4] 5折交叉验证
# cv_scores = cross_val_score(model, X, y_true, cv=5)
# checks.append(("V-REG-4", cv_scores.mean() > 0.7, f"CV R2={cv_scores.mean():.4f}"))

print("=" * 60)
print("VERIFICATION REPORT")
print("=" * 60)
all_pass = True
for check_id, result, detail in checks:
    status = "\\u2713 PASS" if result else "\\u2717 FAIL"
    print(f"  [{check_id}] {status}  {detail}")
    if not result:
        all_pass = False
print("=" * 60)
print(f"OVERALL: {'ALL PASS' if all_pass else 'FAILED — SEE ABOVE'}")
PASS = all_pass
''',

    "optimization": '''"""优化模型验证脚本"""

import numpy as np

checks = []

# [V-OPT-1] 约束可行性检验
# for i, (g, bound) in enumerate(constraints):
#     ok = g <= bound + 1e-6
#     checks.append((f"V-OPT-1-{i}", ok, f"约束{i}: {g:.6f} <= {bound}"))

# [V-OPT-2] 替代求解器交叉验证

# [V-OPT-3] 扰动测试

# [V-OPT-4] 灵敏度快检

print("=" * 60)
print("VERIFICATION REPORT")
print("=" * 60)
all_pass = True
for check_id, result, detail in checks:
    status = "\\u2713 PASS" if result else "\\u2717 FAIL"
    print(f"  [{check_id}] {status}  {detail}")
    if not result:
        all_pass = False
print("=" * 60)
print(f"OVERALL: {'ALL PASS' if all_pass else 'FAILED — SEE ABOVE'}")
PASS = all_pass
''',

    "ode": '''"""微分方程模型验证脚本"""

import numpy as np

checks = []

# [V-ODE-1] 守恒量验证

# [V-ODE-2] 边界条件检验

# [V-ODE-3] 网格收敛性

# [V-ODE-4] 解析解对比

print("=" * 60)
print("VERIFICATION REPORT")
print("=" * 60)
all_pass = True
for check_id, result, detail in checks:
    status = "\\u2713 PASS" if result else "\\u2717 FAIL"
    print(f"  [{check_id}] {status}  {detail}")
    if not result:
        all_pass = False
print("=" * 60)
print(f"OVERALL: {'ALL PASS' if all_pass else 'FAILED — SEE ABOVE'}")
PASS = all_pass
''',
}


def run_verification(root: Path, verify_script: str) -> dict:
    """运行验证脚本并解析结果"""
    script_path = root / verify_script
    if not script_path.exists():
        return {"status": "error", "message": f"验证脚本不存在: {verify_script}"}

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(root),
            capture_output=True, text=True,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "验证脚本执行超时 (120s)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

    output = proc.stdout
    stderr = proc.stderr

    # 解析结构化验证报告
    checks = []
    for line in output.split("\n"):
        m = re.match(r'\s*\[(V-\w+-\d+)\]\s*(✓|✗)\s*(PASS|FAIL)\s*(.+)', line)
        if m:
            check_id = m.group(1)
            # "✓" 是 UTF-8 编码
            passed = "PASS" in line and "FAIL" not in line[:60]
            checks.append({
                "id": check_id,
                "passed": passed,
                "detail": m.group(4).strip(),
            })

    # 备选：解析 "ALL PASS" 或 "FAILED"
    overall_pass = "ALL PASS" in output and "FAILED" not in output.split("OVERALL:")[-1].strip()

    return {
        "status": "ok",
        "script": verify_script,
        "exit_code": proc.returncode,
        "checks": checks,
        "pass_count": sum(1 for c in checks if c["passed"]),
        "fail_count": sum(1 for c in checks if not c["passed"]),
        "overall_pass": overall_pass,
        "stdout_tail": output[-500:] if len(output) > 500 else output,
        "stderr": stderr[-300:] if stderr and len(stderr) > 300 else stderr,
    }


def get_template(model_type: str) -> dict:
    tpl = VERIFICATION_TEMPLATES.get(model_type)
    if tpl:
        return {"status": "ok", "model_type": model_type, "template": tpl}
    return {"status": "error", "message": f"未知模型类型: {model_type}", "available": list(VERIFICATION_TEMPLATES.keys())}


def main():
    parser = argparse.ArgumentParser(description="模型验证协议")
    sub = parser.add_subparsers(dest="action", required=True)

    v = sub.add_parser("verify", help="运行验证脚本")
    v.add_argument("--script", required=True, help="验证脚本路径 (相对于项目根)")

    sub.add_parser("list", help="列出支持的模型类型")

    t = sub.add_parser("template", help="获取验证模板")
    t.add_argument("--type", required=True, dest="model_type", help="模型类型")

    args = parser.parse_args()
    root = _resolve_root()

    if args.action == "verify":
        result = run_verification(root, args.script)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "list":
        print(json.dumps({
            "available_types": list(VERIFICATION_TEMPLATES.keys())
        }, indent=2, ensure_ascii=False))

    elif args.action == "template":
        result = get_template(args.model_type)
        if result["status"] == "ok":
            print(result["template"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()
