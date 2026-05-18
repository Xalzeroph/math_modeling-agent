#!/usr/bin/env python3
"""PDF 文本/表格提取 — 用于读取题目和参考论文"""

import argparse
import json
import sys
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from typing import List, Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def extract_text(pdf_path: Path) -> dict:
    """提取 PDF 文本"""
    if not pdf_path.exists():
        return {"status": "error", "message": f"文件不存在: {pdf_path}"}

    try:
        import pdfplumber
    except ImportError:
        # 回退到 PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            return {"status": "ok", "pages": len(reader.pages), "text": text[:10000], "method": "PyPDF2"}
        except ImportError:
            return {"status": "error", "message": "需要安装 pdfplumber: pip install pdfplumber (或 PyPDF2)"}

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            text_parts = []
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    text_parts.append(f"--- Page {i+1} ---\n{t}")
            return {
                "status": "ok",
                "pages": len(pdf.pages),
                "text": "\n\n".join(text_parts)[:10000],  # 限制输出长度
                "method": "pdfplumber"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def extract_tables(pdf_path: Path, page_range: Optional[str] = None) -> dict:
    """提取 PDF 表格"""
    if not pdf_path.exists():
        return {"status": "error", "message": f"文件不存在: {pdf_path}"}

    try:
        import pdfplumber
    except ImportError:
        return {"status": "error", "message": "需要安装 pdfplumber: pip install pdfplumber"}

    pages_to_extract = None
    if page_range:
        parts = page_range.split("-")
        if len(parts) == 2:
            pages_to_extract = range(int(parts[0]) - 1, int(parts[1]))
        else:
            pages_to_extract = [int(parts[0]) - 1]

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            all_tables = []
            target_pages = [pdf.pages[i] for i in (pages_to_extract or range(len(pdf.pages)))
                          if i < len(pdf.pages)]
            for i, page in enumerate(target_pages):
                tables = page.extract_tables()
                for j, table in enumerate(tables):
                    if table:
                        all_tables.append({
                            "page": (pages_to_extract[i] if pages_to_extract else i) + 1,
                            "table_index": j,
                            "rows": len(table),
                            "cols": len(table[0]) if table and table[0] else 0,
                            "data": table[:20],  # 限制行数
                        })
            return {"status": "ok", "tables": all_tables, "total": len(all_tables)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_pdfs(root: Path) -> List[dict]:
    """列出所有 PDF 文件"""
    ref_dir = root / "references"
    if not ref_dir.exists():
        return []

    pdfs = []
    for pdf in sorted(ref_dir.rglob("*.pdf")):
        pdfs.append({
            "path": str(pdf.relative_to(root)),
            "name": pdf.stem,
            "category": pdf.parent.name,
            "size_kb": pdf.stat().st_size // 1024,
        })
    return pdfs


def main():
    parser = argparse.ArgumentParser(description="PDF 文本/表格提取")
    sub = parser.add_subparsers(dest="action", required=True)

    t = sub.add_parser("extract", help="提取文本")
    t.add_argument("--file", required=True, help="PDF 文件路径")

    tb = sub.add_parser("tables", help="提取表格")
    tb.add_argument("--file", required=True, help="PDF 文件路径")
    tb.add_argument("--pages", default=None, help="页码范围 (如 1-3)")

    sub.add_parser("list", help="列出所有 PDF")

    args = parser.parse_args()
    root = _resolve_root()

    if args.action == "extract":
        pdf_path = root / args.file if not Path(args.file).is_absolute() else Path(args.file)
        result = extract_text(pdf_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "tables":
        pdf_path = root / args.file if not Path(args.file).is_absolute() else Path(args.file)
        result = extract_tables(pdf_path, args.pages)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "list":
        pdfs = list_pdfs(root)
        print(json.dumps({"status": "ok", "total": len(pdfs), "files": pdfs}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
