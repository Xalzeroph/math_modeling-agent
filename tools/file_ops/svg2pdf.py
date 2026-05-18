#!/usr/bin/env python3
"""Convert all SVG figures to PDF for xelatex compilation.

Requires: pip install svglib reportlab
Usage: python tools/file_ops/svg2pdf.py --session "C题"
"""
import argparse
import sys
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
import os
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
except ImportError:
    print("ERROR: need svglib and reportlab. Run: pip install svglib reportlab")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert SVG figures to PDF for LaTeX")
    parser.add_argument("--session", required=True, help="Session name (e.g. C题)")
    args = parser.parse_args()

    session_dir = os.path.join(ROOT, "sessions", args.session)
    if not os.path.isdir(session_dir):
        # try fuzzy
        for d in os.listdir(os.path.join(ROOT, "sessions")):
            if args.session in d:
                session_dir = os.path.join(ROOT, "sessions", d)
                break

    fig_dir = os.path.join(session_dir, "figures")
    if not os.path.isdir(fig_dir):
        print(f"ERROR: figures/ not found at {fig_dir}")
        sys.exit(1)

    svg_files = glob.glob(os.path.join(fig_dir, "*.svg"))
    if not svg_files:
        print("No SVG files found")
        return

    for svg_path in svg_files:
        pdf_path = svg_path.replace(".svg", ".pdf")
        try:
            drawing = svg2rlg(svg_path)
            renderPDF.drawToFile(drawing, pdf_path)
            size_kb = os.path.getsize(pdf_path) // 1024
            print(f"  {os.path.basename(svg_path)} → {os.path.basename(pdf_path)} ({size_kb}KB)")
        except Exception as e:
            print(f"  FAILED {os.path.basename(svg_path)}: {e}")

    print(f"Done: {len(svg_files)} SVGs converted")


if __name__ == "__main__":
    main()
