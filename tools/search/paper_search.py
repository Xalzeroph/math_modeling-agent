#!/usr/bin/env python3
"""学术论文搜索 — 多源聚合: OpenAlex + arXiv + Semantic Scholar"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from typing import List, Optional

# ── OpenAlex ──────────────────────────────────────────────────


def search_openalex(query: str, limit: int = 8, email: Optional[str] = None) -> List[dict]:
    """搜索 OpenAlex（免费 API，无需 key）"""
    params = {
        "search": query,
        "per_page": min(limit, 200),
        "sort": "cited_by_count:desc",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", f"mailto:{email or 'anonymous@example.com'}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return [{"source": "openalex", "error": str(e)}]

    results = []
    for w in data.get("results", [])[:limit]:
        # 摘要重建
        abstract = ""
        if w.get("abstract_inverted_index"):
            idx = w["abstract_inverted_index"]
            words = sorted(idx.items(), key=lambda x: x[1][0] if x[1] else 0)
            abstract = " ".join(w for w, _ in words)

        results.append({
            "source": "openalex",
            "title": w.get("title", ""),
            "doi": w.get("doi", ""),
            "year": w.get("publication_year"),
            "cited_by": w.get("cited_by_count", 0),
            "abstract": abstract[:500],
            "authors": [a["author"]["display_name"] for a in w.get("authorships", [])[:5]],
            "url": w.get("primary_location", {}).get("landing_page_url", ""),
        })
    return results


# ── arXiv ─────────────────────────────────────────────────────

def search_arxiv(query: str, limit: int = 8) -> List[dict]:
    """搜索 arXiv API（免费，无需 key）"""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 30),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            raw = resp.read().decode()
    except Exception as e:
        return [{"source": "arxiv", "error": str(e)}]

    # 简易 XML 解析（避免依赖 lxml）
    results = []
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root_elem = ET.fromstring(raw)
    except ET.ParseError:
        return results

    for entry in root_elem.findall("a:entry", ns):
        title_elem = entry.find("a:title", ns)
        title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

        summary_elem = entry.find("a:summary", ns)
        abstract = summary_elem.text.strip().replace("\n", " ")[:500] if summary_elem is not None else ""

        id_text = ""
        id_elem = entry.find("a:id", ns)
        if id_elem is not None:
            id_text = id_elem.text.strip()

        arxiv_id = id_text.split("/abs/")[-1] if "/abs/" in id_text else id_text

        authors = []
        for author in entry.findall("a:author", ns):
            name_elem = author.find("a:name", ns)
            if name_elem is not None:
                authors.append(name_elem.text.strip())

        published_elem = entry.find("a:published", ns)
        year = published_elem.text[:4] if published_elem is not None else ""

        results.append({
            "source": "arxiv",
            "title": title,
            "arxiv_id": arxiv_id,
            "year": year,
            "abstract": abstract,
            "authors": authors[:5],
            "url": f"https://arxiv.org/abs/{arxiv_id}",
        })

    return results[:limit]


# ── Semantic Scholar ──────────────────────────────────────────

def search_semantic_scholar(query: str, limit: int = 8, api_key: Optional[str] = None) -> List[dict]:
    """搜索 Semantic Scholar Academic Graph API（需免费 key）"""
    if not api_key:
        api_key = ""

    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,year,abstract,authors,externalIds,citationCount,url",
    }
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    if api_key:
        req.add_header("x-api-key", api_key)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return [{"source": "semantic_scholar", "error": str(e)}]

    results = []
    for p in data.get("data", []):
        results.append({
            "source": "semantic_scholar",
            "title": p.get("title", ""),
            "doi": p.get("externalIds", {}).get("DOI", ""),
            "arxiv_id": p.get("externalIds", {}).get("ArXiv", ""),
            "year": p.get("year"),
            "cited_by": p.get("citationCount", 0),
            "abstract": (p.get("abstract") or "")[:500],
            "authors": [a.get("name", "") for a in p.get("authors", [])[:5]],
            "url": p.get("url", ""),
        })
    return results


# ── 统一入口 ─────────────────────────────────────────────────

def search_papers(query: str, limit: int = 10, sources: Optional[List[str]] = None,
                  email: Optional[str] = None, s2_api_key: Optional[str] = None) -> List[dict]:
    """统一搜索入口，按 sources 指定顺序尝试"""
    if sources is None:
        sources = ["openalex", "arxiv"]

    all_results = []
    seen_titles = set()

    for src in sources:
        if src == "openalex":
            r = search_openalex(query, limit, email)
        elif src == "arxiv":
            r = search_arxiv(query, limit)
        elif src == "semantic_scholar":
            r = search_semantic_scholar(query, limit, s2_api_key)
        else:
            continue

        for item in r:
            title_key = item.get("title", "").lower().strip()[:80]
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                all_results.append(item)

        if len(all_results) >= limit:
            break

    return all_results[:limit]


def main():
    parser = argparse.ArgumentParser(description="学术论文搜索")
    parser.add_argument("--query", required=True, help="搜索关键词")
    parser.add_argument("--sources", default="openalex,arxiv",
                        help="来源(逗号分隔): openalex,arxiv,semantic_scholar")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--email", default="", help="OpenAlex polite pool email")
    parser.add_argument("--s2-key", default="", help="Semantic Scholar API key")

    args = parser.parse_args()
    sources = [s.strip() for s in args.sources.split(",")]

    # 尝试从 config.json 获取默认配置
    config_file = Path.cwd() / "config.json"
    email = args.email
    s2_key = args.s2_key
    if config_file.exists() and (not email or not s2_key):
        try:
            c = json.loads(config_file.read_text(encoding="utf-8"))
            if not email:
                email = c.get("email", "")
            if not s2_key:
                s2_key = c.get("semantic_scholar_api_key", "")
        except Exception:
            pass

    results = search_papers(args.query, args.limit, sources, email, s2_key)
    output = json.dumps({"query": args.query, "count": len(results), "results": results},
                        indent=2, ensure_ascii=False)
    # Windows GBK 兼容：无法编码的字符替换为 ?
    try:
        print(output)
    except UnicodeEncodeError:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        print(output)


if __name__ == "__main__":
    from pathlib import Path
    main()
