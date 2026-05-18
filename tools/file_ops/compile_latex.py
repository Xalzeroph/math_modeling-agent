#!/usr/bin/env python3
"""LaTeX 编译器 — 支持 CUMCM (2-pass) 和 MCM/ICM (4-pass)"""

import argparse
import json
import os
import shutil
import subprocess
import sys
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from typing import Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def find_latex_engine() -> Optional[str]:
    """查找可用的 LaTeX 引擎"""
    for engine in ["xelatex", "pdflatex", "lualatex"]:
        if shutil.which(engine):
            return engine
    return None


def check_engine() -> dict:
    engine = find_latex_engine()
    return {
        "available": engine is not None,
        "engine": engine,
        "message": f"找到: {engine}" if engine else "未安装 LaTeX。请安装 TeX Live 或 MiKTeX。"
    }


def auto_copy_template(root: Path, mode: str = "cumcm") -> Optional[Path]:
    """如果 paper/main.tex 不存在，从模板复制"""
    paper_dir = root / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)

    tex_file = paper_dir / "main.tex"
    if tex_file.exists():
        return tex_file

    template_dir = root / "templates"
    template_map = {
        "cumcm": "latex_template.tex",
        "mcm": "mcm_template.tex",
        "icm": "mcm_template.tex",
    }
    tpl_name = template_map.get(mode, "latex_template.tex")
    tpl_path = template_dir / tpl_name

    if tpl_path.exists():
        content = tpl_path.read_text(encoding="utf-8")
        tex_file.write_text(content, encoding="utf-8")
        return tex_file
    return None


def compile_paper(root: Path, mode: str = "cumcm") -> dict:
    """编译 LaTeX 论文"""
    engine = find_latex_engine()
    if not engine:
        return {"success": False, "pdf_path": None, "error": "未找到 LaTeX 引擎。请安装 TeX Live 或 MiKTeX。"}

    tex_file = auto_copy_template(root, mode)
    if not tex_file:
        return {"success": False, "pdf_path": None, "error": "未找到 .tex 文件，模板复制也失败"}

    paper_dir = tex_file.parent
    tex_name = tex_file.name

    errors_output = []

    if mode == "mcm" or mode == "icm":
        # 4-pass: latex -> bibtex -> latex -> latex
        passes = [
            [engine, "-interaction=nonstopmode", tex_name],
            ["bibtex", tex_name.replace(".tex", "")],
            [engine, "-interaction=nonstopmode", tex_name],
            [engine, "-interaction=nonstopmode", tex_name],
        ]
    else:
        # 2-pass for CUMCM
        passes = [
            [engine, "-interaction=nonstopmode", tex_name],
            [engine, "-interaction=nonstopmode", tex_name],
        ]

    for i, cmd in enumerate(passes):
        proc = subprocess.run(
            cmd, cwd=str(paper_dir),
            capture_output=True, text=True,
            timeout=120
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined = stdout + "\n" + stderr

        # 错误检测
        # LaTeX Error 格式: "! LaTeX Error: ..." — 精确匹配避免误报 `!` 在正常文本中
        error_keywords = [
            "LaTeX Error:", "Fatal error", "Undefined control sequence",
            "Emergency stop", "!  ==> Fatal error",
        ]
        for kw in error_keywords:
            if kw in combined:
                lines = combined.split("\n")
                for j, line in enumerate(lines):
                    if kw in line:
                        ctx = lines[max(0, j-2):min(len(lines), j+3)]
                        errors_output.append(f"[Pass {i+1}] {kw}: " + " | ".join(ctx).strip()[:200])

        # 警告检测（不影响编译结果，但值得关注）
        warning_keywords = ["undefined references", "Citation", "Rerun to get"]
        for wk in warning_keywords:
            if wk in combined:
                lines = combined.split("\n")
                for j, line in enumerate(lines):
                    if wk in line:
                        errors_output.append(f"[Pass {i+1}] WARNING {wk}: " + line.strip()[:200])

    pdf_path = paper_dir / tex_name.replace(".tex", ".pdf")
    success = pdf_path.exists()

    return {
        "success": success,
        "engine": engine,
        "pdf_path": str(pdf_path.relative_to(root)) if success else None,
        "passes": len(passes),
        "errors": errors_output if errors_output else None,
        "message": "编译成功" if success else f"编译失败，{len(errors_output)} 个错误"
    }


def main():
    parser = argparse.ArgumentParser(description="LaTeX 编译器")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("check", help="检查 LaTeX 是否安装")

    c = sub.add_parser("compile", help="编译论文")
    c.add_argument("--mode", default="cumcm", choices=["cumcm", "mcm", "icm"])

    args = parser.parse_args()
    root = _resolve_root()

    if args.action == "check":
        print(json.dumps(check_engine(), indent=2, ensure_ascii=False))
    elif args.action == "compile":
        result = compile_paper(root, args.mode)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("errors"):
            print("\n⚠ 警告：编译中检测到以下问题：", file=sys.stderr)
            for e in result["errors"]:
                print(f"  {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
