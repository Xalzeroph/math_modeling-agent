#!/usr/bin/env python3
"""代码自修复引擎 — 运行→解析错误→生成修复提示→重试(最多4轮)

用法:
  python tools/auto_fix.py --script solvers/problem1.py
  python tools/auto_fix.py --verify verifications/verify_problem1.py
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "tools" / "auto_fix.py").exists():
            return d
        d = d.parent
    return Path.cwd()


def _find_script(root: Path, name: str) -> Path:
    """在 sessions 下找第一个匹配的脚本"""
    for py in root.rglob(name):
        return py
    return Path(name)


def run_script(script_path: Path, timeout: int = 60) -> dict:
    """运行脚本并解析输出"""
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(script_path.parent)
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "执行超时", "error_type": "timeout"}
    except Exception as e:
        return {"success": False, "error": str(e), "error_type": "runtime"}

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    # 检测常见错误模式
    patterns = [
        (r"FileNotFoundError.*['\"](.+)['\"]", "file_missing"),
        (r"ImportError.*No module named '(\w+)'", "import_error"),
        (r"ModuleNotFoundError.*No module named '(\w+)'", "import_error"),
        (r"KeyError.*['\"](.+)['\"]", "key_error"),
        (r"ValueError.*: (.+)", "value_error"),
        (r"TypeError.*: (.+)", "type_error"),
        (r"NameError.*name '(\w+)' is not defined", "name_error"),
        (r"AttributeError.*'(\w+)' object has no attribute '(\w+)'", "attr_error"),
        (r"IndexError.*list index out of range", "index_error"),
        (r"MemoryError", "memory_error"),
        (r"SyntaxError.*: (.+)", "syntax_error"),
    ]

    errors = []
    for output in [stderr, stdout]:
        for pat, etype in patterns:
            m = re.search(pat, output)
            if m:
                errors.append({
                    "type": etype,
                    "message": m.group(0)[:200],
                    "detail": m.groups(),
                    "source": "stderr" if output is stderr else "stdout",
                })

    return {
        "success": proc.returncode == 0 and not errors,
        "returncode": proc.returncode,
        "errors": errors,
        "stdout_tail": stdout[-500:] if stdout else "",
        "stderr_tail": stderr[-500:] if stderr else "",
    }


def generate_fix_hint(errors: list) -> str:
    """根据错误类型生成修复提示"""
    hints = {
        "file_missing": "文件未找到。检查文件路径是否正确，数据文件是否在 data/ 目录下。",
        "import_error": "缺少依赖包。运行: pip install <missing_package>。检查包名拼写。",
        "key_error": "字典/DataFrame中缺少指定列名。检查列名拼写，或先打印 df.columns 确认列名。",
        "value_error": "值错误。检查输入数据的形状和类型是否与函数期望一致。",
        "type_error": "类型错误。检查变量类型是否正确（如 str vs int）。",
        "name_error": "变量未定义。检查变量名拼写，确认变量在使用前已赋值。",
        "attr_error": "属性不存在。检查对象类型，确认方法/属性名正确。",
        "index_error": "索引越界。检查列表/数组长度，确认索引在有效范围内。",
        "memory_error": "内存不足。尝试减小数据量、使用生成器、或分块处理。",
        "syntax_error": "语法错误。检查代码语法。",
        "timeout": "执行超时。检查是否有死循环，或增加 timeout 参数。",
    }
    result = ["## 代码自修复分析\n"]
    result.append(f"发现 {len(errors)} 个错误:\n")
    for e in errors:
        etype = e.get("type", "unknown")
        hint = hints.get(etype, "未知错误类型，需人工分析")
        result.append(f"- **{etype}**: {e.get('message', '')[:150]}")
        result.append(f"  修复建议: {hint}")
    return "\n".join(result)


def auto_fix_cycle(root: Path, script_name: str, max_rounds: int = 4) -> dict:
    """完整的自动修复循环"""
    script = _find_script(root, script_name)
    history = []

    for round_num in range(1, max_rounds + 1):
        result = run_script(script)
        result["round"] = round_num
        history.append(result)

        if result["success"]:
            return {
                "status": "ok",
                "rounds": round_num,
                "script": str(script),
                "history": history,
                "message": f"第 {round_num} 轮运行成功",
            }

        # 生成本轮修复提示
        hint = generate_fix_hint(result.get("errors", []))
        result["fix_hint"] = hint

        # 如果是 import 错误，自动安装依赖
        for e in result.get("errors", []):
            if e["type"] == "import_error" and e["detail"]:
                pkg = e["detail"][0]
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                                  capture_output=True, timeout=60)
                    result["auto_install"] = pkg
                except Exception:
                    pass

    return {
        "status": "failed",
        "rounds": max_rounds,
        "script": str(script),
        "history": history,
        "message": f"{max_rounds} 轮自动修复后仍有错误，需人工介入",
        "final_hint": generate_fix_hint(history[-1].get("errors", [])) if history else "",
    }


def main():
    parser = argparse.ArgumentParser(description="代码自修复引擎")
    parser.add_argument("--script", required=True, help="脚本路径或文件名")
    parser.add_argument("--max-rounds", type=int, default=4)
    parser.add_argument("--verify", action="store_true", help="运行验证脚本")

    args = parser.parse_args()
    root = _resolve_root()

    if args.verify:
        script = _find_script(root, args.script)
        result = run_script(script)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        result = auto_fix_cycle(root, args.script, args.max_rounds)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
