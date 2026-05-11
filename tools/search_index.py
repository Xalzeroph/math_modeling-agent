#!/usr/bin/env python3
"""本地搜索索引 — 预建密钥词索引，加速知识检索"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import List


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


RE_WORD = re.compile(r'[\w\u4e00-\u9fff]+')  # 匹配英文词和中文字符


def _tokenize(text: str) -> List[str]:
    tokens = []
    for match in RE_WORD.finditer(text.lower()):
        w = match.group()
        if len(w) >= 2:  # 跳过单字符
            tokens.append(w)
    return tokens


def _file_hash(path: Path) -> str:
    return hashlib.md5(str(path).encode()).hexdigest()[:8]


def build_index(root: Path) -> dict:
    """扫描 algorithms/ 和 references/ 建立逆向索引"""
    index = {
        "version": 1,
        "root": str(root),
        "entries": {},
        "inverted": {},  # token -> [entry_ids]
    }

    # 索引算法文档
    for md in sorted((root / "algorithms").glob("*.md")):
        try:
            content = md.read_text(encoding="utf-8")
        except Exception:
            continue
        eid = _file_hash(md)
        title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else md.stem

        tokens = _tokenize(title + " " + content[:3000])
        index["entries"][eid] = {
            "type": "algorithm",
            "file": str(md.relative_to(root)),
            "title": title,
            "token_count": len(tokens),
        }
        for t in set(tokens):
            index["inverted"].setdefault(t, []).append(eid)

    # 索引 O奖论文
    ref_dir = root / "references"
    if ref_dir.exists():
        for pdf in sorted(ref_dir.rglob("*.pdf")):
            eid = _file_hash(pdf)
            category = pdf.parent.name
            name = pdf.stem
            title = f"{category} {name}"
            tokens = _tokenize(title.lower())
            index["entries"][eid] = {
                "type": "paper",
                "file": str(pdf.relative_to(root)),
                "title": title,
                "category": category,
                "token_count": len(tokens),
            }
            for t in set(tokens):
                index["inverted"].setdefault(t, []).append(eid)

    return index


def query_index(index: dict, query: str, top_k: int = 10) -> List[dict]:
    """查询索引"""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scores: dict[str, float] = {}
    for qt in query_tokens:
        for eid in index.get("inverted", {}).get(qt, []):
            scores[eid] = scores.get(eid, 0) + 1.0

    # 按分数排序
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for eid, score in ranked:
        entry = index.get("entries", {}).get(eid, {}).copy()
        entry["score"] = score
        results.append(entry)

    return results


def main():
    parser = argparse.ArgumentParser(description="本地搜索索引")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("build", help="构建索引")

    q = sub.add_parser("query", help="查询索引")
    q.add_argument("--query", required=True, help="搜索关键词")
    q.add_argument("--top-k", type=int, default=10)

    args = parser.parse_args()
    root = _resolve_root()
    index_file = root / "memory" / "search_index.json"

    if args.action == "build":
        index = build_index(root)
        index_file.parent.mkdir(parents=True, exist_ok=True)
        index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({
            "status": "ok",
            "entries": len(index["entries"]),
            "terms": len(index["inverted"]),
            "file": str(index_file.relative_to(root)),
        }, ensure_ascii=False))

    elif args.action == "query":
        if not index_file.exists():
            print(json.dumps({"status": "error", "message": "索引不存在，请先运行 build"}, ensure_ascii=False))
            sys.exit(1)
        index = json.loads(index_file.read_text(encoding="utf-8"))
        results = query_index(index, args.query, args.top_k)
        print(json.dumps({"status": "ok", "results": results, "count": len(results)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
